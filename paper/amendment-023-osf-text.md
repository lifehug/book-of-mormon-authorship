# Amendment 23: further uses of the time-locked model on the validation benchmark

*Filed 2026-11-05. Evidence: `docs/alm-plan.md` ("Variants"), `paper/amendment-022-osf-text.md`.*

---

**Amendment 23, filed 2026-11-05, while Amendment 22's 125M benchmark run was in progress and
before any of its scores had been read.** The owner asked that every reasonable use of the
time-locked model be tested. Three variants are added to Amendment 22's authorial language models
(ALMs), each run on the same benchmark at both sizes (125M and 297M), each judged by the same pass
rule (overall closed-set accuracy at least 0.90 and open-set false-positive rate at most 0.05,
threshold and rate computed as for General Imposters). **Amendment 22's ALM stays the primary
method.** The variants are secondary: all of them are reported whatever they show, with the
number of variants tried, and a variant that passes where the primary fails is reported as such,
not substituted for it.

**V1, stronger fine-tuning.** Amendment 22 exactly, except the learning rate is 1e-4 (ten times
the registered 1e-5). Motivation: at 1e-5 a short author's copy gets few updates (Hamilton's: 33)
and may barely move from the base model.

**V2, classifier head.** Per task, one copy of the base model with a linear head over the task's
authors, applied to the mean of the final hidden states of a 512-token window; trained with
cross-entropy on the same training text as Amendment 22 (non-overlapping 512-token windows, each
labelled with its author), 3 epochs, learning rate 1e-5, AdamW as Amendment 22, batch 8, classes
weighted by the inverse of their window counts. A test sample's score for an author is the mean
over its 512-token windows of that author's log-probability. Closed set: the highest score.
Verification: the true author's score is a positive; the highest other author's score is an
open-set negative.

**V3, hidden-state features, no fine-tuning.** The base model, unchanged, maps each 1,000-word
block to the mean of its final hidden states over 512-token windows; a sample's vector is the mean
of its blocks' vectors. These vectors replace word frequencies in the benchmark's own trials (the
same 180 tests, references with each test's span left out, and the same imposter pools as
BOM-21): closed set by cosine distance to each author's mean vector; verification by General
Imposters on the vectors with the registered settings (`classic.imposters`). Because the base
model never read the benchmark authors (they were excluded from its training set), no text needs
holding out.

Not covered here and planned under their own issues: style embeddings (BOM-30) and the dating
cross-check (BOM-29).
