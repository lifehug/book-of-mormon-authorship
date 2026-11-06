# The Bayesian synthesis (BOM-35)

Written 2026-11-06, before any Book of Mormon text is scored. Pre-registration 6.7 (with Amendment
7's equal-weight run) fixes the prior, the weights and the sensitivity analyses; this plan fixes how
each method's blind output becomes a likelihood. Draft Amendment 34
(`paper/amendment-034-osf-text.md`). Code: `synth/model.py`.

## Hypotheses

- Each candidate with a reliable confirmatory sample (pre-1830, at least 10,000 masked words; from
  `data/benchmark/alm_candidates_plan.json`): today Ethan Smith, Gilbert J. Hunt, Solomon Spalding.
  Joseph Smith and Oliver Cowdery's pre-1830 samples are flagged unreliable and get no prior mass
  (6.7: "candidates with reliable samples"); their methods' scores are still reported.
- "Not in set".
- Secondary (Amendment 5): the same with the post-1830 reliable samples added (Cowdery, Pratt,
  Rigdon, Phelps), reported as a separate, labelled run.
- The internal narrators (H1c, 6.3) are a separate question and are reported beside, not as a
  hypothesis in this model.

## From a method's output to a likelihood

Three method families, one representative each, the method that gives 6.1 its verification score:

| Family | Method | Closed-set pick | 6.1 call |
| --- | --- | --- | --- |
| Classical | General Imposters | highest share of trials won | `gi_call` |
| Embedding | style fingerprints | smallest cosine distance | `call` |
| Authorial | candidate language models | largest margin over the best control model | `call` |

Per Book of Mormon chunk and family, the observation is (the hypothesis candidate ranked first, 6.1's
band for it: match, inconclusive or non-match). Its likelihood uses only the family's benchmark
behaviour:

```
L(c)    = a              * P(band | true author)     if the pick is c
        = (1 - a)/(K - 1) * P(band | not the author)  otherwise
L(none) = (1 / K)        * P(band | not the author)
```

- `a`: the family's closed-set accuracy on the benchmark (classical and embedding: BOM-21/BOM-30's
  benchmark; authorial: the candidates' held-out windows, Amendment 30).
- `P(band | ...)`: the shares of the benchmark's positives and open-set negatives in each band at
  the committed 6.1 thresholds (`data/blind/thresholds.json`), add-0.5 smoothed so no band has
  probability zero. Computed by `python -m synth.model rates` into
  `data/synthesis/rates_<size>.json` (one per model size), from benchmark data only.
- Under "not in set" the pick is taken as uniform over the K candidates (the benchmark never tests a
  closed-set pick with the author absent; this is an assumption, stated).

**Chunks are not independent** (one book, one author's habits throughout), so a half's evidence from
a family is the **mean** of its chunks' log likelihoods: the half counts as one observation. The sum
(chunks independent) is reported as an upper bound on confidence.

## Weights and the posterior

```
log P(h | half) = log prior(h) + sum_f  w_f * mean_chunks log L_f(h)  + const
w_f = a_f * (section 9 imitation weight of the family's method: 1, 0.5 or 0, from BOM-31)
```

Tempered likelihoods: a weight of 0 removes a family; 1 counts it fully. Prior: 0.5 on "not in set",
0.5 shared equally among the candidate hypotheses. "Both halves" adds the discovery and
confirmation halves' evidence.

## Sensitivity (6.7, Amendment 7)

- Prior on "not in set": 0.2, 0.35, 0.5, 0.65, 0.8.
- Each family dropped in turn (its weight set to 0).
- Equal weights (every family 1), as Amendment 7 adds.
- Chunks independent (upper bound).
- Discovery, confirmation and both halves, separately.
- Each family's own posterior (agreement and conflict between families).

## Reported beside, not multiplied in

- **Dating (BOM-29):** the H3 call (Amendment 19's median rule) from the grammar model, with the
  lexical model and the transformer cross-check beside it. It answers when, not who.
- **Author sweep (BOM-39):** the discovery-half leads against the expected false-lead count.
- **Access (BOM-33):** `data/access/access_table.csv`, the 0-3 documented-availability score per
  source text. Access is a plausibility condition on a *source*, not evidence about style, so it is
  not a likelihood; a candidate the methods favour whose works score 0 is flagged.
- **Manuscript evidence (BOM-34):** dictation errors, scribe changes and the timeline, as a report.
- **6.1/6.2's calls** as registered (and, if the owner's 2026-11-06 decision applies after the 1B
  benchmark, at the best achievable thresholds with the real false-match rates).

## Every size, side by side (owner, 2026-11-06; Amendment 37)

The authorial family exists once per model size (125M, 297M, 1B), so the whole synthesis runs once
per size, with that size's authorial evidence beside the shared classical and embedding families:
`data/synthesis/posterior_<size>.json`. `posterior_sizes.json` puts the sizes' posteriors in one
table for each hypothesis set and half, with each size's most probable hypothesis and whether the
sizes agree. No size is the headline: agreement across sizes is itself evidence, and
disagreement is a finding to report. A size whose candidate models are not yet validated runs
without the authorial family and says so.

## Output

`data/synthesis/posterior_<size>.json` for each size, and `posterior_sizes.json` (names and numbers
only): for primary and secondary hypotheses, the weights, posteriors per half and both, the prior grid, each family's own posterior, drop-one, equal
weights, independent chunks, and the chunk counts per family. Runs in seconds.

## Open (draft Amendment 34)

1. The likelihood above (pick term times band term) and the uniform pick under "not in set".
2. Mean-of-chunks aggregation per half.
3. One representative method per family (General Imposters for classical, not Delta or ENSC).
4. Add-0.5 smoothing of band rates.
5. Access and manuscript evidence beside, not in, the posterior.
6. Candidates with only unreliable samples (Joseph Smith, Cowdery pre-1830) carry no prior mass.
