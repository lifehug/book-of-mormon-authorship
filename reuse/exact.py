"""Exact and near-exact text reuse by passim (BOM-23; 5.5, Amendment 10).

The plan, written and registered before any run, is ``docs/reuse-plan.md``. Two outputs:

* **the reuse table**: the KJV-masked Book of Mormon against every eligible period volume (its
  sealed copies left out), and the same for two reference texts, Hunt's *The Late War* (against
  volumes printed before 1816) and a seeded 1820s sermon collection (before its year);
* **the known-answer score** (Amendment 9): every text, the Book of Mormon included, against
  ``reuse.matched_volumes`` volumes from the ``reuse.window_years`` years before its English was
  written, in ``reuse.matched_draws`` seeded draws; the share of its masked tokens covered.

``scan`` is the lossless prefilter: one pass over the volumes any search needs, recording which
of each target's 5-grams a volume contains (``hits.parquet``). passim cannot align a pair sharing
fewer than ``reuse.min_seeds`` seed 5-grams, and a seed is a 5-gram whose document frequency
across that search is at most ``reuse.seed_max_df``, so only volumes with that many are aligned.

Usage::

    python -m reuse.exact scan [--workers 8]   # -> data/reuse/exact/hits.parquet
    python -m reuse.exact align <search>       # e.g. ossian:draw0, bom:full -> alignments/
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from reuse.rare import gram_ids, tokens

OUT = Path("data/reuse/exact")
KNOWN_ANSWER = Path("data/known_answer/set.jsonl")
SERMONS = Path("data/controls/sermons_1820s.jsonl")
# Amendment 10, Change 3: the matched samples leave out Bibles and New Testaments
BIBLE = re.compile(r"holy bible|new testament|old testament|^the bible|^bible\b", re.I)
FULL = ("bom", "late_war", "sermon")  # targets with a whole-corpus reuse table (Change 1)


def masked_text(work_ids: list[str]) -> str:
    """Normalised text of these volumes with their KJV spans removed (BOM-16, BOM-61 masks)."""
    import gzip

    from ocr_fix.normalize import norm_path
    from segment.build import original_words

    want, spans = set(work_ids), {}
    for group in ("controls", "known_answer"):
        path = Path(f"data/kjv_mask/{group}/spans.jsonl")
        if not path.exists():
            path = path.with_suffix(".jsonl.gz")
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt") as fh:
            for ln in fh:
                if any(w in ln[:200] for w in want):  # cheap prefilter on the id field
                    r = json.loads(ln)
                    if r["id"] in want:
                        spans[r["id"]] = r["spans"]
    missing = want - set(spans)
    if missing:
        raise SystemExit(f"no KJV mask for {sorted(missing)}")
    cat = {
        r["work_id"]: r
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]
        ).to_pylist()
        if r["work_id"] in want
    }
    parts = []
    for w in work_ids:
        text = norm_path(cat[w]).read_text(encoding="utf-8", errors="replace")
        parts.append(" ".join(original_words(text, spans[w])))
    return " ".join(parts)


def sermon_pick(cfg: dict) -> dict:
    """The 1820s sermon collection of the reference table: one seeded draw from the registered
    sermons control, among volumes of 20,000+ words (a collection, not a single sermon)."""
    rows = [json.loads(ln) for ln in SERMONS.read_text().splitlines()]
    rows = sorted((r for r in rows if (r["words"] or 0) >= 20_000), key=lambda r: r["work_id"])
    return random.Random(derive_seed(cfg["reuse"]["sermon_seed"], cfg)).choice(rows)


def targets(cfg: dict) -> dict[str, dict]:
    """key -> {"text", "year", "ids"}: every text BOM-23 aligns, KJV-masked."""
    from reuse.rare import STAND_IN, bom_text, stand_in_text

    years = cfg["reuse"]["english_year"]
    out = {"bom": {"text": bom_text(), "year": years["bom"], "ids": []}}
    out["late_war"] = {"text": stand_in_text(), "year": cfg["reuse"]["late_war_year"],
                       "ids": [STAND_IN]}  # fmt: skip
    s = sermon_pick(cfg)
    out["sermon"] = {"text": masked_text([s["work_id"]]), "year": s["year"], "ids": [s["work_id"]]}
    for ln in KNOWN_ANSWER.read_text().splitlines():
        r = json.loads(ln)
        ids = [v["work_id"] for v in r["volumes"]]
        out[r["key"]] = {"text": masked_text(ids), "year": years[r["key"]], "ids": ids}
    return out


def eligible_any_year(cfg: dict) -> list[dict]:
    """The eligibility of ``metadata.pseudo_biblical.eligible_rows`` without its date range: text,
    a dated year, deduplication keepers, OCR exclusions applied, no newspapers."""
    from metadata.dates import effective_year
    from metadata.pseudo_biblical import CATALOG, DUPES, NOT_WORKS, VOLUMES

    excluded = {r["work_id"] for r in pq.read_table(VOLUMES).to_pylist() if r["ocr_excluded"]}
    nonkeeper = {r["work_id"] for r in pq.read_table(DUPES).to_pylist() if not r["is_keeper"]}
    cols = ["work_id", "source", "year", "has_text", "text_path", "title", "author_norm"]
    out = []
    for r in pq.read_table(CATALOG, columns=cols).to_pylist():
        if not r["has_text"] or r["source"] in NOT_WORKS:
            continue
        if r["work_id"] in excluded or r["work_id"] in nonkeeper:
            continue
        r["year"] = effective_year(r["work_id"], r["year"])
        if r["year"]:
            out.append(r)
    return out


def _title_key(title: str | None) -> str:
    return " ".join(re.findall(r"[a-z]+", (title or "").lower())[:6])


def own_copies(key: str, t: dict, rows: list[dict]) -> set[str]:
    """The target's own copies and editions, left out of its searches: the sealed copies for the
    Book of Mormon (4.2); Hunt's works and every printing of The Late War for it; otherwise any
    volume by the same author or with the same title (its first six words)."""
    if key == "bom":
        from metadata.sealed import sealed_ids

        return sealed_ids()
    if key == "late_war":
        from reuse.rare import target_copies

        return target_copies(rows) | set(t["ids"])
    mine = [r for r in rows if r["work_id"] in set(t["ids"])]
    authors = {r["author_norm"] for r in mine if r["author_norm"]}
    titles = {_title_key(r["title"]) for r in mine} - {""}
    return {
        r["work_id"]
        for r in rows
        if r["work_id"] in set(t["ids"])
        or (r["author_norm"] and r["author_norm"] in authors)
        or _title_key(r["title"]) in titles
    }


def searches(cfg: dict, tg: dict[str, dict], rows: list[dict]) -> dict[str, list[str]]:
    """search name -> volume ids. ``<key>:full`` for the reuse table, ``<key>:draw<i>`` for the
    known-answer samples (Amendment 10, Changes 1 and 3)."""
    rc = cfg["reuse"]
    lo, hi = cfg["corpus"]["date_range"]
    out = {}
    for key, t in tg.items():
        own = own_copies(key, t, rows)
        if key in FULL:
            top = hi if key == "bom" else t["year"] - 1  # the Book of Mormon: all of 1780-1830
            out[f"{key}:full"] = sorted(
                r["work_id"] for r in rows
                if lo <= r["year"] <= top and r["work_id"] not in own
            )  # fmt: skip
        window = sorted(
            r["work_id"] for r in rows
            if t["year"] - rc["window_years"] <= r["year"] < t["year"]
            and r["work_id"] not in own and not BIBLE.search(r["title"] or "")
        )  # fmt: skip
        for i in range(rc["matched_draws"]):
            rng = random.Random(derive_seed(f"bom23:{key}:draw{i}", cfg))
            out[f"{key}:draw{i}"] = sorted(rng.sample(window, rc["matched_volumes"]))
    return out


_GRAMS: dict[str, dict[str, set[int]]] = {}


def _scan_one(job: tuple[str, str, list[str], str]) -> tuple[str, int, dict[str, list[int]]]:
    wid, path, keys, gram_dir = job
    if gram_dir not in _GRAMS:
        _GRAMS[gram_dir] = {
            p.stem: {int(x) for x in p.read_text().split()} for p in Path(gram_dir).glob("*.txt")
        }
    try:
        toks = tokens(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return wid, 0, {}
    grams = gram_ids(toks, load_config()["kjv_mask"]["passim"]["ngram"])
    return wid, len(toks), {k: sorted(grams & _GRAMS[gram_dir][k]) for k in keys}


def scan(workers: int) -> int:
    from ocr_fix.normalize import norm_path

    cfg = load_config()
    n = cfg["kjv_mask"]["passim"]["ngram"]
    OUT.mkdir(parents=True, exist_ok=True)
    tg = targets(cfg)
    gram_dir = OUT / "target_grams"
    gram_dir.mkdir(exist_ok=True)
    for key, t in tg.items():
        g = gram_ids(tokens(t["text"]), n)
        (gram_dir / f"{key}.txt").write_text("\n".join(map(str, sorted(g))))
        print(f"{key}: {len(tokens(t['text'])):,} masked tokens, {len(g):,} {n}-grams", flush=True)
    rows = eligible_any_year(cfg)
    srch = searches(cfg, tg, rows)
    (OUT / "searches.json").write_text(
        json.dumps(
            {
                **stamp(),
                "targets": {k: {"year": t["year"], "ids": t["ids"]} for k, t in tg.items()},
                "searches": srch,
            }
        )
        + "\n"  # fmt: skip
    )
    keys_of: dict[str, set[str]] = {}
    for name, ids in srch.items():
        for w in ids:
            keys_of.setdefault(w, set()).add(name.split(":")[0])
    by_id = {r["work_id"]: r for r in rows}
    jobs = [(w, str(norm_path(by_id[w])), sorted(k), str(gram_dir)) for w, k in keys_of.items()]
    print(f"{len(jobs):,} volumes to scan for {len(srch)} searches", flush=True)
    start, recs = time.time(), []
    with ProcessPoolExecutor(workers) as pool:
        for i, (wid, words, hits) in enumerate(pool.map(_scan_one, jobs, chunksize=32), 1):
            for k, h in hits.items():
                recs.append({"work_id": wid, "target": k, "words": words, "hits": h})
            if i % 20000 == 0:
                print(f"  {i:,}/{len(jobs):,}  {i / (time.time() - start):.0f}/s", flush=True)
    schema = pa.schema([("work_id", pa.string()), ("target", pa.string()),
                        ("words", pa.int64()), ("hits", pa.list_(pa.int64()))])  # fmt: skip
    pq.write_table(
        pa.Table.from_pylist(recs, schema=schema).replace_schema_metadata(
            {"config_sha256": stamp()["config_sha256"]}
        ),
        OUT / "hits.parquet",
    )
    print(f"scanned {len(jobs):,} in {time.time() - start:.0f}s -> {OUT / 'hits.parquet'}")
    return 0


# Alignment ---------------------------------------------------------------------------------
#
# passim is handed, for each candidate volume, only the stretches around its seed 5-grams, with
# MARGIN tokens either side. An alignment cannot jump more than ``max_gap_chars`` between
# matching n-grams, so a margin this wide holds every alignment a seed can start; one that runs
# into a stretch's edge (not the volume's) is flagged ``at_edge`` for inspection. The margin is
# an implementation limit, not an analytic choice: it changes how much text passim reads, not
# what it can find, except where flagged.
MARGIN = 1000
WORK = Path("data/corpus/reuse_runs")


def _toks(text: str) -> list[tuple[str, int, int]]:
    from kjv_mask.align import _tokens

    return _tokens(text, 0)


def _hash(words: list[str]) -> int:
    import hashlib

    h = hashlib.blake2b(" ".join(words).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") >> 1  # as reuse.rare.gram_ids


def _seed_positions(toks: list[tuple[str, int, int]], n: int, seeds: set[int]) -> list[int]:
    words = [t[0] for t in toks]
    return [i for i in range(len(words) - n + 1) if _hash(words[i : i + n]) in seeds]


def _regions(wid: str, text: str, n: int, seeds: set[int]) -> list[dict]:
    """The stretches of a volume around its seeds, merged where their margins meet."""
    toks = _toks(text)
    spans: list[list[int]] = []
    for i in _seed_positions(toks, n, seeds):
        a, b = max(0, i - MARGIN), min(len(toks), i + n + MARGIN)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    out = []
    for a, b in spans:
        cb, ce = toks[a][1], toks[b - 1][2]
        out.append({"id": f"{wid}@{cb}", "work_id": wid, "begin": cb, "end": ce,
                    "edge_lo": a > 0, "edge_hi": b < len(toks), "text": text[cb:ce],
                    "words": b - a})  # fmt: skip
    return out


def _passim(docs: list[dict], work: Path, cfg: dict) -> list[dict]:
    """passim between the target series and the source series, cap on document frequency off
    (Amendment 10, Change 2b); cached by input and settings, resumes, deletes nothing."""
    import hashlib
    import os
    import subprocess

    from kjv_mask.align import FAILURES, JAVA_HOME, SPARK_MEMORY, SPARK_MEMORY_RETRY, _finished

    p, rc = cfg["kjv_mask"]["passim"], cfg["reuse"]
    params = [p["ngram"], rc["min_seeds"], p["passim_min_align_chars"], p["max_gap_chars"],
              p["relative_overlap"]]  # fmt: skip
    key = hashlib.sha256(
        json.dumps([params, [d["id"] for d in docs], [len(d["text"]) for d in docs]]).encode()
    ).hexdigest()[:16]
    work = work / key
    work.mkdir(parents=True, exist_ok=True)
    done = _finished(work)
    if done is None:
        inp = work / "in.jsonl"
        with inp.open("w") as fh:
            for d in docs:
                rec = {"id": d["id"], "series": d["series"], "text": d["text"]}
                fh.write(json.dumps(rec) + "\n")
        for memory in (SPARK_MEMORY, *SPARK_MEMORY_RETRY):
            attempt = 0
            while (work / f"out.{attempt}").exists() or (attempt == 0 and (work / "out").exists()):
                attempt += 1
            out_dir = work / ("out" if attempt == 0 else f"out.{attempt}")
            cmd = [
                "passim", "--fields", "series", "--filterpairs", "series <> series2", "--pairwise",
                "-n", str(p["ngram"]), "-m", str(rc["min_seeds"]),
                "-a", str(p["passim_min_align_chars"]), "-g", str(p["max_gap_chars"]),
                "--maxDF", "1000000000", "--log-level", "ERROR",
                "--src-overlap", str(p["relative_overlap"]),
                "--dst-overlap", str(p["relative_overlap"]), str(inp), str(out_dir),
            ]  # fmt: skip
            env = {**os.environ, "JAVA_HOME": JAVA_HOME,
                   "SPARK_SUBMIT_ARGS": f"--driver-memory {memory}"}  # fmt: skip
            r = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if r.returncode == 0:
                done = out_dir
                break
            FAILURES.parent.mkdir(parents=True, exist_ok=True)
            with FAILURES.open("a") as fh:
                fh.write(json.dumps({"work": str(work), "memory": memory, "exit": r.returncode,
                                     "stderr_tail": r.stderr[-3000:]}) + "\n")  # fmt: skip
        else:
            raise RuntimeError(f"passim failed at every heap size on {work}; see {FAILURES}")
    out = []
    for f in sorted((done / "align.json").glob("*.json")):
        for line in f.read_text().splitlines():
            r = json.loads(line)
            if r["series"] == "target":
                out.append({"t": r["id"], "tb": r["begin"], "te": r["end"],
                            "s": r["id2"], "sb": r["begin2"], "se": r["end2"]})  # fmt: skip
            else:
                out.append({"t": r["id2"], "tb": r["begin2"], "te": r["end2"],
                            "s": r["id"], "sb": r["begin"], "se": r["end"]})  # fmt: skip
    return out


def _pieces(text: str) -> list[tuple[int, int]]:
    """Character ranges of a target cut as Amendment 6 cuts long texts."""
    p = load_config()["kjv_mask"]["passim"]
    toks = _toks(text)
    size, lap = p["piece_words"], p["piece_overlap"]
    if len(toks) <= size:
        return [(0, len(text))]
    out, a = [], 0
    while a < len(toks):
        b = min(len(toks), a + size)
        out.append((toks[a][1], toks[b - 1][2]))
        if b == len(toks):
            break
        a = b - lap
    return out


def _search_hits(search: str, ids: list[str]) -> dict[str, list[int]]:
    key = search.split(":")[0]
    want = set(ids)
    t = pq.read_table(OUT / "hits.parquet", filters=[("target", "=", key)]).to_pylist()
    return {r["work_id"]: r["hits"] for r in t if r["work_id"] in want}


def align(search: str, workers: int) -> int:
    """Every reused passage for one search (``<key>:full`` or ``<key>:draw<i>``)."""
    from collections import Counter
    from difflib import SequenceMatcher

    from ocr_fix.normalize import norm_path

    cfg = load_config()
    rc, p = cfg["reuse"], cfg["kjv_mask"]["passim"]
    n, min_tokens = p["ngram"], cfg["kjv_mask"]["verbatim"]["min_tokens"]
    meta = json.loads((OUT / "searches.json").read_text())
    ids = meta["searches"][search]
    key = search.split(":")[0]
    hits = _search_hits(search, ids)
    df: Counter = Counter()
    for h in hits.values():
        df.update(h)
    seeds = {g for g, c in df.items() if c <= rc["seed_max_df"]}
    cands = sorted(w for w, h in hits.items() if sum(g in seeds for g in h) >= rc["min_seeds"])
    print(f"{search}: {len(ids):,} volumes, {len(seeds):,} seed 5-grams, "
          f"{len(cands):,} candidates", flush=True)  # fmt: skip

    import unicodedata

    target = unicodedata.normalize("NFKC", targets_text(cfg, key))
    ttoks = _toks(target)
    starts = [t[1] for t in ttoks]
    rows = {r["work_id"]: r for r in eligible_any_year(cfg) if r["work_id"] in set(cands)}
    regions: list[dict] = []
    texts: dict[str, str] = {}
    for w in cands:
        text = unicodedata.normalize(
            "NFKC", norm_path(rows[w]).read_text(encoding="utf-8", errors="replace")
        )
        texts[w] = text
        regions += _regions(w, text, n, seeds)
    batch_words = p["batch_words"]
    batches, cur, size = [], [], 0
    for r in regions:
        if cur and size + r["words"] > batch_words:
            batches.append(cur)
            cur, size = [], 0
        cur.append(r)
        size += r["words"]
    if cur:
        batches.append(cur)
    by_id = {r["id"]: r for r in regions}
    pieces = _pieces(target)
    print(f"  {len(regions):,} source stretches in {len(batches)} batches x {len(pieces)} "
          f"target pieces", flush=True)  # fmt: skip
    import bisect

    found = []
    start = time.time()
    for bi, batch in enumerate(batches, 1):
        for pb, pe in pieces:
            docs = [{"id": f"t@{pb}", "series": "target", "text": target[pb:pe]}]
            docs += [{"id": r["id"], "series": "source", "text": r["text"]} for r in batch]
            for a in _passim(docs, WORK / search.replace(":", "_"), cfg):
                src = by_id[a["s"]]
                tb, te = pb + a["tb"], pb + a["te"]
                i, j = bisect.bisect_left(starts, tb), bisect.bisect_left(starts, te)
                tw = [t[0] for t in ttoks[i:j]]
                if len(tw) < min_tokens:
                    continue
                sb, se = src["begin"] + a["sb"], src["begin"] + a["se"]
                sw = [t[0] for t in _toks(texts[src["work_id"]][sb:se])]
                # seeds the two passages share, not merely seeds somewhere in the target's span
                tg = {_hash(tw[x : x + n]) for x in range(len(tw) - n + 1)} & seeds
                k = len(tg & {_hash(sw[x : x + n]) for x in range(len(sw) - n + 1)})
                if k < rc["min_seeds"]:
                    continue
                sm = SequenceMatcher(a=tw, b=sw, autojunk=False)
                same = sum(b.size for b in sm.get_matching_blocks())
                at_edge = (src["edge_lo"] and a["sb"] < 200) or (
                    src["edge_hi"] and a["se"] > len(src["text"]) - 200
                )
                found.append({"work_id": src["work_id"], "t_begin": tb, "t_end": te,
                              "t_tok_begin": i, "t_tok_end": j, "s_begin": sb, "s_end": se,
                              "tokens": len(tw), "identity": round(same / len(tw), 4),
                              "seeds": k, "at_edge": bool(at_edge)})  # fmt: skip
        print(f"  batch {bi}/{len(batches)}, {len(found):,} passages, "
              f"{time.time() - start:.0f}s", flush=True)  # fmt: skip
    # the target's pieces overlap, so a passage in an overlap is found twice: keep the longer
    found.sort(key=lambda r: (r["work_id"], r["t_begin"], -r["tokens"]))
    kept: list[dict] = []
    for r in found:
        if kept and kept[-1]["work_id"] == r["work_id"] and r["t_begin"] < kept[-1]["t_end"]:
            continue
        kept.append(r)
    covered = set()
    for r in kept:
        covered.update(range(r["t_tok_begin"], r["t_tok_end"]))
    res = {**stamp(), "search": search, "volumes": len(ids), "seeds": len(seeds),
           "candidates": len(cands), "target_tokens": len(ttoks), "passages": len(kept),
           "sources": len({r["work_id"] for r in kept}),
           "covered_share": len(covered) / len(ttoks), "at_edge": sum(r["at_edge"] for r in kept),
           "rows": kept}  # fmt: skip
    (OUT / "alignments").mkdir(parents=True, exist_ok=True)
    (OUT / "alignments" / f"{search.replace(':', '_')}.json").write_text(json.dumps(res) + "\n")
    print(f"{search}: {len(kept):,} passages from {res['sources']:,} volumes, "
          f"{res['covered_share']:.2%} of the target covered", flush=True)  # fmt: skip
    return 0


def targets_text(cfg: dict, key: str) -> str:
    """One target's masked text (the same construction as ``targets``, built alone)."""
    from reuse.rare import bom_text, stand_in_text

    if key == "bom":
        return bom_text()
    if key == "late_war":
        return stand_in_text()
    if key == "sermon":
        return masked_text([sermon_pick(cfg)["work_id"]])
    for ln in KNOWN_ANSWER.read_text().splitlines():
        r = json.loads(ln)
        if r["key"] == key:
            return masked_text([v["work_id"] for v in r["volumes"]])
    raise SystemExit(f"unknown target {key}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--workers", type=int, default=8)
    al = sub.add_parser("align")
    al.add_argument("search", help="e.g. ossian:draw0, bom:full")
    al.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == "scan":
        return scan(a.workers)
    if a.cmd == "align":
        return align(a.search, a.workers)
    return 1


if __name__ == "__main__":
    sys.exit(main())
