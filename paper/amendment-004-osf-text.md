# Amendment 4: genre reliability on a sample, and a label-perturbation test

*Paste-ready text for https://osf.io/6ugxc/. Reasoning in `paper/amendment-004-draft.md`.*

---

**Amendment 4, [DATE], before the corpus is labelled and before any calibration.** Pass one of
genre labelling is still running, no labelled output has been inspected, and the Book of Mormon
text remains sealed under 4.2 until BOM-32. No hypothesis, decision rule or threshold in the
original registration is changed, and the eight categories are unchanged.

**What prompted this.** Amendment 3 made two changes at once: it allowed a work to carry two
labels, and it required every record to be labelled twice with the agreement between passes
published as a reliability figure. The first change undercut the second. The 72% inter-model
disagreement that motivated double-labelling was, by measurement, about one third taxonomy
holes -- works that genuinely belonged to two categories the single-label scheme forced into
one. Allowing two labels removes that class of disagreement at its source. The census of second
passes was sized for a problem Amendment 3 had already solved.

A second, more basic point was overlooked when Amendment 4's predecessor was written. Genre
enters this study in exactly three places, and all three are pool-level: imposter selection
from genre-matched controls (5.1), genre normalization of the rare-phrase score (5.5), and the
genre-stratified null of at least 500 period volumes (6.5). No decision rule reads the label of
an individual record. The registered reliability apparatus measured per-record consistency,
which is not the quantity any conclusion depends on.

**Change 1: reliability is estimated on a stratified sample, not a census.** Amendment 3's
"every record is labelled twice" is replaced by a second pass over a stratified sample of 5,000
records, over-sampling the ambiguous categories and every record marked `uncertain`. Agreement
is reported with its confidence interval and the stratification published. At this sample size
the interval on an agreement proportion is under one percentage point, which is finer than the
quantity warrants.

The sample is stratified by source and by decade as well as by category, and agreement is
reported for each stratum, not only in aggregate. This is the one thing a census does that a
sample need not: a failure confined to one source or one period is not category-shaped and
would survive an aggregate figure. Stratifying on the dimensions along which the corpus was
assembled forces such a failure to appear in a cell of the published table.

**Change 2: the second pass uses a different model family than the first.** Amendment 3 did not
say so, and a second pass by the same model at temperature zero is close to deterministic: on a
re-ask of 20 already-labelled records, 19 returned identical labels, the single difference being
arithmetic nondeterminism rather than uncertainty. Such a figure would measure the hardware. The
second pass is therefore run by a model from a different family than the first, named in the
published method along with both models' versions. Moving reliability to a sample makes the
strongest available adversary affordable, which a census did not.

**Change 3: a label-perturbation test, which the registration did not previously contain.**
Because every use of genre is pool-level, the question that matters is not whether a given
record is labelled correctly but whether the conclusions survive the error rate that validation
measures. The hand-adjudicated sample yields an error rate per path. That rate is then injected:
labels are corrupted at random at the measured rate, with the corruption drawn from the observed
confusion between categories rather than uniformly, and the genre-dependent analyses -- the 5.1
imposter pools, the 5.5 normalization and the 6.5 null -- are recomputed over at least 100 such
perturbations. Published for each: the shift in the 99th percentile of the null, and whether any
source changes its significant-parallel status under 6.5. This runs as an axis of the BOM-40
multiverse. A conclusion that changes under perturbation at the measured error rate is reported
as label-dependent, whatever its sign.

**What is unchanged.** The eight categories, the two-label maximum, the `uncertain` option, the
few-shot prompt and its published examples, and the 300-record hand-adjudicated stratified
validation sample with its accuracy reported separately for the rule-decided and model-decided
paths. Amendment 3's routing of `uncertain` and disagreeing records to human adjudication stands,
now operating over the sampled subset.

**Direction of this change.** It removes roughly 277,000 redundant model calls and adds a
sensitivity analysis the registration did not have. The reliability figure survives with a
materially wider but still negligible interval. It is filed before any labelled output has been
read, so that it cannot be contingent on what the labels turn out to say.
