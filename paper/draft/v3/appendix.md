*The appendices below were brought up to outline version 3 on 2026-11-14 by an AI model, from the results files, sections 1-14, the amendments and the run guide, and are under review.*

## Appendix A. Methods in detail

Every number below is read from the file named beside it; settings come from
`config/preregistered.yaml` (keys are given as `block.key`), and every output carries the SHA-256
of that file. The pre-registration is `paper/preregistration.md` (OSF https://osf.io/6ugxc/);
amendments are cited by number and listed in its section 11 (1-46 also filed on OSF, 47-58 recorded
in the repository only). Commands are in `eval/README.md` with what each needs, writes and costs.
"Section" means a section of this paper unless it says "pre-registration". Model sizes are named
`pilot` (125M), `base` (297M) and `mid` (590M) in commands and file names. A step marked *post hoc*
was decided after a relevant result had been seen; a step marked *exploratory* was not registered
at all. Every review, screen or second reading mentioned is simulated by an AI model.

### 1. Data (section 2)

**Corpus (2.1).** The period corpus is assembled from Harvard Institutional Books 1.0, HathiTrust
public domain volumes, the Internet Archive, Chronicling America and EEBO-TCP (Phases I and II, the
early modern reference for dating). The catalog holds 695,021 records
(`data/catalog/catalog.parquet`); the 1780-1830 window is flagged per record (`in_period`), with
corrected years from the date audit (BOM-64, Amendment 12). Licensed text is never redistributed;
derived tables and the steps to obtain each source are (`docs/replication.md`; Amendment 18).

**Quality and duplicates (2.2).** OCR is cleaned and measured (BOM-14); reprints and later editions
are collapsed by MinHash similarity on 5-gram shingles, with a second pass by title, author and
year across sources (Amendment 6; `data/catalog/DEDUP.md`).

**Spelling.** Pre-1700 text is normalised with MorphAdorner; text from 1700 on keeps its printed
forms apart from artifacts (long s, ligatures, OCR), since lexical modernisation would erase the
grammatical forms the dating model reads (`normalization`; Amendment 6).

**Sealing (2.4; pre-registration 4.2).** The Book of Mormon is excluded from every model's
training, tuning, threshold and feature selection until the blind run, except the registered
replications of prior studies (BOM-22; section 4). Catalogued copies are sealed by title
(`data/catalog/sealed.json`), and any volume holding 20 or more of the Book of Mormon's original
12-token strings is removed from training sets (Amendment 6); in practice these are later texts
quoting it under early catalog dates.

**KJV masking (2.4; pre-registration 4.4).** The Book of Mormon, candidate and control texts are
aligned to the King James Bible (with Apocrypha) with passim at frozen settings, validated on 200
alignments (Amendment 2; `kjv_mask/`). Attribution and dating read original spans only; borrowing
reads the full text with KJV spans labelled. Masked shares: Book of Mormon 6.82% (18,336 of
268,811 words, `data/kjv_mask/bom/report.json`); candidates 3.71%
(`data/kjv_mask/candidates/report.json`); controls 1.78% of 1.55 billion words in 17,456 texts
(`data/kjv_mask/controls/report.json`).

**Segmentation and split (2.5; pre-registration 4.5).** The text is segmented by internal narrator,
dictation order and scribe, each cut into 2,000- and 5,000-word chunks (756 chunks,
`data/bom/segments/chunks.jsonl`). The 5,000-word chunks are split into a discovery and a
confirmation half by a seeded draw stratified by narrator (`data/bom/segments/split.json`, seed
20261017): 22 discovery and 25 confirmation chunks.

**Candidates and controls (2.6, 2.7).** Candidate samples are fixed by BOM-13 with provenance tiers
(handwritten, dictated, printed by the author, posthumous; Amendment 5); masked word counts per
sample (`data/benchmark/alm_candidates_plan.json`): Ethan Smith 277,391; Gilbert J. Hunt 56,956;
Solomon Spalding 41,833; Joseph Smith dictated pre-1830 2,720 (3,039 training tokens) and
post-1830 5,039, handwritten post-1830 6,363; Oliver Cowdery handwritten pre-1830 1,310 and
printed post-1830 44,338; Parley P. Pratt 91,478; Sidney Rigdon 21,516; W. W. Phelps 28,479.
Samples under 10,000 masked words carry the unreliable-sample flag (`candidates.min_masked_words`).
Post-1830 samples are a secondary analysis under Amendment 5's time-split gate, which no method
passed (`data/benchmark/timesplit.json`). Control groups (BOM-18): pseudo-biblical (a published
curation, Amendment 6), 1820s sermons and tracts, histories with Native American origin texts,
general prose.

**The quotation rule for candidate samples (2.4, 9.2; Amendment 43, post hoc).** The seal was
enforced on training data and not on candidate samples. Every run of 8 or more words a sample
shares with the Book of Mormon's narrative is classed as biblical, stock, predating the passage,
written in the same weeks, or written after it (`python -m eval.bom_overlap`;
`docs/bom-overlap-analysis.md`). Only quotations are dropped: passages built from shared runs of
at least 8 words, gaps of at most 5 words merged, at least 20 words long, written after the
matching passage was dictated (`candidates.bom_quotation: {ngram: 8, min_words: 20, max_gap: 5}`;
`python -m eval.bom_quotes check`). The candidate models were retrained and the sealed set rescored
(`data/blind/a43/`, `python -m eval.per_candidate report --run a43`); the registered run stays as
git tag `blind-registered-2026-11-10` and `data/blind/per_candidate.json`. After the rule
Cowdery's 1829 sample is 844 tokens, shorter than one training sequence, so its model takes no
training step.

**Later Joseph Smith samples (post hoc).** His non-revelatory writing of 1831-33, pooled as one
unit (Amendment 44), and his revelations of 1830-34 (Amendment 54; subsection 18) are used only in
section 6's checks and section 14, never in the registered comparison.

### 2. Classical stylometry (section 5; pre-registration 5.1; BOM-20)

Most-frequent-word features (100, 300, 1,000; culled below 20% document frequency), Burrows' Delta
(Burrows 2002) and Cosine Delta on z-scores, the General Imposters method (Koppel and Winter 2014;
100 trials, half the features per trial, imposters from the genre-matched controls) and extended
nearest shrunken centroids (ENSC; Schaalje, Fields, Roper and Snow 2011). Delta has no verification
score and counts only as "which listed candidate is closest" (Amendment 8). Settings: the `classic`
block. The registered character n-grams, part-of-speech n-grams and content-word set were not run
(`paper/deviations.md`, D3; section 12). The older methods are baselines; they are not combined
with the language models or with each other.

### 3. The time-locked language models (2.8; pre-registration 5.2; BOM-27)

GPT-style decoders trained from scratch on the 1780-1830 corpus with the Book of Mormon and
post-1830 text excluded, with a byte-level BPE tokenizer of 32,000 entries fitted on the same data
(Amendment 16; `docs/timelocked-plan.md`; `timelocked_lm` block). Training set: 202,816 volumes,
989 held out for validation loss (`data/timelocked_lm/training_set.parquet`); one epoch over
25,052,872 windows of 1,025 tokens (25.7 billion tokens); 48,931 steps of 524,288 tokens. Every
model-based test runs at all three finished sizes, reported side by side with none treated as the
headline (Amendment 37):

| Size | Layers x width x heads | Parameters | Final validation loss | Hardware |
| --- | --- | --- | --- | --- |
| 125M (pilot) | 14 x 768 x 12 | 124,475,136 | 2.5148 | 1 H100 |
| 297M (base) | 24 x 960 x 15 | 297,170,880 | 2.3248 | 1 H100 |
| 1B (large, Amendment 26) | 32 x 1,600 x 25 | 1,035,878,400 | abandoned after a loss spike at step ~15,800 (Amendment 38) | 4 H100 |
| 590M (mid, QK-norm, Amendment 39) | 28 x 1,280 x 20 | 592,849,664 | 2.1917 | 2 H100 |

The base models are public under CC BY-NC 4.0 (BOM-66; `etherfuse/timelocked-1830-125m`,
`-300m` for the 297M, `-590m`); section 13 lists what else is published.

### 4. Author models (2.8, 5, 6; pre-registration 5.2; BOM-28)

Called authorial language models in the pre-registration and candidate models in sections 6-7. One
copy of a time-locked model is fine-tuned per author: 3 epochs, learning rate 1e-5 constant, AdamW
(0.9, 0.95), weight decay 0.1, 1,024-token sequences, batch 8, float32 (Amendment 22; `alm` block).
A text's score for an author is the mean over 512-token windows of the fine-tuned model's log-loss
minus the base model's (`alm.score_window`). On the benchmark, testable authors hold out their last
max(5, ceil(n/4)) 1,000-word blocks (`alm.holdout_share: 0.25`), tested in up to 20 distinct
5,000-word windows (`alm.max_tests`). Three variants are reported beside the primary method
(Amendment 23): V1, learning rate 1e-4; V2, a classifier head on mean hidden states; V3, the base
model's hidden states fed to the classical trials. V1 and V2 were rerun at a rate chosen on
held-out training text (Amendment 41, post hoc; `alm.lr_select_grid`), and V2 with five further
seeds (Amendment 42, post hoc; `alm.v2_seed_runs`); V2 carries no weight (section 5.1).

Candidate and control models (Amendment 30): one per candidate sample and per control group
(300,000-word seeded samples, `alm.control_words`), held-out tails never trained on and reserved
for the blind run's decoys; the registered match statistic (pre-registration 6.1) is the best
control model's score minus the candidate's. They were retrained after Amendment 43 (subsection 1);
the candidate models are public (`etherfuse/bom-authorship-candidate-models`). The GPT-2
comparison of section 5.2 runs the same pipeline with GPT-2 (124M, 355M) as the base, on the
benchmark only (`prior_work.gpt2_models`; `python -m eval.prior_work ablation gpt2|gpt2-medium`;
`data/benchmark/alm_gpt2.json`, `alm_gpt2_medium.json`).

### 5. Style embeddings (5.1, 6; pre-registration 5.4; BOM-30)

A LUAR-style encoder (Rivera-Soto et al. 2021): a period base model, mean-pooled over 128-token
passages, an episode of 8 passages, projected to 512 dimensions, trained with symmetric InfoNCE
(temperature 0.05) on two episodes per author from different works, 64 authors a step, 20,000
steps (Amendment 24; `style_embed` block). Authors: the training set's named, non-corporate authors
with at least two works; 8,527 qualify, 854 (10%, seeded hash) held out as the sweep's calibration
pool, 7,673 trained on (`data/style_embed/authors.parquet`). One encoder was trained on the 297M
backbone and one on the 590M (`data/benchmark/style_embed.json`, `style_embed_mid.json`). Scored in
BOM-21's own 180 trials: cosine closed set and General Imposters on the vectors. Section 14's
second encoder is subsection 22.

### 6. Benchmark and pass rule (2.7, 5; pre-registration 7; BOM-21, BOM-75)

**Three steps.** Part 1 (registered): the Federalist papers, pseudo-biblical texts with known
authors, dictated text (Scott); 7 authors with tests, 110 held-out tests for the language models,
and BOM-21's own 180 seeded trials for the classical methods and encoders. BOM-75
(Amendment 48, before any author was drawn): four authors in each of four genres (fiction, legal
and political, sermons, history), drawn in a seeded order (`part2_benchmark.seed`) from period
authors with at least four distinct works and 60,000 words, each capped at 300,000 words, after
rules against translations and repeated texts and an AI screen of each drawn author from catalog
titles and years (`data/benchmark/part2/screen.json`; correction to Amendment 48, before any
scoring); 23 authors, 430 tests with Part 1's. Amendment 56 (post hoc): subsection 15.

**Pass rule.** Closed-set accuracy at least 0.90 on 5,000-word samples and an open-set false-match
rate at most 0.05 (`benchmark.pass_closed_set`, `benchmark.max_open_set_fpr`). As built, the
open-set threshold was the 95th percentile of the negatives, which yields about 5% for any method
with continuous scores; Amendment 25 (post hoc, labelled) corrects it: the threshold is the 5th
percentile of positives (`benchmark.open_set_accept: 0.95`), a negative at or above it is a false
match, measured by two-fold cross-fitting (seed `benchmark-open-set-fold`). Amendment 47 keeps the
bar for the larger benchmark and adds that at least 0.90 of true authors must be called a match at
the threshold and that every rate carries a 95% Wilson interval (`part2` block). Commands:
`python -m eval.open_set rescore` (`data/benchmark/open_set.json`) and `rescore --part2`
(`data/benchmark/part2/open_set.json`). Stricter versions of the false-match rate are in
subsection 16.

### 7. Borrowing (section 3; BOM-23 to BOM-26)

- **Exact reuse** (3.1; BOM-23; Amendment 10): passim alignment of the masked text against every
  eligible volume printed before it, own copies left out (`reuse/exact.py`).
- **Rare phrases** (3.2; BOM-24; Amendments 8, 12-13): 4-grams with document frequency at most 5
  in the 1780-1830 population, counted by distinct text; a source's score is rare shared 4-grams
  per 10,000 of its words, placed against the population and its genre (`data/reuse/bom/rare.json`).
- **Paraphrase** (3.3; BOM-25; Amendment 14): the eligible corpus (278,796 volumes) cut into
  128-word passages and embedded with bge-small-en-v1.5, chosen on a known-answer paraphrase test;
  exact search in each target's date window; a parallel beats the query's best match among 10,000
  random window passages. Named sources are scored directly against their registered control
  groups and against a null of 500 genre- and length-matched volumes scored the same way
  (Amendment 21, post hoc: the null's genre label was chosen after the sources' ranks were seen).
- **Story order** (3.4; BOM-25; Amendment 15): 2,000-word blocks reduced by a hosted model to at
  most 12 role-named events (model-assisted, checked on 20 King James chapters read twice: median
  agreement 0.92); Smith-Waterman alignment with a 1,000-shuffle order test
  (`data/semantic/skeleton/`).
- **Triage** (3.3; BOM-26; Amendment 27): 1,069 registered hit pairs labelled BIBLICAL, COMMON or
  SPECIFIC by `claude-sonnet-5-5`; a simulated second review by `claude-opus-5-5`, blind to the
  first label, of every SPECIFIC and a seeded 10% of the rest; a pair is specific only if both say
  so (`data/semantic/triage.json`).
- **Known-answer controls** (3.6; Amendment 9; BOM-61): every borrowing test is first run on nine
  genuine period translations of ancient texts and three compositions presented as ancient; a test
  that does not separate them is reported as uninformative on the translation question.
- **Proposed parallels** (3.3; exploratory): where the catalog-matched sources of Grunder's *Mormon
  Parallels* rank in the four searches (`python -m eval.grunder_ranks`;
  `data/semantic/grunder_ranks.json`).
- ***View of the Hebrews* close-up** (exploratory; examples for the reader, no new test):
  `python -m semantic.closeup` re-reads the paraphrase, rare-phrase and story-order results and
  pulls out by fixed rules the five closest passage pairs and the weakest-matched passages on each
  side, every look-alike event pair with its place in each book, and the same for Josephus against
  Genesis-Judges as the yardstick (`closeup.show: 5`, `closeup.words: 60`, `closeup.subject_top`,
  `closeup.null_bands`). It reads the public-domain 1823 text only. Output:
  `data/semantic/closeup_view_of_the_hebrews.json`, which repeats the registered numbers (2 rare
  phrases; 29.6 against a bar of 45.0, 77 of 500 matched volumes closer; 3 of its 160 events in
  order, against 108 for the yardstick).

### 8. Dating (8.1; pre-registration 5.3, 6.4; BOM-29)

Two regularised multinomial logistic regressions over 31 date bins from 1473 to 1830
(Amendments 2, 17): a grammar model on 61 rates per 1,000 tokens of grammatical features drawn
from the early modern English literature and fixed before fitting (`dating/features.py`), read
from the printed text through a letter-only fold; and a lexical model on word frequencies with
every grammar word removed. Sample: 51,044 training segments of 2,000 tokens from 27,194 volumes;
13,169 held-out segments from authors never seen in training (`data/dating/segments.parquet`). The
grammar model alone decides H3; Amendment 19 (post hoc, before any Book of Mormon scoring) decides
H3a/H3b on segment median years (more than half in 1780-1830, or in 1473-1700), keeping the
registered interval rule beside it. A transformer cross-check (Amendment 29) feeds the 297M model's
mean hidden states to the same classifier (`data/dating/transformer_validation.json`). H3c is a
permutation test of the text's predicted years against the pseudo-biblical control volumes, run
after unblinding (`python -m dating.classifier h3c`; `data/dating/h3c.json`), reported also with
each of the text's 12 books as one unit.

### 9. Author sweep, as registered (7.8; pre-registration 5.6, 6.6; BOM-39, BOM-47)

Units: 23,875 named, non-corporate authors (23,872 swept: three had no word-frequency profile) in
the training set's volumes with at least 10,000 words (`data/sweep/authors.parquet`;
`sweep.min_words`); each profile is up to 20 seeded 1,000-word blocks round-robin over the
author's works, normalised and KJV-masked (`python -m sweep.units build`). Two signals, each
separate: Cosine Delta on the 300 most frequent words and the registered style encoder's cosine
distance (`python -m sweep.index mfw`, `embed`). The query is the 22 discovery chunks, distance
averaged over chunks. Calibration (`python -m sweep.calibrate`; `data/sweep/calibration.json`):
200 books by 200 style-held-out authors, their profiles rebuilt without the book; the sweep is
usable if the true author ranks first in at least 70% of books under each signal
(`sweep.usable_top1`); a lead beats the 5th percentile of best-false-match distances under both
(`sweep.lead_percentile`). The expected false-lead count is measured by leave-one-out over the 200
books before the sweep runs (Amendment 28). The plausibility gate is read as period and (place or
access) (Amendment 40, before any lead was seen). The calibration gave 27% and 30% against the 70%
bar and 0.035 expected false leads per query, so the registered sweep is not usable (7.8).
Amendment 57's library-wide runs (the older methods as sweeps, `python -m sweep.older`; one
author-labelled model) are not reported in the body and not described here; section 14's search is
subsections 22-25.

