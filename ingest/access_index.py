"""Index what a local newspaper printed and advertised, for the access evidence (BOM-33).

Scope and ceiling. BOM-33's ceiling is "this was demonstrably available in the area", never
"he read it". This module indexes *what the paper carried*: a dated, page-level record of
Book of Mormon and Golden Bible items, and of printed matter offered for sale nearby. It
records availability, which is a fact about the newspaper. It makes no claim about what any
person read, and no output of this module should be quoted as though it did.

The search is fragmentation-proof, which it has to be. BOM-14 measured the Wayne Sentinel's
single-letter token rate at 0.300 against Chronicling America's 0.041, because NYS Historic
Newspapers' text view breaks words into lone characters -- ``t h e b o o k``. A plain substring
search for "book of mormon" finds nothing in such a page. So every page is also reduced to a
*squeezed* form with all whitespace and punctuation removed, and terms are matched against
that. ``goldenbible`` matches whether the page reads "Golden Bible" or "G o l d e n B i b l e".

The cost is false positives across word boundaries: squeezing makes "...the gold. Bible..."
and "goldbible" identical, and a term like ``plates`` will also fire inside "plate sets". Short
and common terms are therefore excluded by design, every hit carries the raw snippet that
produced it, and the output is a list for a human to read, not a count to report.

Terms are fixed in ``TERMS`` before running, so the index cannot be tuned until it says
something. Usage::

    python -m ingest.access_index build data/newspapers/wayne_sentinel --name wayne_sentinel
    python -m ingest.access_index summary data/access/wayne_sentinel_access.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

OUT_DIR = Path("data/access")

# Fixed before the index was first run. Grouped so a hit's meaning is explicit.
# Bare "nephi" was dropped after validation: squeezed, "ne Philadelphia" becomes
# "nephiladelphia" and five of eight hits were that. The genitive forms do not collide.
# Bare "mormon" was dropped for the same reason -- its only 1829 hit was inside a garbled
# apothecary advertisement. Distinctive multi-word forms only.
TERMS: dict[str, tuple[str, ...]] = {
    "book_of_mormon": (
        "bookofmormon",
        "ofnephi",
        "handofmoroni",
        "lamanite",
        "moroni",
    ),
    "golden_bible": ("goldenbible", "goldbible", "goldenplates", "goldplates"),
    "smith_family": ("josephsmith", "smithjun", "smithjunior"),
    "grandin_imprint": ("egrandin", "ebgrandin", "grandin"),
    "scripture_adjacent": ("lostisrael", "tenlosttribes", "hebrewsindians", "israelindians"),
    "bookselling": ("bookstore", "booksfor sale", "justreceived", "newbooks", "bookbindery"),
    "sermons_tracts": ("sermondelivered", "discoursedelivered", "religioustract"),
}

# Matched against the squeezed page, so they carry no spaces.
_SQUEEZE = re.compile(r"[^a-z0-9]+")
_DATE = re.compile(r"(\d{4})(\d{2})(\d{2})")


def squeeze(text: str) -> str:
    """Lowercase with every non-alphanumeric character removed."""
    return _SQUEEZE.sub("", text.lower())


def snippet(raw: str, squeezed: str, pos: int, width: int = 90) -> str:
    """A readable fragment of the original around a squeezed-form hit.

    The squeezed offset is not the raw offset, so this walks the raw text counting only the
    characters that survive squeezing until it reaches the match.
    """
    kept = 0
    start = 0
    for i, ch in enumerate(raw):
        if not _SQUEEZE.match(ch.lower()):
            if kept == pos:
                start = i
                break
            kept += 1
    lo = max(0, start - width // 3)
    return " ".join(raw[lo : start + width].split())


def page_date(page_id: str) -> str | None:
    m = _DATE.search(page_id)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def build(root: Path, name: str) -> int:
    text_dir = root / "text"
    if not text_dir.is_dir():
        print(f"no text/ under {root}", file=sys.stderr)
        return 1
    files = sorted(text_dir.glob("*.txt"))
    rows: list[dict] = []
    for p in files:
        raw = p.read_text(encoding="utf-8", errors="replace")
        sq = squeeze(raw)
        if not sq:
            continue
        for group, terms in TERMS.items():
            for term in terms:
                key = squeeze(term)
                start = 0
                while (pos := sq.find(key, start)) != -1:
                    rows.append(
                        {
                            "page_id": p.stem,
                            "date": page_date(p.stem),
                            "group": group,
                            "term": term,
                            "snippet": snippet(raw, sq, pos),
                        }
                    )
                    start = pos + len(key)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}_access.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for r in sorted(rows, key=lambda r: (r["date"] or "", r["page_id"], r["group"])):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(files):,} pages scanned, {len(rows):,} hits -> {out}")
    by_group = Counter(r["group"] for r in rows)
    for g, n in by_group.most_common():
        pages = len({r["page_id"] for r in rows if r["group"] == g})
        print(f"  {g:<22}{n:>6,} hits on {pages:>4} pages")
    return 0


def summary(path: Path) -> int:
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not rows:
        print("no hits", file=sys.stderr)
        return 1
    years = Counter((r["date"] or "????")[:4] for r in rows)
    print("hits by year")
    for y in sorted(years):
        print(f"  {y}  {years[y]:>5,}")
    print("\nearliest hit per group")
    for g in TERMS:
        hits = [r for r in rows if r["group"] == g and r["date"]]
        if hits:
            first = min(hits, key=lambda r: r["date"])
            print(f"  {g:<22}{first['date']}  {first['page_id']}")
            print(f"      {first['snippet'][:100]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("root", type=Path)
    b.add_argument("--name", required=True)
    s = sub.add_parser("summary")
    s.add_argument("path", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        return build(a.root, a.name)
    if a.cmd == "summary":
        return summary(a.path)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
