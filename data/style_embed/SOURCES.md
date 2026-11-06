# data/style_embed/ (BOM-30, Amendment 24)

Ids and counts only; no text.

| File | What | Rebuild |
| --- | --- | --- |
| `authors.parquet` | the 8,527 qualifying authors (catalog `author_norm`): split (`train` / `heldout`, seeded hash `bom30-heldout`), works, volumes, sampled passages | `python -m style_embed.data build` |
| `works.parquet` | each author's works (first six title words) and the volume ids in each | same |
| `build.json` | config stamp and totals | same |

The sampled passages themselves are licensed text in another form (Harvard and HathiTrust volumes
among them) and stay in `data/corpus/style_embed/` (not in git), covered by
`data/manifests/style_embed_passages.jsonl`. Sources: the time-locked training set
(`data/timelocked_lm/training_set.parquet`) and the catalog (`data/catalog/catalog.parquet`).
