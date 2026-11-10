# Methods (draft, BOM-36)

Every number below is read from the file named beside it; settings come from
`config/preregistered.yaml`, and every output carries the SHA-256 of that file. The
pre-registration is `paper/preregistration.md` (OSF https://osf.io/6ugxc/); amendments are cited by
number and listed in its section 11. Commands are in `eval/README.md`.

## 1. Data

**Corpus.** The period corpus is assembled from Harvard Institutional Books 1.0, HathiTrust public
domain volumes, the Internet Archive, Chronicling America and EEBO-TCP (Phases I and II, the early
modern reference for dating). The catalog holds 695,021 records (`data/catalog/catalog.parquet`);
the 1780-1830 window is flagged per record (`in_period`), with corrected years from the date audit
(BOM-64, Amendment 12). Licensed text is never redistributed; derived tables and the steps to obtain
each source are (`docs/replication.md`; Amendment 18).

**Quality and duplicates.** OCR is cleaned and measured (BOM-14); reprints and later editions are
collapsed by MinHash similarity on 5-gram shingles, with a second pass by title, author and year
across sources (Amendment 6; `data/catalog/DEDUP.md`).

**Spelling.** Pre-1700 text is normalised with MorphAdorner; text from 1700 on keeps its printed
forms apart from artifacts (long s, ligatures, OCR), since lexical modernisation would erase the
grammatical forms the dating model reads (`config/preregistered.yaml` `normalization`; Amendment 6).

**Sealing (4.2).** The Book of Mormon is excluded from every model's training, tuning, threshold
and feature selection until the blind run, except the registered replications of prior studies
(BOM-22). Catalogued copies are sealed by title (`data/catalog/sealed.json`), and any volume
holding 20 or more of the Book of Mormon's original 12-token strings is removed from training sets
(Amendment 6); in practice these are later texts quoting it under early catalog dates.

**KJV masking (4.4).** The Book of Mormon, candidate and control texts are aligned to the King
James Bible (with Apocrypha) with passim at frozen settings, validated on 200 alignments
(Amendment 2; `kjv_mask/`). Attribution and dating read original spans only; borrowing reads the
full text with KJV spans labelled. Masked shares: Book of Mormon 6.82% (18,336 of 268,811 words,
`data/kjv_mask/bom/report.json`); candidates 3.71% (`data/kjv_mask/candidates/report.json`);
controls 1.78% of 1.55 billion words in 17,456 texts (`data/kjv_mask/controls/report.json`).

**Segmentation and split (4.5).** The text is segmented by internal narrator, dictation order and
scribe, each cut into 2,000- and 5,000-word chunks (756 chunks, `data/bom/segments/chunks.jsonl`).
The 5,000-word chunks are split into a discovery and a confirmation half by a seeded draw
stratified by narrator (`data/bom/segments/split.json`, seed 20261017): 22 discovery and 25
confirmation chunks.

**Candidates and controls (section 3).** Candidate samples are fixed by BOM-13 with provenance
tiers (handwritten, dictated, printed by the author, posthumous; Amendment 5); masked word counts
per sample (`data/benchmark/alm_candidates_plan.json`): Ethan Smith 277,391; Gilbert J. Hunt
56,956; Solomon Spalding 41,833; Joseph Smith dictated pre-1830 2,720 and post-1830 5,039,
handwritten post-1830 6,363; Oliver Cowdery handwritten pre-1830 1,310 and printed post-1830
44,338; Parley P. Pratt 91,478; Sidney Rigdon 21,516; W. W. Phelps 28,479. Samples under 10,000
masked words carry the unreliable-sample flag. Post-1830 samples are a secondary analysis under
Amendment 5's time-split gate. Control groups (BOM-18): pseudo-biblical (a published curation,
Amendment 6), 1820s sermons and tracts, histories with Native American origin texts, general prose.

## 2. Classical stylometry (5.1; BOM-20)

Most-frequent-word features (100, 300, 1,000; culled below 20% document frequency), Burrows' Delta
and Cosine Delta on z-scores, the General Imposters method (100 trials, half the features per
trial, imposters from the genre-matched controls) and extended nearest shrunken centroids (ENSC;
Fields, Schaalje and Roper 2011). Delta enters the synthesis as closed-set evidence only, since it
has no verification score (Amendment 8). Settings: `classic` block of the config.

## 3. The time-locked language models (5.2; BOM-27)

