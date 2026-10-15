"""Word-level differences between a manuscript and the 1830 edition (BOM-05).

Takes the alignment from ``ingest.align`` and, for every 1830 paragraph that a manuscript
covers, compares the paragraph's words with the manuscript words mapped to the same span.
Reports similarity per paragraph and per book, and lists the most-changed paragraphs, so the
amount of editing between dictation, copying, and typesetting is on record.

Usage::

    python -m ingest.diff_report data/bom/1830/edition_1830.jsonl data/bom/jsp_printers.jsonl \
        -o data/bom/diff_printers.jsonl --report data/bom/diff_printers_report.md
"""

from __future__ import annotations

import argparse
import bisect
import difflib
import json
import sys
from pathlib import Path

from ingest.align import Mapper, load_jsonl, monotone_chain, ngram_anchors, tokens


def paragraph_diffs(edition: list[dict], pages: list[dict]) -> list[dict]:
    ed_recs = [r for r in edition if r["book"] is not None and r["kind"] in ("body", "synopsis")]
    ed_tokens: list[str] = []
    ed_bounds: list[int] = []
    for r in ed_recs:
        ed_bounds.append(len(ed_tokens))
        ed_tokens.extend(tokens(r["text"]))
    ed_bounds.append(len(ed_tokens))
    ms_tokens: list[str] = []
    for p in pages:
        ms_tokens.extend(tokens(p["text"]))
    chain = monotone_chain(ngram_anchors(ed_tokens, ms_tokens))
    to_ms = Mapper(chain, len(ed_tokens), len(ms_tokens))
    anchored_ed = [i for i, _ in chain]
    rows = []
    for q, r in enumerate(ed_recs):
        e0, e1 = ed_bounds[q], ed_bounds[q + 1]
        # covered only if an anchor falls inside the paragraph
        k = bisect.bisect_left(anchored_ed, e0)
        if k >= len(anchored_ed) or anchored_ed[k] >= e1:
            rows.append({"seq": r["seq"], "book": r["book"], "chapter": r["chapter"],
                         "words": e1 - e0, "covered": False})  # fmt: skip
            continue
        m0, m1 = to_ms(e0), to_ms(e1)
        a, b = ed_tokens[e0:e1], ms_tokens[m0:m1]
        sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
        changed = sum(
            max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"
        )
        rows.append(
            {
                "seq": r["seq"],
                "book": r["book"],
                "chapter": r["chapter"],
                "words": e1 - e0,
                "covered": True,
                "ms_words": m1 - m0,
                "ratio": round(sm.ratio(), 4),
                "changed_words": changed,
            }
        )
    return rows


def report(rows: list[dict], label: str) -> str:
    cov = [r for r in rows if r["covered"]]
    lines = [f"# Difference report: {label}", ""]
    if not cov:
        return "\n".join(lines + ["No covered paragraphs."]) + "\n"
    tw = sum(r["words"] for r in cov)
    tc = sum(r["changed_words"] for r in cov)
    lines.append(f"- Covered paragraphs: {len(cov)} of {len(rows)}; words compared: {tw:,}")
    lines.append(f"- Words in a changed region: {tc:,} ({100 * tc / max(1, tw):.2f}%)")
    lines.append(
        f"- Mean paragraph similarity (difflib ratio): "
        f"{sum(r['ratio'] for r in cov) / len(cov):.4f}"
    )
    by_book: dict[str, list[int]] = {}
    for r in cov:
        b = by_book.setdefault(r["book"], [0, 0, 0])
        b[0] += 1
        b[1] += r["words"]
        b[2] += r["changed_words"]
    lines += ["", "| Book | Paragraphs | Words | Changed | % |", "| --- | --- | --- | --- | --- |"]
    for b, (n, w, c) in by_book.items():
        lines.append(f"| {b} | {n} | {w:,} | {c:,} | {100 * c / max(1, w):.2f} |")
    worst = sorted(cov, key=lambda r: r["ratio"])[:15]
    lines += [
        "",
        "## Least similar paragraphs",
        "",
        "| seq | Book | Ch | Words | Ratio |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in worst:
        lines.append(
            f"| {r['seq']} | {r['book']} | {r['chapter']} | {r['words']} | {r['ratio']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("edition", type=Path)
    ap.add_argument("pages", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--label", default="")
    a = ap.parse_args(argv)
    rows = paragraph_diffs(load_jsonl(a.edition), load_jsonl(a.pages))
    with a.out.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    text = report(rows, a.label or a.pages.stem)
    if a.report:
        a.report.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
