# Authorial language models on the validation benchmark (BOM-28)

Written 2026-11-05, before any authorial language model was fine-tuned or scored. Registered as
Amendment 22 (OSF revision 6aed5219b9cd9627025f6179). Settings: `alm.*` and
`timelocked_lm.finetune_*` in `config/preregistered.yaml`; code in `alm/benchmark.py`.

## What is registered already

5.2: one fine-tuned copy of the time-locked base model (BOM-27) per candidate; a segment's score
for a candidate is the log-perplexity ratio between that candidate's model and the base model over
fixed 512-token windows, averaged. Amendment 2: 3 epochs at learning rate 1e-5; the benchmark runs
at 125M and at 300M, a registered decision point. 6.1 and 7: a method passes the benchmark with
closed-set accuracy at least 0.90 on 5,000-word samples and an open-set false-positive rate at
most 0.05.

## What Amendment 22 fixes

- **Texts.** The benchmark's tasks, authors and works (BOM-21), as original words with the
  benchmark's King James masks, joined by spaces (a language model reads running text).
- **Held-out text.** A fine-tuned model cannot leave out a test sample it trained on, so in the
  Federalist and imitation-scripture tasks each testable author (at least 10 blocks of 1,000
  words) holds out its last max(5, ceil(n/4)) blocks; its tests are the distinct 5,000-word
  windows in that tail (up to 20). Jay is too short to test and is a candidate on all its text.
  The dictated task tests Scott's three dictated volumes (20 samples each), as the benchmark does.
- **Fine-tuning.** 3 epochs, learning rate 1e-5 constant, AdamW (0.9, 0.95), weight decay 0.1,
  clip 1.0, 1,024-token sequences, batch 8, float32 on the M4. Weights are not kept: each model
  scores its task's tests as soon as it is trained.
- **Decisions.** Closed set by the lowest score; verification score minus the score; threshold and
  false-positive rate exactly as General Imposters'.

## Sizes

