# King James Bible: sources and how to recreate `data/kjv/`

Everything here is public domain and committed.

## 1. Working text: 1769 standardized KJV with Apocrypha (eBible.org)

- `raw/ebible-eng-kjv_vpl.txt`: eBible.org's verse-per-line export of the King James Version
  with Apocrypha/Deuterocanon, ID `eng-kjv`, 1769 standardized text, public domain.
  https://ebible.org/kjv/ (download: https://eBible.org/Scriptures/eng-kjv_vpl.zip).
  `raw/ebible-eng-kjv_about.htm` is the archive's own notice.
- `kjv.jsonl`: one record per verse from `ingest.kjv`: book code, book name, section (OT,
  Apocrypha, NT), chapter, verse, reference, `text` (brackets that mark translator-supplied
  words removed) and `text_marked` (brackets kept). 80 books, 36,822 verses, about 934,000
  words.
- Why this text: the 1769 Oxford standardization is the text every American KJV of the 1820s
  reprinted; a clean digital edition avoids OCR noise in the masking step (BOM-16).

## 2. Period witness: 1828 H. & E. Phinney, Cooperstown, with Apocrypha

- `raw/phinney-1828-cooperstown-ocr.txt`: raw OCR of a scanned copy of the 1828 Phinney
  stereotype edition (Brigham Young University copy), Internet Archive item
  `holybiblecontain00cann`. This is the edition Joseph Smith's family bought in October 1829
  and later used for the Bible revision (Joseph Smith Papers, "Bible Used for Bible
  Revision"). Not parsed; used only to confirm the printing carries the 1769 text.
- `reports/phinney_1828_vs_1769.md`: anchor-reach comparison from `ingest.kjv --check-ocr`.

## 3. Rebuild

```
scripts/fetch_kjv.sh
uv run python -m ingest.kjv data/kjv/raw/ebible-eng-kjv_vpl.txt -o data/kjv/kjv.jsonl \
    --check-ocr data/kjv/raw/phinney-1828-cooperstown-ocr.txt \
    --report data/kjv/reports/phinney_1828_vs_1769.md
uv run python -m metadata.manifest verify data/kjv data/manifests/kjv.jsonl
```

Fetched 2026-10-15.
