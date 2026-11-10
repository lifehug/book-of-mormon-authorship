# Authorship, borrowing and dating of the earliest Book of Mormon text: an open, pre-registered computational study

*Draft, 2026-11-10. Dave Taylor, with analysis by an AI model (Claude). Every review step is
simulated by an AI model and labelled so; the blinding was simulated (the scoring ran without the
key; the analyst is an AI model). Repository: https://github.com/lifehug/book-of-mormon-authorship;
pre-registration: https://osf.io/6ugxc/ (frozen 2026-10-15; 44 dated amendments, the post hoc ones
labelled).*

## Abstract

We ask three questions of the 1830 Book of Mormon text: whose writing it most resembles (Q1),
what it borrowed from earlier books (Q2), and when its English dates from (Q3). The study takes no
position on the book's origin or on inspiration; it reports which known writers or books, if any,
the text closely resembles, with measured error rates. Every threshold was fixed in a public
pre-registration before the text was scored. We built a corpus of about 200,000 English volumes
printed 1780-1830, trained GPT-style language models on that period only (125M, 297M and 590M
parameters), masked every King James Bible span, and validated every method on known-answer tasks
before a single blind run in which 168 Book of Mormon chunks were mixed with 43 decoys. The
right candidate was ranked first for most candidate decoys (15-21 of 22 by method); the candidate
models, the only family able to call a match at its registered threshold, matched none of the 21
control passages. No candidate author (Joseph Smith, Oliver Cowdery, Sidney Rigdon, Solomon
Spalding, Ethan Smith, Gilbert J. Hunt, Parley P. Pratt, W. W. Phelps) is matched under the
registered rule. The registered Bayesian synthesis, which covers only the three candidates with
adequate pre-1830 samples (Ethan Smith, Hunt, Spalding), gives "none of these three" 0.744 (prior
0.5); Joseph Smith's and Cowdery's pre-1830 samples are too small for it (2,702 and 1,309 words)
and are untested by it, not ruled out. A sweep of 23,872 period authors, which failed its own
usability test, finds no lead. *The Late War* (1816) and *The First Book of Napoleon* (1809) pass
the registered rare-phrase rule, as does the American pseudo-biblical genre generally; no proposed
source shares a copied passage, a plot sequence or a pair of passages judged specific. The grammar of the text dates mostly before 1700 (median
1661) and is more archaic than period imitations of biblical style (p 0.0001). No method passes
the registered open-set bar (5% false matches; the best stable rate is 22%), so all attribution
results are graded evidence. Where methods must rank someone first, they rank Joseph Smith's
1828-29 revelations closest, a sample in the text's own scriptural register; his ordinary prose of
1831-33 sits mid-pack. Code, data tables, every trained model and every decision are public and
rerunnable.

## 1. Introduction

The Book of Mormon was published in 1830. Its origin has been argued for two centuries, and
computational studies have reached opposite conclusions: wordprint studies found its narrators
distinct from each other and from nineteenth-century candidates (Larsen, Rencher and Layton
1980); nearest-shrunken-centroid classification pointed to Sidney Rigdon and Solomon Spalding
(Jockers, Witten and Criddle 2008); a reanalysis showed that result depended on a closed candidate
list (Fields, Schaalje and Roper 2011). Each was criticised for its setup more than its arithmetic:
closed candidate sets that force a pick, features that measure biblical register rather than
authorship, choices made after seeing the data, and models that had read the text.

This study is designed against those failures:

1. **Open-set evaluation.** Every attribution method may answer "none of these", and its rate of
   false matches is measured on known-answer tasks before it is used.
2. **King James masking.** Every span aligned to the King James Bible (6.8% of the text) is
   removed before attribution and dating.
3. **Pre-registration.** Thresholds, features, seeds and model choices were fixed publicly before
   scoring; every later change is a dated amendment, and those made after seeing results are
   labelled post hoc.
4. **No leakage.** The text was kept out of every model's training and calibration until one blind
   run. (A gap in this rule, found after unblinding, is reported in section 9.)
5. **Period-only language models** trained on 1780-1830 English, so "ordinary" means ordinary for
   the period.
6. **A whole-library sweep** of every author in the period corpus, not only named suspects.

What stylometry can see is the English on the page and whoever produced it; it cannot see how
that English came to be, and in particular cannot separate a composer from a dictator or a
translator. The study therefore makes no claim about translation, inspiration or the truth of the
book's contents. Everything is runnable from the repository; texts that cannot be redistributed
are replaced by derived tables and by the steps to obtain them (`docs/replication.md`).


