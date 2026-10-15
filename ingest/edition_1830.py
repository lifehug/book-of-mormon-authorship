"""Parse the 1830 edition text layer into books, chapters, paragraphs, and pages (BOM-05).

Input is ``pdftotext -layout`` output of the Jenson reproduction (see data/bom/SOURCES.md):
pages are separated by form feeds, the first line of each page is a running header with the
1830 page number, book titles are capitalized lines without digits, chapters are ``CHAPTER
N.`` lines, and a new paragraph starts on a line indented by two or more spaces. Soft hyphens
(U+00AD) mark line-end word breaks and are joined.

Usage::

    python -m ingest.edition_1830 data/bom/1830/jenson-reproduction-1830.txt \
        -o data/bom/1830/edition_1830.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
CHAPTER_RE = re.compile(r"^\s*CHAPTER\s+([IVXLC]+)\.?\s*$")
HEADER_RE = re.compile(r"^\s*(?:(\d{1,3})\s+)?([A-Z][A-Z ,.'’]+?)\.?\s*(?:\s(\d{1,3}))?\s*$")
TITLE_RE = re.compile(r"^\s*[A-Z][A-Z ,.'’;:-]{5,}$")

# 1830 title lines -> canonical book names, in order of appearance.
BOOKS = [
    ("THE FIRST BOOK OF NEPHI", "1 Nephi"),
    ("THE SECOND BOOK OF NEPHI", "2 Nephi"),
    ("THE BOOK OF JACOB", "Jacob"),
    ("THE BOOK OF ENOS", "Enos"),
    ("THE BOOK OF JAROM", "Jarom"),
    ("THE BOOK OF OMNI", "Omni"),
    ("THE WORDS OF MORMON", "Words of Mormon"),
    ("THE BOOK OF MOSIAH", "Mosiah"),
    ("THE BOOK OF ALMA", "Alma"),
    ("THE BOOK OF HELAMAN", "Helaman"),
    ("THE BOOK OF NEPHI", "3 Nephi"),  # "the son of Nephi, which was the son of Helaman"
    ("THE BOOK OF NEPHI", "4 Nephi"),  # "which is the son of Nephi, one of the disciples"
    ("BOOK OF MORMON", "Mormon"),
    ("BOOK OF ETHER", "Ether"),
    ("THE BOOK OF MORONI", "Moroni"),
]
END_MARKERS = ("THE END", "THE TESTIMONY OF THREE WITNESSES")


def _norm_title(s: str) -> str:
    s = s.strip().rstrip(",.").strip()
    return s[4:] if s.startswith("THE ") else s


def roman(s: str) -> int:
    total, prev = 0, 0
    for ch in reversed(s):
        v = ROMAN[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


def join_lines(lines: list[str]) -> str:
    out = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if out.endswith("­"):
            out = out[:-1] + line
        elif out:
            out += " " + line
        else:
            out = line
    return out.replace("­", "")


def parse(text: str) -> list[dict]:
    pages = text.split("\f")
    records: list[dict] = []
    book_idx = -1
    book = None
    chapter = 0
    para_no = 0
    kind = "front"
    buf: list[str] = []
    buf_page = None
    page_no = None
    pending_title: list[str] = []
    ended = False
    after_chapter = False

    def emit_title() -> None:
        nonlocal pending_title, kind
        records.append(
            {
                "seq": len(records) + 1,
                "book": book,
                "chapter": 0,
                "para": 0,
                "kind": "title",
                "page_start": page_no,
                "page_end": page_no,
                "text": " ".join(pending_title),
            }
        )
        pending_title = []
        kind = "body"

    def flush() -> None:
        nonlocal buf, para_no, buf_page
        joined = join_lines(buf)
        if joined:
            para_no += 1
            records.append(
                {
                    "seq": len(records) + 1,
                    "book": book,
                    "chapter": chapter if book else None,
                    "para": para_no,
                    "kind": kind,
                    "page_start": buf_page,
                    "page_end": page_no,
                    "text": joined,
                }
            )
        buf, buf_page = [], None

    for p_i, page in enumerate(pages):
        lines = page.split("\n")
        if p_i > 0 and lines:
            m = HEADER_RE.match(lines[0])
            if m and (m.group(1) or m.group(3)):
                page_no = int(m.group(1) or m.group(3))
                lines = lines[1:]
            elif page_no is not None:
                page_no += 1  # a page without a running header (book opening)
        for line in lines:
            stripped = line.strip()
            if ended:
                continue
            if stripped.rstrip(".") in END_MARKERS:
                flush()
                ended = True
                continue
            m = CHAPTER_RE.match(line)
            if m and book:
                if pending_title:
                    emit_title()
                flush()
                chapter = roman(m.group(1))
                para_no = 0
                kind = "body"
                after_chapter = True
                pending_title = []
                continue
            if TITLE_RE.match(line) and not any(c.isdigit() for c in stripped):
                nxt = book_idx + 1
                want = _norm_title(BOOKS[nxt][0]) if nxt < len(BOOKS) else None
                if want and _norm_title(stripped).startswith(want):
                    flush()
                    book_idx = nxt
                    book = BOOKS[nxt][1]
                    chapter, para_no, kind = 0, 0, "title"
                    pending_title = [stripped]
                    continue
                if pending_title:
                    pending_title.append(stripped)
                    continue
                if book is None and stripped == "PREFACE.":
                    flush()
                    kind = "preface"
                    continue
            if pending_title:
                emit_title()
            if not stripped:
                continue
            indent = len(line) - len(line.lstrip(" "))
            if indent >= 2 and buf:
                flush()
                if kind == "synopsis":
                    kind = "body"
            if not buf:
                buf_page = page_no
                if after_chapter:
                    # A chapter synopsis starts flush left; a body paragraph is indented.
                    kind = "synopsis" if indent < 2 else "body"
                    after_chapter = False
            buf.append(line)
    flush()
    records = [r for r in records if r["book"] is not None or r["kind"] == "preface"]
    # Opening pages carry no running header; count back from the first numbered page.
    known = [r["page_start"] for r in records if r["page_start"] is not None]
    if known:
        for r in records:
            if r["page_start"] is None and r["book"] is not None:
                r["page_start"] = known[0] - 1
                if r["page_end"] is None:
                    r["page_end"] = r["page_start"]
    return records


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    a = ap.parse_args(argv)
    recs = parse(a.src.read_text(encoding="utf-8"))
    with a.out.open("w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    books: dict[str, dict] = {}
    for r in recs:
        b = books.setdefault(r["book"] or "(front)", {"chapters": 0, "paras": 0, "words": 0})
        b["chapters"] = max(b["chapters"], r["chapter"] or 0)
        b["paras"] += 1
        b["words"] += len(r["text"].split())
    for name, b in books.items():
        print(f"{name:16s} chapters={b['chapters']:3d} paras={b['paras']:5d} words={b['words']:7d}")
    print(f"total words: {sum(b['words'] for b in books.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
