"""Align manuscript pages to 1830 edition paragraphs (BOM-05).

Both the printer's manuscript (PM) and the original manuscript (OM) are page-level
transcripts with no verse or paragraph structure. The 1830 edition has chapters and
paragraphs. This module maps every manuscript page onto the 1830 paragraph sequence so the
three texts can be compared unit by unit.

Method: normalize both texts to word tokens, find word 5-grams that occur exactly once in
each text (anchors), keep the longest monotone chain of anchors, and interpolate between
anchors to map any manuscript token offset to a 1830 token offset. Paragraph boundaries in
the 1830 text then give, for each manuscript page, the paragraphs it covers, and for each
paragraph, the pages (and scribes) that carry it. Gaps in the OM show up as paragraphs with
no OM page.

Usage::

    python -m ingest.align data/bom/1830/edition_1830.jsonl data/bom/jsp_printers.jsonl \
        -o data/bom/align_printers.jsonl --report data/bom/align_printers_report.md
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from collections import Counter
from pathlib import Path

WORD_RE = re.compile(r"[a-z0-9]+")
BRACKET_RE = re.compile(r"\[[^\]]*\]")  # editorial insertions like "[ 2 pages not extant ]"
N = 5


def tokens(text: str) -> list[str]:
    text = BRACKET_RE.sub(" ", text.lower())
    text = text.replace("&", " and ")
    return WORD_RE.findall(text)


def ngram_anchors(a: list[str], b: list[str], n: int = N) -> list[tuple[int, int]]:
    """(i, j) pairs where a[i:i+n] == b[j:j+n] and that n-gram is unique in both."""
    ca = Counter(tuple(a[i : i + n]) for i in range(len(a) - n + 1))
    cb = Counter(tuple(b[j : j + n]) for j in range(len(b) - n + 1))
    pos_b = {tuple(b[j : j + n]): j for j in range(len(b) - n + 1) if cb[tuple(b[j : j + n])] == 1}
    out = []
    for i in range(len(a) - n + 1):
        g = tuple(a[i : i + n])
        if ca[g] == 1 and g in pos_b:
            out.append((i, pos_b[g]))
    return out


def monotone_chain(pairs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Longest chain with strictly increasing second coordinates (pairs sorted by first)."""
    pairs = sorted(pairs)
    tails: list[int] = []
    tails_idx: list[int] = []
    prev = [-1] * len(pairs)
    for k, (_, j) in enumerate(pairs):
        pos = bisect.bisect_left(tails, j)
        if pos == len(tails):
            tails.append(j)
            tails_idx.append(k)
        else:
            tails[pos] = j
            tails_idx[pos] = k
        prev[k] = tails_idx[pos - 1] if pos > 0 else -1
    chain = []
    k = tails_idx[-1] if tails_idx else -1
    while k != -1:
        chain.append(pairs[k])
        k = prev[k]
    return chain[::-1]


