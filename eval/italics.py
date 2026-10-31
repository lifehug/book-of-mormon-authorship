"""The King James italics test (BOM-62; Amendment 11).

Plan, registered before any count: ``docs/italics-plan.md``. Within every King James span the
registered masking found (4.4), each King James word is kept, changed or dropped by the text; the
shares of italic (translator-supplied) and roman words kept are compared.

``ranges`` records, from each independent translation's layout, the character ranges that hold
its translation text, before any italic word in it is counted: notes and dissertations quote the
King James text and would make an independent translation look dependent (Amendment 11).

Usage::

    python -m eval.italics ranges   # -> data/italics/translation_ranges.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import stamp

OUT = Path("data/italics")

# How each volume's translation is found, read from its layout (headings), not from its content.
LAYOUT = {
    "internet_archive:isaiahnewtransla01lowt": (
        "volume 1 holds the preliminary dissertation, then the translation from the heading "
        "'ISAIAH.' before 'THE VISION OF ISAIAH' to the end of the volume",
        "from_vision",
    ),
    "internet_archive:isaiahnewtransla02lowt": (
        "volume 2 holds only the notes ('NOTES ON ISAIAH'); no translation text",
        "none",
    ),
    "internet_archive:bim_eighteenth-century_a-new-translation-of-isa_1790": (
        "the translation runs from its first 'SECTION I' to the heading 'NOTES on ISAIAH'; "
        "short textual footnotes on its pages stay in (they cannot be cut from the OCR)",
        "section_to_notes",
    ),
    "institutional_books:AH5KIN": (
        "each psalm runs from its heading 'PSALM <n>.' to the following 'NOTES.' heading",
        "psalm_blocks",
    ),
}
# Gilbert Wakefield's Matthew (1782), listed in Amendment 11, is left out before any count: its
# OCR interleaves translation, Greek notes and scrambled columns line by line, so no range
# holds translation alone (docs/italics-plan.md, deviations before counting).


def _text(wid: str) -> str:
    from ocr_fix.normalize import norm_path

    row = next(
        r
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]
        ).to_pylist()
        if r["work_id"] == wid
    )
    return norm_path(row).read_text(encoding="utf-8", errors="replace")


def _ranges(rule: str, s: str) -> list[list[int]]:
    if rule == "none":
        return []
    if rule == "from_vision":
        m = re.search(r"ISAIAH\.\s+I\s*S\s*A\s*I\s*A\s*H\.\s+\S*\s*HE\s+VISION", s)
        return [[m.start(), len(s)]] if m else []
    if rule == "section_to_notes":
        a = re.search(r"(?m)^\s*SECTION\s+I\b", s)
        b = re.search(r"NOTES\s+on\s*'?\s*IS", s)
        return [[a.start(), b.start()]] if a and b else []
    if rule == "psalm_blocks":
        heads = [m.start() for m in re.finditer(r"(?m)^\W*PSALM\s+[IVXLC]+\.", s)]
        notes = [m.start() for m in re.finditer(r"(?m)^\s*NOTES\.", s)]
        out = []
        for h in heads:
            nxt = [x for x in notes if x > h]
            following = [x for x in heads if x > h]
            end = min(nxt[0] if nxt else len(s), following[0] if following else len(s))
            out.append([h, end])
        return out
    raise ValueError(rule)


def ranges() -> int:
    cfg = load_config()
    result = {**stamp(), "volumes": {}}
    for wid in cfg["italics"]["independent"]:
        if wid not in LAYOUT:
            result["volumes"][wid] = {"rule": "left out before counting", "ranges": []}
            print(f"{wid}: left out (layout cannot be cut)")
            continue
        how, rule = LAYOUT[wid]
        s = _text(wid)
        rs = _ranges(rule, s)
        chars = sum(b - a for a, b in rs)
        result["volumes"][wid] = {"rule": how, "ranges": rs, "chars": chars, "of": len(s)}
        print(f"{wid}: {len(rs)} ranges, {chars:,} of {len(s):,} characters")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "translation_ranges.json").write_text(json.dumps(result, indent=1) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["ranges"]:
        return ranges()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
