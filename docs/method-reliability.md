# How much to trust each method (BOM-28, BOM-36)

Written 2026-11-09, before unblinding, from benchmark data only. It records what the checks of
2026-11-09 showed about each method's stability, and how much weight each method's Book of
Mormon result can carry. The synthesis (BOM-35) and the paper's discussion read from this.
Every number is in `data/benchmark/` and reproducible from the code and `config/preregistered.yaml`.

## The checks

| Check | What it tests | Files |
| --- | --- | --- |
| Three model sizes (125M, 297M, 590M) | Does a method improve, hold, or break as the model grows? | `alm_<size>*.json` |
| Same settings on another machine | Is a result a property of the method or of one run? | `alm_<size>_v1_lrsel.json`, `alm_pilot_v2_lrsel.json` |
| Five further random seeds (Amendment 42) | How far does a method move on luck alone? | `alm_<size>_v2_seed<k>.json` |
| Learning rate chosen on held-out training text (Amendment 41) | Was a failure the method or its setting? | `lr_select_<size>.json` |
| GPT-2 in place of our models (BOM-68) | Does the time-locked training matter? | `alm_gpt2*.json` |
| Imitation test (BOM-31) | Can it see through deliberate imitation? | `imitation.json` |

All on the same 110 held-out tests (180 trials for the classical methods, the style embeddings and
V3), judged by Amendment 22's rule. "False matches" is the open-set false-match rate: how often a
method says "match" for a candidate who did not write the text.

## What each method showed

| Method | Right author (125M / 297M / 590M) | False matches | Stable? | Weight its Book of Mormon result can carry |
| --- | --- | --- | --- | --- |
| **Primary language-model method** (fine-tuned copy per candidate) | 0.936 / 0.991 / 0.982 | 0.473 / 0.382 / **0.218** | **Yes.** Rerun on another machine it matched to the decimal (V1 at 1e-5 is the same procedure: 0.991 / 0.382 at 297M, 0.982 / 0.218 at 590M). Improves steadily with size. | **The strongest model-based evidence.** Ranks candidates reliably; its "match" calls still carry a 22% false-match rate at 590M, so a match is a lead, not a verdict. |
| V1 (ten times the learning rate) | 0.936 / 0.936 / 0.627 | 0.455 / 0.473 / 0.818 | No: the rate damaged the 590M (loss on new text +0.81 nats). At a sensible rate it *is* the primary method. | None beyond the primary method's. Report the registered run as a failed setting. |
| V2 (classifier head) | registered 0.900 / 0.909 / 0.764; seed range 0.66-0.93 / 0.51-0.76 / 0.40-0.78 | registered 0.282 / 0.136 / 0.391; seed range **0.09-0.93** / **0.53-0.98** / **0.32-0.93** | **No.** The same settings give false-match rates from 9% to 93% depending only on the seed. The 297M's 13.6% was an outlier. | **None.** Report as a range; no conclusion rests on it. |
| V3 (base model's internal states) | 0.839 / 0.844 / 0.844 | 0.689 / 0.717 / 0.706 | Stable, but flat: size does not help. | Low: high false-match rate. |
| General Imposters (classical) | 0.833 | 0.617 | Deterministic | Moderate as a ranker; weak at "match". |
| Burrows / Cosine Delta (classical) | 1.000 / 0.972 | no verification score | Deterministic | Good rankers on the classical trials; cannot say "none". |
| ENSC | 1.000 | 0.661 | Deterministic | Ranker; its own "none" answer is unreliable. |
| Style embeddings (297M encoder) | 0.839 | 0.500 | One run | Moderate; the 590M encoder is in training. |
| GPT-2 124M / 355M, primary method | 0.900 / 0.945 | 0.918 / 0.855 | One run each | Shows the time-locked training matters: our models halve the false matches. |

**No method passes the registered bar** (right author at least 0.90 *and* false matches at most
0.05). Every method can rank candidates; none can yet say "none of these" reliably.

## Imitation

The 17 imitation texts (BOM-31) test whether a method is fooled by someone writing in another's
style. The classical methods do best (Burrows and Cosine Delta 13/18); every model-based method
does worse (primary 5 / 7 / 6 of 17 by size), and size does not help. **If the Book of Mormon was
written in deliberate imitation of scripture, the model-based methods are the more likely to be
misled.** The synthesis already weights each family by its imitation result.

## How this shapes reading the blind results

1. **Lead with the primary method and the classical methods.** They are stable and reproducible.
   Report every other method beside them, never instead.
2. **A "match" is a lead, not an attribution.** The best false-match rate is 22% (primary, 590M).
   With seven candidates, a chance match is expected somewhere; the false-match ladder
   (Amendment 33) gives each call its real rate.
3. **Agreement across independent families counts more than any one method.** The registered
   rule 6.2 asks for two families; the synthesis (BOM-35) weights each by benchmark accuracy and
   imitation robustness.
4. **V2 carries no weight**, whatever it says about the Book of Mormon.
5. **Size trends are evidence too.** If the primary method's answer firms up from 125M to 590M,
   that is a better sign than any single size's call; if it wanders, say so.
6. **Sample size:** 110 tests gives a 95% interval of roughly 15-30% around the 590M's 21.8%.

## What would raise trust

- A larger model: the primary method's false matches fell 0.473, 0.382, 0.218; a 1B with QK-norm
  might reach about 0.10-0.17 (an extrapolation from three points, not a forecast).
- More benchmark tests, to narrow the intervals.
- Seed spreads for the primary method too (it reproduced exactly across machines, but has one
  seed per author).
