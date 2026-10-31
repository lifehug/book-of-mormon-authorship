# data/italics/: the King James italics test (BOM-62)

Plan: `docs/italics-plan.md` (Amendment 11). Offsets and counts only; no text.

| File | What | Rebuild |
| --- | --- | --- |
| `translation_ranges.json` | character ranges of each independent translation's translation text, read from its layout before any count | `uv run python -m eval.italics ranges` (seconds) |

Sources: Lowth's *Isaiah* (1795) https://archive.org/details/isaiahnewtransla01lowt and
https://archive.org/details/isaiahnewtransla02lowt; *A New Translation of Isaiah* (1790)
https://archive.org/details/bim_eighteenth-century_a-new-translation-of-isa_1790; *A New
Translation of the Book of Psalms* (1807), Harvard Institutional Books `AH5KIN` (text not
published; `docs/replication.md`). Italics: `data/kjv/kjv.jsonl` (`text_marked`).
