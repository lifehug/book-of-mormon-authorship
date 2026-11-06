# The gain over prior work, on equal terms (BOM-68)

Written 2026-11-06. Code: `eval/prior_work.py`. Amendment 36 (`paper/amendment-036-osf-text.md`,
draft) pins the GPT-2 ablation and the table's settings. Owner's goal (2026-11-05): a clear measure
of how much better, or not, the project's models and methods do than prior work, on the same tests,
with uncertainty.

## One table

Every method on the BOM-21 benchmark (Federalist, imitation scripture, dictated), with:
- closed-set accuracy overall and by task, with a 95% bootstrap interval over tests;
- Amendment 25's open-set false-match rate (threshold from the positives) and the pass verdict
  (closed set at least 0.90, false matches at most 0.05);
- the test set it was measured on, since there are two (below);
- McNemar's exact test for every pair of methods measured on the same tests in the same order.

**Two test sets, and why.** The classical methods, the style embeddings and V3 score BOM-21's own
trials (180 tests; each test's span is left out of the references). A fine-tuned language model
cannot leave a test out of what it trained on, so the ALM primary, V1 and V2 score Amendment 22's
held-out tails (110 tests). Accuracies on the two sets are not directly comparable: pairs are
tested only within a set, and the table says which set each number comes from.

## Current numbers (2026-11-06, `python -m eval.prior_work table`)

| Set | Method | Prior or ours | Tests | Closed set (95%) | False matches | Passes |
| --- | --- | --- | ---: | --- | ---: | --- |
| trials | Burrows' Delta | prior | 180 | 1.000 (1.000-1.000) | n/a (no verification score) | - |
| trials | Cosine Delta | prior | 180 | 0.972 (0.944-0.994) | n/a | - |
| trials | ENSC | prior | 180 | 1.000 (no per-test records) | 0.661 | no |
| trials | General Imposters | prior | 180 | 0.833 (0.778-0.889) | 0.617 | no |
| trials | Style embeddings | ours | 180 | 0.839 (0.783-0.889) | 0.500 | no |
| trials | V3 hidden states, 125M | ours | 180 | 0.839 (0.783-0.889) | 0.689 | no |
| trials | V3 hidden states, 297M | ours | 180 | 0.844 (0.789-0.894) | 0.717 | no |
| tails | ALM primary, 125M | ours | 110 | 0.936 (0.891-0.982) | 0.473 | no |
| tails | ALM primary, 297M | ours | 110 | 0.991 (0.973-1.000) | 0.382 | no |
| tails | V1 (lr 1e-4), 125M | ours | 110 | 0.936 (0.891-0.982) | 0.455 | no |
| tails | V1, 297M | ours | 110 | 0.936 (0.891-0.982) | 0.473 | no |
| tails | V2 classifier head, 125M | ours | 110 | 0.900 (0.845-0.955) | 0.282 | no |
| tails | V2, 297M | ours | 110 | 0.909 (0.855-0.955) | 0.136 | no |

Paired results that matter (McNemar, exact):
- **Word counts beat model features on closed-set accuracy.** Burrows' Delta beats V3 at 297M (28
  tests only Delta gets right, 0 only V3; p < 1e-8) and Cosine Delta beats it (24 to 1). V3 ties
  General Imposters (20 to 18) and the style embeddings (20 to 19).
- **Within the language models, size helps the primary score:** the 297M primary beats the 125M
  primary (6 to 0, p 0.03) and V2 at 297M (10 to 1, p 0.01). V2 trades closed-set accuracy for the
  lowest false-match rate of any method (0.136).
- **No method passes.** The best false-match rate is V2 at 297M, 0.136, against the 0.05 bar.

Published numbers beside ours (item 4 of the issue) are BOM-22's replications: Jockers, Witten and
Criddle 2008 (NSC and Delta chapter attributions, published counts against ours, with our texts and
with their data) and Fields, Schaalje and Roper (ENSC). They attribute Book of Mormon chapters,
not benchmark tests, so they appear as counts beside ours, not as accuracies.

## What remains

| Run | Why | Where | Cost / time |
| --- | --- | --- | --- |
| Classical methods on the held-out tails | the only way to compare the fine-tuned ALMs with Delta and General Imposters on identical tests | Mac CPU | minutes; code to write (`eval.benchmark`'s methods on `alm.benchmark.plan`'s tests and training text) |
| GPT-2 124M ablation (`ablation gpt2`) | what training on 1780-1830 text adds at the pilot's size | Mac GPU (as the 125M ALM runs) | a few hours, no money |
| GPT-2 355M ablation (`ablation gpt2-medium`) | the same at the base's size | one H100 (the Mac swaps at this size) | ~1 h, ~$4 |
| The 1B (BOM-27) rows | the working model's benchmark | H100, already queued (`scripts/after_1b.sh`) | ~$15-40 |
| Rescore and table | after each run | Mac | seconds |

The ablation is directly comparable to the ALM rows: same plan, held-out tails, fine-tuning,
scoring and verdict; only the base model and its tokenizer differ.

## Limits

- GPT-2 (2019, WebText) read modern web text that may include the Book of Mormon and writing about
  it; it is a benchmark-only comparison and is never applied to the Book of Mormon.
- GPT-2's sizes (124M, 355M) are close to, not equal to, the time-locked pilot (124M) and base
  (297M); its tokenizer differs.
- ENSC's benchmark records keep no per-test prediction, so it has no interval and no paired test.

## Classical methods on the language models' own tests (run 2026-11-06)

`python -m eval.prior_work classic-tails` (about 3 minutes on the Mac CPU) scores Burrows and
Cosine Delta, General Imposters and ENSC (the benchmark's calibrated shrinkage 0.5, alpha 0.5) on
Amendment 22's 110 held-out tests, in the same order, so `table` pairs them with the fine-tuned
models test by test (`data/benchmark/prior_work_classic_tails.json`).

| Method (held-out tails, n=110) | Closed set | False matches |
| --- | --- | --- |
| Burrows Delta | 0.955 | - |
| Cosine Delta | 0.818 | - |
| General Imposters | 0.745 | 0.827 |
| ENSC | 0.964 | 0.782 |
| ALM 297M primary | 0.991 | 0.382 |
| ALM 297M V2 | 0.909 | 0.136 |

Paired (exact McNemar): the 297M primary beats General Imposters 27 to 0 (p 1.5e-8) and Cosine
Delta 19 to 0 (p 4e-6); against Burrows Delta (4 to 0, p 0.13) and ENSC (3 to 0, p 0.25) the
difference is not significant. On false matches every fine-tuned model is far below General
Imposters and ENSC on these tests.

GPT-2 ablation on a rented H100: `python -m eval.prior_work files` lists its 43 input files; the
job pins `transformers==5.22.1` (declared in the `semantic` extra) on the pod.
