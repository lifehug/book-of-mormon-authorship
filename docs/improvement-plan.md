# Improving the prior methods: the plan, written before any test (BOM-60)

Committed 2026-10-30, before any of the runs below exist. BOM-21 (benchmark), BOM-22
(replications), BOM-57 (fidelity) and BOM-58 (repair or retire) found where the classical methods
fail and why. This issue tests specific improvements, as a contribution to the methods, not as a
way to rescue a method for this study: a method retired in BOM-58 stays retired here, and any
improvement used later in this study must first be registered by amendment.

## Data, and the order things happen in

- **Development** uses only data already seen: the BOM-21 tasks and the 30 fresh authors of
  BOM-58 (`data/benchmark/repair.json`).
- **Evaluation** happens once, at the end, on a second set of 30 corpus authors drawn with seed
  `"bom60-eval"` from BOM-20's eligible pool, excluding every author used by BOM-20, BOM-21,
  BOM-48 and BOM-58, and collective attributions; built exactly as BOM-58's fresh set. Each
  improvement is fixed (code and settings committed) before the evaluation set is drawn.
- Every improvement is reported against the unimproved method on the same data.

## The improvements

1. **Rarity counted by work, not by volume** (feeds BOM-24). A 4-gram's document frequency counts
   distinct works (copies collapsed through the deduplication tables and the work key of
   `metadata.pseudo_biblical`) instead of volumes. *Test:* the Johnson replication rerun both ways;
   success means a reprinted source (*The Late War*, ~11 printings) is no longer blind under the
   registered rule (at most 5 documents), without the whole-corpus null changing its 99th
   percentile for a single-printing stand-in by more than the sampling error measured in BOM-45.
2. **A verification score for Delta.** Delta's distance to the nearest profile, turned into a
   "none of these" decision by a threshold set at a 5% false-"none" rate on in-set tests (the rule
   of Amendment 7, Change 4). *Test:* section 7's open-set bar (at most 5% false positives) on the
   evaluation set, closed-set accuracy unchanged.
3. **ENSC's text-size model refitted.** Schaalje et al.'s variance model (2011, eq. 12) was fitted
   on two authors. Refit `s^2 = a c^p / w^q` on many corpus authors (development data), and test
   whether the open-set rate still swings with candidate sample length (BOM-57's sweep) and whether
   ENSC then meets section 7 on the evaluation set.
4. **General Imposters.** (a) More rounds (1,000) so the score cannot pin at its maximum; (b)
   imposters matched to the test's register (imitation-scripture imposters for imitation-scripture
   tests). *Test:* section 7 on the evaluation set, against the registered settings.
5. **Closed-set traps, measured** (no new method): how the answer moves with candidate-sample
   choice and with unscreened quotation of the target, from BOM-22's numbers.

## What counts as an improvement

An improvement is reported as **working** if on the evaluation set it beats the unimproved method
on the measure it targets and does not make the other measure worse by more than its 95%
interval; it **meets the bar** if it also passes section 7. Both are reported, as is any
improvement that fails.

## Output

A methods report (`paper/methods-report.md`): what failed, why, the change, the evaluation
result. The benchmark itself is described as a reusable resource within BOM-44's licence limits
(derived data only for licensed texts).
