"""Near-duplicate detection and per-author word counts (BOM-12).

Pre-registration 4.3: *"Reprints and later editions are collapsed to the earliest edition by
MinHash similarity above 0.8 on 5-gram shingles."* Every parameter comes from
``corpus.dedup`` in the config; none is hard-coded here.

**Nothing is deleted.** Duplicates are labelled, with each group's earliest member marked as the
keeper, because `CLAUDE.md` says flag rather than delete and because BOM-40's multiverse varies
corpus-level choices, which is impossible if an earlier stage has already thrown rows away.
Stages that want one row per work filter on ``is_keeper`` themselves.

**No model is involved.** MinHash is a deterministic estimator: same input and seed, same output,
always. Nothing is trained, so 4.2's sealing of the Book of Mormon does not arise. Deterministic
is not the same as exact -- signature agreement estimates Jaccard with error around 1/sqrt(perms)
-- but it errs identically on every run, which is what reproducibility needs.

**One pass, not two.** Word counts and signatures are computed together while a document is in
memory. Both stages would otherwise read the same ~150-200 GB, and the word count is nearly free
because it is I/O-bound while hashing is CPU-bound.

Shingles are hashed in a stream with a running minimum per permutation, rather than materialised
as a set. A large Internet Archive item can carry 500,000 shingles, and eight workers each
holding one would not fit in 16 GB.

Measured on the mini (10 cores): read and count at 113 MB/s, signatures at about 0.02s a
document, so roughly 25-35 minutes for the corpus across 8 workers.

Usage::

    python -m metadata.dedup signatures          # the parallel pass, resumable by shard
    python -m metadata.dedup pairs               # LSH over the signatures, writes duplicates
    python -m metadata.dedup authors             # word counts per normalised author
    python -m metadata.dedup metadata            # Amendment 6's pass by title, author, year
    python -m metadata.dedup combine             # one keeper flag from both passes

Each command takes ``--text raw`` (the default, the catalog's text as fetched: BOM-12's run) or
``--text normalized`` (BOM-14's cleaning plus BOM-15's spelling normalisation, the order 4.3
lists). The two write to separate files, so both results stay published side by side: raw OCR
of the same book from two sources rarely reaches 0.8 similarity (``DEDUP.md``), and the second
run measures how much cleaning and normalising recover.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import sha256_of_config

CATALOG = Path("data/catalog/catalog.parquet")
SIG_DIR = Path("data/catalog/signatures")
DUPES = Path("data/catalog/duplicates.parquet")
AUTHORS = Path("data/catalog/author_words.parquet")

# per text variant: signatures dir, duplicates table, author totals
OUTPUTS = {
    "raw": (SIG_DIR, DUPES, AUTHORS),
    "normalized": (
        Path("data/catalog/signatures_normalized"),
        Path("data/catalog/duplicates_normalized.parquet"),
        Path("data/catalog/author_words_normalized.parquet"),
    ),
}

PERMS = 128
SHARD = 5000
_MERSENNE = (1 << 61) - 1

SIG_SCHEMA = pa.schema(
    [
        ("work_id", pa.string()),
        ("words", pa.int64()),
        ("chars", pa.int64()),
        ("shingles", pa.int64()),
        ("signature", pa.list_(pa.int64(), PERMS)),
    ]
)

DUPE_SCHEMA = pa.schema(
    [
        ("work_id", pa.string()),
        ("group_id", pa.int64()),
        ("group_size", pa.int64()),
        ("is_keeper", pa.bool_()),
        ("best_similarity", pa.float64()),
    ]
)


def _permutations() -> tuple[np.ndarray, np.ndarray]:
    """Fixed hash permutations. Seeded from the config so a rerun reproduces them exactly."""
    rs = np.random.RandomState(load_config()["seed"] % (2**32))
    a = rs.randint(1, _MERSENNE, PERMS, dtype=np.int64)
    b = rs.randint(0, _MERSENNE, PERMS, dtype=np.int64)
    return a, b


def signature_of(text: str, k: int, a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, int, int]:
    """MinHash signature, word count and shingle count, in one streaming pass."""
    words = text.split()
    n = len(words)
    if n < k:
        return np.full(PERMS, _MERSENNE, dtype=np.int64), n, 0
    best = np.full(PERMS, _MERSENNE, dtype=np.int64)
    batch: list[int] = []
    shingles = n - k + 1
    for i in range(shingles):
        s = " ".join(words[i : i + k]).encode("utf-8", "replace")
        batch.append(int.from_bytes(hashlib.blake2b(s, digest_size=8).digest(), "big") & 0x7FFFFFFF)
        if len(batch) >= 4096:
            h = np.array(batch, dtype=np.int64)
            np.minimum(
                best, ((a[:, None] * h[None, :] + b[:, None]) % _MERSENNE).min(axis=1), out=best
            )
            batch.clear()
    if batch:
        h = np.array(batch, dtype=np.int64)
        np.minimum(best, ((a[:, None] * h[None, :] + b[:, None]) % _MERSENNE).min(axis=1), out=best)
    return best, n, shingles


def _text_path(row: dict, text: str) -> str:
    if text == "raw":
        return row["text_path"]
    from ocr_fix.normalize import norm_path

    return str(norm_path(row))


def _do_shard(job: tuple[int, list[tuple[str, str]], int, Path]) -> tuple[int, int]:
    """Worker: one shard of (work_id, path) to one parquet file. Idempotent."""
    idx, items, k, sig_dir = job
    out = sig_dir / f"{idx:05d}.parquet"
    if out.exists():
        return idx, 0
    a, b = _permutations()
    rows = []
    for work_id, path in items:
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        sig, words, shingles = signature_of(text, k, a, b)
        rows.append(
            {
                "work_id": work_id,
                "words": words,
                "chars": len(text),
                "shingles": shingles,
                "signature": sig.tolist(),
            }
        )
    tmp = out.with_suffix(".parquet.tmp")
    pq.write_table(
        pa.Table.from_pylist(rows, schema=SIG_SCHEMA).replace_schema_metadata(
            {"config_sha256": sha256_of_config()}
        ),
        tmp,
    )
    tmp.replace(out)
    return idx, len(rows)


def signatures(workers: int, limit: int | None, text: str = "raw") -> int:
    sig_dir = OUTPUTS[text][0]
    cfg = load_config()
    k = cfg["corpus"]["dedup"]["shingle"]
    rows = [r for r in pq.read_table(CATALOG).to_pylist() if r["has_text"]]
    if limit:
        rows = rows[:limit]
    sig_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for i in range(0, len(rows), SHARD):
        chunk = [(r["work_id"], _text_path(r, text)) for r in rows[i : i + SHARD]]
        jobs.append((i // SHARD, chunk, k, sig_dir))
    todo = [j for j in jobs if not (sig_dir / f"{j[0]:05d}.parquet").exists()]
    print(f"{len(rows):,} docs, {len(jobs):,} shards, {len(todo):,} to do, {workers} workers")
    if not todo:
        return 0
    start = time.time()
    done = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for _idx, _n in pool.map(_do_shard, todo):
            done += 1
            if done % 5 == 0 or done == len(todo):
                el = time.time() - start
                left = (len(todo) - done) * el / done / 60
                print(
                    f"  {done}/{len(todo)} shards  {el / 60:.1f}m elapsed  ~{left:.0f}m left",
                    flush=True,
                )
    print(f"signatures written to {sig_dir}")
    return 0


def _load_signatures(sig_dir: Path = SIG_DIR) -> tuple[list[str], np.ndarray]:
    files = sorted(sig_dir.glob("*.parquet"))
    if not files:
        raise SystemExit(f"no signatures under {sig_dir}; run `signatures` first")
    ids: list[str] = []
    sigs: list[np.ndarray] = []
    for f in files:
        t = pq.read_table(f)
        ids.extend(t.column("work_id").to_pylist())
        sigs.append(np.array(t.column("signature").to_pylist(), dtype=np.int64))
    return ids, np.vstack(sigs)


def pairs(bucket_cap: int, text: str = "raw") -> int:
    """LSH over the signatures, then an exact signature check at the registered threshold.

    LSH is tuned for recall rather than precision -- 16 bands of 8 rows catches pairs from about
    0.71 similarity upward -- and every candidate is then verified against the real threshold.
    Buckets larger than ``bucket_cap`` are reported and skipped rather than silently dropped;
    newspaper pages share enough boilerplate to produce very large buckets.
    """
    cfg = load_config()
    thresh = cfg["corpus"]["dedup"]["threshold"]
    sig_dir, dupes, _ = OUTPUTS[text]
    ids, sigs = _load_signatures(sig_dir)
    print(f"{len(ids):,} signatures loaded, threshold {thresh}")

    bands, rows_per = 16, PERMS // 16
    candidates: set[tuple[int, int]] = set()
    skipped = 0
    for band in range(bands):
        block = sigs[:, band * rows_per : (band + 1) * rows_per]
        buckets: dict[bytes, list[int]] = defaultdict(list)
        for i, row in enumerate(block):
            buckets[row.tobytes()].append(i)
        for members in buckets.values():
            if len(members) < 2:
                continue
            if len(members) > bucket_cap:
                skipped += 1
                continue
            for x in range(len(members)):
                for y in range(x + 1, len(members)):
                    candidates.add((members[x], members[y]))
    print(f"{len(candidates):,} candidate pairs; {skipped:,} buckets over cap {bucket_cap:,}")

    # Union-find over verified pairs.
    parent = list(range(len(ids)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    verified = 0
    best: dict[int, float] = defaultdict(float)
    for i, j in candidates:
        sim = float((sigs[i] == sigs[j]).mean())
        if sim >= thresh:
            verified += 1
            best[i] = max(best[i], sim)
            best[j] = max(best[j], sim)
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj
    print(f"{verified:,} pairs at or above {thresh}")

    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(ids)):
        r = find(i)
        if best[i]:
            groups[r].append(i)

    cat = {r["work_id"]: r for r in pq.read_table(CATALOG).to_pylist()}
    out = []
    for gid, (_, members) in enumerate(sorted(groups.items())):
        if len(members) < 2:
            continue
        keeper = min(members, key=lambda i: (cat[ids[i]]["year"] or 9999, ids[i]))
        for i in members:
            out.append(
                {
                    "work_id": ids[i],
                    "group_id": gid,
                    "group_size": len(members),
                    "is_keeper": i == keeper,
                    "best_similarity": best[i],
                }
            )
    pq.write_table(
        pa.Table.from_pylist(out, schema=DUPE_SCHEMA).replace_schema_metadata(
            {"config_sha256": sha256_of_config()}
        ),
        dupes,
    )
    ngroups = len({r["group_id"] for r in out})
    print(f"{ngroups:,} duplicate groups covering {len(out):,} works -> {dupes}")
    print(f"nothing deleted; {len(out) - ngroups:,} rows are non-keepers and are flagged only")
    return 0


def authors(text: str = "raw") -> int:
    """Word counts per normalised author, so BOM-39 has units with known sample sizes."""
    sig_dir, dupes, out_path = OUTPUTS[text]
    words: dict[str, int] = {}
    for f in sorted(sig_dir.glob("*.parquet")):
        t = pq.read_table(f, columns=["work_id", "words"])
        ws = t.column("work_id").to_pylist()
        ns = t.column("words").to_pylist()
        for wid, n in zip(ws, ns, strict=True):
            words[wid] = n
    cat = [r for r in pq.read_table(CATALOG).to_pylist() if r["has_text"]]
    keep = set()
    if dupes.exists():
        d = pq.read_table(dupes).to_pylist()
        drop = {r["work_id"] for r in d if not r["is_keeper"]}
        keep = {r["work_id"] for r in cat} - drop
        print(f"excluding {len(drop):,} flagged non-keepers from author totals")
    else:
        keep = {r["work_id"] for r in cat}
        print("no duplicates file yet; author totals include every work", file=sys.stderr)

    agg: dict[str, dict] = {}
    for r in cat:
        if r["work_id"] not in keep or not r["author_norm"]:
            continue
        a = agg.setdefault(r["author_norm"], {"works": 0, "words": 0, "earliest": None})
        a["works"] += 1
        a["words"] += words.get(r["work_id"], 0)
        y = r["year"]
        if y and (a["earliest"] is None or y < a["earliest"]):
            a["earliest"] = y
    out = [
        {"author_norm": k, "works": v["works"], "words": v["words"], "earliest_year": v["earliest"]}
        for k, v in sorted(agg.items(), key=lambda kv: -kv[1]["words"])
    ]
    schema = pa.schema(
        [
            ("author_norm", pa.string()),
            ("works", pa.int64()),
            ("words", pa.int64()),
            ("earliest_year", pa.int32()),
        ]
    )
    pq.write_table(
        pa.Table.from_pylist(out, schema=schema).replace_schema_metadata(
            {"config_sha256": sha256_of_config()}
        ),
        out_path,
    )
    big = sum(1 for r in out if r["words"] >= 10000)
    print(f"{len(out):,} normalised authors -> {out_path}")
    print(f"{big:,} have 10,000+ words (section 3's reliable-sample floor)")
    for r in out[:8]:
        print(f"  {r['words']:>12,}  {r['works']:>5} works  {r['author_norm'][:50]}")
    return 0


METADATA_DUPES = Path("data/catalog/duplicates_metadata.parquet")
COMBINED = Path("data/catalog/duplicates_combined.parquet")
# newspaper pages are not works: every page of a title in a year shares title, author and year
NOT_WORKS = {"chronicling_america"}


def _keeper(members: list[int], rows: list[dict]) -> int:
    """Earliest year, then earliest in the catalog (its row order)."""
    return min(members, key=lambda i: (rows[i]["year"] or 9999, i))


def _write_groups(groups: list[list[int]], rows: list[dict], best: dict, out: Path) -> int:
    recs = []
    for gid, members in enumerate(sorted(groups, key=min)):
        keep = _keeper(members, rows)
        for i in sorted(members):
            recs.append({"work_id": rows[i]["work_id"], "group_id": gid,
                         "group_size": len(members), "is_keeper": i == keep,
                         "best_similarity": best.get(i, 0.0)})  # fmt: skip
    pq.write_table(
        pa.Table.from_pylist(recs, schema=DUPE_SCHEMA).replace_schema_metadata(
            {"config_sha256": sha256_of_config()}
        ),
        out,
    )
    print(f"{len(groups):,} groups, {len(recs):,} works, "
          f"{len(recs) - len(groups):,} non-keepers -> {out}")  # fmt: skip
    return 0


def metadata_groups(rows: list[dict], keys: list[str]) -> list[list[int]]:
    """Amendment 6's second pass: rows sharing every key, in more than one source."""
    by: dict[tuple, list[int]] = defaultdict(list)
    for i, r in enumerate(rows):
        if r["has_text"] and r["source"] not in NOT_WORKS and all(r[k] for k in keys):
            by[tuple(r[k] for k in keys)].append(i)
    return [m for m in by.values() if len({rows[i]["source"] for i in m}) > 1]