### 10. Blind procedure (2.5, 6; pre-registration 8; BOM-32)

The narrator scheme's whole chunks (121 of 2,000 words, 47 of 5,000) are sealed with decoys at one
per four chunks, half from candidates' held-out tails and half from control volumes no model
trained on; Joseph Smith contributes none (Amendment 32; `blind` block). Opaque ids, the key
written outside the repository, hashes of key and sealed set committed (`python -m blind.seal`).
The analysis is run by a new AI session given only the scoring script and no access to the key
(`python -m blind.run`): this is **simulated blinding**, since one person designed and runs the
study. Outputs are hashed and committed before unblinding (`python -m blind.unblind`;
`data/blind/unblinded.json`); decoys must be identified at benchmark accuracy;
leave-one-candidate-out follows. Per-chunk scorers apply each method exactly as validated, and both
readings of the match rule and a false-match ladder are reported (Amendment 33;
`blind.fpr_ladder`). `python -m eval.per_candidate report` gives each candidate sample's mean rank,
chunks ranked first and match calls per method and size (section 7's table).

### 11. Synthesis (9.3; pre-registration 6.7; BOM-35)

Per chunk and method family, the observation is the top-ranked candidate and its match band; its
likelihood under each hypothesis uses the family's benchmark accuracy and band rates
(Amendment 34; `synthesis` block). Families are weighted by benchmark accuracy times the imitation
weight of subsection 12. Prior 0.5 on "author not in set", the rest shared among candidates with
reliable samples; sensitivity over the prior from 0.2 to 0.8, dropping each family, equal weights.
One posterior per model size (Amendment 37; `data/synthesis/posterior_<size>.json`). Dating, the
sweep, access and manuscript evidence are reported beside the posterior, not multiplied into it.
The placebo (post hoc, raised by the simulated reviews; no amendment) runs the same synthesis on
the candidates' own held-out passages and on control passages
(`data/synthesis/placebo/decoys.json`); the posterior leans to "not in set" there too, so it is
reported as registered and carries little information.

### 12. Imitation robustness (5.3; pre-registration 9; BOM-31)

Three authors who wrote both imitation scripture and ordinary prose (Snowden, Dodsley, Kenrick;
the only three the corpus-wide search found, `python -m eval.dual_register`,
`data/benchmark/dual_register.json`); forward test: 18 imitation windows (17 for the language
models) against 13 candidates (the three plus 10 seeded distractors) with references from ordinary
prose; the forward accuracy sets each method's synthesis weight (full at 80% or above, half at
60-80%, none below); the reverse test is reported (Amendment 31; `python -m eval.imitation report`;
`data/benchmark/imitation.json`). The file also holds, per method, each author's accuracy and the
number of authors with most passages right; counted that way (a correction of 2026-11-12, no
amendment) the test is too small to judge either family.