GPT-style decoders trained from scratch on the 1780-1830 corpus with the Book of Mormon and
post-1830 text excluded, with a byte-level BPE tokenizer of 32,000 entries fitted on the same data
(Amendment 16; `docs/timelocked-plan.md`). Training set: 202,816 volumes, 989 held out for
validation loss (`data/timelocked_lm/training_set.parquet`); one epoch over 25,052,872 windows of
1,025 tokens; 48,931 steps of 524,288 tokens. Three sizes are trained and every model-based test
runs at all three, reported side by side with none treated as the headline (Amendment 37):

| Size | Layers x width x heads | Parameters | Final validation loss | Hardware |
| --- | --- | --- | --- | --- |
| 125M (pilot) | 14 x 768 x 12 | 124,475,136 | 2.5148 | 1 H100 |
| 297M (base) | 24 x 960 x 15 | 297,170,880 | 2.3248 | 1 H100 |
| 1B (large, Amendment 26) | 32 x 1,600 x 25 | 1,035,878,400 | abandoned after a loss spike at step ~15,800 (Amendment 38) | 4 H100 |
| 590M (mid, QK-norm, Amendment 39) | 28 x 1,280 x 20 | 592,849,664 | 2.1917 | 2 H100 |

The models are public under CC BY-NC 4.0 (BOM-66; `huggingface.co/etherfuse/timelocked-1830-125m`
and siblings).

## 4. Authorial language models (5.2; BOM-28)

One copy of a time-locked model is fine-tuned per author: 3 epochs, learning rate 1e-5 constant,
AdamW (0.9, 0.95), weight decay 0.1, 1,024-token sequences, batch 8, float32 (Amendment 22). A
text's score for an author is the mean over 512-token windows of the fine-tuned model's log-loss
minus the base model's. On the benchmark, testable authors hold out their last max(5, ceil(n/4))
1,000-word blocks, tested in distinct 5,000-word windows. Three variants are reported beside the
primary method (Amendment 23): V1, learning rate 1e-4; V2, a classifier head on mean hidden
states; V3, the base model's hidden states fed to the classical trials. Candidate and control
models (Amendment 30): one per candidate sample and per control group (300,000-word seeded
samples), held-out tails never trained on and reserved for the blind run's decoys; 6.1's
statistic is the best control model's score minus the candidate's.

## 5. Style embeddings (5.4; BOM-30)

A LUAR-style encoder: the 297M base model, mean-pooled over 128-token passages, an episode of 8
passages, projected to 512 dimensions, trained with symmetric InfoNCE (temperature 0.05) on two
episodes per author from different works, 64 authors a step, 20,000 steps (Amendment 24). Authors:
the training set's named, non-corporate authors with at least two works; 8,527 qualify, 854 (10%,
seeded hash) held out as the sweep's calibration pool (`data/style_embed/authors.parquet`).
Scored in BOM-21's own trials: cosine closed set and General Imposters on the vectors.

## 6. Benchmark and pass rule (section 7; BOM-21)

Tasks: the Federalist Papers; pseudo-biblical texts with known authors; dictated texts (Scott); and
open-set cases with the true author removed. A method passes with closed-set accuracy at least 0.90
on 5,000-word samples and an open-set false-positive rate at most 0.05. As built, the open-set
threshold was the 95th percentile of the negatives, which yields about 5% for any method with
continuous scores; Amendment 25 (post hoc, labelled) corrects it: the threshold is the 5th
percentile of positives (95% acceptance of true authors), a negative at or above it is a false
match, measured by two-fold cross-fitting (seed `benchmark-open-set-fold`;
`data/benchmark/open_set.json`).

## 7. Borrowing (Q2; 5.5, 6.5; BOM-23 to BOM-26)

- **Exact reuse** (BOM-23; Amendment 10): passim alignment of the masked text against every
  eligible volume printed before it, own copies left out (`reuse/exact.py`).
- **Rare phrases** (BOM-24; Amendments 12-13): 4-grams with document frequency at most 5 in the
  1780-1830 population; a source's score is rare shared 4-grams per 10,000 of its words, placed
  against the population and its genre (`data/reuse/bom/rare.json`).
- **Paraphrase** (BOM-25; Amendment 14): the eligible corpus (278,796 volumes) cut into 128-word
  passages and embedded with bge-small-en-v1.5, chosen on a known-answer paraphrase test; exact
  search in each target's date window; a parallel beats the query's best match among 10,000 random
  window passages. Named sources are scored directly against their registered control groups and
  against a null of 500 genre- and length-matched volumes scored the same way (Amendment 21).
- **Story order** (BOM-25; Amendment 15): 2,000-word blocks reduced by a hosted model to at most
  12 role-named events (model-assisted, checked on 20 King James chapters read twice: median
  agreement 0.92); Smith-Waterman alignment with a 1,000-shuffle order test.