# Part I. Data and methods

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


# Part II. Validation, borrowing and dating checks

These results do not depend on the blind run. The borrowing results (section 1) are the
registered answers to Q2. Sections 2 to 4 are validation; sections 5 and 6 are production and
access evidence reported beside the synthesis. Numbers are read from the files named.

## 1. Borrowing (Q2)

### 1.1 Exact reuse (BOM-23; `docs/reuse-plan.md`)

With KJV spans masked, 58 passages in 47 earlier-catalogued volumes align with the Book of Mormon,
covering 0.52% of it. Seventeen of the 47 are later texts quoting it under catalog dates decades
too early (Congressional serial-set volumes catalogued 1817, *The Millennial Harbinger*
catalogued 1830); without them the share is 0.16%. The other 30 volumes share short, loose
religious stock phrases (9-46 tokens, identity 0.27-0.67). For comparison, *The Late War* (1816)
shares 8.92% with earlier books and an 1821 sermon collection 2.47%.

### 1.2 Rare phrases (BOM-24; `data/reuse/bom/rare.json`)

| Source | Rare shared 4-grams | Per 10,000 words | Rank of 204,520 | p (95% interval) |
| --- | --- | --- | --- | --- |
| *The First Book of Napoleon* (1809) | 12 | 5.45 | 63 | 0.0003 (0.0002-0.0031) |
| *The Late War* (1816, 9 printings) | 22 | 3.86 | 131 | 0.0006 (0.0004-0.0017) |
| *View of the Hebrews* (1825) | 2 | 0.37 | 9,496 | 0.046 (0.017-1.0) |
| Spalding, *Manuscript Story* | 1 | 0.24 | - | 0.068 |
| Luke (KJV), against the masked text | 0 | 0 | - | 1.0 |

*The Late War* and *Napoleon* are significant by the registered rule. Within the curated
pseudo-biblical group (post hoc), the 1829 reprint of Ilive's *Book of Jasher* shares more (7.99
per 10,000 words, 31 phrases); the shared phrases are battle and chronicle formulas. The rule
calls 2,044 volumes significant, mostly short pieces sharing one phrase.

### 1.3 Paraphrase (BOM-25; `data/semantic/named.json`, `named_null.json`)

| Source | Rank in group | Score (95% interval) | Null median | Null 99th pct. | Percentile | Stands out |
| --- | --- | --- | --- | --- | --- | --- |
| *View of the Hebrews* (1825) | 1 of 49 | 29.6 (28.0-31.3) | 14.6 | 45.0 | 84.6 | no |
| *View of the Hebrews* (1823) | 2 of 49 | 29.5 (27.9-31.1) | 9.2 | 38.4 | 94.0 | no |
| *The First Book of Napoleon* | 3 of 18 | 7.9 (6.9-9.0) | 0.1 | 8.8 | 98.4 | no |
| *The Late War* (1816) | 6 of 18 | 1.9 (1.4-2.4) | 0.4 | 14.6 | 79.8 | no |
| Spalding, *Manuscript Story* | 12 of 49 | 5.5 | - | - | - | no (rank) |

*View of the Hebrews* leads the origins-of-the-American-Indians group, but 77 of 500
genre-and-length-matched religious volumes score higher. In the whole-corpus search (163,121,310
passages, 221,373 volumes in the window; `data/semantic/corpus_bom.json`) editions of Josephus take
14 of the top 20 places; the registered rule flags 622 sources, which mostly measures biblical
register.

### 1.4 Story order (BOM-25; `data/semantic/skeleton/`)

No source shares the Book of Mormon's order of events at the registered level (order p at most
0.01). Among the 20 leading search sources the longest shared run is 9 of its 1,421 events
(Josephus, order p 0.24); the positive control, Josephus against Genesis-Judges, shares 108 events
in order (p 0.001). Named sources: *View of the Hebrews* 1823, 3 events, order p 0.97, rank 17 of
49; 1825, 2 events, p 1.0, rank 43 of 49; Spalding, 4 events, p 0.67; *The Late War*, 2 events,
p 1.0; *Napoleon*, 3 events, p 1.0.

### 1.5 Known-answer controls (Amendment 9)

Exact reuse (U 4 of 27, p 0.964), rare phrases (U 6/27, p 0.927) and paraphrase (U 14/27, p 0.50)
do not separate genuine translations of ancient texts from compositions presented as ancient, and
the King James italics test is not shown to work (`docs/italics-plan.md`). None of the borrowing
tests therefore bears on the translation question; each describes which period books share the
Book of Mormon's wording, ideas or plot.

