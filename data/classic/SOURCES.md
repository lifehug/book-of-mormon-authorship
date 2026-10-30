# Classical stylometry outputs (Phase 3)

## `corpus_run.json` (BOM-20)

Built by `python -m classic.corpus_run` (seconds). The classical methods of `classic/` run on
corpus v1.0 to show they work at scale on real authors. A demonstration only: it sets no
threshold and feeds no decision (that is BOM-21), and the Book of Mormon is not touched.

1,890 personal authors have 4+ distinct works of 15,000+ words in 1780-1830 that pass the OCR
cutoff and are duplicate keepers; 30 are drawn with the root seed. Each work contributes one
5,000-word sample from its middle; one work per author is held out and attributed among all 30
from the rest. Chance is 1 in 30 (3%). With 30 tests, each accuracy is uncertain by about +/-15
points.

Holds: the authors drawn, each one's held-out work, and per method its accuracy (Delta on 100,
300 and 1,000 most frequent words, Burrows and Cosine; Cosine Delta on character 3- and
4-grams), General Imposters scores for the true author and for one wrong author per test, and
ENSC accuracy and "none of the above" count at every shrinkage value in the registered grid.

Main finding: ENSC's open-set rule at its default alpha said "none of these" for 11 of 30 works
whose author was in the set, so its alpha must be calibrated on the benchmark (BOM-21), as the
library's own notes say. Shrinkage above 1 lowers accuracy here.

## `multiverse_demo_curve.json`, `multiverse_demo_curve.svg` (BOM-40)

Copied from `results/multiverse/` after `uv run bom multiverse`: the corpus run above repeated
under 54 configurations (`config/multiverse.yaml`: culling fraction 0.1/0.2/0.3, imposter trials
100/500, feature and imposter fractions 0.3/0.5/0.7). For each finding of the registered run
(each held-out work, each method: right author or not), the share of configurations that agree.
Median agreement 100%, lowest 50%. The Delta findings barely move; the 1,000-word lists move for
one work (67%); General Imposters moves most (94% on average, 50% at worst), as its sampling
settings change. A first demonstration of the runner; the curve is redrawn on the benchmark in
BOM-21.

## `multiverse_benchmark_curve.*`, `multiverse_benchmark_summary.json` (BOM-21, 2026-10-30)

`uv run bom multiverse` with `config/multiverse.yaml` stages `[classic_corpus_run, benchmark]`:
54 configurations (all combinations of the ranges there), each rerunning the corpus demo and the
validation benchmark. Copied from `results/multiverse/` (not in git). The summary counts, for each
method, in how many configurations it passes the closed-set bar and both halves of section 7.
Run under the config as it stood before Amendment 7 registered its pending entries (no value the
benchmark reads changed), and with the BOM-20 ENSC that BOM-57 later found not faithful.
