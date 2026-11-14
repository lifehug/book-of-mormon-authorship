*The appendices below are carried over from the 2026-11-10 draft and have not yet been brought up to outline version 3; where they differ from sections 1-14, the sections are right.*

## Appendix A. Methods in detail

Every number below is read from the file named beside it; settings come from
`config/preregistered.yaml`, and every output carries the SHA-256 of that file. The
pre-registration is `paper/preregistration.md` (OSF https://osf.io/6ugxc/); amendments are cited by
number and listed in its section 11. Commands are in `eval/README.md`.

### 1. Data

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

### 2. Classical stylometry (5.1; BOM-20)

Most-frequent-word features (100, 300, 1,000; culled below 20% document frequency), Burrows' Delta
and Cosine Delta on z-scores, the General Imposters method (100 trials, half the features per
trial, imposters from the genre-matched controls) and extended nearest shrunken centroids (ENSC;
Fields, Schaalje and Roper 2011). Delta enters the synthesis as closed-set evidence only, since it
has no verification score (Amendment 8). Settings: `classic` block of the config.

### 3. The time-locked language models (5.2; BOM-27)

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

### 4. Authorial language models (5.2; BOM-28)

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

### 5. Style embeddings (5.4; BOM-30)

A LUAR-style encoder: the 297M base model, mean-pooled over 128-token passages, an episode of 8
passages, projected to 512 dimensions, trained with symmetric InfoNCE (temperature 0.05) on two
episodes per author from different works, 64 authors a step, 20,000 steps (Amendment 24). Authors:
the training set's named, non-corporate authors with at least two works; 8,527 qualify, 854 (10%,
seeded hash) held out as the sweep's calibration pool (`data/style_embed/authors.parquet`).
Scored in BOM-21's own trials: cosine closed set and General Imposters on the vectors.

### 6. Benchmark and pass rule (section 7; BOM-21)

Tasks: the Federalist Papers; pseudo-biblical texts with known authors; dictated texts (Scott); and
open-set cases with the true author removed. A method passes with closed-set accuracy at least 0.90
on 5,000-word samples and an open-set false-positive rate at most 0.05. As built, the open-set
threshold was the 95th percentile of the negatives, which yields about 5% for any method with
continuous scores; Amendment 25 (post hoc, labelled) corrects it: the threshold is the 5th
percentile of positives (95% acceptance of true authors), a negative at or above it is a false
match, measured by two-fold cross-fitting (seed `benchmark-open-set-fold`;
`data/benchmark/open_set.json`).

### 7. Borrowing (Q2; 5.5, 6.5; BOM-23 to BOM-26)

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

### 8. Dating (Q3; 5.3, 6.4; BOM-29)

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

### 9. Author sweep (5.6, 6.6; BOM-39, BOM-47)

Units: 23,875 named, non-corporate authors (23,872 swept: three had no word-frequency profile) in the training set's volumes with at least 10,000
words (`data/sweep/authors.parquet`); each profile is up to 20 seeded 1,000-word blocks
round-robin over the author's works, normalised and KJV-masked. Two signals, each separate: Cosine
Delta on the 300 most frequent words and the style embedding's cosine distance. The query is the
22 discovery chunks, distance averaged over chunks. Calibration: 200 books by 200 style-held-out
authors, their profiles rebuilt without the book; the sweep is usable if the true author ranks
first in at least 70% of books under each signal; a lead beats the 5th percentile of
best-false-match distances under both. The expected false-lead count is measured by
leave-one-out over the 200 books before the sweep runs (Amendment 28).

### 10. Blind procedure (section 8; BOM-32)

The narrator scheme's whole chunks (121 of 2,000 words, 47 of 5,000) are sealed with decoys at one
per four chunks, half from candidates' held-out tails and half from control volumes no model
trained on; Joseph Smith contributes none (Amendment 32). Opaque ids, the key written outside the
repository, hashes of key and sealed set committed. The analysis is run by a new AI session given
only the scoring script and no access to the key: this is **simulated blinding**, since one person
designed and runs the study. Outputs are hashed and committed before unblinding; decoys must be
identified at benchmark accuracy; leave-one-candidate-out follows. Per-chunk scorers apply each
method exactly as validated (Amendment 33).

### 11. Synthesis (6.7; BOM-35)

