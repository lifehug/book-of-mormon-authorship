# pipeline/

One entry point for the analysis stages, and the multiverse runner. Issue: BOM-40.

| Command | What |
| --- | --- |
| `uv run bom run` | runs every registered stage under `config/preregistered.yaml` into `results/<config-hash>/`, with `stamp.json` (config hash, path, whether it is the registered config, git commit) |
| `uv run bom run --config my.yaml --not-strict` | the same under any config; outputs say `registered: false` |
| `uv run bom multiverse` | reruns the stages under every combination of the ranges in `config/multiverse.yaml` (feature tier by default) and writes `results/multiverse/curve.json` and `curve.svg`: per conclusion of the registered run, the share of configurations that agree |

The official result is the registered config. The multiverse is a robustness check: a
conclusion that holds in most reasonable configurations is sturdier than one that holds only in
ours. Anyone can add a config file by pull request and post their result.
`config/tiers.yaml` says what changing each setting costs to recompute.
