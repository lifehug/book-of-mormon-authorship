# data/lab/

The lab's registry (`docs/lab/README.md`).

| File | What | Rebuild |
| --- | --- | --- |
| `registry.parquet` | one row for each catalogued work: source, kind, has text, corrected year, words, genre, duplicate keeper, OCR exclusion, author kind, swept author and life status, style-model split, language-model training split, in the passage index, sealed. Ids and flags only, no text. | `python -m lab.registry build` (seconds; reads `data/catalog/`, `data/ocr_quality/volumes.parquet`, `data/timelocked_lm/training_set.parquet`, `data/sweep/people.parquet`, `data/style_embed/authors.parquet`, and the shard tables of `data/corpus/semantic/index/`) |
| `registry.json` | column meanings, value counts, and what each rule set (`lab.views` in the config) admits | the same command |