### 1.6 Triage (BOM-26; `data/semantic/triage.json`, `docs/triage-plan.md`)

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
0.505.

**Reading (Q2).** No named proposed source stands out under its registered null in any of the
four searches except rare phrases, where *The Late War* and *Napoleon* pass a rule that the whole
imitation-scripture genre also passes. No passage is copied and no plot is shared. Every surfaced
similarity is explained, on triage, by King James wording (36%) or period stock phrasing (64%).

## 2. Benchmark (section 7; `data/benchmark/open_set.json`, `prior_work.json`)

| Method | Size | Federalist | Imitation scripture | Dictated (Scott) | Overall | False matches | Passes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| General Imposters | - | | | | 0.833 | 0.617 | no |
| ENSC (its own "none") | - | | | | 1.000 | 0.661 | no |
| Style embeddings | - | | | | 0.839 | 0.500 | no |
| ALM primary | 125M | 0.769 | 0.958 | 1.000 | 0.936 | 0.473 | no |
| ALM primary | 297M | 1.000 | 0.958 | 1.000 | 0.991 | 0.382 | no |
| ALM primary | 590M | 1.000 | 0.917 | 1.000 | 0.982 | 0.218 | no |
| V1 (lr 1e-4, registered) | 125M / 297M / 590M | | | | 0.936 / 0.936 / 0.627 | 0.455 / 0.473 / 0.818 | no |
| V1 at the rate chosen on held-out training text (Amendment 41, post hoc) | 125M / 297M / 590M | | | | 0.936 / 0.991 / 0.982 | 0.473 / 0.382 / 0.218 | no |
| V2 (classifier head, registered) | 125M / 297M / 590M | | | | 0.900 / 0.909 / 0.764 | 0.282 / 0.136 / 0.391 | no |
| V2 at the chosen rate (Amendment 41, post hoc) | 125M / 297M / 590M | | | | 0.764 / 0.773 / 0.564 | 0.591 / 0.400 / 0.755 | no |
| V2, five further seeds (Amendment 42, post hoc): range | 125M / 297M / 590M | | | | 0.66-0.93 / 0.51-0.76 / 0.40-0.78 | 0.09-0.93 / 0.53-0.98 / 0.32-0.93 | no |
| V3 (hidden states) | 125M / 297M / 590M | | | | 0.839 / 0.844 / 0.844 | 0.689 / 0.717 / 0.706 | no |
| GPT-2, primary method (BOM-68 ablation) | 124M / 355M | | | | 0.900 / 0.945 | 0.918 / 0.855 | no |

