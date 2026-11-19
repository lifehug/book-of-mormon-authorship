# data/lab/

The lab's registry (`docs/lab/README.md`).

| File | What | Rebuild |
| --- | --- | --- |
| `registry.parquet` | one row for each catalogued work: source, kind, has text, corrected year, words, genre, duplicate keeper, OCR exclusion, author kind, swept author and life status, style-model split, language-model training split, in the passage index, sealed. Ids and flags only, no text. | `python -m lab.registry build` (seconds; reads `data/catalog/`, `data/ocr_quality/volumes.parquet`, `data/timelocked_lm/training_set.parquet`, `data/sweep/people.parquet`, `data/style_embed/authors.parquet`, and the shard tables of `data/corpus/semantic/index/`) |
| `registry.json` | column meanings, value counts, and what each rule set (`lab.views` in the config) admits | the same command |
| `sources.json` | the record of every outside source fetched for the new tests (BOM-99, BOM-102 to BOM-108): exact address, terms, where it sits on disk, size, SHA-256, date, and whether the fetch succeeded. Names and numbers only. The files themselves are in `data/corpus/lab/sources/` (open material; local disk and backup) and `data/private/lab/sources/` (copyrighted; private repository). | `python -m lab.sources fetch` (about an hour; resumes), then `python -m lab.sources marc` for the translation labels. Why each source: `docs/research/2026-11-18-sources-for-new-tests.md` |