def metadata_pass() -> int:
    mp = load_config()["corpus"]["dedup"]["metadata_pass"]
    rows = pq.read_table(CATALOG).to_pylist()
    return _write_groups(metadata_groups(rows, mp["keys"]), rows, {}, METADATA_DUPES)


def combine(minhash: Path = OUTPUTS["normalized"][1]) -> int:
    """Union of the MinHash groups (on normalised text) and the metadata groups."""
    rows = pq.read_table(CATALOG).to_pylist()
    index = {r["work_id"]: i for i, r in enumerate(rows)}
    parent = list(range(len(rows)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    best: dict[int, float] = {}
    for path in (minhash, METADATA_DUPES):
        groups: dict[int, list[int]] = defaultdict(list)
        for r in pq.read_table(path).to_pylist():
            i = index[r["work_id"]]
            groups[r["group_id"]].append(i)
            best[i] = max(best.get(i, 0.0), r["best_similarity"])
        for members in groups.values():
            for i in members[1:]:
                parent[find(i)] = find(members[0])
    merged: dict[int, list[int]] = defaultdict(list)
    for i in best:
        merged[find(i)].append(i)
    return _write_groups([m for m in merged.values() if len(m) > 1], rows, best, COMBINED)


CHECK = Path("data/catalog/dedup_metadata_check.json")


def _vocab(path: Path) -> set[str]:
    """Words of four or more letters occurring at least twice: robust to most OCR noise."""
    import re
    from collections import Counter

    c = Counter(re.findall(r"[a-z]{4,}", path.read_text(errors="replace").lower()))
    return {w for w, n in c.items() if n >= 2}


def check_metadata(n: int = 200) -> int:
    """Amendment 6's check against the text, on a seeded sample of metadata groups.

    For each group's keeper and every other member: the ratio of their word counts and the
    overlap of their vocabularies. Same OCR reused scores about 1.0; the same work read by two
    OCR engines 0.4-0.6; different volumes of one work about 0.45 with similar lengths. The
    check reports what the pass merges; it cannot tell volumes from copies, and under the
    amendment both count as one work.
    """
    import json
    import random

    from ocr_fix.normalize import norm_path

    rows = {r["work_id"]: r for r in pq.read_table(CATALOG).to_pylist()}
    words = {}
    for f in OUTPUTS["normalized"][0].glob("*.parquet"):
        for r in pq.read_table(f, columns=["work_id", "words"]).to_pylist():
            words[r["work_id"]] = r["words"]
    groups: dict[int, list[dict]] = defaultdict(list)
    for r in pq.read_table(METADATA_DUPES).to_pylist():
        groups[r["group_id"]].append(r)
    rng = random.Random(f"{load_config()['seed']}:dedup-metadata-check")
    pairs = []
    for gid in rng.sample(sorted(groups), min(n, len(groups))):
        keep = next(r["work_id"] for r in groups[gid] if r["is_keeper"])
        vk = _vocab(norm_path(rows[keep]))
        for r in groups[gid]:
            if r["work_id"] == keep:
                continue
            vo = _vocab(norm_path(rows[r["work_id"]]))
            wk, wo = words.get(keep) or 0, words.get(r["work_id"]) or 0
            pairs.append({"group": gid, "keeper": keep, "member": r["work_id"],
                          "sources": [rows[keep]["source"], rows[r["work_id"]]["source"]],
                          "length_ratio": max(wk, wo) / max(1, min(wk, wo)),
                          "vocab_overlap": len(vk & vo) / max(1, len(vk | vo))})  # fmt: skip
    same_ocr = sum(p["vocab_overlap"] >= 0.9 for p in pairs)
    near_len = sum(p["length_ratio"] <= 1.5 for p in pairs)
    summary = {"groups": min(n, len(groups)), "pairs": len(pairs),
               "same_ocr_reused": same_ocr, "length_within_1.5x": near_len,
               "length_beyond_1.5x": len(pairs) - near_len,
               "median_vocab_overlap": sorted(p["vocab_overlap"] for p in pairs)[len(pairs) // 2],
               "pairs_detail": pairs}  # fmt: skip
    CHECK.write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "pairs_detail"}, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("signatures")
    s.add_argument("--workers", type=int, default=8)
    s.add_argument("--limit", type=int)
    p = sub.add_parser("pairs")
    p.add_argument("--bucket-cap", type=int, default=2000)
    au = sub.add_parser("authors")
    sub.add_parser("metadata")
    sub.add_parser("combine")
    sub.add_parser("check-metadata")
    for x in (s, p, au):
        x.add_argument("--text", choices=sorted(OUTPUTS), default="raw")
    a = ap.parse_args(argv)
    if a.cmd == "signatures":
        return signatures(a.workers, a.limit, a.text)
    if a.cmd == "pairs":
        return pairs(a.bucket_cap, a.text)
    if a.cmd == "authors":
        return authors(a.text)
    if a.cmd == "metadata":
        return metadata_pass()
    if a.cmd == "combine":
        return combine()
    if a.cmd == "check-metadata":
        return check_metadata()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