The 1B was abandoned after a loss spike and replaced by the 590M with QK-norm (Amendments 38,
39). False matches for the primary method fall with size: 0.473, 0.382, 0.218. V1's registered
rate (ten times Amendment 22's) damaged the 590M: its fine-tuned models raised the loss on new
text by 0.81 nats (0.56 at 297M), and at the rate chosen on held-out training text V1 is the
primary method (1e-5 at every size). V2 is unstable: at 125M its rerun at the registered
rate and seed on an H100 gave 0.764 / 0.591 against the Mac run's 0.900 / 0.282, so its single
registered numbers are reported beside the spread of five further seeds (Amendment 42).

**No method passes** the registered bar (closed set at least 0.90 and false matches at most
0.05). Every method can rank candidates; none can yet say "none of these" reliably. Classical
methods, style embeddings and V3 are scored on BOM-21's 180 trials; the fine-tuned models on 110
held-out tests, so the two groups are compared within, not across (BOM-68; paired exact McNemar
tests in `data/benchmark/prior_work.json`).

**Candidate models** (`data/benchmark/alm_candidates_<size>.json`): held-out closed-set accuracy
among candidates, 297M / 590M: Ethan Smith 1.0 / 1.0 (20 tests), Spalding 1.0 / 1.0 (7), Cowdery
printed 1.0 / 1.0 (7), Phelps 1.0 / 1.0 (3), Hunt 0.8 / 0.8 (10), Pratt 1.0 / 0.95 (19), Rigdon
0.5 / 1.0 (2); 0.956 of 68 windows at both sizes. Samples under 10,000 words are untested.

## 3. Dating validation (Q3; `data/dating/validation.json`)

| | Grammar (decides H3) | Lexical |
| --- | --- | --- |
| Held-out mean error | 23 years | 13 years |
| 90% interval coverage | 0.91 | 0.76 |
| Median 90% interval width, 1780-1830 text | 85 years | 19 years |
| Held-out 1780-1830 volumes called H3a (Amendment 19) | 1,464 of 1,875 | |
| Held-out pre-1700 volumes called H3b | 3,729 of 4,144 | |
| Pseudo-biblical controls vs ordinary 1780-1830 | -53 years (p 0.0001) | -5.5 years (p 0.26) |
| King James text | 1631 (H3b) | 1710 |
| Known-answer separation (Amendment 9) | p 0.57, none | p 0.81, none |

King James imitation alone moves the grammar model's date back by about half a century; this is
the comparison H3c registers. The transformer cross-check (Amendment 29,
`data/dating/transformer_validation.json`): held-out mean error 10.1 years, 90% interval coverage
0.94, and King James imitation moves it by +0.8 years where the grammar model moves -53.

## 4. Imitation robustness, classical methods (BOM-31; `data/benchmark/imitation.json`)

| Method | Forward (imitation text to real author) | Weight | Reverse |
| --- | --- | --- | --- |
| Burrows' Delta | 13/18 = 0.72 (0.47-0.90) | 0.5 | 0.38 |
| Cosine Delta | 13/18 = 0.72 (0.47-0.90) | 0.5 | 0.29 |
| General Imposters | 11/18 = 0.61 (0.36-0.83) | 0.5 | 0.12 |
| ENSC | 7/18 = 0.39 (0.17-0.64) | 0 | 0.25 |

| Style embeddings (297M encoder) | 7/18 = 0.39 (0.17-0.64) | 0 | 0.54 |
| ALM primary 125M / 297M / 590M | 5 / 7 / 6 of 17 (0.29 / 0.41 / 0.35) | 0 | 0.25 / 0.17 / 0.04 |
| V1 125M / 297M / 590M | 0 / 2 / 0 of 17 | 0 | 0.12 / 0.42 / 0.00 |
| V3 125M / 297M / 590M | 4 / 4 / 5 of 17 | 0 | 0.00 / 0.25 / 0.21 |
| Style embeddings (590M encoder) | 10/18 = 0.56 (0.31-0.78) | 0 | 0.42 |

The model-based methods are no better than the classical ones at seeing through imitation, and
size does not help: the 590M's primary method names the real author in 6 of 17 imitation texts.

## 5. Production evidence (BOM-34; `data/manuscript/summary.json`, `docs/manuscript-evidence.md`)

The catalog types 1,597 corrections on the original manuscript's 231 surviving pages and 2,136
on the printer's manuscript's 468. Sound-alike word corrections (listed homophones such as
where/were, there/their) are far more common in the dictated original than in the copied
printer's manuscript:

| Comparison | Original | Printer's | Odds ratio | Fisher p |
| --- | ---: | ---: | ---: | ---: |
| All pages: homophone fixes / substitutions | 36 / 693 | 8 / 927 | 6.3 | 1e-7 |
| Same passages only | 36 / 693 | 2 / 457 | 12.5 | 2e-6 |
| Oliver Cowdery as scribe in both | 36 / 590 | 6 / 837 | 9.0 | 2e-9 |

This bears on how the words reached the page (by ear, then copied by eye); it cannot distinguish
whether a dictated text was composed, recited or read aloud.

## 6. Access evidence (BOM-33; `data/access/access_table.csv`, `docs/access-evidence.md`)

Of 33 texts scored: 15 at 3 (documented within Joseph Smith's reach; all but one are editions of
Josephus, in the Manchester library's accessions and in Palmyra bookstore advertisements including
January-May 1829), 2 at 2, 10 at 1, 6 at 0. Named sources: *View of the Hebrews* 1825 edition 2
(advertised in Utica, 1826), 1823 edition 1; *The Late War* 1 (Palmyra "Historical Reader"
advertisements of 1827-1830 do not name the author); *The First Book of Napoleon* 0; Spalding's
manuscript 0. Availability is not use.


# Part III. The blind run

Unblinded 2026-11-10 (`data/blind/unblinded.json`; first read in `docs/results-first-read.md`).
Read in the order of trust fixed before unblinding (`docs/method-reliability.md`): the primary
language-model method and the classical methods first; every other method beside them; V2 carries
no weight.

## Decoys

| Method | Right candidate ranked first (of 22 candidate decoys) | Control decoys called a match (of 21) | Candidate decoys matched to their author |
| --- | --- | --- | --- |
| Burrows' / Cosine Delta | 20 / 15 | (no match call) | |
| General Imposters | 19 | 0 | 0 (cannot reach *match* at its registered threshold) |
| Style encoders 297M / 590M | 16 / 18 | 0 | 0 (registered rule) |
| Candidate models 125M / 297M / 590M | 20 / 21 / 19 | 0 | 20 / 14 / 11 |

The run is valid by section 8's rule: decoys are identified at about benchmark accuracy, and no
method calls a passage by a non-candidate a match.

## Attribution (Q1)

**Match calls.** General Imposters and the style encoders return no *match* for any of the 168
chunks under the registered thresholds. The candidate models return 10, 5 and 3 matches by size
(125M, 297M, 590M), fewer than their benchmark false-match rates (22-47%) would produce for text by
no candidate. **H1a (a candidate matched by two independent families on both halves) is not
supported for any candidate.**

**The author sweep (descriptive only).** The sweep failed its registered usability test (true
author first for 27-35% of 200 held-out books against the required 70%), so its result is
descriptive, not evidence. No author of the 23,872 swept passes both lead thresholds on the
discovery half (expected by chance 0.035 per query; `data/sweep/calibration.json`). The nearest by both
signals are writers in the scriptural and prophetic register (John Wroe, George Fox, William
Sewel), none near a threshold.

**Synthesis (6.7).** Posterior over the primary candidates (pre-1830 confirmatory samples), both
halves: **not in set 0.744** (prior 0.5); Gilbert J. Hunt 0.089, Solomon Spalding 0.085, Ethan
Smith 0.082. Both model-based families carry an imitation weight of zero (section 9 of the
pre-registration; they were misled by deliberate imitation, BOM-31), so only General Imposters
enters and the posterior is identical at every model size. Across the prior grid (0.2-0.8) "not in
set" runs 0.42-0.92; under equal family weights or treating chunks as independent, 1.00; dropping
General Imposters returns the prior. Secondary set (post-1830 samples, Amendment 5): not in set
0.715, Pratt 0.122. **H1b ("none of these") is favoured for the three candidates the synthesis can
test, but not established**, since no method passes the open-set bar. The synthesis excludes, by
the registered rule (3: samples under 10,000 words), the two candidates the methods rank closest:
Joseph Smith (2,702 pre-1830 words) and Cowdery (1,309). They are untested by it, not ruled out.

**Narrators, scribes and dictation order (6.3, H1c).** The four principal narrators separate at
0.744 (chance 0.277, p 0.001) and the first and last parts of the dictation at 0.758 (chance
0.502, p 0.001); the surviving original manuscript holds three hands in the scored text (Oliver Cowdery, John
Whitmer and the unidentified Scribe 3, the last two only in 1 Nephi), but only Cowdery's fills at
least three continuous 2,000-word chunks, and most of the manuscript does not survive, so scribes
cannot be compared. Both are
below the 0.96 the same method reaches on distinct authors: narrators are **not separable as
different authors**, and dictation order explains the differences about as well.

## A leakage found after unblinding, and the rerun (Amendment 43, post hoc)

After unblinding, the 590M candidate models ranked Oliver Cowdery's pre-1830 sample closest to 119
of 168 chunks. That sample, his "Articles of the Church of Christ" (June 1829), is 40% word-for-word
Book of Mormon text: it copies the sacrament prayers and baptismal instructions. Parley P. Pratt's
books also quote the text. The sealing rule had been enforced on the training corpus but not on
candidate samples.

Every run a candidate sample shares with the text was classed by a rule fixed before the matches
were read: biblical; period stock phrasing; written before the matching passage was dictated; in
the same weeks; or after it (`docs/bom-overlap-analysis.md`). Only **quotations** were dropped:
passages of 20 or more words written after the matching passage existed. Masking every shared run
was rejected because it would also remove genuine shared idiom, above all from Joseph Smith's
1828-29 revelations, which contain no quotation (one shared phrase predates the passage it
matches; the rest were dictated in the same weeks) and are unchanged. The candidate models were
retrained and the sealed set rescored by every method that reads candidate samples.

| Method | Registered run: ranked closest (of 168) | Without quotations | Matches |
| --- | --- | --- | --- |
| Cosine Delta | Joseph Smith 131, Hunt 31 | Joseph Smith 148, Hunt 20 | 0 -> 0 |
| Burrows' Delta | Joseph Smith 77, Hunt 47, Pratt 37 | Joseph Smith 91, Hunt 49, Pratt 25 | 0 -> 0 |
| General Imposters | Pratt 74, Joseph Smith 48 | Joseph Smith 66, Pratt 66 | 0 -> 0 |
| Candidate models 125M / 297M / 590M | Joseph Smith 82 / 133 / 46; Cowdery 29 / 34 / 119 | Joseph Smith 159 / 168 / 131 | 10 / 5 / 3 -> 2 / 2 / 0 |
| Synthesis, not in set | 0.744 | 0.744 | |

The Cowdery ranking was leakage and disappears. Match calls fall, the synthesis is unchanged, and
every method ranks Joseph Smith's pre-1830 sample closest. The registered run stays the main
record (git tag `blind-registered-2026-11-10`); the rerun is reported beside it (`data/*/a43/`).

## Register: Joseph Smith's revelatory and ordinary prose (Amendment 44, post hoc)

Joseph Smith's only pre-1830 sample is revelation (1828-29, 2,702 words), written in a scriptural
voice like the text's; every other candidate sample is a sermon, treatise, history, romance or
newspaper prose. His non-revelatory writing of 1831-33 (letters and the 1832 history, about 11,600
tokens) was pooled into one unit and scored beside it. Mean rank among 12 candidate samples on the
168 chunks (1 = closest):

| Method | Revelations, 1828-29 | Ordinary prose, 1831-33 |
| --- | --- | --- |
| Candidate models 125M / 297M / 590M | 1.1 / 1.0 / 1.3 | 6.1 / 6.3 / 5.4 |
| Style encoders 297M / 590M | 1.1 / 1.5 | 4.7 / 5.7 |
| Cosine Delta | 1.2 | 3.3 |
| General Imposters | 3.6 | 6.1 |
| Burrows' Delta | 7.7 | 2.7 |

Seven of eight methods place his revelations closest and his ordinary prose in the middle;
Burrows' Delta, which rests most on function words, reverses them. The closeness to Joseph Smith
runs mainly through the revelatory register, which is the register of the text. His ordinary prose
is all post-1830: its closeness would be uninformative (he had read the book) and its distance is
the informative direction. No ordinary prose of his survives from before 1830, so his style before
the book cannot be tested.

## Prior studies replicated (BOM-22)

Each earlier study's published method was run on our texts before any of our own methods touched
the Book of Mormon (`paper/replication-report.md`): Larsen, Rencher and Layton (1980), speakers
differ and almost no block resembles a candidate, **replicated**; Holmes (1992), Joseph Smith's own
writing separates while the revelations sit with the book's prophets, **replicated**; Jockers,
Witten and Criddle (2008), the method reproduces on their data but the leading candidate follows
the texts chosen for each candidate (Pratt on ours, Rigdon on theirs): **method yes, result no**;
Schaalje, Fields, Roper and Snow (2011), most chapters to an unobserved author, **replicated**, with
the answer depending on candidate sample length; Johnson and Johnson (2013), *The Late War* in the
top 0.05% for shared rare phrases, but 30 books are denser, mostly other imitation scripture:
**partly**.

## Dating the text (Q3)

Of the 215 segments of the 168 chunks, the grammar model (which decides H3) places 78% of segment
medians before 1700 and 7% in 1780-1830 (median of medians 1661): **H3b**. The lexical model (1736)
and the transformer cross-check (1755) place the majority in neither window. **H3c is rejected**:
the text dates earlier than the 1780-1830 pseudo-biblical control volumes (grammar 1661 vs 1734,
lexical 1738 vs 1794; permutation p 0.0001; `data/dating/h3c.json`). The grammar model dates King
James imitation about 53 years early in validation, so part of the early date is the biblical
register; the text is nevertheless more archaic by these measures than the period's other biblical
imitations, and the transformer, which imitation did not move in validation, still dates it before
them (1755 vs 1805). Treating each book of the text, rather than each chunk, as one unit (chunks of
one book are not independent) leaves the result unchanged: 12 books, grammar mean 1664, p 0.0025;
lexical 1724, p 0.0001.

Two cautions. H3b is not diagnostic between accounts of the text's origin: an early-modern
placement is predicted by an early-modern source, by imitation of one, and by the King James
register. And the dating models learned 1780-1830 English from printed, edited books; nonstandard
upstate New York and New England vernacular, which the 1830 text contains and which edited print
removed, may read as archaic to them. No unedited-vernacular control was available.

## Public claims (BOM-42)

Seventeen public claims from critical, apologetic and academic sources were registered with their
decision rules before any result (`data/claims/register.yaml`). Verdicts: supported 2, contradicted
6, mixed 4, not addressed 1, untestable 4 (`docs/claims-verdicts.md`). Supported: with "none of the
above" allowed, no nineteenth-century candidate is the author (Fields 2011); the narrators are not
distinct and sit close to Joseph Smith's revelations (Holmes 1992). Contradicted: dependence on
*View of the Hebrews*; Rigdon and Spalding as contributors (Jockers 2008); distinct narrators
(Larsen 1980); Spalding's manuscript as source; Cowdery or Rigdon as author; an 1820s environment
in the language (Brodie 1945; language only). Mixed: *The Late War*; early-modern syntax that
imitation cannot explain (Skousen and Carmack); the American pseudo-biblical genre (Shalev); *The
First Book of Napoleon*. An untestable claim is not a contradicted one.


# Part IV. Limitations

**No method passes the benchmark.** Every attribution method ranks candidates well (closed-set
accuracy up to 0.991 at 297M) but none keeps false matches at or below the registered 5% (best
stable result: 0.218, the primary method at 590M; `data/benchmark/open_set.json`). V2's 0.136 at
297M was one lucky seed: five further seeds gave 0.53-0.98 (Amendment 42). Under the registered thresholds General
Imposters and the style embeddings cannot return *match* at all (their calibrated match threshold
is 1.0, the largest possible score), so section 6.2's two-family rule could not have supported any
candidate; both readings of 6.1 and the false-match ladder are reported (Amendment 33). Results are
therefore graded evidence, not attributions.

**Methods differ in stability** (`docs/method-reliability.md`, written before unblinding). The
primary language-model method reproduces exactly across machines and improves with model size;
V1's registered learning rate broke at 590M (Amendment 41); V2 swings from 9% to 98% false matches
across seeds and carries no weight; the model-based methods are weaker than the classical ones on
imitation (BOM-31). The blind results are read in that order of trust.

**"Closest" to Joseph Smith is confounded with register.** No candidate is matched, and Joseph
Smith's sample ranks closest (after Book of Mormon quotations are removed from the samples,
Amendment 43). That sample is the only one in the text's own register: revelations dictated in a
scriptural voice in 1828-29, the only writing of his that survives from before the book. His
ordinary prose of 1831-33, scored the same way, sits mid-pack for seven of eight methods (Burrows'
Delta reverses; Amendment 44, `data/blind/a44/`). The methods cannot separate shared register from
shared authorship, nor the person who dictated a text from the person who composed it, and no
pre-1830 ordinary prose exists to test his style before the book. Whether his later prose drifted
toward the book's style is a separate question, tabled with its sources (BOM-73).

