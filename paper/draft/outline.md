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
  **[RESULT: style and model-based parts at 125M, 297M and 1B, `data/benchmark/imitation.json`]**
- Time-locked models at three sizes side by side (Amendment 37):
  **[RESULT: 1B benchmark rows, `data/benchmark/alm_large*.json`, `data/benchmark/open_set.json`]**
- Candidate and control models validated on held-out text:
  297M done (`data/benchmark/alm_candidates_base.json`);
  **[RESULT: 125M and 1B, `data/benchmark/alm_candidates_{pilot,large}.json`]**
- Author sweep calibration: **[RESULT: top-1 rate per signal, usable verdict, lead thresholds,
  `data/sweep/calibration.json`]**; expected false leads (BOM-47) **[RESULT: mean, median, 95th
  percentile of leave-one-out counts, same file]**.
- Comparison with prior work (BOM-68): table built (`data/benchmark/prior_work.json`);
  **[RESULT: 1B rows; classical methods on the 110 held-out tests; GPT-2 ablation]**

## 5. Results: borrowing (Q2), final

`results_so_far.md` 1: exact reuse, rare phrases, paraphrase, story order, triage. No source
stands out under the registered nulls; 0 of 1,069 triaged pairs specific under both passes.

## 6. Results: dating (Q3)

- Validation final (`results_so_far.md` 3).
- **[RESULT: Book of Mormon segments' median years and H3a/H3b/neither call, grammar model
  (decides), lexical and transformer beside; H3c permutation p against the pseudo-biblical
  controls; `data/blind/outputs/dating*.json` after unblinding]**

## 7. Results: attribution (Q1)

- **[RESULT: decoy accuracy per method, `data/blind/unblinded.json`]** (the run is repeated with
  the fault documented if decoys are not identified at benchmark accuracy, section 8)
- **[RESULT: per candidate, per method, per half: match / non-match / inconclusive under 6.1,
  registered reading and, if the 1B does not reach 6.1's 5% rate, Amendment 33 option (b)
  beside it]**
- **[RESULT: H1a / H1b, with the statement that under the registered thresholds two of three
  families cannot return *match* if that remains so]**
- **[RESULT: H1c narrators vs scribes vs dictation order, `eval.scribes`,
  `data/manuscript/scribes.json` or equivalent]**
- **[RESULT: leave-one-candidate-out]**
- **[RESULT: author sweep leads on the discovery half against the expected false-lead count;
  plausibility gate outcome for leads and for the 100 random authors]**

## 8. Synthesis

- **[RESULT: posterior per hypothesis, per model size (125M, 297M, 1B) and whether the sizes
  agree, `data/synthesis/posterior_sizes.json`; sensitivity over the prior 0.2-0.8 and
  drop-one-family]**
- Access evidence (BOM-33) and manuscript evidence (BOM-34) reported beside, not multiplied in
  (Amendment 34).

## 9. Production evidence

`results_so_far.md` 5 (dictation evidence in the manuscripts) and 6 (access table).

## 10. Applying the results to public claims (BOM-42)

**[RESULT: claim-by-claim table, after the synthesis]**

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
