# Amendment 36: the gain over prior work, and the GPT-2 ablation (BOM-68)

*Filed 2026-11-06. Evidence: `docs/prior-work-plan.md`, `eval/prior_work.py`.*

---

**Amendment 36, filed 2026-11-06, before the GPT-2 ablation is run.** BOM-68 compares the project's
models and methods with prior work on equal terms. Reporting of registered runs (the benchmark
table) needs no amendment; this fixes the two items that were not pinned.

**The table.** Every method on the BOM-21 benchmark: closed-set accuracy overall and by task with
a 95% percentile bootstrap interval over tests (10,000 resamples, seed `bom68-boot`), Amendment 25's
open-set false-match rate and pass verdict, and the test set (BOM-21's trials, or Amendment 22's
held-out tails for fine-tuned models). McNemar's exact test is reported for every pair of methods
measured on the same tests. The classical methods are also run on the held-out tails, so the
fine-tuned models can be compared with them on identical tests.

**The ablation.** Amendment 22's authorial-model pipeline (plan, held-out tails, 3 epochs at
1e-5, batch 8, 1,024-token sequences, float32, 512-token scoring windows, verdict) is repeated with
an off-the-shelf modern model in place of the time-locked base: GPT-2 small (124M) and medium
(355M), the public OpenAI releases on Hugging Face, with their own tokenizer, the revision pinned to
the commit resolved at first download and recorded. The difference from the time-locked rows is
the value of training on 1780-1830 text. GPT-2 read modern web text that may include the Book of
Mormon, so it is used on the benchmark only and never applied to the Book of Mormon.

**Published numbers.** Where prior studies report results on data we share, their numbers are shown
beside ours with the differences in setup stated: Jockers, Witten and Criddle (2008) and Fields,
Schaalje and Roper (2011) as reproduced in BOM-22.
