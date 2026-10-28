"""A period word list for OCR repair (BOM-14).

The scoring lexicon (``data/lexicon/english_words.txt``, Webster's Second) holds base forms
only: no ``houses``, ``things`` or ``has``, and none of the period spellings a 1780-1830 text
uses (``shew``, ``publick``, ``honour``). Repair needs to know that ``houfes`` should become
``houses``, so it needs inflections and period spelling, and the best source of both is text
typed by hand from the period's own printing: the TCP's ECCO and Evans transcriptions dated
1700 or later. They are keyed, not OCR'd, so a word in them is a word.

Keyed text is not perfect: ``firft`` occurs in 2 of these texts, against 6,446 for
``first``. So the file keeps each word's document frequency, not just membership, and repair
compares frequencies rather than asking whether a form exists (``ocr_fix.clean``). A word
outside Webster is kept when it occurs in at least ``MIN_DOCS`` texts; Webster words are kept
whatever their frequency, with that frequency (possibly 0). Both thresholds are analytic
choices registered by Amendment 6 (``corpus.ocr_cleaning.lexicon_min_docs``).

Usage::

    python -m ocr_fix.lexicon build      # -> data/lexicon/period_words.tsv (word, texts, tokens)

The third column, total occurrences, is what word segmentation needs (``ocr_fix.defragment``):
document frequency saturates at the number of texts, so it makes a keying slip in 3 texts look
only 2,000 times rarer than ``the`` when in running text it is a million times rarer.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq

CATALOG = Path("data/catalog/catalog.parquet")
WEBSTER = Path("data/lexicon/english_words.txt")
OUT = Path("data/lexicon/period_words.tsv")
MIN_DOCS = 2  # registered, Amendment 6
COLLECTIONS = {"ecco", "evans"}
FROM_YEAR = 1700

_WORD = re.compile(r"[a-z]+")


def words_of(path: str) -> Counter:
    text = Path(path).read_text(encoding="utf-8", errors="replace").replace("ſ", "s").lower()
    return Counter(_WORD.findall(text))


def build(workers: int) -> int:
    rows = pq.read_table(CATALOG, columns=["source", "genre_src", "year", "text_path"]).to_pylist()
    paths = [
        r["text_path"]
        for r in rows
        if r["source"] == "tcp"
        and r["text_path"]
        and (r["genre_src"] or "") in COLLECTIONS
        and (r["year"] or 0) >= FROM_YEAR
    ]
    df: Counter = Counter()
    tf: Counter = Counter()
    with ProcessPoolExecutor(workers) as pool:
        for ws in pool.map(words_of, paths, chunksize=32):
            df.update(ws.keys())
            tf.update(ws)
    period = {w for w, n in df.items() if n >= MIN_DOCS}
    webster = set(WEBSTER.read_text().split())
    words = sorted(period | webster)
    OUT.write_text("".join(f"{w}\t{df.get(w, 0)}\t{tf.get(w, 0)}\n" for w in words))
    print(
        f"{len(paths):,} keyed texts; {len(period):,} words in >= {MIN_DOCS} texts; "
        f"{len(period - webster):,} not in Webster; {len(words):,} written to {OUT}"
    )
    return 0


def load(path: Path = OUT) -> dict[str, int]:
    """word -> number of keyed texts it occurs in (0 for a Webster word TCP never uses)."""
    return _column(path, 1)


def load_tokens(path: Path = OUT) -> dict[str, int]:
    """word -> total occurrences in those texts (0 for a Webster word TCP never uses)."""
    return _column(path, 2)


def _column(path: Path, i: int) -> dict[str, int]:
    out = {}
    for line in path.read_text().splitlines():
        parts = line.split("\t")
        out[parts[0]] = int(parts[i])
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(argv)
    return build(a.workers) if a.cmd == "build" else 1


if __name__ == "__main__":
    sys.exit(main())