class Mapper:
    """Piecewise-linear map from positions in text A to positions in text B."""

    def __init__(self, chain: list[tuple[int, int]], len_a: int, len_b: int):
        self.xs = [0] + [i for i, _ in chain] + [len_a]
        self.ys = [0] + [j for _, j in chain] + [len_b]

    def __call__(self, i: int) -> int:
        k = bisect.bisect_right(self.xs, i) - 1
        k = max(0, min(k, len(self.xs) - 2))
        x0, x1, y0, y1 = self.xs[k], self.xs[k + 1], self.ys[k], self.ys[k + 1]
        if x1 == x0:
            return y0
        return y0 + round((i - x0) * (y1 - y0) / (x1 - x0))


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def align(edition: list[dict], pages: list[dict]) -> tuple[list[dict], dict]:
    ed_recs = [r for r in edition if r["book"] is not None and r["kind"] in ("body", "synopsis")]
    ed_tokens: list[str] = []
    ed_bounds: list[int] = []  # start token of each paragraph
    for r in ed_recs:
        ed_bounds.append(len(ed_tokens))
        ed_tokens.extend(tokens(r["text"]))
    ms_tokens: list[str] = []
    ms_bounds: list[int] = []
    for p in pages:
        ms_bounds.append(len(ms_tokens))
        ms_tokens.extend(tokens(p["text"]))
    anchors = ngram_anchors(ms_tokens, ed_tokens)
    chain = monotone_chain(anchors)
    to_ed = Mapper(chain, len(ms_tokens), len(ed_tokens))

    def para_at(tok: int) -> int:
        return max(0, bisect.bisect_right(ed_bounds, tok) - 1)

    covered: dict[int, list[dict]] = {}
    page_rows = []
    for k, p in enumerate(pages):
        start = ms_bounds[k]
        end = ms_bounds[k + 1] if k + 1 < len(ms_bounds) else len(ms_tokens)
        if end - start < N:
            page_rows.append({"page": p["page"], "tokens": end - start, "para_first": None})
            continue
        e0, e1 = to_ed(start), max(to_ed(end - 1), to_ed(start))
        p0, p1 = para_at(e0), para_at(e1)
        page_rows.append(
            {
                "page": p["page"],
                "editorial_page": p.get("editorialPageNumber"),
                "tokens": end - start,
                "scribes": [s.get("name") for s in p.get("scribes") or []],
                "book_first": ed_recs[p0]["book"],
                "chapter_first": ed_recs[p0]["chapter"],
                "para_first": ed_recs[p0]["seq"],
                "book_last": ed_recs[p1]["book"],
                "chapter_last": ed_recs[p1]["chapter"],
                "para_last": ed_recs[p1]["seq"],
            }
        )
        for q in range(p0, p1 + 1):
            covered.setdefault(q, []).append(page_rows[-1])
    para_rows = []
    for q, r in enumerate(ed_recs):
        cov = covered.get(q, [])
        para_rows.append(
            {
                "seq": r["seq"],
                "book": r["book"],
                "chapter": r["chapter"],
                "para": r["para"],
                "words": len(tokens(r["text"])),
                "pages": [c["page"] for c in cov],
                "scribes": sorted({s for c in cov for s in c.get("scribes", [])}),
            }
        )
    stats = {
        "ms_tokens": len(ms_tokens),
        "ed_tokens": len(ed_tokens),
        "anchors": len(anchors),
        "chain": len(chain),
        "pages": len(pages),
        "pages_aligned": sum(1 for r in page_rows if r.get("para_first")),
        "paragraphs": len(para_rows),
        "paragraphs_covered": sum(1 for r in para_rows if r["pages"]),
    }
    return page_rows, {"paragraphs": para_rows, "stats": stats}


def report(stats: dict, para_rows: list[dict], label: str) -> str:
    uncovered = [r for r in para_rows if not r["pages"]]
    by_book: dict[str, list[int]] = {}
    for r in para_rows:
        by_book.setdefault(r["book"], [0, 0])
        by_book[r["book"]][0] += 1
        by_book[r["book"]][1] += bool(r["pages"])
    lines = [f"# Alignment report: {label}", ""]
    lines.append(
        f"- Manuscript tokens: {stats['ms_tokens']:,}; 1830 tokens: {stats['ed_tokens']:,}"
    )
    lines.append(
        f"- Unique shared 5-gram anchors: {stats['anchors']:,}; monotone chain: {stats['chain']:,}"
    )
    lines.append(f"- Pages aligned: {stats['pages_aligned']} of {stats['pages']}")
    lines.append(
        f"- 1830 paragraphs covered: {stats['paragraphs_covered']} of {stats['paragraphs']}"
        f" ({100 * stats['paragraphs_covered'] / max(1, stats['paragraphs']):.1f}%)"
    )
    lines += ["", "| Book | Paragraphs | Covered |", "| --- | --- | --- |"]
    for b, (n, c) in by_book.items():
        lines.append(f"| {b} | {n} | {c} |")
    if uncovered:
        lines += ["", "## Uncovered paragraph runs (1830 seq)", ""]
        run = [uncovered[0]["seq"]]
        runs = []
        for r in uncovered[1:]:
            if r["seq"] == run[-1] + 1:
                run.append(r["seq"])
            else:
                runs.append(run)
                run = [r["seq"]]
        runs.append(run)
        for run in runs:
            first = next(r for r in para_rows if r["seq"] == run[0])
            last = next(r for r in para_rows if r["seq"] == run[-1])
            lines.append(
                f"- seq {run[0]}-{run[-1]}: {first['book']} ch {first['chapter']} to "
                f"{last['book']} ch {last['chapter']} ({len(run)} paragraphs)"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("edition", type=Path)
    ap.add_argument("pages", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True, help="per-page alignment JSONL")
    ap.add_argument("--paragraphs", type=Path, help="per-paragraph coverage JSONL")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--label", default="")
    a = ap.parse_args(argv)
    page_rows, extra = align(load_jsonl(a.edition), load_jsonl(a.pages))
    with a.out.open("w", encoding="utf-8") as fh:
        for r in page_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    if a.paragraphs:
        with a.paragraphs.open("w", encoding="utf-8") as fh:
            for r in extra["paragraphs"]:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    text = report(extra["stats"], extra["paragraphs"], a.label or a.pages.stem)
    if a.report:
        a.report.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
