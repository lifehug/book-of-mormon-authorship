"""Rare-phrase scoring, and sizing the null it is judged against (BOM-45; part of BOM-24).

5.5: for each 4-gram in a target text, its document frequency across the corpus; a volume's score
is the length-normalised count of shared 4-grams whose document frequency is at most
``borrowing.max_df`` (5). 6.5: a source is a significant parallel if its score is above the 99th
percentile of a null built from at least 500 period volumes, stratified by genre.

BOM-45 asks how big that null must be for its 99th percentile not to be mostly noise. The
answer depends on the shape of the score distribution, not on which text is the target, so it is
measured against a stand-in, Gilbert Hunt's *The Late War* (KJV-masked), and the Book of Mormon
is not touched until the null is fixed.

``scan`` makes one pass over every period volume and records which target 4-grams each contains;
document frequencies and every volume's score follow from that. ``size`` draws genre-stratified
samples of n volumes from those scores, 1,000 times per n, and reports the spread of the 99th
percentile. The chosen n is the smallest whose 95% interval lies within ``tolerance`` of the
threshold (``pending_amendment: borrowing.null_sample``).

Usage::

    python -m reuse.rare scan [--workers 8]
    python -m reuse.rare size
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kjv_mask.align import _WORD
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/reuse/null_sizing")
HITS = OUT / "hits.parquet"
STAND_IN = "internet_archive:latewarbetween_00hunt"


def tokens(text: str) -> list[str]:
    """Amendment 2's tokenisation (as KJV masking): NFKC, lowercase, word characters."""
    import unicodedata

    return [m.group(0).lower() for m in _WORD.finditer(unicodedata.normalize("NFKC", text))]


def gram_ids(toks: list[str], n: int) -> set[int]:
    """Hashed ``n``-grams (``borrowing.ngram``; 5.5 registers 4)."""
    out = set()
    for i in range(len(toks) - n + 1):
        h = hashlib.blake2b(" ".join(toks[i : i + n]).encode(), digest_size=8).digest()
        out.add(int.from_bytes(h, "big") >> 1)
    return out


def stand_in_text() -> str:
    from ocr_fix.normalize import norm_path
    from segment.build import original_words

    cat = pq.read_table(
        "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]
    ).to_pylist()
    row = next(r for r in cat if r["work_id"] == STAND_IN)
    prefix = json.dumps({"id": STAND_IN})[:-1]
    spans_file = Path("data/kjv_mask/controls/spans.jsonl")
    spans = next(json.loads(ln)["spans"] for ln in spans_file.open() if ln.startswith(prefix))
    text = norm_path(row).read_text(encoding="utf-8", errors="replace")
    return " ".join(original_words(text, spans))


_TARGET: set[int] | None = None


def _scan_one(job: tuple[str, str, int]) -> tuple[str, int, list[int]]:
    global _TARGET
    if _TARGET is None:
        _TARGET = {int(x) for x in (OUT / "target_grams.txt").read_text().split()}
    wid, path, n = job
    try:
        toks = tokens(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return wid, 0, []
    return wid, len(toks), sorted(gram_ids(toks, n) & _TARGET)


def scan(workers: int) -> int:
    from metadata.pseudo_biblical import eligible_rows
    from ocr_fix.normalize import norm_path

    OUT.mkdir(parents=True, exist_ok=True)
    n = load_config()["borrowing"]["ngram"]
    target = gram_ids(tokens(stand_in_text()), n)
    (OUT / "target_grams.txt").write_text("\n".join(map(str, sorted(target))))
    rows = [r for r in eligible_rows(load_config()) if r["work_id"] != STAND_IN]
    jobs = [(r["work_id"], str(norm_path(r)), n) for r in rows]
    print(f"stand-in has {len(target):,} distinct 4-grams; {len(jobs):,} volumes", flush=True)
    start, recs = time.time(), []
    with ProcessPoolExecutor(workers) as pool:
        for i, (wid, n, hit) in enumerate(pool.map(_scan_one, jobs, chunksize=32), 1):
            recs.append({"work_id": wid, "words": n, "hits": hit})
            if i % 20000 == 0:
                print(f"  {i:,}/{len(jobs):,}  {i / (time.time() - start):.0f}/s", flush=True)
    schema = pa.schema(
        [("work_id", pa.string()), ("words", pa.int64()), ("hits", pa.list_(pa.int64()))]
    )
    pq.write_table(
        pa.Table.from_pylist(recs, schema=schema).replace_schema_metadata(
            {"config_sha256": stamp()["config_sha256"]}
        ),
        HITS,
    )
    print(f"scanned {len(recs):,} in {time.time() - start:.0f}s -> {HITS}")
    return 0


def target_copies(recs: list[dict]) -> set[str]:
    """The stand-in's own copies and editions. They must not count towards a 4-gram's document
    frequency: seven missed copies of The Late War made its distinctive phrases look common
    (document frequency 6-9) and the null collapsed to zero. For the Book of Mormon the sealed
    copies (4.2) play this part."""
    import re

    meta = {
        r["work_id"]: r
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "author_norm", "title"]
        ).to_pylist()
    }
    late_war = re.compile(r"late war.{0,80}(1812|britain)", re.I)
    return {
        r["work_id"]
        for r in recs
        if (meta[r["work_id"]]["author_norm"] or "").startswith("hunt, gilbert")
        or late_war.search(meta[r["work_id"]]["title"] or "")
    }