Per chunk and method family, the observation is the top-ranked candidate and its 6.1 band; its
likelihood under each hypothesis uses the family's benchmark accuracy and band rates
(Amendment 34). Families are weighted by benchmark accuracy times the imitation weight of
section 9. Prior 0.5 on "author not in set", the rest shared among candidates with reliable
samples; sensitivity over the prior from 0.2 to 0.8, dropping each family, equal weights. One
posterior per model size (Amendment 37). Dating, the sweep, access and manuscript evidence are
reported beside the posterior, not multiplied into it.

### 12. Imitation robustness (section 9; BOM-31)

Three authors who wrote both imitation-scripture and ordinary prose (Snowden, Dodsley, Kenrick);
forward test: 18 imitation windows against 13 candidates (the three plus 10 seeded distractors)
with references from ordinary prose; the forward accuracy sets each method's weight (full at
80% or above, half at 60-80%, none below); the reverse test is reported (Amendment 31).

### 13. Manuscript evidence (BOM-34)

Corrections in the Joseph Smith Papers transcripts of the original and printer's manuscripts are
typed from the transcripts' markup (strike-outs, insertions, new-hand notes): listed homophones
primary, a sound-match code beside (Amendment 35). Dictated original and copied printer's
manuscript are compared with the scribe held fixed. Word pairs stay private; ids, pages, hands,
types and counts are public (`data/manuscript/`).

### 14. Access evidence (BOM-33)

Each candidate source is scored 0-3 for documented availability before mid-1829 (3, within Joseph
Smith's documented reach; 2, in western or central New York; 1, in print in the United States
only; 0, no evidence of circulation), every score cited (`data/access/access_table.csv`).


## Appendix B. Detailed tables

These results do not depend on the blind run. The borrowing results (section 1) are the
registered answers to Q2. Sections 2 to 4 are validation; sections 5 and 6 are production and
access evidence reported beside the synthesis. Numbers are read from the files named.

### 1. Borrowing (Q2)

#### 1.1 Exact reuse (BOM-23; `docs/reuse-plan.md`)

With KJV spans masked, 58 passages in 47 earlier-catalogued volumes align with the Book of Mormon,
covering 0.52% of it. Seventeen of the 47 are later texts quoting it under catalog dates decades
too early (Congressional serial-set volumes catalogued 1817, *The Millennial Harbinger*
catalogued 1830); without them the share is 0.16%. The other 30 volumes share short, loose
religious stock phrases (9-46 tokens, identity 0.27-0.67). For comparison, *The Late War* (1816)
shares 8.92% with earlier books and an 1821 sermon collection 2.47%.

#### 1.2 Rare phrases (BOM-24; `data/reuse/bom/rare.json`)

| Source | Rare shared 4-grams | Per 10,000 words | Rank of 204,520 | p (95% interval) |
| --- | --- | --- | --- | --- |
| *The First Book of Napoleon* (1809) | 12 | 5.45 | 63 | 0.0003 (0.0002-0.0031) |
| *The Late War* (1816; 9 printings in the library, 4 distinct texts) | 22 | 3.86 | 131 | 0.0006 (0.0004-0.0017) |
| *View of the Hebrews* (1825) | 2 | 0.37 | 9,496 | 0.046 (0.017-1.0) |
| Spalding, *Manuscript Story* | 1 | 0.24 | - | 0.068 |
| Luke (KJV), against the masked text | 0 | 0 | - | 1.0 |

*The Late War* and *Napoleon* are significant by the registered rule. Within the curated
pseudo-biblical group (post hoc), the 1829 reprint of Ilive's *Book of Jasher* shares more (7.99
per 10,000 words, 31 phrases); the shared phrases are battle and chronicle formulas. The rule
calls 2,044 volumes significant, mostly short pieces sharing one phrase.

#### 1.3 Paraphrase (BOM-25; `data/semantic/named.json`, `named_null.json`)

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

#### 1.4 Story order (BOM-25; `data/semantic/skeleton/`)

No source shares the Book of Mormon's order of events at the registered level (order p at most
0.01). Among the 20 leading search sources the longest shared run is 9 of its 1,421 events
(Josephus, order p 0.24); the positive control, Josephus against Genesis-Judges, shares 108 events
in order (p 0.001). Named sources: *View of the Hebrews* 1823, 3 events, order p 0.97, rank 17 of
49; 1825, 2 events, p 1.0, rank 43 of 49; Spalding, 4 events, p 0.67; *The Late War*, 2 events,
p 1.0; *Napoleon*, 3 events, p 1.0.

#### 1.5 Known-answer controls (Amendment 9)

