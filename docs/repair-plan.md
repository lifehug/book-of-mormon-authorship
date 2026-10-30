# Repair or retire: the plan, written before any test is run (BOM-58)

Committed 2026-10-30, before the fresh-data runs below exist. Its purpose is that the decision
cannot be shaped by the results: every change is named here first, tested on texts no earlier
step has used, and registered by amendment before it touches the Book of Mormon.

## What failed, and why (from BOM-21 and BOM-57)

- **General Imposters** failed section 7 under the registered settings (closed set 83.3%, match
  threshold at the maximum score). BOM-57 found our implementation faithful, so the failure is
  the method's. Across 54 settings it passed in 8, every one with 30% of features sampled per
  round (registered 50%).
- **ENSC** failed (66% open-set false positives). BOM-57 found our BOM-20 version was not the
  published method; replacing it with the published method (`classic/ensc_published.py`) is a
  correction, not a new choice. The published method has its own open-set parameter, lambda, in
  place of our alpha, so the registered alpha rule is carried over to lambda.
- **Burrows' and Cosine Delta**: closed-set evidence only (decision D1). Nothing to repair.

## The candidate repairs

1. **General Imposters, `feature_fraction` 0.3**; trials, imposter fraction, distance and word
   culling as registered.
2. **ENSC, published method**: Schaalje et al.'s latent author with the 2011 text-size
   adjustment, on relative frequencies of the benchmark's word features; shrinkage by 10-fold
   cross-validation over the registered grid (Amendment 2); lambda the smallest value on the grid
   `repair.ensc_lambda_grid_provisional` (most willing to say "none") whose false-"none" rate on
   in-set tests is at most 5% (the rule of Amendment 7, Change 4, applied to lambda).

## The fresh test

`repair.fresh_authors_provisional` corpus authors (30), drawn with seed `"bom58-fresh"` from
BOM-20's eligible pool (personal authors, not a candidate, at least `corpus_run.min_works`
distinct works of 15,000+ words), excluding every author used by BOM-20, BOM-21 or BOM-48. Each
author's held-out work (seeded) gives `benchmark.trials` 5,000-word tests; references are the
author's other works. Closed set: attribution among the 30. Open set: the true author removed.
General Imposters' imposters come from the general-prose control, excluding the 30, at the
registered pool size.

## The decision rule

A method is **repaired** if, with its candidate repair, it meets both section 7 bars (closed set
at least 90%; open-set false positives at most 5%) on the fresh test **and** on the BOM-21 tasks.
Otherwise it is **retired** for this study. Each result is reported beside the registered
settings' result on the same data. A repaired method is used on the Book of Mormon only after an
OSF amendment registers the repair (the next amendment, Amendment 8).