**The borrowing and dating tests cannot speak to translation.** None separates genuine
translations of ancient texts from compositions presented as ancient (Amendment 9; section 1.5 of
`results_so_far.md`). They describe resemblance and period, not process.

**One person, simulated review and simulated blinding.** The study is designed and run by one
person with AI assistance. Every review step (adversarial, draft, peer) and the second triage pass
are simulated by AI models and labelled as such; the blind run's "fresh session" is a new AI
session without the key, not an independent analyst. None of this is independent scrutiny.

**Small and uneven candidate samples.** Joseph Smith's undisputed pre-1830 writing is 2,720
dictated words; Oliver Cowdery's pre-1830 handwritten sample is 1,310. Both are below the
10,000-word floor and are reported as unreliable samples, not as non-matches. Candidate corpora
mix provenance (dictated, edited, posthumously published); each sample's tier is recorded.

**Dictation and scribes.** Several hands stand between any author and the page. The manuscript
evidence shows dictation-type errors but cannot say what was dictated from; the scribe/narrator
comparison (6.3) runs only after unblinding.

**The corpus.** OCR quality is uneven (measured, BOM-14/BOM-50); catalog dates are wrong for some
volumes (corrected where the text names later years, BOM-64); author names conflate namesakes and
split variants. 72% of the original manuscript is lost.