### 13. Manuscript evidence (8.2; BOM-34)

Corrections in the Joseph Smith Papers transcripts of the original and printer's manuscripts are
typed from the transcripts' markup (strike-outs, insertions, new-hand notes): listed homophones
primary, a sound-match code beside (Amendment 35). Dictated original and copied printer's
manuscript are compared with the scribe held fixed. Word pairs stay private; ids, pages, hands,
types and counts are public (`data/manuscript/`).

### 14. Access evidence (3.5; BOM-33)

Each candidate source is scored 0-3 for documented availability before mid-1829 (3, within Joseph
Smith's documented reach; 2, in western or central New York; 1, in print in the United States
only; 0, no evidence of circulation), every score cited (`data/access/access_table.csv`).

### 15. Paired comparison, counting by author, and the 32 further authors (5.1; Amendments 52, 55(a), 56; all post hoc)

**Same tests for every method (Amendment 52).** Burrows' and Cosine Delta, General Imposters and
ENSC (at BOM-75's calibrated shrinkage and alpha, with Amendment 48's imposter pairings) are run on
exactly the held-out tails the language models were scored on:
`python -m eval.prior_work classic-tails` (110 tests), `--part2` (430;
`data/benchmark/prior_work_classic_tails_p2.json`) and `--ext` (640;
`prior_work_classic_tails_p3.json`). Amendment 52's own test, an exact two-sided McNemar test per
passage with Holm's correction over the 12 size-by-method comparisons
(`prior_work.head_to_head`), is kept as a count, not as the test.

**The unit is the author (Amendment 55(a)).** Up to 20 passages come from one author and are not
independent. An author counts for a side when that side wins more of the passages on which the two
methods disagree; the test is an exact two-sided sign test over authors that are not tied,
Holm-corrected over the 12 comparisons; "ours better" or "theirs better" needs a Holm p under 0.05
(`prior_work.by_author.alpha`), otherwise "no difference shown". Beside it: the accuracy gap with
a 95% interval from resampling authors (5,000 resamples, seed `a55-authors`). Command:
`python -m eval.clustered head-to-head`; results in `data/benchmark/clustered.json`
(`head_to_head_by_author`).

**32 more authors and a stopping rule (Amendment 56).** Written before any further author was
drawn: each of Amendment 48's four genres continues down its existing seeded order by exactly the
same rules and screen until 8 more authors per genre are kept (`part2_benchmark.extension`), 32 in
all, in eight tasks of four (`p3_<genre>_1`, `_2`), so that no registered task or test changes;
every size and every older method is scored on the same 640 held-out tests; the by-author test is
applied to all 55 authors together, with the 32 new and the 23 old reported beside; no authors are
added after that, whatever the result. Commands: `python -m eval.part2_benchmark --ext`
(`data/benchmark/part2/authors_ext.json`), `python -m alm.benchmark <size> --ext`
(`data/benchmark/alm_<size>_p3.json`), `python -m eval.clustered head-to-head --ext`
(`clustered.json`, `head_to_head_by_author_a56`: `all_55`, `new_32`, `bom75_23`).

### 16. The verification curve and score normalisation (5.4; Amendment 55(b), post hoc)

Computed on the language models' saved scores for BOM-75's 430 tests; the registered bar is kept
and reported unchanged. For three statistics fixed in the amendment (`prior_work.verification`):
*raw*, the registered score; *z-norm*, each candidate model's score in standard deviations above
its mean on other authors' tests in its task; *z-margin*, the top candidate's z-norm score less the
runner-up's. Each author is held out in turn: his tests enter no mean, spread or threshold. Reported
per size and statistic: the area under the trade-off curve, the equal-error rate, and at target
false-match rates of 1%, 2%, 5% and 10% and at the registered 95% point the false-match rate
actually obtained on held-out authors and the share of true authors confirmed (ranked first and
above the threshold), each with a Wilson interval and an interval from resampling authors. The
normalised statistics need another test author in the task, so they cover 344 tests from 20
authors: the dictated task (one test author) is left out as the amendment says, and the Federalist
task (two) dropped out by the same rule, which the amendment had not named; the raw curve is given
on all 430 tests and also without the dictated task (370 tests, 22 authors). Only the language
models are put through this. Command: `python -m eval.clustered curve`; results in
`data/benchmark/clustered.json` (`verification_curve`). Appendix B.2 gives the four target rates.

### 17. List size, the tournament and per-model scaling (5.5, 14.3; Amendment 58, post hoc; follow-ups exploratory)

