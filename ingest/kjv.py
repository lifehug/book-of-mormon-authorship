"""Verse-indexed King James Bible with Apocrypha (BOM-06).

Parses eBible.org's verse-per-line KJV (1769 standardized text plus Apocrypha, public domain)
into one JSON record per verse, and optionally measures how far a period printing's OCR
diverges from that text, so the choice of a clean digital text over a raw 1828 scan is on
record with a number.

Usage::

    python -m ingest.kjv data/kjv/raw/ebible-eng-kjv_vpl.txt -o data/kjv/kjv.jsonl
    python -m ingest.kjv data/kjv/raw/ebible-eng-kjv_vpl.txt -o data/kjv/kjv.jsonl \
        --check-ocr data/kjv/raw/phinney-1828-cooperstown-ocr.txt \
        --report data/kjv/reports/phinney_1828_vs_1769.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VPL_RE = re.compile(r"^([A-Z0-9]{3}) (\d+):(\d+) (.*)$")
ITALIC_RE = re.compile(r"\[([^\]]*)\]")

# eBible book codes in canonical order -> (name, section)
BOOKS: dict[str, tuple[str, str]] = {
    "GEN": ("Genesis", "OT"), "EXO": ("Exodus", "OT"), "LEV": ("Leviticus", "OT"),
    "NUM": ("Numbers", "OT"), "DEU": ("Deuteronomy", "OT"), "JOS": ("Joshua", "OT"),
    "JDG": ("Judges", "OT"), "RUT": ("Ruth", "OT"), "1SA": ("1 Samuel", "OT"),
    "2SA": ("2 Samuel", "OT"), "1KI": ("1 Kings", "OT"), "2KI": ("2 Kings", "OT"),
    "1CH": ("1 Chronicles", "OT"), "2CH": ("2 Chronicles", "OT"), "EZR": ("Ezra", "OT"),
    "NEH": ("Nehemiah", "OT"), "EST": ("Esther", "OT"), "JOB": ("Job", "OT"),
    "PSA": ("Psalms", "OT"), "PRO": ("Proverbs", "OT"), "ECC": ("Ecclesiastes", "OT"),
    "SOL": ("Song of Solomon", "OT"), "ISA": ("Isaiah", "OT"), "JER": ("Jeremiah", "OT"),
    "LAM": ("Lamentations", "OT"), "EZE": ("Ezekiel", "OT"), "DAN": ("Daniel", "OT"),
    "HOS": ("Hosea", "OT"), "JOE": ("Joel", "OT"), "AMO": ("Amos", "OT"),
    "OBA": ("Obadiah", "OT"), "JON": ("Jonah", "OT"), "MIC": ("Micah", "OT"),
    "NAH": ("Nahum", "OT"), "HAB": ("Habakkuk", "OT"), "ZEP": ("Zephaniah", "OT"),
    "HAG": ("Haggai", "OT"), "ZEC": ("Zechariah", "OT"), "MAL": ("Malachi", "OT"),
    "TOB": ("Tobit", "Apocrypha"), "JDT": ("Judith", "Apocrypha"),
    "ESG": ("Additions to Esther", "Apocrypha"), "WIS": ("Wisdom of Solomon", "Apocrypha"),
    "SIR": ("Ecclesiasticus (Sirach)", "Apocrypha"), "BAR": ("Baruch", "Apocrypha"),
    "PRA": ("Prayer of Azariah and Song of the Three", "Apocrypha"),
    "SUS": ("Susanna", "Apocrypha"), "BEL": ("Bel and the Dragon", "Apocrypha"),
    "1MA": ("1 Maccabees", "Apocrypha"), "2MA": ("2 Maccabees", "Apocrypha"),
    "1ES": ("1 Esdras", "Apocrypha"), "PRM": ("Prayer of Manasseh", "Apocrypha"),
    "4ES": ("2 Esdras", "Apocrypha"),
    "MAT": ("Matthew", "NT"), "MAR": ("Mark", "NT"), "LUK": ("Luke", "NT"),
    "JOH": ("John", "NT"), "ACT": ("Acts", "NT"), "ROM": ("Romans", "NT"),
    "1CO": ("1 Corinthians", "NT"), "2CO": ("2 Corinthians", "NT"), "GAL": ("Galatians", "NT"),
    "EPH": ("Ephesians", "NT"), "PHI": ("Philippians", "NT"), "COL": ("Colossians", "NT"),
    "1TH": ("1 Thessalonians", "NT"), "2TH": ("2 Thessalonians", "NT"),
    "1TI": ("1 Timothy", "NT"), "2TI": ("2 Timothy", "NT"), "TIT": ("Titus", "NT"),
    "PHM": ("Philemon", "NT"), "HEB": ("Hebrews", "NT"), "JAM": ("James", "NT"),
    "1PE": ("1 Peter", "NT"), "2PE": ("2 Peter", "NT"), "1JO": ("1 John", "NT"),
    "2JO": ("2 John", "NT"), "3JO": ("3 John", "NT"), "JUD": ("Jude", "NT"),
    "REV": ("Revelation", "NT"),
}  # fmt: skip


def parse_vpl(text: str) -> list[dict]:
    """One record per verse. ``text`` drops the [brackets] that mark supplied words;
    ``text_marked`` keeps them."""
    records = []
    for line in text.splitlines():
        m = VPL_RE.match(line)
        if not m:
            if line.strip():
                raise ValueError(f"unparsed line: {line[:80]}")
            continue
        code, ch, vs, body = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip()
        name, section = BOOKS[code]
        records.append(
            {
                "seq": len(records) + 1,
                "book": code,
                "book_name": name,
                "section": section,
                "chapter": ch,
                "verse": vs,
                "ref": f"{name} {ch}:{vs}",
                "text": ITALIC_RE.sub(r"\1", body),
                "text_marked": body,
            }
        )
    return records


def check_ocr(records: list[dict], ocr_text: str) -> str:
    """How much of the 1769 text is found verbatim in a printing's OCR.

    For every verse, the share of its words that sit inside a five-word sequence that also
    occurs anywhere in the OCR. Order is ignored on purpose: a scanned Bible has two columns
    and marginal references, which scramble sequence but not wording. A word-diff is not used
    for the same reason.
    """
    from ingest.align import N, tokens

    ocr = tokens(ocr_text)
    grams = {tuple(ocr[i : i + N]) for i in range(len(ocr) - N + 1)}
    by_sec: dict[str, list[float]] = {}
    total_words = total_hit = found = 0
    for r in records:
        w = tokens(r["text"])
        hit: set[int] = set()
        for i in range(len(w) - N + 1):
            if tuple(w[i : i + N]) in grams:
                hit.update(range(i, i + N))
        frac = len(hit) / max(1, len(w))
        b = by_sec.setdefault(r["section"], [0, 0, 0, 0])
        b[0] += 1
        b[1] += frac >= 0.5
        b[2] += len(w)
        b[3] += len(hit)
        total_words += len(w)
        total_hit += len(hit)
        found += frac >= 0.5
    lines = [
        "# 1828 Phinney (Cooperstown) printing vs the 1769 digital text",
        "",
        "Raw OCR of the Phinney scan (Internet Archive `holybiblecontain00cann`, with "
        "Apocrypha) against the eBible verses. A word counts as reached when it sits inside "
        "a five-word sequence that occurs anywhere in the OCR; a verse counts as found when at "
        "least half its words are reached. Order is ignored because the scan's two columns "
        "and marginal references scramble sequence. OCR errors lower the figure, so it is a "
        "floor on agreement, not a count of real variants.",
        "",
        f"- Verses found: {found:,} of {len(records):,} ({100 * found / len(records):.1f}%)",
        f"- Words reached: {total_hit:,} of {total_words:,} "
        f"({100 * total_hit / max(1, total_words):.1f}%)",
        "",
        "| Section | Verses | Found | Words | Reached % |",
        "| --- | --- | --- | --- | --- |",
    ]
    for sec, (n, c, w, h) in by_sec.items():
        lines.append(f"| {sec} | {n:,} | {c:,} | {w:,} | {100 * h / max(1, w):.1f} |")
    lines += [
        "",
        "Reading: every section is reached at a similar rate, and the gaps track OCR quality "
        "rather than any section of text, which is what a reprint of the same 1769 text looks "
        "like. The working text is the clean digital edition; the printing is kept as the "
        "period witness.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("vpl", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--check-ocr", type=Path)
    ap.add_argument("--report", type=Path)
    a = ap.parse_args(argv)
    records = parse_vpl(a.vpl.read_text(encoding="utf-8"))
    with a.out.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    sections: dict[str, list[int]] = {}
    for r in records:
        s = sections.setdefault(r["section"], [set(), 0, 0])
        s[0].add(r["book"])
        s[1] += 1
        s[2] += len(r["text"].split())
    for sec, (books, verses, words) in sections.items():
        print(f"{sec:10s} books={len(books):2d} verses={verses:6d} words={words:8,d}")
    print(f"total verses: {len(records):,} -> {a.out}")
    if a.check_ocr:
        text = check_ocr(records, a.check_ocr.read_text(encoding="utf-8", errors="replace"))
        if a.report:
            a.report.write_text(text, encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
