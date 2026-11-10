# Paper outline (BOM-36, draft 2026-11-06)

Working title: *Authorship, borrowing and dating of the earliest Book of Mormon text: an open,
pre-registered computational study.*

Sections drafted now: `methods.md`, `results_so_far.md`, `limitations.md`. Everything marked
**[RESULT: ...]** waits on the blind run (BOM-32), the synthesis (BOM-35) or another run still in
progress, and is filled from the named file when it exists. Framing throughout: the study
identifies close candidates or their absence, with the evidence; it makes no claim about
translation, inspiration or the truth of the book's contents (pre-registration section 1).

## 1. Introduction

- The three registered questions (Q1 attribution, open-set; Q2 borrowing; Q3 dating) and what
  stylometry can and cannot see (whoever produced the English).
- Prior computational work (Jockers et al. 2008; Fields, Schaalje and Roper 2011; Schaalje et
  al.; Larsen, Rencher and Layton 1980) and the gaps this study addresses: open-set evaluation,
  KJV masking, a period-only language model, blind scoring, a whole-corpus sweep.
- Pre-registration (OSF https://osf.io/6ugxc/, frozen 2026-10-15) and its 37 dated amendments.
- Everything runnable from the repository; licensed text replaced by derived tables and
  procedures (`docs/replication.md`).

## 2. Data

From `methods.md` section 1: corpus, sealing, quality and deduplication, KJV masking,
segmentation, candidates and controls.

## 3. Methods

`methods.md` sections 2-11.

## 4. Validation (no Book of Mormon text)

- Benchmark table, every method, nothing passes the registered bar (`results_so_far.md` 2).
- Known-answer controls (Amendment 9): no borrowing or dating test separates genuine
  translations from compositions presented as ancient (`results_so_far.md` 1.5, 3).
- Dating validation (`results_so_far.md` 3).
- Imitation robustness: classical methods done (`results_so_far.md` 4);
  model-based methods 0 / 2 / 0 to 7 of 17 by size, style encoders 7 and 10 of 18; every
  model-based method gets imitation weight 0 (`results_so_far.md` 4).
- Time-locked models at three sizes side by side (Amendment 37):
  125M / 297M / 590M (the 1B abandoned, Amendments 38-39): primary method 0.936 / 0.991 / 0.982
  right author, 0.473 / 0.382 / 0.218 false matches; V1 and V2 checks (Amendments 41-42) and the
  method-reliability reading in `docs/method-reliability.md`.
- Candidate and control models validated on held-out text:
  297M done (`data/benchmark/alm_candidates_base.json`);
  590M likewise (0.956 of 68 held-out windows at 297M and 590M).
- Author sweep calibration (`data/sweep/calibration.json`): true author first 27% (word
  frequencies), 30% (style), 34.5% (either) on 200 held-out books, not usable by the registered
  70%; expected false leads (BOM-47) mean 0.035, median 0, 95th percentile 0 per book; the
  plausibility gate passes 10% of random authors (Amendment 40).
- Comparison with prior work (BOM-68): table built (`data/benchmark/prior_work.json`);
  590M rows, classical methods on the 110 held-out tests and the GPT-2 ablation (124M / 355M:
  0.918 / 0.855 false matches) are in the table.

## 5. Results: borrowing (Q2), final

`results_so_far.md` 1: exact reuse, rare phrases, paraphrase, story order, triage. No source
stands out under the registered nulls; 0 of 1,069 triaged pairs specific under both passes.

## 6. Results: dating (Q3)

- Validation final (`results_so_far.md` 3).
- 215 segments of the 168 chunks: grammar model (decides) median of medians 1661, 78% before
  1700 and 7% in 1780-1830: **H3b**; lexical 1736 and transformer 1755 (both "neither"). The
  transformer, not moved by King James imitation in validation, still dates the text before the
  1780-1830 pseudo-biblical controls (1805). **H3c rejected** (`data/dating/h3c.json`): the
  chunks date earlier than the pseudo-biblical control volumes (grammar 1661 vs 1734, lexical 1738
  vs 1794; permutation p 0.0001 for both), so the early dating is not what period imitators of
  King James style produce.

## 7. Results: attribution (Q1)

- Decoys (`docs/results-first-read.md` 1): the right candidate ranked first on 15-21 of 22
  candidate decoys by method; no method called any of the 21 control decoys a match; the candidate
  models matched their own held-out text on 20 / 14 / 11 of 22 by size.
- Match calls on the 168 chunks: General Imposters 0 (both rules), style encoders 0 (registered;
  the achievable rule, at 50% benchmark false matches, matches often), candidate models 10 / 5 / 3
  by size, all to the small pre-1830 Joseph Smith and Cowdery samples or post-1830 samples
  (`docs/results-first-read.md` 2-3; per chunk and half in `data/blind/unblinded.json`).
- H1a (a candidate matched by two independent families): **not supported**; under the registered
  thresholds General Imposters and the style encoders cannot return *match*. H1b ("none of these"):
  favoured by the synthesis (8) but not established, since no method passes the open-set bar.
- H1c (`data/benchmark/scribes.json`): narrators 0.744 (chance 0.277, p 0.001), dictation order
  0.758 (chance 0.502, p 0.001), scribe untestable (all Cowdery); below the 0.96 benchmark
  accuracy, so not separable as distinct authors.
- Leave-one-candidate-out (590M): with Cowdery left out the chunks go to Joseph Smith (127 of
  168); with Joseph Smith left out, to Cowdery (158): the two small production-circle samples
  absorb each other's chunks.
- Author sweep: 0 leads on the discovery half (0.035 expected by chance); the gate had nothing
  to judge; nearest by both signals are scriptural and prophetic writers (Wroe, Fox, Sewel),
  none near a threshold.

## 8. Synthesis

- Posterior, primary candidates, both halves: **not in set 0.744** (prior 0.5), Hunt 0.089,
  Spalding 0.085, Ethan Smith 0.082; identical at 125M, 297M and 590M because both model-based
  families carry imitation weight 0 (section 9), so only General Imposters enters. Prior 0.2-0.8:
  not in set 0.42-0.92. Dropping General Imposters leaves the prior (0.5); equal weights or
  independent chunks: 1.00. Secondary set (post-1830 samples): not in set 0.715, Pratt 0.122.
- Access evidence (BOM-33) and manuscript evidence (BOM-34) reported beside, not multiplied in
  (Amendment 34).

## 9. Production evidence

`results_so_far.md` 5 (dictation evidence in the manuscripts) and 6 (access table).

## 10. Applying the results to public claims (BOM-42)

`data/claims/claims.json` holds the evidence for each of the 17 claims (4 untestable); each
claim's verdict is set from its pre-written rule in `data/claims/register.yaml`, with the
reasoning in `docs/claims-verdicts.md`: supported 2, contradicted 6, mixed 4, not addressed 1,
untestable 4.

## 11. Limitations

`limitations.md`.

## 12. Deviations from the pre-registration

The full list of amendments with dates, OSF revisions and post hoc labels, generated from
`paper/preregistration.md` section 11; post hoc items: Amendments 8, 13 (partly), 19, 20, 21,
25, 26, 31 (disclosure), 33 option (b) if used, 37 (owner's decision after results at two sizes).

## 13. Simulated review

**[RESULT: the three simulated reviewers of BOM-03 run on the full draft, their objections and
the responses, published alongside and labelled simulated (BOM-38)]**

## Appendices

- A. Every command, in order (`eval/README.md`).
- B. Data availability and the steps to obtain restricted sources (`docs/replication.md`).
- C. Checksums (`data/manifests/`).
