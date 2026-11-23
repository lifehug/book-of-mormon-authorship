# data/synthesis

The Bayesian synthesis of the finished study (BOM-35, section 6.7 of the pre-registration). Every
file here is derived from other tracked results in this repository; nothing was downloaded.

| File | What | Rebuild |
| --- | --- | --- |
| `rates_<size>.json` (`pilot`, `base`, `mid`) | each method family's closed-set accuracy and the shares of benchmark positives and negatives in each 6.1 band, from benchmark data only | `python -m synth.model rates [pilot base large]`, from `data/blind/thresholds.json` and the benchmark results |
| `posterior_<size>.json`, `posterior_sizes.json` | the posterior over the reliable candidates and "not in set", per half and both, with the prior grid, drop-one, equal weights, independent chunks and the secondary candidates | `python -m synth.model run`, from the `rates` files, `data/blind/unblinded.json` and `data/benchmark/imitation.json` |
| `a43/` | the same files for the Amendment 43 rerun | as above, with the Amendment 43 inputs (`data/blind/a43/unblinded.json`) |
| `placebo/decoys.json` | the placebo check of the synthesis on decoy texts (BOM-38, statistician major 1) | the BOM-38 placebo step; see `eval/README.md` |

Added 2026-11-23, after the `study-v1` tag, because `scripts/release_check.py` found the directory
without one. The files themselves are unchanged.
