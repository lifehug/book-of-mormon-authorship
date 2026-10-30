"""Replications of the published Book of Mormon stylometry (BOM-22).

The designs are fixed in ``docs/prior-studies.md``, written before anything here ran. This runs
each *published* method on the 1830 text, the one exception 4.2 makes to the seal; none of the
project's own methods is used, and nothing here feeds a calibration or a threshold.

This module so far holds the shared units:

* ``modern_chapters``: the 239 modern chapters (the units of Jockers, Witten and Criddle 2008),
  located in the 1830 text. Project Gutenberg's public-domain text (ebook 17, the 1920 edition)
  supplies the chapter divisions only; each chapter's first words are found in the 1830 text of
  the same book by fuzzy alignment (the later edition corrected the grammar), and the 1830 text is
  cut there.

Usage::

    python -m eval.replicate chapters     # -> data/benchmark/replication/chapters_1830.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from rapidfuzz import fuzz

from classic import tokenize

DIR = Path("data/benchmark/replication")
GUTENBERG = DIR / "book-of-mormon-pg17.txt"
EDITION = Path("data/bom/1830/edition_1830.jsonl")
CHAPTERS = DIR / "chapters_1830.jsonl"
# long enough that formula openings ("in the commencement of the ... year") differ
ANCHOR_WORDS = 30
NEAR_BEST = 5  # points below the best that still count as a match
MIN_ANCHOR = 80
BOOKS = [
    "1 Nephi",
    "2 Nephi",
    "Jacob",
    "Enos",
    "Jarom",
    "Omni",
    "Words of Mormon",
    "Mosiah",
    "Alma",
    "Helaman",
    "3 Nephi",
    "4 Nephi",
    "Mormon",
    "Ether",
    "Moroni",
]
_TITLES = {  # Gutenberg's book title lines, for the books without chapter headings too
    "Enos": "THE BOOK OF ENOS",
    "Jarom": "THE BOOK OF JAROM",
    "Omni": "THE BOOK OF OMNI",
    "Words of Mormon": "THE WORDS OF MORMON",
    "4 Nephi": "FOURTH NEPHI",
}


def modern_openings() -> list[tuple[str, int, str]]:
    """(book, chapter, first verse text) for every modern chapter, in order."""
    t = GUTENBERG.read_text(encoding="utf-8")
    t = t[t.find("*** START") : t.find("*** END")]
    verse = re.compile(r"(?m)^(\d+):1 (.+(?:\n(?!\d+:\d+ ).+)*)")
    out = []
    for book in BOOKS:
        if book in _TITLES:
            i = t.find(_TITLES[book], t.find("Contents") + 2000)
            m = verse.search(t, i)
            out.append((book, 1, " ".join(m.group(2).split())))
            continue
        for h in re.finditer(rf"(?m)^{re.escape(book)} Chapter (\d+)\s*$", t):
            m = verse.search(t, h.end())
            out.append((book, int(h.group(1)), " ".join(m.group(2).split())))
    return out


def edition_by_book() -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for ln in EDITION.read_text().splitlines():
        r = json.loads(ln)
        if r["book"]:
            by.setdefault(r["book"], []).append(r)
    return by


def locate(opening: str, windows: list[str]) -> tuple[int, float]:
    """The earliest window that matches ``opening``'s first words nearly as well as the best.

    Taking the best alone fails on the book's formulas: Alma 2's "And it came to pass in the
    commencement of the fifth year" scored a hair lower than "... of the ninth year" much later,
    and the later match swallowed the chapters between. Chapters run in order, so the true
    opening is the earliest strong match.
    """
    from rapidfuzz import process

    probe = " ".join(tokenize(opening)[:ANCHOR_WORDS])
    scores = process.cdist([probe], windows, scorer=fuzz.ratio)[0]
    best = float(scores.max())
    good = [k for k, v in enumerate(scores) if v >= max(best - NEAR_BEST, MIN_ANCHOR)]
    k = good[0] if good else int(scores.argmax())
    return k, float(scores[k])


def chapters() -> int:
    from ocr_fix.normalize import artifacts

    openings = modern_openings()
    by = edition_by_book()
    out = []
    for book in BOOKS:
        paras = by[book]
        words, owner = [], []
        for p in paras:
            toks = tokenize(artifacts(p["text"])[0])
            words += toks
            owner += [p["seq"]] * len(toks)
        chs = [(c, o) for b, c, o in openings if b == book]
        windows = [
            " ".join(words[i : i + ANCHOR_WORDS])
            for i in range(max(1, len(words) - ANCHOR_WORDS + 1))
        ]
        starts = []
        for k, (c, o) in enumerate(chs):
            if c == 1:
                starts.append((c, 0, 100.0))
                continue
            # after the previous chapter's anchor, leaving room for the chapters still to come
            lo = starts[-1][1] + 1
            hi = len(windows) - (len(chs) - k - 1)
            j, s = locate(o, windows[lo:hi])
            starts.append((c, lo + j, s))
        for k, (c, i, s) in enumerate(starts):
            j = starts[k + 1][1] if k + 1 < len(starts) else len(words)
            out.append(
                {
                    "book": book,
                    "chapter": c,
                    "start_word": i,
                    "end_word": j,
                    "seq_first": owner[i],
                    "seq_last": owner[j - 1],
                    "words": j - i,
                    "anchor_score": round(s, 1),
                    "text": " ".join(words[i:j]),
                }
            )
    DIR.mkdir(parents=True, exist_ok=True)
    with CHAPTERS.open("w") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    weak = [r for r in out if r["anchor_score"] < 80]
    print(
        f"{len(out)} chapters, {sum(r['words'] for r in out):,} words; "
        f"anchors under 80: {[(r['book'], r['chapter'], r['anchor_score']) for r in weak]}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["chapters"]:
        return chapters()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
