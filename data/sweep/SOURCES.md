# data/sweep

The author sweep's units (BOM-39; Amendment 28, `docs/sweep-plan.md`). Ids, offsets and counts
only; no text.

| File | What | Rebuild |
| --- | --- | --- |
| `authors.parquet` | the 23,875 swept authors: works (title groups), volumes, words, profile blocks, and for the 200 calibration authors the book held out of their profile | `python -m sweep.units build` |
| `blocks.parquet` | every block: id, author, role (`profile`, `calib_profile`, `calib_query`), volume, start (whitespace word), length | the same |
| `coverage.json` | shortlist coverage at K on the 200 known books, each tagged by identity class, genre class and profile works (exploratory) | `python -m sweep.coverage` |

Inputs: `data/timelocked_lm/training_set.parquet` (the volumes), `data/catalog/catalog.parquet`
(authors, titles), `data/catalog/signatures_normalized/` (volume word counts),
`data/style_embed/authors.parquet` (who was held out of the style encoder). A block's text is
`sweep.units.block_text`: whitespace words `start` to `start + words` of the volume's BOM-15
normalised text, which lives under `data/corpus/` (licensed, not redistributed; see
`docs/replication.md`).