- **Triage** (BOM-26; Amendment 27): 1,069 registered hit pairs labelled BIBLICAL, COMMON or
  SPECIFIC by `claude-sonnet-5-5`; a simulated second review by `claude-opus-5-5`, blind to the
  first label, of every SPECIFIC and a seeded 10% of the rest; a pair is specific only if both say
  so.
- **Known-answer controls** (Amendment 9; BOM-61): every borrowing test is first run on nine
  genuine period translations of ancient texts and three compositions presented as ancient; a test
  that does not separate them is reported as uninformative on the translation question.

## 8. Dating (Q3; 5.3, 6.4; BOM-29)

Two regularised multinomial logistic regressions over 31 date bins from 1473 to 1830
(Amendments 2, 17): a grammar model on 61 rates per 1,000 tokens of grammatical features drawn
from the early modern English literature and fixed before fitting (`dating/features.py`), read
from the printed text through a letter-only fold; and a lexical model on word frequencies with
every grammar word removed. Sample: 51,044 training segments of 2,000 tokens from 27,194 volumes;
13,169 held-out segments from authors never seen in training (`data/dating/segments.parquet`). The
grammar model alone decides H3; Amendment 19 (post hoc, before any Book of Mormon scoring) decides
H3a/H3b on segment median years (more than half in 1780-1830, or in 1473-1700), keeping 6.4's
interval rule beside it. A transformer cross-check (Amendment 29) feeds the 297M model's mean
hidden states to the same classifier.

## 9. Author sweep (5.6, 6.6; BOM-39, BOM-47)

Units: 23,875 named, non-corporate authors in the training set's volumes with at least 10,000
words (`data/sweep/authors.parquet`); each profile is up to 20 seeded 1,000-word blocks
round-robin over the author's works, normalised and KJV-masked. Two signals, each separate: Cosine
Delta on the 300 most frequent words and the style embedding's cosine distance. The query is the
22 discovery chunks, distance averaged over chunks. Calibration: 200 books by 200 style-held-out
authors, their profiles rebuilt without the book; the sweep is usable if the true author ranks
first in at least 70% of books under each signal; a lead beats the 5th percentile of
best-false-match distances under both. The expected false-lead count is measured by
leave-one-out over the 200 books before the sweep runs (Amendment 28).

## 10. Blind procedure (section 8; BOM-32)

The narrator scheme's whole chunks (121 of 2,000 words, 47 of 5,000) are sealed with decoys at one
per four chunks, half from candidates' held-out tails and half from control volumes no model
trained on; Joseph Smith contributes none (Amendment 32). Opaque ids, the key written outside the
repository, hashes of key and sealed set committed. The analysis is run by a new AI session given
only the scoring script and no access to the key: this is **simulated blinding**, since one person
designed and runs the study. Outputs are hashed and committed before unblinding; decoys must be
identified at benchmark accuracy; leave-one-candidate-out follows. Per-chunk scorers apply each
method exactly as validated (Amendment 33).

## 11. Synthesis (6.7; BOM-35)

Per chunk and method family, the observation is the top-ranked candidate and its 6.1 band; its
likelihood under each hypothesis uses the family's benchmark accuracy and band rates
(Amendment 34). Families are weighted by benchmark accuracy times the imitation weight of
section 9. Prior 0.5 on "author not in set", the rest shared among candidates with reliable
samples; sensitivity over the prior from 0.2 to 0.8, dropping each family, equal weights. One
posterior per model size (Amendment 37). Dating, the sweep, access and manuscript evidence are
reported beside the posterior, not multiplied into it.

## 12. Imitation robustness (section 9; BOM-31)

Three authors who wrote both imitation-scripture and ordinary prose (Snowden, Dodsley, Kenrick);
forward test: 18 imitation windows against 13 candidates (the three plus 10 seeded distractors)
with references from ordinary prose; the forward accuracy sets each method's weight (full at
80% or above, half at 60-80%, none below); the reverse test is reported (Amendment 31).

## 13. Manuscript evidence (BOM-34)

Corrections in the Joseph Smith Papers transcripts of the original and printer's manuscripts are
typed from the transcripts' markup (strike-outs, insertions, new-hand notes): listed homophones
primary, a sound-match code beside (Amendment 35). Dictated original and copied printer's
manuscript are compared with the scribe held fixed. Word pairs stay private; ids, pages, hands,
types and counts are public (`data/manuscript/`).

## 14. Access evidence (BOM-33)

Each candidate source is scored 0-3 for documented availability before mid-1829 (3, within Joseph
Smith's documented reach; 2, in western or central New York; 1, in print in the United States
only; 0, no evidence of circulation), every score cited (`data/access/access_table.csv`).