**List size (Amendment 58; on the owner's question, before any list-size result).** Pool: the 55
benchmark authors with held-out tests and their 1,070 tests. Each author's model is fine-tuned
again as registered and scores all 1,070 tests (`python -m alm.benchmark bundle --pool`,
`scripts/a58_pool.sh`; `data/benchmark/alm_<size>_pool.json`); an author's score does not depend on
who else is listed, so every list is read from that one table. The older methods are refitted on
every list, since their word lists and z-scores depend on it (`python -m eval.list_size classic`).
Lists of 2, 4, 8, 12, 20, 30 and 55 (`list_size.sizes`): *random*, 30 seeded draws per author and
size (`list_size.draws_per_author`, seed `a58-lists`); *similar*, the author and its nearest
authors by Cosine Delta between training profiles (`list_size.similar_mfw: 300`). Accuracy is the
mean over authors with a 95% author-resampled interval (`list_size.resamples: 5000`); the decision
test is subsection 15's sign test on similar lists of 12 (`list_size.decision_size`), Holm over
12. The retrained models reproduce the saved picks on 100%, 99.5% and 100% of tests at 125M, 297M
and 590M. Command: `python -m eval.list_size prepare`, `report`; results in
`data/benchmark/list_size.json`.

**Tournament (BOM-93, exploratory).** On the 55-author list: straight ranking on one passage
against heats with a final (5 heats of 11 keeping 4 or 2; 11 heats of 5 keeping 2 or 1;
`list_size.tournament.heats`), the final scored on the same passage or a fresh one, 20 random heat
assignments per passage; and several non-overlapping passages averaged (1, 2, 3, 5, 8). Command:
`python -m eval.list_size tournament`; `data/benchmark/list_size_tournament.json`.

**Per-model scaling (BOM-90 follow-up, exploratory and post hoc).** Each model's score is put on
its own scale (its mean and spread on other authors' passages), the scale set on one group of
authors (BOM-75's 23 or Amendment 56's 32) and tested on the other, both directions; raw against
scaled, by author (`list_size.normalised`). Command: `python -m eval.list_size normalised`;
`data/benchmark/list_size_normalised.json`. Appendix B.2 gives the results of both follow-ups.

### 18. The Joseph Smith checks (section 6; Amendments 44, 45, 49-51, 53, 54, 55(c), 46)

All were decided after unblinding. Each ranks samples on the 168 sealed chunks by the Amendment 43
score; "first" is the number of chunks on which a sample is closest.

- **Ordinary prose and the whole ranking (6.1; Amendments 44 and 53, post hoc).** His
  non-revelatory writing of 1831-33 is pooled into one unit and scored beside the 1828-29
  revelations by the classical methods, the style encoders and candidate models at every size
  (`python -m eval.js_register classic | style | alm | report`; `data/blind/a44/`). Amendment 53 is
  a reporting step with no new model: every candidate sample's mean rank and firsts for every
  method, candidate samples only, with the 1828-29 revelations in the list and taken out
  (`python -m eval.js_register people`; `data/blind/a44/people.json`).
- **Equal dose (6.2; Amendment 45, post hoc, raised by the simulated reviews).** Every larger
  candidate sample and the pooled ordinary prose is fine-tuned again on two seeded slices of
  exactly the revelation sample's 3,039 training tokens (`candidates.dose_check: {slices: 2, seed:
  a45-dose}`) at every size, 20 equal-dose models, and the revelation model is ranked among them
  (`python -m eval.js_register dose <size>`, `dose-report`; `data/blind/a45/report.json`).
- **Cross-work recognition (section 7; Amendment 49, recorded before any model was trained).** For
  each candidate with two or more works, one model per held-out work is trained on the other works;
  up to 20 5,000-word windows of the held-out work are scored by that model and by every other
  candidate's model; a window is recognised when its own author's model scores closest; "not a
  match" would need a rate of at least 0.90 (`part2.exclusion_min_decoy_recognition`; Amendment
  47). Commands: `python -m eval.part2_decoys plan`, `lowo <size>`, `report`;
  `data/benchmark/part2/decoys_report.json`.
- **Placebo writers (6.3; Amendment 49).** Writers of imitation scripture or prophecy who died
  before 1 September 1827 (`part2.placebo_primary_died_before`): Snowden, Stiles, Ilive, Southcott,
  Brothers, Reader; and, reported separately, Levi H. Dowling (born 1844). Death dates are from an
  AI model's knowledge, labelled as such (`data/benchmark/part2/placebo.json`). Each is given the
  equal dose and ranked in one pool with Amendment 45's models and the revelation model. Rule
  written first (Amendment 47): if any of the six has a median rank at or better than the
  revelation model's, "ranked first" is read as register, not person
  (`python -m eval.part2_decoys placebo <size>`).
- **Twelve slices (6.3; Amendment 51, post hoc, after the first placebo results).** A 3,039-token
  sample is one training batch, so a new seed cannot change its model; the chance element is which
  tokens are taken. Each placebo writer is trained on up to 12 non-overlapping slices spread evenly
  through the text (`part2.placebo_slices_max`), one model per slice; each slice replaces the
  writer's models in the pool, and the count of slices at or better than the revelation model is
  reported, "slice-stable" when more than half are (`part2.placebo_slice_majority`). The revelation
  sample is the whole of its text and stays one model
  (`python -m eval.part2_decoys placebo-slices <size>`; `decoys_report.json`).
- **Seeds (6.5; Amendment 50, recorded before the run).** Every Amendment 43 unit, the 11 candidate
  samples and four controls, is fine-tuned again at every size with five further seeds
  (`part2.seeds_per_candidate`) and rescored; a result is seed-stable when the original run's share
  of chunks ranked first lies within the five new seeds' range
  (`python -m eval.part2_seeds run <size>`, `report`; `data/benchmark/part2/seeds_report.json`).
  The seed only orders batches, so one-batch models (every Joseph Smith sample) do not vary.
- **Later revelations (6.4; Amendment 54, post hoc; rule recorded before any text was prepared).**
  Sample: every section of Revelation Book 1 dated after March 1830 whose title begins
  "Revelation" (`js_later.title_prefix`): 95 sections, 65,222 words, 60,375 after masking and
  64,501 tokens (`data/blind/a54/plan.json`); masked as the candidates
  (`python -m kjv_mask.run js_later`) and checked by Amendment 43's rule
  (`python -m eval.js_later shared`; `data/blind/a54/shared_runs.json`). *Whole sample:* added as
  one unit to Amendment 53's ranking for every method and size. *Equal dose:* 12 non-overlapping
  slices of the 1828-29 sample's length, spread through the book in order
  (`js_later.slices_max`), one model per slice, each ranked in Amendment 51's pool; the count at or
  better than the 1828-29 model, slice-stable when more than half (`js_later.slice_majority`).
  The reading was stated before the run and is descriptive. Commands:
  `python -m eval.js_later sections | plan | classic | style | alm | report`;
  `data/blind/a54/report.json`.
- **Chunk length (6.4a; Amendment 55(c), post hoc, reporting only).** The 168 chunks are the text
  cut twice, so the firsts of Amendments 53 and 54 are also counted separately on the 121
  chunks of 2,000 words and the 47 of 5,000 (`python -m eval.clustered by-length`;
  `data/blind/a55_by_length.json`). The equal-dose, placebo and seed files are not broken down by
  length.
- **Prose over time (6.6; BOM-73; Amendment 46, post hoc, filed before any scoring).** Distance to
  the masked Book of Mormon of 2,000-word blocks by period (`js_time.bins`, `js_time.floor_words:
  2000`), by Burrows' and Cosine Delta (300 words) and the 297M and 590M style encoders, each
  reported separately; texts KJV-masked, Book of Mormon quotations dropped, comparison blocks that
  mention Mormonism dropped (`js_time.exclude_topic`); slopes compared with the unexposed group's
  by permutation within writer, which cannot be read for lines with one block per period and is
  not used (`python -m eval.js_time assemble`, `measure`; `data/js_time/results.json`;
  `docs/js-over-time-plan.md`).

### 19. Internal voices (8.2; pre-registration 6.3)

Leave-one-out Cosine Delta sorts the text's 2,000-word chunks by narrator, by dictation order and
by scribe, each against 1,000 shuffles of the labels; a grouping needs at least three chunks per
label (`python -m eval.scribes run`; `data/benchmark/scribes.json`).

### 20. The verification comparison (5.4; BOM-96; exploratory)

Existing verification tools beside ours, on known books (`nobody` block). `python -m eval.nobody
prepare` takes the sweep's first 200 known books (`nobody.books`) and pairs each with its true
author and 10 seeded other known-book authors (`nobody.others`, seed `bom96-nobody`): 2,200 pairs.
The questioned text is the book's first 5,000-word query chunk; a candidate's known text is their
profile, rebuilt without the book for the true author; King James spans are cut and punctuation
kept. Verifiers, each scoring a (book, candidate) pair:

- **LambdaG** (Nini et al. 2024), from its authors' R package `idiolect`: POSnoise content masking
  (Halvani and Graner 2021), grammar models of order 10, 30 repetitions (the package's defaults),
  the other profiles as the reference population (`scripts/lambdag.R`, run with `Rscript`;
  `data/corpus/nobody/lambdag.csv`).
- **LUAR** (Rivera-Soto et al. 2021), `rrivera1849/LUAR-MUD`, trained on Reddit, loaded from a
  local copy of its repository whose code was read first; each text one episode of up to 64 pieces
  (`nobody.luar_pieces`, `nobody.luar_tokens: 128`) (`python -m eval.nobody luar --local <dir>`).
- **Two modern style models**, off the shelf: `AnnaWegmann/Style-Embedding` (content-controlled)
  and `StyleDistance/styledistance`; each text embedded in 100-word pieces, averaged, cosine
  (`nobody.neural`, `nobody.neural_words`; `python -m eval.nobody neural`).
- **Ours:** the second style encoder, closest episode (subsection 22), and the author models of
  subsection 24 at both doses, where they scored the same book.

`python -m eval.nobody report` writes, per verifier, the area under the curve, the share of true
authors confirmed when 5% of false pairs are accepted, and the share of false pairs accepted when
95% of true authors are confirmed (`data/sweep/nobody.json`). The 11,264-token author models cover
197 of the 200 true pairs and 1,976 of the 2,000 false pairs, since a few pool authors have too
little text for that dose; every other verifier scores all 2,200. The modern models are used for
this known-answer comparison only and never on the Book of Mormon.

### 21. The whole library: overview (section 14; exploratory throughout)

Nothing in subsections 21-25 was pre-registered. The choices were made in November 2026 with
earlier results in view; each is in the configuration file before the result it governs, each tool
was tested on books of known authorship first, and the procedure for the Book of Mormon
(`eval/library_bom.py` and the `library_search` block) was fixed in one commit (`9ed5940`) before
any Book of Mormon vector under the second encoder was made. The gallery is subsection 9's 23,872
swept authors and their profiles.

### 22. The second style encoder, per-episode vectors and coverage (14.1; BOM-89; exploratory)

**Encoder (`style_embed/v2.py`; `style_embed_v2` block).** The registered encoder's log shows
training loss falling to 0.03 while held-out accuracy stayed flat from step 1,000. The second
encoder keeps Amendment 24's design, backbone (297M) and author split and changes three things:
256 freshly drawn passages per work instead of 32 (`passages_per_work`); on half the steps
(`hard_step_share: 0.5`) a batch drawn from one genre with each author's paired episode from a
work in a different genre when there is one (after arXiv:2408.05192 and Agarwal et al. 2025); and
a validation split of 5% of the training authors (`validation_share`), checked every 500 steps,
that selects the kept weights. Amendment 24's held-out authors, which include every known book
below, are never trained on and never used to choose anything. Commands:
`python -m style_embed.v2 build`, `train --out <dir>` (about 5 hours on an H100).

**Per-episode vectors (`sweep/index.py episodes`).** Every unit (author profile, rebuilt profile,
query chunk) is embedded as one vector per consecutive episode of 8 passages of 128 tokens, about
1,024 tokens, with the whole-unit vector beside (`python -m sweep.index episodes --model <style.pt>
--tag _v2`; vectors private under `data/corpus/sweep/episodes_v2/`).

**Score and coverage (`sweep/episodes.py`, `sweep/coverage.py`).** An author's score for a
questioned text is, for each of the text's episodes, the similarity to the author's closest
episode, averaged over the text's episodes (`sweep.episodes.top`; the closest-3 variant is also
written). Coverage at K is the share of known books whose true author is among the K closest
(`sweep.coverage.ks`), over all swept authors and over those not known to be dead or under age in
1829 (subsection 23); each book is tagged by genre group (the share of the author's profile blocks
in the book's genre: same at 0.5 or more, cross at zero, `sweep.coverage.same_share`), by identity
(life dates agree between book and profile) and by the number of works in the profile; ranges are
95% intervals from resampling books. `--profile-episodes N` cuts every profile to its middle N
consecutive episodes, an equal size for every author. Commands: `python -m sweep.coverage`
(`data/sweep/coverage.json`, the registered encoder), `python -m sweep.episodes --tag _v2
[--profile-episodes N]` (`data/sweep/coverage_episodes_v2.json`, `_v2_11.json`, `_v2_2.json`).

**Further known books (`sweep/units.py ext`).** Every further eligible held-out author is added as
a known book, one seeded book per author (`sweep.ext_seed`), built and masked as the registered 200
are: 527 more, 727 in all (`python -m sweep.units ext`, `python -m kjv_mask.run sweep_ext`,
`scripts/sweep_ext_chain.sh`; `data/sweep/ext_authors.parquet`, `ext_blocks.parquet`).

**Stopping rule.** Set before the second encoder's result was seen: take the better variant by
coverage of the cross-genre known books at a shortlist of 1,000 and stop work on the search there.

### 23. Life dates (14.2; BOM-91; exploratory)

`sweep/people.py` takes each swept author's life dates from the catalog's author field where it
carries exactly one pair (9,902 authors; 896 carry two different pairs and are left undated as two
people). For 12,435 of the 13,077 authors the catalog leaves undated it asks the Library of
Congress name authority file and accepts a match only when exactly one person with the same
surname and forenames was born at least 12 years before the author's earliest volume here
(`sweep.people.min_age_at_print`): 1,698 dated, 612 ambiguous, 10,125 with no match; 642 were not
asked. The rule was checked on 494 authors the catalog does date (`sweep.people.check_sample`): it
dated 219, and 212 agree. Status in 1829 (`sweep.people.year`): alive and at least 15
(`min_age`) 6,016; dead 5,493; too young 91; unknown 12,275; with a birth year only, an author is
presumed dead when older than 90 (`max_age`). No author is removed from any ranking; the dead stay
as decoys. Commands: `python -m sweep.people lookup` (outside requests, on the owner's approval,
every reply cached in `data/sweep/loc_cache.jsonl`), `build`; `data/sweep/people.parquet`,
`people.json`.

### 24. The author models on one shared pool (14.3; BOM-94; exploratory)

`eval/library_pool.py` tests the author models on the library's task before any Book of Mormon
run (`library_pool` block). Pool: the 200 known-book authors, each trained on the profile rebuilt
without the book, and 800 seeded other swept authors (`pool_size: 1000`, seed `bom94-pool`). Every
author gets equal-dose models trained as Amendment 45's: three slices of the 1828-29 revelation
sample's 3,039 tokens, evenly spread (`small_slices`), and one slice of 11 sequences of 1,024
tokens, 11,264 tokens (`large_sequences`); 982 of the 1,000 have enough text for the larger dose,
so 3,982 models at 125M. Tests: the first two query chunks of each known book, the first 1,536
tokens of each (`test_chunks`, `test_tokens`), 373 passages. Every model scores every test (mean
window loss minus the base model's). The report gives, per dose (the median of the three small
slices, one small slice, the large), how often the true author is first and in the top 5, 10 and
20 of a random list of 2 to 1,000 pool authors (`sizes`), computed exactly from the number of pool
authors scoring closer and counted by author; by passage and with a book's chunks averaged; with
raw scores and with each model's scores on its own scale (set on the other half of the books); for
all books and by genre group. Commands: `python -m eval.library_pool prepare`, `run pilot` (GPU),
`report pilot`; `data/sweep/pool_pilot.npz`, `pool_report_pilot.json`; the comparison with the
encoder on the same pool is `data/sweep/pool_fusion_pilot.json`. Only the 125M size was run.

### 25. The Book of Mormon against the library (14.4, 14.5; BOM-95; exploratory)

`eval/library_bom.py`, by the procedure frozen in commit `9ed5940` (`library_search` block).

- **Query and gallery (`embed`).** The 168 sealed chunks (475 episodes) and every candidate unit of
  sections 6 and 7, with Joseph Smith's pooled ordinary prose and his 1830-34 revelations (masked,
  quotations dropped), are embedded per episode by the second encoder; the gallery is every swept
  author's profile episodes, tagged alive, unknown, dead or too young in 1829.
- **Ranking and the by-person lists (`rank`).** Score as subsection 22. Three rankings by profile
  size: *small*, every profile cut to its middle 2 episodes, the 1828-29 revelation sample's own
  count; *large*, 11 episodes (`large_episodes`); *full*, everything each author has. A candidate's
  place is the number of library authors scoring closer, plus one; a candidate with more text than
  the size is also scored on every other non-overlapping slice (best, median and worst place). Per
  ranking the file lists the 50 closest with status and life dates (`top`), every candidate's
  place among all authors and among those not known to be dead or under age, the dead authors in
  the top 20, 100 and 1,000 against their share of the gallery (`dead_k`; the decoy check of 14.5),
  and the same ranking from the 2,000-word and the 5,000-word chunks alone with the overlap of
  their top 20 (`overlap_k`). Output: `data/sweep/bom_ranking.json`,
  `data/sweep/bom_library_ranks.json`. The coverage that goes with each ranking is subsection 22's
  at the same profile size. Biographical notes on the leading names in 14.4 are from an
  AI-simulated lookup and are not in the results file.
- **Genre check (`genre`).** A known-answer test in the Book of Mormon's own neighbourhood: the
  search's coverage on known books whose author is among the 500, 1,000 or 2,000 library authors
  closest to the Book of Mormon (`near`), and on sermon and devotional books, beside all known
  books (`data/sweep/bom_genre_check.json`).
- **Second opinion (`second`).** The encoder's 200 closest library authors (`second_opinion`) and
  the candidate units are given subsection 24's equal-dose models at 125M (832 models: 212 units
  at the small dose, 198 with enough text for the large) and scored on the 168 sealed chunks;
  units are ranked per dose by mean score, with the chunks each is closest on. Commands:
  `python -m eval.library_pool prepare-bom`, `run pilot --name _bom` (GPU),
  `python -m eval.library_bom second pilot`; `data/sweep/pool_bom_pilot.npz`,
  `bom_second_opinion_pilot.json`. Section 14.3 found this the weaker of the two instruments on
  this task.

Not run: the author models at 297M and 590M on the library, and the encoder on a 590M backbone.


## Appendix B. Detailed tables

Tables the body points to without giving in full, each checked against the file named. Section 1
holds the registered borrowing results (section 3). Sections 2 to 4 are validation (sections 5 and
8.1); sections 5 and 6 are production and access evidence (sections 8.2 and 3.5).

### 1. Borrowing (section 3)

#### 1.1 Exact reuse (3.1; BOM-23; `docs/reuse-plan.md`)

With KJV spans masked, 58 passages in 47 earlier-catalogued volumes align with the Book of Mormon,
covering 0.52% of it. Seventeen of the 47 are later texts quoting it under catalog dates decades
too early (Congressional serial-set volumes catalogued 1817, *The Millennial Harbinger*
catalogued 1830); without them the share is 0.16%. The other 30 volumes share short, loose
religious stock phrases (9-46 tokens, identity 0.27-0.67). For comparison, *The Late War* (1816)
shares 8.92% with earlier books and an 1821 sermon collection 2.47%.

#### 1.2 Rare phrases (3.2; BOM-24; `data/reuse/bom/rare.json`)

| Source | Rare shared 4-grams | Per 10,000 words | Rank of 204,520 | p (95% interval) |
| --- | --- | --- | --- | --- |
| *The First Book of Napoleon* (1809) | 12 | 5.45 | 63 | 0.0003 (0.0002-0.0031) |
| *The Late War* (1816; 9 printings in the library, 4 distinct texts) | 22 | 3.86 | 131 | 0.0006 (0.0004-0.0017) |
| *View of the Hebrews* (the 1823 edition's text) | 2 | 0.37 | 9,496 | 0.046 (0.017-1.0) |
| Spalding, *Manuscript Story* | 1 | 0.24 | - | 0.068 |
| Luke (KJV), against the masked text | 0 | 0 | - | 1.0 |

*The Late War* and *Napoleon* are significant by the registered rule. Within the curated
pseudo-biblical group (post hoc), the 1829 reprint of Ilive's *Book of Jasher* shares more (7.99
per 10,000 words, 31 phrases); the shared phrases are battle and chronicle formulas. The rule
calls 2,044 volumes significant, mostly short pieces sharing one phrase.

#### 1.3 Paraphrase (3.3; BOM-25; `data/semantic/named.json`, `named_null.json`)

| Source | Rank in group | Score (95% interval) | Null median | Null 99th pct. | Percentile | Stands out |
| --- | --- | --- | --- | --- | --- | --- |
| *View of the Hebrews* (1825) | 1 of 49 | 29.6 (28.0-31.3) | 14.6 | 45.0 | 84.6 | no |
| *View of the Hebrews* (1823) | 2 of 49 | 29.5 (27.9-31.1) | 9.2 | 38.4 | 94.0 | no |
| *The First Book of Napoleon* | 3 of 18 | 7.9 (6.9-9.0) | 0.1 | 8.8 | 98.4 | no |
| *The Late War* (1816) | 6 of 18 | 1.9 (1.4-2.4) | 0.4 | 14.6 | 79.8 | no |
| Spalding, *Manuscript Story* | 12 of 49 | 5.5 | - | - | - | no (rank) |

*View of the Hebrews* leads the origins-of-the-American-Indians group, but 77 of 500
genre-and-length-matched religious volumes score higher (the null's genre label was chosen post
hoc, Amendment 21). In the whole-corpus search (163,121,310 passages, 221,373 volumes in the
window; `data/semantic/corpus_bom.json`) editions of Josephus take 14 of the top 20 places; the
registered rule flags 622 sources, which mostly measures biblical register.

#### 1.4 Story order (3.4; BOM-25; `data/semantic/skeleton/`)

Positive controls (`controls.json`): Josephus against Genesis-Judges shares 108 events in order
(order p 0.001); the *Testaments of the Twelve Patriarchs* 8 (p 0.003); Ilive's *Book of Jasher*
4 (p 0.75), so the test missed one of its three controls. Among the 20 leading search sources
the longest run shared with the Book of Mormon is 9 of its 1,421 events (Josephus, order p 0.24).
Named sources (`bom.json`): *View of the Hebrews* 1823, 3 events, order p 0.97, rank 17 of 49;
1825, 2 events, p 1.0, rank 43 of 49; Spalding, 4 events, p 0.67; *The Late War*, 2 events, p 1.0;
*Napoleon*, 3 events, p 1.0. One of the 49 books in the origins group reaches the registered level
(order p at most 0.01): Church's *History of Philip's War*, 6 events, p 0.008; with 49 books tested
it is read as chance (3.4). No other book in either subject group has an order p under 0.05.

#### 1.5 Known-answer controls (3.6; Amendment 9)

Exact reuse (U 4 of 27, p 0.964), rare phrases (U 6/27, p 0.927) and paraphrase (U 14/27, p 0.50)
do not separate genuine translations of ancient texts from compositions presented as ancient, and
the King James italics test is not shown to work (`docs/italics-plan.md`). None of the borrowing
tests therefore bears on the translation question; each describes which period books share the
Book of Mormon's wording, ideas or plot.

#### 1.6 Triage (3.3; BOM-26; `data/semantic/triage.json`, `docs/triage-plan.md`)

| Search | Biblical | Common | Specific (first pass) |
| --- | ---: | ---: | ---: |
| Paraphrase, named sources | 104 | 144 | 1 |
| Paraphrase, 20 leading sources | 149 | 350 | 1 |
| Paraphrase, random sample | 104 | 146 | 0 |
| Rare phrases, named sources | 10 | 23 | 0 |
| Rare phrases, 20 densest volumes | 15 | 22 | 0 |
| **All** | **382** | **685** | **2** |

The simulated second review re-labelled both first-pass SPECIFIC pairs COMMON (Spalding's
elephant-like "Mammoons"; survival in a just war in a collected *Works* of 1820): **0 pairs
specific under both passes.** Agreement on the 104 doubly labelled pairs 0.740, Cohen's kappa
0.505. Both passes are by AI models.

**Reading.** No named proposed source stands out under its registered null in any of the four
searches except rare phrases, where *The Late War* and *Napoleon* pass a rule that other imitation
scripture also passes (a post hoc comparison). No passage is copied; the one story-order result at
the registered level is not a named source and is read as chance. Every surfaced pair is
labelled, on triage, King James wording (36%) or period stock phrasing (64%).

### 2. Benchmark (section 5)

#### 2.1 Part 1, every method and variant (5.1, 5.2; `data/benchmark/open_set.json`)

Closed-set accuracy and false matches at the Amendment 25 threshold. The language models, V1, V2
and GPT-2 are on Part 1's 110 held-out tests. General Imposters, ENSC, the style encoders and V3
are on BOM-21's own 180 trials, a different draw, and are compared within that set only; the
older methods' figures on the 110 shared tests (Amendment 52) are in section 5.1 and 5.4.

| Method | Size | Federalist | Imitation scripture | Dictated (Scott) | Overall | False matches | Passes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| General Imposters (180 trials) | - | | | | 0.833 | 0.617 | no |
| ENSC (its own "none"; 180 trials) | - | | | | 1.000 | 0.661 | no |
| Style encoders, 297M / 590M backbone (180 trials) | - | | | | 0.839 / 0.839 | 0.500 / 0.628 | no |
| Language models, primary | 125M | 0.769 | 0.958 | 1.000 | 0.936 | 0.473 | no |
| Language models, primary | 297M | 1.000 | 0.958 | 1.000 | 0.991 | 0.382 | no |
| Language models, primary | 590M | 1.000 | 0.917 | 1.000 | 0.982 | 0.218 | no |
| V1 (lr 1e-4, registered) | 125M / 297M / 590M | | | | 0.936 / 0.936 / 0.627 | 0.455 / 0.473 / 0.818 | no |
| V1 at the rate chosen on held-out training text (Amendment 41, post hoc) | 125M / 297M / 590M | | | | 0.936 / 0.991 / 0.982 | 0.473 / 0.382 / 0.218 | no |
| V2 (classifier head, registered) | 125M / 297M / 590M | | | | 0.900 / 0.909 / 0.764 | 0.282 / 0.136 / 0.391 | no |
| V2 at the chosen rate (Amendment 41, post hoc) | 125M / 297M / 590M | | | | 0.764 / 0.773 / 0.564 | 0.591 / 0.400 / 0.755 | no |
| V2, five further seeds (Amendment 42, post hoc): range | 125M / 297M / 590M | | | | 0.66-0.93 / 0.51-0.76 / 0.40-0.78 | 0.09-0.93 / 0.53-0.98 / 0.32-0.93 | no |
| V3 (hidden states; 180 trials) | 125M / 297M / 590M | | | | 0.839 / 0.844 / 0.844 | 0.689 / 0.717 / 0.706 | no |
| GPT-2, primary method (BOM-68) | 124M / 355M | | | | 0.900 / 0.945 | 0.918 / 0.855 | no |

V1's registered rate (ten times Amendment 22's) damaged the 590M; at the rate chosen on held-out
training text V1 is the primary method (1e-5 at every size). V2 is unstable across seeds and
machines and carries no weight. **No method passes** the registered bar. On Part 1 false matches
for the primary method fall with size (0.473, 0.382, 0.218); on the 32 authors of Amendment 56
the order reverses (section 5.5).

**Candidate models, registered run** (`data/benchmark/alm_candidates_<size>.json`): held-out
closed-set accuracy among candidates, 125M / 297M / 590M: Ethan Smith 1.0 / 1.0 / 1.0 (20 tests),
Spalding 1.0 / 1.0 / 1.0 (7), Cowdery printed 1.0 / 1.0 / 1.0 (7), Phelps 1.0 / 1.0 / 1.0 (3),
Hunt 0.9 / 0.8 / 0.8 (10), Pratt 1.0 / 1.0 / 0.95 (19), Rigdon 0.5 / 0.5 / 1.0 (2); 66, 65 and 65
of 68 windows. Samples under 10,000 words are untested. These tests come from works the models
also trained on; the cross-work check of section 7 (subsection A.18) is the harder one.

#### 2.2 The verification curve at four targets (5.4; Amendment 55(b), post hoc; `data/benchmark/clustered.json`)

Language models, BOM-75's tests, each author held out in turn. Cells are false matches obtained on
held-out authors / true authors confirmed, in percent.

| Statistic (tests) | Target 1% | Target 2% | Target 5% | Target 10% | Registered 95% point |
| --- | --- | --- | --- | --- | --- |
| Raw, 125M (430) | 2.6 / 18.8 | 2.6 / 27.9 | 5.6 / 60.9 | 10.9 / 74.0 | 56.5 / 86.3 |
| Raw, 297M (430) | 2.8 / 23.5 | 2.8 / 27.9 | 5.8 / 53.0 | 9.5 / 74.0 | 51.9 / 87.4 |
| Raw, 590M (430) | 3.0 / 18.8 | 3.0 / 19.8 | 6.0 / 37.7 | 11.4 / 73.3 | 51.4 / 87.4 |
| z-norm, 125M (344) | 12.8 / 68.6 | 14.2 / 70.3 | 20.6 / 75.0 | 25.3 / 78.2 | 65.1 / 85.2 |
| z-norm, 297M (344) | 5.8 / 67.7 | 9.3 / 73.3 | 16.6 / 78.8 | 25.0 / 81.4 | 48.3 / 85.5 |
| z-norm, 590M (344) | 12.8 / 58.7 | 15.7 / 66.3 | 19.2 / 70.9 | 30.8 / 79.9 | 54.1 / 87.2 |
| z-margin, 125M (344) | 15.7 / 67.2 | 18.0 / 71.2 | 21.5 / 74.1 | 26.5 / 76.7 | 82.3 / 86.6 |
| z-margin, 297M (344) | 11.0 / 68.3 | 12.2 / 71.2 | 19.5 / 77.9 | 26.2 / 79.4 | 69.2 / 85.2 |
| z-margin, 590M (344) | 15.7 / 68.9 | 20.3 / 69.8 | 25.6 / 71.5 | 34.9 / 73.3 | 78.8 / 86.0 |

Area under the curve and equal-error rate: raw 0.907 / 0.906 / 0.894 and 15.5% / 14.2% / 16.0%;
z-norm 0.866 / 0.903 / 0.862 and 19.5% / 14.3% / 19.7%; z-margin 0.853 / 0.877 / 0.815 and 19.1% /
16.8% / 22.9%. Without the dictated task (370 tests, 22 authors) the raw area is 0.890 / 0.894 /
0.883. The raw score roughly holds the false-match rate it aims for; the normalised scores do not.

#### 2.3 List size: similar lists, the decision test and the follow-ups (5.5, 14.3; Amendment 58, post hoc)

Accuracy by author, in percent, on lists of the author and its nearest authors by Cosine Delta
(`data/benchmark/list_size.json`; random lists are in section 5.5):

| List size | 2 | 4 | 8 | 12 | 20 | 30 | 55 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Language models, 125M | 95.2 | 91.1 | 89.5 | 88.3 | 86.8 | 86.1 | 85.7 |
| Language models, 297M | 95.8 | 91.7 | 90.1 | 89.0 | 87.8 | 86.6 | 86.1 |
| Language models, 590M | 94.7 | 90.1 | 89.1 | 87.5 | 86.5 | 83.1 | 82.3 |
| Burrows' Delta | 87.6 | 78.5 | 68.9 | 63.6 | 60.5 | 60.8 | 61.8 |
| Cosine Delta | 84.5 | 78.5 | 68.2 | 63.4 | 60.8 | 60.0 | 58.5 |
| ENSC | 83.9 | 74.8 | 64.9 | 59.5 | 55.7 | 55.4 | 54.3 |
| General Imposters | 79.5 | 67.4 | 56.1 | 51.6 | 49.7 | 49.1 | 48.4 |

Decision test on similar lists of 12, authors ahead - behind (tied), all with Holm p below 10^-6
and read "ours better":

| Language models against | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Burrows' Delta | 36-3 (16) | 36-3 (16) | 36-3 (16) |
| Cosine Delta | 37-4 (14) | 36-3 (16) | 36-4 (15) |
| ENSC | 41-4 (10) | 41-3 (11) | 40-4 (11) |
| General Imposters | 48-3 (4) | 47-3 (5) | 47-3 (5) |

**Follow-ups on the 55-author list (exploratory).** Accuracy by author, in percent
(`data/benchmark/list_size_tournament.json`, `list_size_normalised.json`):

| | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Straight ranking, one passage | 86 | 86 | 82 |
| Heats then a final on the same passage (four designs) | 84-86 | 84-86 | 82-83 |
| Heats then a final on a fresh passage | 83-85 | 83-85 | 80-81 |
| True author reaches the final | 95-98 | 94-97 | 91-96 |
| 2 / 3 / 5 / 8 passages averaged, straight ranking | 90 / 93 / 94 / 97 | 91 / 90 / 91 / 91 | 86 / 85 / 85 / 84 |
| One passage: raw score / score on each model's own scale | 86 / 85 | 86 / 88 | 82 / 84 |
| Authors better scaled - better raw (tied), one passage | 8-10 (37) | 12-7 (36) | 14-10 (31) |

The heats rows are over the 53 authors with a fresh passage to spare. A tournament does not beat
straight ranking on one passage. Averaging more passages helps the 125M steadily; at 297M the gain
stops at two passages and at 590M it is small. Fewer authors have enough passages for the longer
averages (40 of 55 for eight). Scaling each model's score shows no difference by the sign test on one passage (p 0.36 to
0.81).

### 3. Dating validation (8.1; `data/dating/validation.json`)

| | Grammar (decides H3) | Lexical |
| --- | --- | --- |
| Held-out mean error | 23 years | 13 years |
| 90% interval coverage | 0.91 | 0.76 |
| Held-out 1780-1830 volumes called H3a (Amendment 19) | 1,464 of 1,875 | 1,697 of 1,875 |
| Held-out pre-1700 volumes called H3b | 3,729 of 4,144 | 4,110 of 4,144 |
| Pseudo-biblical controls vs ordinary 1780-1830 | -53 years (p 0.0001) | -5.5 years (p 0.26) |
| King James text | 1631 (H3b) | 1710 (neither) |
| Known-answer separation (Amendment 9) | p 0.57, none | p 0.81, none |

King James imitation alone moves the grammar model's date back by about half a century. The
transformer cross-check (Amendment 29, `data/dating/transformer_validation.json`): held-out mean
error 10.1 years, 90% interval coverage 0.94, and King James imitation moves it by +0.8 years
(p 0.88) where the grammar model moves -53.

### 4. Imitation test (5.3; BOM-31; `data/benchmark/imitation.json`)

Forward: imitation text attributed to its real author among 13. "Weight" is the registered
synthesis weight that the forward passage count set (subsection A.12).

| Method | Forward, passages | Authors with most passages right | Weight | Reverse |
| --- | --- | --- | --- | --- |
| Burrows' Delta | 13/18 = 0.72 (0.47-0.90) | 1 of 3 | 0.5 | 0.38 |
| Cosine Delta | 13/18 = 0.72 (0.47-0.90) | 1 of 3 | 0.5 | 0.29 |
| General Imposters | 11/18 = 0.61 (0.36-0.83) | 1 of 3 | 0.5 | 0.12 |
| ENSC | 7/18 = 0.39 (0.17-0.64) | 0 of 3 | 0 | 0.25 |
| Style encoder, 297M | 7/18 = 0.39 (0.17-0.64) | 1 of 3 | 0 | 0.54 |
| Style encoder, 590M | 10/18 = 0.56 (0.31-0.78) | 2 of 3 | 0 | 0.42 |
| Language models, 125M / 297M / 590M | 5 / 7 / 6 of 17 (0.29 / 0.41 / 0.35) | 1 / 2 / 2 of 3 | 0 | 0.25 / 0.17 / 0.04 |
| V1, 125M / 297M / 590M | 0 / 2 / 0 of 17 | 0 / 0 / 0 of 3 | 0 | 0.12 / 0.42 / 0.00 |
| V3, 125M / 297M / 590M | 4 / 4 / 5 of 17 | 1 / 1 / 1 of 3 | 0 | 0.00 / 0.25 / 0.21 |

Snowden supplies 11 of the 18 passages. By passage the Delta methods lead; by author the order
reverses. The earlier reading that the model-based methods are weaker under imitation is withdrawn
(2026-11-12): three authors are too few to judge either way.

### 5. Production evidence (8.2; BOM-34; `data/manuscript/summary.json`, `docs/manuscript-evidence.md`)

The catalog types 1,597 corrections on the original manuscript's 231 surviving pages and 2,136
on the printer's manuscript's 468. Sound-alike word corrections (listed homophones such as
where/were, there/their) are far more common in the dictated original than in the copied
printer's manuscript:

| Comparison | Original | Printer's | Odds ratio | Fisher p |
| --- | ---: | ---: | ---: | ---: |
| All pages: homophone fixes / substitutions | 36 / 693 | 8 / 927 | 6.3 | 1e-7 |
| Same passages only | 36 / 693 | 2 / 457 | 12.5 | 2e-6 |
| Oliver Cowdery as scribe in both | 36 / 590 | 6 / 837 | 9.0 | 2e-9 |

The tests treat corrections on one page as independent, which overstates their certainty. This
bears on how the words reached the page (by ear, then copied by eye); it cannot distinguish whether
a dictated text was composed, recited or read aloud.

### 6. Access evidence (3.5; BOM-33; `data/access/access_table.csv`, `docs/access-evidence.md`)

Of 33 texts scored: 15 at 3 (documented within Joseph Smith's reach; all but one are editions of
Josephus, in the Manchester library's accessions and in Palmyra bookstore advertisements including
January-May 1829), 3 at 2, 9 at 1, 6 at 0. Named sources: *View of the Hebrews* 2 for both editions
(the 1823 advertised and reviewed in Vermont and eastern New York, the 1825 advertised in Utica in
1826); *The Late War* 1 (Palmyra "Historical Reader" advertisements of 1827-1830 do not name the
author); *The First Book of Napoleon* 0; Spalding's manuscript 0. Availability is not use.


## Appendix C. References

- Agarwal, S., J. Barry, S. Fincke and S. Miller. "Cross-genre authorship attribution via LLM-based
  retrieve-and-rerank." 2025. arXiv:2510.16819. (The "2025 retrieve-and-rerank study" of section
  14.1.)
- Brodie, Fawn M. *No Man Knows My History*. 1945.
- Burrows, John. "'Delta': a measure of stylistic difference and a guide to likely authorship."
  *Literary and Linguistic Computing* 17(3) (2002): 267-287. https://doi.org/10.1093/llc/17.3.267
- Grieve, Jack. "Register variation explains stylometric authorship analysis." *Corpus Linguistics
  and Linguistic Theory* (published online 2 January 2023). https://doi.org/10.1515/cllt-2022-0040
- Grunder, Rick. *Mormon Parallels*. 2014 (PDF edition; purchased, not redistributed).
- Halvani, O., and L. Graner. "POSNoise: an effective countermeasure against topic biases in
  authorship analysis." 2021. arXiv:2005.06605. (The content masking LambdaG uses.)
- Holmes, David I. "A Stylometric Analysis of Mormon Scripture and Related Texts." *Journal of the
  Royal Statistical Society A* 155(1) (1992): 91-120. https://doi.org/10.2307/2982671
- Howe, Eber D. *Mormonism Unvailed*. 1834.
- Huang, Kong and Huang. "Authorship Verification Based on CoSENT." CLEF 2023 Working Notes,
  CEUR-WS Vol. 3497 (2023), paper 215.
- Jockers, Matthew L., Daniela M. Witten and Craig S. Criddle. "Reassessing Authorship of the Book
  of Mormon Using Delta and Nearest Shrunken Centroid Classification." *Literary and Linguistic
  Computing* 23(4) (2008): 465-491. https://doi.org/10.1093/llc/fqn040
- Johnson, Chris, and Duane Johnson. Rare four-word phrase search over about 110,000 pre-1830
  books. 2013.
- Koppel, M., and Y. Winter. "Determining if two documents are written by the same author."
  *Journal of the American Society for Information Science and Technology* 65(1) (2014): 178-187.
  https://doi.org/10.1002/asi.22954
- Larsen, Wayne A., Alvin C. Rencher and Tim Layton. "Who Wrote the Book of Mormon? An Analysis of
  Wordprints." *BYU Studies* 20(3) (1980): 225-251.
- Nini, A., O. Halvani, L. Graner, V. Gherardi and S. Ishihara. "Authorship Verification based on
  the Likelihood Ratio of Grammar Models." 2024. arXiv:2403.08462 (later version titled "Grammar
  as a Behavioral Biometric").
- Rivera-Soto, R. A., O. E. Miano, J. Ordonez, B. Y. Chen, A. Khan, M. Bishop and N. Andrews.
  "Learning Universal Authorship Representations." EMNLP 2021: 913-919.
  https://aclanthology.org/2021.emnlp-main.70
- Runnells, Jeremy. *Letter to a CES Director*. 2013. https://read.cesletter.org/bom/
- "Sadiri": the data-selection study for cross-genre authorship retrieval cited in section 14.1.
  2024. arXiv:2408.05192.
- Schaalje, G. Bruce, Paul J. Fields, Matthew Roper and Gregory L. Snow. "Extended Nearest Shrunken
  Centroid Classification: A New Method for Open-Set Authorship Attribution of Texts of Varying
  Sizes." *Literary and Linguistic Computing* 26(1) (2011): 71-88.
  https://doi.org/10.1093/llc/fqq029 (Cited as "Fields et al. 2011" in the claims register.)
- Shalev, Eran. *American Zion: The Old Testament as a Political Text from the Revolution to the
  Civil War*. Yale University Press, 2013.
- Skousen, Royal, and Stanford Carmack. *The Book of Mormon Critical Text Project*, volume 3; *A
  Plain Exposition of Book of Mormon English*. 2018-2025.
- Spencer, Stan. "Missing Words: King James Bible Italics, the Translation of the Book of Mormon,
  and Joseph Smith as an Unlearned Reader." *Interpreter* 38 (2020): 45-106.
- Stamatatos, E., et al. "Overview of the Authorship Verification Task at PAN 2023." CLEF 2023
  Working Notes, CEUR-WS Vol. 3497 (2023).
- The Church of Jesus Christ of Latter-day Saints. Gospel Topics Essays ("Book of Mormon
  Translation"; "Book of Mormon and DNA Studies"). 2013-2015.
- The Joseph Smith Papers (https://www.josephsmithpapers.org/): the original and printer's
  manuscripts, Revelation Book 1 and the documents listed in `data/candidates/sources.json` and
  `data/js_time/sources.json`.
- Wang, H. "Authorship identification under domain shift: a survey of stylistic measures and
  learned author representations." 2023. arXiv:2310.00436.
- Wright, David P. "Joseph Smith's Interpretation of Isaiah in the Book of Mormon." *Dialogue*
  31(4) (1998).

Software and models used as published, by their public identifiers: GPT-2 (`gpt2`, `gpt2-medium`);
`rrivera1849/LUAR-MUD`; `AnnaWegmann/Style-Embedding`; `StyleDistance/styledistance`; the R package
`idiolect` (LambdaG); passim; MorphAdorner; `bge-small-en-v1.5`.

Sources for the period corpus (Harvard Institutional Books 1.0, HathiTrust, the Internet Archive,
Chronicling America, EEBO-TCP) are listed with their terms in `docs/replication.md`.