**Post hoc decisions.** Several choices were made after some results were seen and are labelled:
Amendments 8, 13 (partly), 19, 20, 21, 25, 26, 37, the disclosed slip in 31, and Amendment 33's
option (b) if used. Each is listed with its reason in section 11 of the pre-registration.

**Models.** The time-locked models were trained on the period corpus, which includes held-out
authors' volumes used later for calibration (language modelling, not authorship supervision);
the dating cross-check reports volumes the model trained on separately for this reason
(Amendment 29). The fine-tuning settings were fixed for all sizes in advance and may not suit the
largest. The GPT-2 ablation is benchmark-only, since GPT-2 read modern text possibly including the
Book of Mormon.

**Replication.** Licensed texts cannot be redistributed (Harvard Institutional Books, HathiTrust,
Joseph Smith Papers transcripts). Derived tables, checksums and the steps to obtain every source
are published (`docs/replication.md`), and every result is rerunnable from the repository with
those sources.

**Access is not use.** The access table records documented availability; it does not show that
anyone read a given book.

**A sweep with no leads says nothing beyond the corpus.** The sweep's top-1 rate on 200 held-out
books is 27-35%, below the registered 70% (not usable as an attribution tool), and it found no
lead (0, against 0.035 expected by chance; `docs/results-first-read.md` 5). Writers outside the
23,872 swept authors, or whose work did not survive in print, are not covered.