def scores(recs: list[dict], max_df: int, per_words: int) -> dict[str, float]:
    """Rare shared 4-grams per ``per_words`` words of the volume (5.5's length normalisation)."""
    df: Counter = Counter()
    for r in recs:
        df.update(r["hits"])
    rare = {g for g, n in df.items() if n <= max_df}
    return {
        r["work_id"]: per_words * sum(g in rare for g in r["hits"]) / r["words"]
        for r in recs
        if r["words"] > 0
    }


def size() -> int:
    cfg = load_config()
    b = cfg["borrowing"]
    from metadata.dates import effective_year

    lo, hi = cfg["corpus"]["date_range"]
    years = {
        r["work_id"]: r["year"]
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "year"]
        ).to_pylist()
    }
    # BOM-56: the scan predates the date check; volumes whose corrected year is out of the window
    # still count towards document frequency (they are real books) but are not drawn for the null
    recs = pq.read_table(HITS).to_pylist()
    copies = target_copies(recs)
    recs = [r for r in recs if r["work_id"] not in copies]
    sc = scores(recs, b["max_df"], b["per_words"])
    sc = {
        w: v
        for w, v in sc.items()
        if (y := effective_year(w, years.get(w))) is not None and lo <= y <= hi
    }
    genre = {
        r["work_id"]: (r["genre"] or "uncertain").split(",")[0]
        for r in pq.read_table("data/catalog/genre.parquet").to_pylist()
    }
    strata: dict[str, list[float]] = defaultdict(list)
    for w, s in sc.items():
        strata[genre.get(w, "uncertain")].append(s)
    total = sum(len(v) for v in strata.values())
    arrays = {g: np.array(v) for g, v in strata.items()}
    rng = np.random.default_rng(derive_seed("null-sizing", cfg))
    population = np.percentile(np.concatenate(list(arrays.values())), b["null_percentile"])
    curve = {}
    for n in b["null_sizing"]["sizes"]:
        q = []
        for _ in range(b["null_sizing"]["draws"]):
            draw = np.concatenate(
                [
                    rng.choice(a, size=max(1, round(n * len(a) / total)), replace=False)
                    for a in arrays.values()
                    if len(a)
                ]
            )
            q.append(np.percentile(draw, b["null_percentile"]))
        q = np.array(q)
        lo, hi = np.percentile(q, [2.5, 97.5])
        med = float(np.median(q))
        curve[str(n)] = {
            "median": med,
            "sd": float(q.std()),
            "ci95": [float(lo), float(hi)],
            "half_width_rel": float((hi - lo) / 2 / med) if med > 0 else None,
        }
    tol = b["null_sizing"]["tolerance"]
    chosen = next(
        (
            int(n)
            for n, c in curve.items()
            if c["half_width_rel"] is not None and c["half_width_rel"] <= tol
        ),
        None,
    )
    result = {
        **stamp(),
        "stand_in": STAND_IN,
        "volumes": total,
        "population_threshold": float(population),
        "per_stratum": {g: len(v) for g, v in strata.items()},
        "curve": curve,
        "tolerance": tol,
        "chosen_n": chosen,
        "target_copies_excluded": len(copies),
        "share_nonzero": float(np.mean(np.concatenate(list(arrays.values())) > 0)),
    }
    (OUT / "sizing.json").write_text(json.dumps(result, indent=1) + "\n")
    for n, c in curve.items():
        hw = "n/a" if c["half_width_rel"] is None else f"+/-{c['half_width_rel']:.0%}"
        print(
            f"  n={int(n):>6,}  99th pct {c['median']:.3f}  95% CI {c['ci95'][0]:.3f}-"
            f"{c['ci95'][1]:.3f}  ({hw})"
        )
    print(f"population threshold {population:.3f}; chosen n = {chosen}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--workers", type=int, default=8)
    sub.add_parser("size")
    a = ap.parse_args(argv)
    return scan(a.workers) if a.cmd == "scan" else size()


if __name__ == "__main__":
    sys.exit(main())
