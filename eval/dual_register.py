"""Dual-register authors: how many measurements section 9's method weights rest on (BOM-46).

Section 9 weights each method in the synthesis by its accuracy at identifying authors from their
imitation-biblical samples, in bands at 80% and 60%. That accuracy can only be measured on authors
who wrote both an imitation-biblical work and ordinary prose. This counts them, from BOM-54's
curated list: an author qualifies with at least one curated work and at least
``power.reference_floor_words`` of other 1780-1830 prose (BOM-43's floor) that is not itself on
the list, passes the OCR cutoff and is a duplicate keeper. Another copy or edition of a curated
work is not other prose (``metadata.pseudo_biblical.work_key``), and each other work counts once,
at its longest copy, since the dedup keeps cross-source reprints apart.

If the count is small, the section 9 accuracies are reported with confidence intervals and the
equal-weight sensitivity analysis is registered (the issue's own fallback).

Usage::

    python -m eval.dual_register      # -> data/benchmark/dual_register.json
"""

from __future__ import annotations

import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import stamp

CURATED = Path("data/controls/pseudo_biblical_curated.txt")
OUT = Path("data/benchmark/dual_register.json")


def run() -> int:
    from metadata.pseudo_biblical import eligible_rows, work_key

    if not CURATED.exists():
        raise SystemExit(f"{CURATED} missing: BOM-54's curated list comes first")
    cfg = load_config()
    floor = max(cfg["power"]["reference_floor_words"].values())
    curated = set(CURATED.read_text().split())
    cat = {
        r["work_id"]: r
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "author_norm", "title"]
        ).to_pylist()
    }
    words = {}
    for f in glob.glob("data/catalog/signatures_normalized/*.parquet"):
        for r in pq.read_table(f, columns=["work_id", "words"]).to_pylist():
            words[r["work_id"]] = r["words"]
    pb_authors = {cat[w]["author_norm"] for w in curated if cat.get(w) and cat[w]["author_norm"]}
    pb_works = {work_key(cat[w]["title"]) for w in curated if cat.get(w)}
    other: dict[str, dict[str, int]] = defaultdict(dict)
    for r in eligible_rows(cfg):
        a, key = r["author_norm"], work_key(r["title"])
        if a in pb_authors and r["work_id"] not in curated and key not in pb_works:
            other[a][key] = max(other[a].get(key, 0), words.get(r["work_id"]) or 0)
    prose = {a: sum(other[a].values()) for a in pb_authors}
    qualified = sorted(a for a in pb_authors if prose[a] >= floor)
    result = {
        **stamp(),
        "curated_works": len(curated),
        "authors_with_a_curated_work": len(pb_authors),
        "floor_words": floor,
        "dual_register_authors": qualified,
        "other_prose_words": {a: prose[a] for a in sorted(pb_authors)},
        "other_prose_works": {a: dict(sorted(other[a].items())) for a in sorted(other)},
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(f"{len(pb_authors)} authors have a curated pseudo-biblical work;")
    print(f"{len(qualified)} also have {floor:,}+ words of other prose: {qualified}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