# Discussion

**What the evidence supports.** The methods rank real authors correctly on most decoys, and the
candidate models, which can call a match, called none of the control passages one. On the Book of
Mormon, no method makes a confident match to any proposed author. The registered synthesis leans
against the three candidates it can test (Ethan Smith, Hunt, Spalding; "none of these three"
0.744 from a prior of 0.5); it cannot test Joseph Smith or Cowdery, whose pre-1830 samples are too
small, and says nothing for or against them. *The Late War* and *The First Book of Napoleon* pass
the registered rare-phrase rule, as the pseudo-biblical genre does generally; no proposed source
shares a copied passage or a plot sequence, and no surfaced pair of passages was judged specific
(each is explained by King James wording or period stock phrasing).
The text's grammar dates earlier than its period and earlier than the period's other imitations of
biblical style.

**Decisions made after results existed.** The registered analysis stands as the main record; each
of the following was added later, is labelled post hoc, and is reported beside it:

| Amendment | Decided after | What it changed | Effect on the headline |
| --- | --- | --- | --- |
| 19 | dating validation | H3a/H3b decided on segment medians | none on Book of Mormon results (before scoring) |
| 33 | benchmark | both 6.1 readings and a false-match ladder reported | none (both shown) |
| 38-39 | the 1B's loss spike | 590M replaces 1B | one model size |
| 41-42 | the 590M benchmark | V1/V2 learning rate, V2 seeds | V2 given no weight |
| 43 | unblinding | Book of Mormon quotations dropped from candidate samples | Cowdery ranking removed; synthesis unchanged |
| 44 | unblinding | Joseph Smith's ordinary prose scored | register confound stated |
| 45 | the simulated reviews | ranking rechecked at equal training dose | see section on dose |

