# Validation benchmark results (BOM-21)

Pre-registration section 7: before any Book of Mormon scoring, each method runs on known authors.
A method **passes** if its closed-set accuracy on 5,000-word samples is at least 90% and, at its
calibrated threshold, its open-set false-positive rate is at most 5%. A method that fails is
reported and excluded from the synthesis. Construction: Amendment 7, Change 8. Code:
`eval/benchmark.py`. Numbers: `benchmark.json` (run 2); run 1, with its two defects, in `run1/`.

## Tasks

The Federalist Papers (Hamilton, Madison, Jay); four known authors of imitation scripture (Hunt,
Snowden, Linning, Hughes); Walter Scott's two novels dictated in 1819, against his hand-written
novels and ten contemporaries. 20 seeded 5,000-word tests per author, held out of the reference.

## Verdicts (run 2, registered settings)

| Method | Closed set (>= 90%) | Open-set false positives (<= 5%) | Verdict |
| --- | --- | --- | --- |
| Burrows' Delta | 100% | cannot say "none" (no verification score in 6.1) | closed-set evidence only (decision D1, post hoc) |
| Cosine Delta | 97.2% | cannot say "none" | closed-set evidence only (D1) |
| General Imposters | 83.3% | match threshold at the maximum score | **fails** |
| ENSC (BOM-20 version) | 100% | 66.1% at alpha 0.5 | **fails** |

Where General Imposters goes wrong: Hunt's passages are given to Snowden 13 times in 20 (both
wrote American war history in King James style), and Scott's dictated novels to Galt 11 times in
60. ENSC says "none of these" too rarely.

## Does the verdict depend on the settings? (54 alternative configurations)

`bom multiverse` reran the benchmark under every combination in `config/multiverse.yaml`
(`data/classic/multiverse_benchmark_summary.json`):

| Method | Closed-set bar met | Both halves met |
| --- | --- | --- |
| Burrows' Delta | 54 of 54 | (cannot say "none") |
| Cosine Delta | 54 of 54 | (cannot say "none") |
| ENSC (BOM-20 version) | 54 of 54 | 0 of 54 |
| General Imposters | 18 of 54 | 8 of 54 |

The Deltas' and ENSC's verdicts do not depend on the settings. General Imposters' does: it passes
in 8 configurations, all of which sample 30% of the features per round (registered: 50%). That
is a lead for BOM-58, not a result: choosing the passing setting after seeing it would be
fitting the benchmark, so it must be stated in advance, tested on fresh known-author texts and
registered before use.

## What happened next

BOM-57 found the General Imposters implementation faithful (its failure is the method's) and the
BOM-20 ENSC not faithful (its failure was our reconstruction's). BOM-58 decides repair or
retirement under those findings.
