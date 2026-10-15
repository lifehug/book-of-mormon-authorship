"""Record which portions of the original manuscript survive (BOM-05).

Reads the per-page JSONL from ``ingest.jsp original`` and the per-page alignment from
``ingest.align``, and writes a table of surviving and missing stretches: each page's editorial
number, the modern reference the Joseph Smith Papers give it, word count, scribes, the 1830
paragraphs it maps to, and any "[ N pages not extant ]" markers the transcript carries.

Usage::

    python -m ingest.extant data/bom/jsp_original.jsonl data/bom/align_original.jsonl \
        -o data/bom/original_extant.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ingest.align import load_jsonl, tokens

GAP_RE = re.compile(r"\[\s*([^\]]*?not extant[^\]]*?)\s*\]", re.I)
REF_RE = re.compile(r"\[([^\]]+)\]")


def rows(pages: list[dict], aligned: list[dict]) -> list[dict]:
    amap = {a["page"]: a for a in aligned}
    out = []
    for p in pages:
        html_text = p.get("clear_html", "")
        gaps = GAP_RE.findall(re.sub(r"<[^>]+>", " ", html_text))
        toc = p.get("toc") or {}
        title = toc.get("pageTitle", "")
        ref = REF_RE.search(title)
        a = amap.get(p["page"], {})
        out.append(
            {
                "page": p["page"],
                "editorial_page": p.get("editorialPageNumber"),
                "jsp_title": title,
                "modern_ref": ref.group(1) if ref else "",
                "words": len(tokens(p.get("text", ""))),
                "scribes": [s.get("name") for s in p.get("scribes") or []],
                "para_first": a.get("para_first"),
                "para_last": a.get("para_last"),
                "book_first": a.get("book_first"),
                "chapter_first": a.get("chapter_first"),
                "gaps": gaps,
            }
        )
    return out


def markdown(table: list[dict]) -> str:
    total_words = sum(r["words"] for r in table)
    lines = [
        "# Original manuscript: surviving portions",
        "",
        f"{len(table)} transcribed pages, {total_words:,} words. Pages are the Joseph Smith "
        "Papers' sequence; modern references are the Papers' own page titles. Gap markers are "
        "the transcript's editorial notes about pages that do not survive.",
        "",
        "| Page | Ed. page | Modern ref | Words | Scribes | 1830 book/ch (first) | Gap notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in table:
        bk = f"{r['book_first']} {r['chapter_first']}" if r["book_first"] else ""
        lines.append(
            f"| {r['page']} | {r['editorial_page'] or ''} | {r['modern_ref']} | {r['words']} | "
            f"{', '.join(s for s in r['scribes'] if s)} | {bk} | {'; '.join(r['gaps'])} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("pages", type=Path)
    ap.add_argument("aligned", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    a = ap.parse_args(argv)
    table = rows(load_jsonl(a.pages), load_jsonl(a.aligned))
    a.out.write_text(markdown(table), encoding="utf-8")
    with a.out.with_suffix(".jsonl").open("w", encoding="utf-8") as fh:
        for r in table:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(table)} pages, {sum(r['words'] for r in table):,} words -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