**What it does not support.** No method passes the registered open-set bar, so "none of these" is
graded evidence, not a verdict; the synthesis rests on the classical family alone, because the
model-based methods were misled by deliberate imitation; and the candidate samples are uneven and,
for the writers closest to the text, small. Where methods must rank someone first they rank Joseph
Smith's 1828-29 revelations, which share the text's register and were dictated by the same person
in the same months; his ordinary prose does not stand out. These methods cannot separate register
from authorship, nor the person who dictated a text from the person who composed it, and none of
the borrowing or dating tests separates a genuine translation from a text presented as ancient
(Amendment 9). The study therefore says nothing about how the text was produced, whether it is a
translation, or whether it is inspired.

**What changed along the way.** Three decisions were made after results existed and are labelled
so: the learning rate of two benchmark variants, which the larger model exposed (Amendments 41-42);
the removal of Book of Mormon quotations from candidate samples, after unblinding revealed that one
candidate's sample was 40% quotation (Amendment 43); and the comparison of Joseph Smith's
revelatory and ordinary prose (Amendment 44). Each is reported beside the registered result, not
in place of it.

**What would sharpen it.** Larger models (the false-match rate fell from 47% to 22% between 125M
and 590M parameters); more and larger candidate samples, especially pre-1830 writing outside the
scriptural register, which does not survive for Joseph Smith; more benchmark tasks, to narrow the
error rates; and the time series of Joseph Smith's and his contemporaries' prose after 1830 (BOM-73,
`docs/js-over-time-research.md`).

**Reproducing it.** The pre-registration and its amendments, the code, the configuration file
every number is stamped with, every result file and every trained model are public
(`etherfuse/timelocked-1830-*` and `etherfuse/bom-authorship-*` on Hugging Face, with SHA-256
lists in `data/manifests/`). Three sources are licensed and cannot be redistributed; the steps to
obtain them are in `docs/replication.md`. Mistakes are possible; every one can be found and redone.