Exact reuse (U 4 of 27, p 0.964), rare phrases (U 6/27, p 0.927) and paraphrase (U 14/27, p 0.50)
do not separate genuine translations of ancient texts from compositions presented as ancient, and
the King James italics test is not shown to work (`docs/italics-plan.md`). None of the borrowing
tests therefore bears on the translation question; each describes which period books share the
Book of Mormon's wording, ideas or plot.

#### 1.6 Triage (BOM-26; `data/semantic/triage.json`, `docs/triage-plan.md`)

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

### 2. Benchmark (section 7; `data/benchmark/open_set.json`, `prior_work.json`)

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

### 3. Dating validation (Q3; `data/dating/validation.json`)

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

### 4. Imitation robustness, classical methods (BOM-31; `data/benchmark/imitation.json`)

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

### 5. Production evidence (BOM-34; `data/manuscript/summary.json`, `docs/manuscript-evidence.md`)

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

### 6. Access evidence (BOM-33; `data/access/access_table.csv`, `docs/access-evidence.md`)

Of 33 texts scored: 15 at 3 (documented within Joseph Smith's reach; all but one are editions of
Josephus, in the Manchester library's accessions and in Palmyra bookstore advertisements including
January-May 1829), 2 at 2, 10 at 1, 6 at 0. Named sources: *View of the Hebrews* 1825 edition 2
(advertised in Utica, 1826), 1823 edition 1; *The Late War* 1 (Palmyra "Historical Reader"
advertisements of 1827-1830 do not name the author); *The First Book of Napoleon* 0; Spalding's
manuscript 0. Availability is not use.


## Appendix C. References

- Brodie, Fawn M. *No Man Knows My History*. 1945.
- Holmes, David I. "A Stylometric Analysis of Mormon Scripture and Related Texts." *Journal of the
  Royal Statistical Society A* 155(1) (1992): 91-120. https://doi.org/10.2307/2982671
- Howe, Eber D. *Mormonism Unvailed*. 1834.
- Jockers, Matthew L., Daniela M. Witten and Craig S. Criddle. "Reassessing Authorship of the Book
  of Mormon Using Delta and Nearest Shrunken Centroid Classification." *Literary and Linguistic
  Computing* 23(4) (2008): 465-491. https://doi.org/10.1093/llc/fqn040
- Johnson, Chris, and Duane Johnson. Rare four-word phrase search over about 110,000 pre-1830
  books. 2013.
- Larsen, Wayne A., Alvin C. Rencher and Tim Layton. "Who Wrote the Book of Mormon? An Analysis of
  Wordprints." *BYU Studies* 20(3) (1980): 225-251.
- Runnells, Jeremy. *Letter to a CES Director*. 2013. https://read.cesletter.org/bom/
- Schaalje, G. Bruce, Paul J. Fields, Matthew Roper and Gregory L. Snow. "Extended Nearest Shrunken
  Centroid Classification: A New Method for Open-Set Authorship Attribution of Texts of Varying
  Sizes." *Literary and Linguistic Computing* 26(1) (2011): 71-88.
  https://doi.org/10.1093/llc/fqq029
- Shalev, Eran. *American Zion: The Old Testament as a Political Text from the Revolution to the
  Civil War*. Yale University Press, 2013.
- Skousen, Royal, and Stanford Carmack. *The Book of Mormon Critical Text Project*, volume 3; *A
  Plain Exposition of Book of Mormon English*. 2018-2025.
- Spencer, Stan. "Missing Words: King James Bible Italics, the Translation of the Book of Mormon,
  and Joseph Smith as an Unlearned Reader." *Interpreter* 38 (2020): 45-106.
- The Church of Jesus Christ of Latter-day Saints. Gospel Topics Essays ("Book of Mormon
  Translation"; "Book of Mormon and DNA Studies"). 2013-2015.
- Wright, David P. "Joseph Smith's Interpretation of Isaiah in the Book of Mormon." *Dialogue*
  31(4) (1998).
- Grunder, Rick. *Mormon Parallels*. 2014 (PDF edition; purchased, not
  redistributed).
- The Joseph Smith Papers (https://www.josephsmithpapers.org/): the original and printer's
  manuscripts, Revelation Book 1 and the documents listed in `data/candidates/sources.json` and
  `data/js_time/sources.json`.

Sources for the period corpus (Harvard Institutional Books 1.0, HathiTrust, the Internet Archive,
Chronicling America, EEBO-TCP) are listed with their terms in `docs/replication.md`.
