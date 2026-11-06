# Amendment 22: authorial language models on the validation benchmark

*Filed 2026-11-05. Evidence: `docs/alm-plan.md`, `alm/benchmark.py`, `eval/benchmark.py`,
`data/benchmark/tasks.json`.*

---

**Amendment 22, filed 2026-11-05, before any authorial language model is fine-tuned or scored.**
It fixes how section 5.2's authorial language models (ALMs) are run on the section 6.1/7
validation benchmark, at both registered sizes (Amendment 2's decision point). The score, the
fine-tuning epochs and learning rate, and the pass rule are as already registered.

**Texts.** The same three tasks, authors and works as the benchmark (BOM-21): the Federalist
papers by author; the known-author imitation-scripture works with King James spans masked; the
eleven novelists' reference works and Scott's three dictated volumes. A language model reads
running text, so each work is used as its original words (the benchmark's masking applied) joined
by spaces, not as the lowercased word lists the count-based methods use.

**Held-out text.** In the Federalist and imitation-scripture tasks the benchmark draws test samples
from an author's own reference text and leaves each sample out of that author's profile; a
fine-tuned model cannot leave text out after training on it. So each author's text is cut into
1,000-word blocks; an author is testable if it has at least 10 (5 for a 5,000-word sample plus
`benchmark.min_reference_blocks`); a testable author's last h = max(5, ceil(n/4)) blocks are held
out and the model is fine-tuned on the rest. Test samples are the distinct 5-block windows at
1-block steps inside the held-out tail, all of them if 20 or fewer, otherwise 20 drawn with seed
`bom28-alm-tests`. An untestable author (Jay) is a candidate fine-tuned on all its text. In the
dictated task the tests are separate volumes, so every model is fine-tuned on all reference text
and each dictated volume gives 20 random 5,000-word samples (seed `bom28-alm-tests`), as in the
benchmark.

**Fine-tuning.** One copy of the base model per author, from its trained weights: 3 epochs at
learning rate 1e-5 (registered), constant, AdamW (0.9, 0.95), weight decay 0.1, gradient clip
1.0; the author's training text tokenized with the base tokenizer, works separated by the
end-of-text token, cut into non-overlapping 1,024-token sequences (the last partial one dropped),
batches of 8, order shuffled each epoch with seed `bom28-alm-train` and the author; float32 on
the project's Apple M4.

**Score and decisions.** As 5.2: a test sample is cut into non-overlapping 512-token windows (a
last partial window is dropped); the score for candidate b is the mean over windows of the
difference between b's model's and the base model's mean token log-loss (the log-perplexity
ratio). Closed set: the candidate with the lowest score. Verification score: minus the score; the
true author's is a positive, the highest among the other candidates an open-set negative. The
match threshold and the open-set false-positive rate are computed exactly as for General
Imposters (6.1: the 95th percentile of negatives; the rate measured on two held-out folds, seed
`benchmark-alm-fold`). The method passes, as 7, with overall closed-set accuracy at least 0.90 and
open-set false-positive rate at most 0.05. Both sizes are run and both results are reported;
Amendment 2's further amendment on size stays available.
