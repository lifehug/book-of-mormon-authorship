# Amendment 33 (DRAFT, not filed): the blind run's per-chunk scorers and 6.1 thresholds (BOM-32)

*Draft 2026-11-06. Evidence: `docs/blind-run-plan.md`, `classic/blind_score.py`,
`style_embed/blind_score.py`, `alm/blind_score.py`, `blind/thresholds.py`. File before anything is
sealed or scored.*

---

**Amendment 33, filed [date], before anything is sealed or any Book of Mormon text is scored.**
It fixes how each validated attribution method scores a sealed chunk, which section 8 and 6.1 leave
open. Decision rules are unchanged.

**References.** Every attribution method compares a chunk with the same candidate units as the
authorial models (Amendment 30: candidate x sample type x period in the admitted provenance tiers,
King James spans masked), with every decoy span listed in `data/blind/withheld.json` cut out of the
references, so no decoy is scored against its own text. Units under 10,000 words are scored and
carry the unreliable-sample flag.

**Decoys come only from text no authorial model trained on.** Amendment 32's candidate decoys
are drawn only from the candidate unit's held-out tail recorded in BOM-28's plan (Amendment 30),
the unit's documents taken in the plan's order, and a unit without a held-out tail gives none;
candidate texts are grouped by the plan's units, not by file name. Control decoys are drawn only
from volumes no control model sampled. Each candidate still keeps 10,000 words out of the decoys
as its reference. Otherwise a model would score a decoy it had trained on.

**Classical methods** (as validated in BOM-21): 1,000-token reference blocks, the middle registered
MFW count from the reference blocks only, Burrows and Cosine Delta on the mean profiles (z-scored on
the blocks), General Imposters with the registered settings, ENSC with the benchmark's calibrated
shrinkage and alpha. **General Imposters' pool** for the Book of Mormon is the pseudo-biblical
benchmark task's pool (the curated list filled from the pseudo-biblical controls: 5.1's
genre-matched controls), less the candidates' own works and every withheld source volume. Seeds
`bom32-classic` and `bom32-style`.

**Style embeddings** (as validated in BOM-30): each chunk and each unit's references embedded as one
episode; cosine distance for the closed set; General Imposters on the vectors against the same pool,
embedded, for verification.

**Authorial models** (as validated in BOM-28): each unit model's mean window log-loss minus the base
model's; the closed set is the lowest-scoring candidate; 6.1's statistic is each candidate's margin
over the best control model. Each model's weights are checked against the SHA-256 recorded when it
was trained.

**6.1 thresholds,** from benchmark data only (`eval.benchmark.calibrate_gi`: match above the 95th
percentile of open-set negatives, non-match below the 5th percentile of positives): General
Imposters from the committed BOM-21 thresholds; style embeddings from the BOM-30 benchmark's own
positives and negatives; authorial models from the candidates' held-out windows (positives: the true
candidate's margin on its own windows; negatives: each window's largest margin of any other
candidate). Written to `data/blind/thresholds.json` and committed before the blind run.


**[Choose one at filing, after the 1B benchmark; owner's decision of 2026-11-06.]**
(a) If every method family that the working model affects reaches 6.1's 5% rate on the benchmark,
6.1 and 6.2 stand as registered.
(b) Otherwise, **post hoc** (decided after the benchmark results, before any Book of Mormon text is
scored): the registered 6.1 thresholds are not achievable for General Imposters and the style
embeddings (their match thresholds are 1.0, the largest possible score). Each method returns
*match* when its score reaches its calibrated threshold (at or above, not strictly above), and the
false-match rate it actually achieves on the benchmark is reported beside every call. 6.2's
two-family rule is unchanged. The registered reading is reported beside it.
