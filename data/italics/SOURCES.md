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

## The 1828 Phinney Bible (the check of the italics, Amendment 11)

Internet Archive item `holybiblecontain00cann` (H. & E. Phinney stereotype edition, Cooperstown,
1828; Brigham Young University copy), https://archive.org/details/holybiblecontain00cann. In
`phinney/`, downloaded 2026-10-31: `holybiblecontain00cann_hocr_searchtext.txt.gz` (the scan's
searchable text), `..._hocr_pageindex.json.gz` (which characters of it are on which page) and
`..._page_numbers.json` and `..._scandata.xml` (which leaves are shown to readers; it maps an OCR page to its image number), each from `https://archive.org/download/holybiblecontain00cann/<file>`.
They locate a verse's page; the page images themselves are fetched by `eval.italics check` into
`phinney/pages/` (not committed; public domain, refetched by the same command).

`phinney_check.jsonl`: one line per answer, appended; the last line for a word wins. Rows
without `leaves` were asked before the leaf mapping was fixed (2026-10-31): their ITALIC and
ROMAN answers name the verse and stand, their NOT_FOUND rows were the wrong page and were asked
again. Rebuild: `uv run python -m eval.italics check`.
