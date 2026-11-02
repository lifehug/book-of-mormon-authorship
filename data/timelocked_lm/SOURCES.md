# data/timelocked_lm (BOM-27; Amendment 16; plan `docs/timelocked-plan.md`)

All derived from the comparison corpus (`data/catalog/catalog.parquet`, texts under
`data/corpus/normalized/`, not in git). No text is stored here.

- `training_set.parquet`: work id, source, corrected year, split (train / validation) for the
  202,816 training volumes. `python -m timelocked_lm.data select`.
- `selection.json`: counts, every excluded id with its reason, and the contamination report
  (kept volumes by number of shared Book of Mormon 12-token strings; all below 20).
- `tokenizer.json`: the byte-level BPE (32,000 entries). `python -m timelocked_lm.tokenize train`.
- `tokenizer_sample.json`: the ids of the 2,456 volumes the tokenizer was fit on.

The token files (`data/corpus/timelocked_lm/tokens/`, ~50 GB, the licensed text encoded) are
local only and covered by `data/manifests/timelocked_lm_tokens.jsonl` when complete.