| Task | Authors | Tests |
| --- | --- | --- |
| Federalist | 3 (Hamilton, Madison tested; Jay a candidate) | 26 (Hamilton 20, Madison 6) |
| Imitation scripture | 4 (Hughes, Hunt, Linning, Snowden) | 24 (11, 10, 2, 1) |
| Dictated | 11 novelists | 60 (Scott's dictated volumes) |

Fewer tests than the count-based methods' 180, because tests must come from text the author's
model never read; the counts are reported with the result.

## Known weaknesses, stated now

- Punctuation is not in the texts (the benchmark's word lists drop it); the base model was trained
  with it. This is the same for every candidate and for the base, so the ratio largely cancels it,
  but scores are lower-quality than on running text with punctuation.
- Short authors (Hughes 10,000 training words, Jay 8,377) give weak models; a short author's
  model may lose to a long one's on length alone.
- One fine-tune per author, one seed.

## Variants (Amendment 23, OSF revision 6aed57846119836b77b6964f)

Filed during the 125M primary run, before any of its scores were read, at the owner's request to
run every reasonable use of the model. Secondary; reported with the number tried.

| Variant | What changes | Code |
| --- | --- | --- |
| V1 stronger fine-tuning | Amendment 22 at learning rate 1e-4 | `alm.benchmark --variant v1` |
| V2 classifier head | one copy per task trained to name the author of a 512-token window | `alm.variants v2` |
| V3 hidden-state features | the unchanged base model's hidden states replace word counts in BOM-21's own trials (cosine nearest centroid; General Imposters) | `alm.variants v3` |

V3 reads the benchmark's word lists (lowercased, no punctuation) joined by spaces, since it reuses
BOM-21's trials as they are; the base model was trained on cased, punctuated text.

## Results (2026-11-06)

All eight runs, judged by the corrected open-set check (Amendment 25; `data/benchmark/open_set.json`,
original number beside it). Right author: closed-set accuracy (bar 0.90); false matches: the share
of tests whose best wrong author still reaches the score 95% of true authors reach (bar 0.05).

| Method | Size | Federalist | Imitation scripture | Dictated (Scott) | Overall | False matches | Passes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Primary (Amendment 22) | 125M | 0.769 | 0.958 | 1.000 | 0.936 | 0.473 | no |
| Primary | 297M | **1.000** | 0.958 | 1.000 | **0.991** | 0.382 | no |
| V1 learning rate 1e-4 | 125M | 0.808 | 0.917 | 1.000 | 0.936 | 0.455 | no |
| V1 | 297M | 0.769 | 0.958 | 1.000 | 0.936 | 0.473 | no |
| V2 classifier head | 125M | 0.769 | 1.000 | 0.917 | 0.900 | 0.282 | no |
| V2 | 297M | 0.769 | 1.000 | 0.933 | 0.909 | **0.136** | no |
| V3 hidden-state features | 125M | 0.600 | 1.000 | 0.783 | 0.839 | 0.689 | no |
| V3 | 297M | 0.650 | 1.000 | 0.767 | 0.844 | 0.717 | no |
| *General Imposters (BOM-21)* | - | | | | 0.833 | 0.617 | no |
| *ENSC (BOM-21, its own "none")* | - | | | | 1.000 | 0.661 | no |

Eight variants of the model-based method were tried (counting both sizes); none passes, so no
multiplicity question arises. What the runs show:

- **Size helps on both halves.** At 297M the primary method attributes every Federalist sample
  correctly (Madison 6 of 6, against 0 of 6 at 125M) and keeps Scott's dictated novels at 60 of 60;
  false matches fall from 0.473 to 0.382, and V2's from 0.282 to 0.136.
- **Every method can rank the candidates; none can yet say "none of these" reliably.** The best,
  V2 at 297M, still lets the best wrong author reach a true author's score 14% of the time.
- **Stronger fine-tuning (V1) does not help; the model's features in the old methods (V3) do worse
  than the language-model methods.**
- The 297M runs ran on a rented H100 (the Mac mini's 16 GB swaps on a 297M fine-tune); same code
  and settings, float32.

**Size decision (Amendment 2's decision point), owner 2026-11-06:** accuracy on the hard half is
still rising steeply with size, so the owner chose a 1B model on 8 H100s (BOM-70 for funding;
Amendment 26 to pin it). The 1B is benchmarked the same way when it exists.

## Candidate models (BOM-28, Amendment 30)

Written 2026-11-06, before any candidate or control model is fine-tuned. Code: `alm/candidates.py`
(`plan`, `train`, `validate`) and `scripts/candidates_pod.py` (the rented H100). The Book of
Mormon is not read: these models score the sealed text only in BOM-32.

**Which models.** 5.2 asks for one fine-tuned copy per candidate and per control group. A unit is a
candidate's sample type in one period, in Amendment 5's admitted provenance tiers (handwritten,
dictated, printed by the author, posthumous; scribal copies stay catalogued and out), King James
spans masked as the Book of Mormon's are (4.4), so Joseph Smith's dictated and handwritten samples
are separate units as section 3 requires. Pre-1830 units are the confirmatory ones; post-1830 units
are Amendment 5's secondary analysis, used only where BOM-48's time-split gate allows and read
one-way for the exposed candidates.

| Unit | Masked words | Held out (blocks) | Trains on | Flag |
| --- | ---: | ---: | ---: | --- |
| Ethan Smith, printed, pre-1830 | 277,391 | 70 | 207,000 | |
| Gilbert J. Hunt, printed, pre-1830 | 56,956 | 14 | 42,000 | |
| Solomon Spalding, posthumous, pre-1830 | 41,833 | 11 | 30,000 | |
| Joseph Smith, dictated, pre-1830 | 2,720 | untested | 2,720 | unreliable sample |
| Oliver Cowdery, handwritten, pre-1830 | 1,310 | untested | 1,310 | unreliable sample |
| Joseph Smith, dictated, post-1830 | 5,039 | untested | 5,039 | unreliable sample |
| Joseph Smith, handwritten, post-1830 | 6,363 | untested | 6,363 | unreliable sample |
| Oliver Cowdery, printed, post-1830 | 44,338 | 11 | 33,000 | |
| Parley P. Pratt, printed, post-1830 | 91,478 | 23 | 68,000 | |
| Sidney Rigdon, printed, post-1830 | 21,516 | 6 | 15,000 | |
| W. W. Phelps, printed, post-1830 | 28,479 | 7 | 21,000 | |

Rigdon, Pratt and Phelps have no pre-1830 text, so no confirmatory model (as BOM-43's table).

**Control groups.** One model each for the four registered groups (BOM-18): pseudo-biblical (the
curated list, `controls.pseudo_biblical`), 1820s sermons and tracts, histories with Native American
origin texts, and general prose. The groups run to hundreds of millions of words, so each model
trains on a seeded sample of about `alm.control_words` (300,000, the order of the largest candidate)
masked words: volumes in a seeded order, the middle `max(alm.control_passage_words,
ceil(300,000 / volumes))` words of each, so the 17 curated pseudo-biblical volumes each give about
17,600 words and the large groups 5,000 from each of 60 volumes.

**Held-out text, and decoys.** Amendment 22's rule unchanged: a unit with at least 10 blocks of
1,000 words holds out its last max(5, ceil(n/4)) blocks, and its tests are the distinct 5,000-word
windows in that tail (up to 20). Shorter units train on all their text and are not tested; they
already carry the unreliable flag. The tails are never trained on, so they are where BOM-32 draws
its decoy segments for candidates and controls (8: decoys from known candidates and controls);
`data/benchmark/alm_candidates_plan.json` records each tail's position.

**Training and weights.** Amendment 22's fine-tuning (3 epochs, 1e-5, AdamW, 1,024-token
sequences, batch 8, float32) from the working model the 1B benchmark picks (`base` or `large`).
Unlike the benchmark, the weights are kept (`data/corpus/alm/candidates/<size>/`, SHA-256 in the
result), because BOM-32 scores the sealed text with them.

**Validation.** Every model scores every unit's held-out windows. Reported per unit: closed-set
accuracy among all units and among the candidates, and 6.1's authorial-model score, the margin
between a candidate's model and the best control model (best control score minus the candidate's;
above zero, the candidate fits better than every control). On a control's held-out text the best
candidate's margin is reported too: how far a wrong candidate gets past the controls. The 6.1
thresholds for this margin are calibrated with the other methods' before the blind run (BOM-32);
nothing here sets them.

**Cost.** About 15 fine-tunes of 2,700 to 400,000 tokens. At 297M on one H100 in float32, well
under an hour in all; at 1B, about 2 to 3 hours plus saving and fetching about 60 GB of weights.
