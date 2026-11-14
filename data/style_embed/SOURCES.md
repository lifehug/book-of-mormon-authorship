# data/style_embed/ (BOM-30, Amendment 24)

Ids and counts only; no text.

| File | What | Rebuild |
| --- | --- | --- |
| `authors.parquet` | the 8,527 qualifying authors (catalog `author_norm`): split (`train` / `heldout`, seeded hash `bom30-heldout`), works, volumes, sampled passages | `python -m style_embed.data build` |
| `works.parquet` | each author's works (first six title words) and the volume ids in each | same |
| `build.json` | config stamp and totals | same |
| `v2_works.parquet`, `v2_build.json` | BOM-89 step 3 (exploratory): each work's genre and its author's split (BOM-30's held-out authors unchanged; 5% of the training authors as validation); totals. Passages (256 per work) in `data/corpus/style_embed/v2/`, manifest `data/manifests/style_embed_v2_passages.jsonl` | `python -m style_embed.v2 build` |

The sampled passages themselves are licensed text in another form (Harvard and HathiTrust volumes
among them) and stay in `data/corpus/style_embed/` (not in git), covered by
`data/manifests/style_embed_passages.jsonl`. Sources: the time-locked training set
(`data/timelocked_lm/training_set.parquet`) and the catalog (`data/catalog/catalog.parquet`).
