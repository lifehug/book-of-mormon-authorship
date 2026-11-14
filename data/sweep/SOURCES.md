# data/sweep

The author sweep's units (BOM-39; Amendment 28, `docs/sweep-plan.md`). Ids, offsets and counts
only; no text.

| File | What | Rebuild |
| --- | --- | --- |
| `authors.parquet` | the 23,875 swept authors: works (title groups), volumes, words, profile blocks, and for the 200 calibration authors the book held out of their profile | `python -m sweep.units build` |
| `blocks.parquet` | every block: id, author, role (`profile`, `calib_profile`, `calib_query`), volume, start (whitespace word), length | the same |
| `coverage.json` | shortlist coverage at K on the 200 known books, each tagged by identity class, genre class and profile works (exploratory) | `python -m sweep.coverage` |
| `loc_cache.jsonl` | Library of Congress name authority replies (labels only) for authors without catalog life dates and the 500-author check sample; source `https://id.loc.gov/authorities/names/suggest2` (public data) | `python -m sweep.people lookup` |
| `people.parquet`, `people.json` | each swept author's life dates, their source and status in 1829; summary and the lookup's known-answer check (exploratory) | `python -m sweep.people build` |
| `ext_authors.parquet`, `ext_blocks.parquet` | BOM-89 (exploratory): 527 further known books (every other eligible held-out author, one seeded book each), blocks as the 200's | `python -m sweep.units ext` |
| `coverage_episodes<tag>[_N].json`, `bom_ranking.json`, `bom_second_opinion_<size>.json`, `pool_<name>_<size>.npz`, `pool_report_<size>.json`, `pool_fusion_pilot.json` | BOM-89/94/95 results (exploratory); see `eval/README.md` for each command | as named there |

Inputs: `data/timelocked_lm/training_set.parquet` (the volumes), `data/catalog/catalog.parquet`
(authors, titles), `data/catalog/signatures_normalized/` (volume word counts),
`data/style_embed/authors.parquet` (who was held out of the style encoder). A block's text is
`sweep.units.block_text`: whitespace words `start` to `start + words` of the volume's BOM-15
normalised text, which lives under `data/corpus/` (licensed, not redistributed; see
`docs/replication.md`).
