# Decisions made after results were seen

Every choice made after the relevant results were known is recorded here, with who made it and
why. The paper's limitations section (BOM-36) reports each one; none may be presented as
pre-registered. Choices that change how the registered analysis runs are also listed in
`config/preregistered.yaml` under `pending_amendment` until an OSF amendment registers them.

## D1. Burrows' and Cosine Delta enter the synthesis as closed-set evidence only (2026-10-30)

**Decided by:** the owner, Dave Taylor, after BOM-21 run 2's results were seen.

**The problem.** Section 7 passes a method only if its closed-set accuracy is at least 90% *and*
its open-set false-positive rate is at most 5%; a method that fails is excluded. Burrows' Delta
(100%) and Cosine Delta (97.2%) clear the closed-set bar, but section 6.1 gives them no
verification score, so they cannot say "none of these" and the open-set half cannot be applied.
The registration did not anticipate a method that can take only half the test.

**The decision.** The two Deltas are kept, limited to closed-set answers: which listed candidate
is closest. They are never used as evidence that a candidate did or did not write a text, and
never toward a "none of these" conclusion.

**What the paper must say** (owner's condition). That the Deltas **did not pass the registered
bar**, because its open-set half could not be shown; that they are kept only for closed-set
answers; and that this was decided after the benchmark results were known. Every Delta result
in the paper carries that limitation beside it, not only in a footnote.

**Limitation found later (BOM-58, 2026-10-30).** On 30 fresh corpus authors the Deltas'
closed-set accuracy is 63% (Burrows) and 62% (Cosine), against 100% and 97% on the BOM-21 tasks
of 3 to 11 authors: the closed-set bar is met at the scale of a short candidate list, not a
corpus-wide one. The paper reports this beside every Delta result.

**Status:** to be registered in the next OSF amendment (`pending_amendment`:
`synthesis.delta_closed_set_only`). Evidence: `data/benchmark/benchmark.json` (verdict),
BOM-21 issue.

## D2. General Imposters' pseudo-biblical imposter pool topped up to the registered 200 (2026-10-30)

**Decided by:** Claude, during BOM-21; registered post hoc as Amendment 7, Change 8 (OSF revision
6ae500f8f0e01c4f4105c6bd). Run 1 used 10 imposters and let in a copy of a test author's book; run
2 used all curated works plus a seeded fill from Amendment 3's list. Run 1 is published beside
run 2 (`data/benchmark/run1/`). General Imposters failed section 7 in both runs.
