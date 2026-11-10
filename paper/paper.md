# Authorship, borrowing and dating of the earliest Book of Mormon text: an open, pre-registered computational study

*Draft, 2026-11-10. Dave Taylor, with analysis by an AI model (Claude). Every review step is
simulated by an AI model and labelled so; the blinding was simulated (the scoring ran without the
key; the analyst is an AI model). Repository: https://github.com/lifehug/book-of-mormon-authorship;
pre-registration: https://osf.io/6ugxc/ (frozen 2026-10-15; 45 dated amendments, the post hoc ones
labelled).*

## Abstract

We ask three questions of the 1830 Book of Mormon text: whose writing it most resembles (Q1), what
it borrowed from earlier books (Q2), and when its English dates from (Q3). The study takes no
position on the book's origin or on inspiration; it reports which known writers or books, if any,
the text closely resembles, with each method's error rate measured on known answers.

The test is larger than any before it. We catalogued 695,021 items from five sources (633,706
from the period's books and newspapers, 61,315 early modern texts for dating), including Harvard's Institutional Books (released 2025, new to this question), and trained
GPT-style language models on that period alone (125M, 297M and 590M parameters; 202,816 volumes,
25.7 billion tokens), so that "ordinary" means ordinary for 1830. Every King James span was masked,
every threshold was fixed in a public pre-registration, and the text was scored once, blind, mixed
with 43 decoys. All models are public.

We separate two questions that earlier studies merged. **Ranking** ("whose sample is closest?")
works well: on held-out known-author tests the candidate models put the true author first 94-99%
of the time. **Matching** ("is it confidently this person?") does not yet work: the same models
also say "match" to a wrong author on 22-47% of tests, falling with model size, against a
registered bar of 5%. Prior methods rerun on the same tests do worse (78-92%).

Results. No candidate (Joseph Smith, Oliver Cowdery, Sidney Rigdon, Solomon Spalding, Ethan Smith,
Gilbert J. Hunt, Parley P. Pratt, W. W. Phelps) is matched under the
registered rule: 3-10 of 168 chunks reach "match" in the registered run and 0-2 once Book of Mormon
quotations are removed from the candidate samples, fewer than the false-match rates predict for
text by no candidate. Where the methods must rank, they rank Joseph Smith's 1828-29
revelations closest, also when every candidate model is trained on the same amount of text (at
125M and 297M; at 590M a slice of *The Late War* competes); that
sample is the only one in the text's own scriptural register, and his ordinary prose of 1831-33
sits mid-pack. No proposed source shares a copied passage, a plot sequence or a passage judged
specific; *The Late War* and *The First Book of Napoleon* pass the registered rare-phrase rule, as
the pseudo-biblical genre generally does. The text's grammar dates mostly before 1700 (median
1661) and is more archaic than period imitations of biblical style (p 0.0001). Seventeen public
claims were judged by rules written before any result: 2 supported, 6 contradicted, 4 mixed, 1
not addressed, 4 untestable. Code, data tables, every trained model and every decision are public
and rerunnable.

## 1. Introduction

The Book of Mormon was published in 1830. Its origin has been argued for two centuries, and
computational studies have reached opposite conclusions: wordprint studies found its narrators
distinct from each other and from nineteenth-century candidates (Larsen, Rencher and Layton
1980); nearest-shrunken-centroid classification pointed to Sidney Rigdon and Solomon Spalding
(Jockers, Witten and Criddle 2008); a reanalysis allowing "none of these" sent most chapters to an
unobserved author (Schaalje, Fields, Roper and Snow 2011); a rare-phrase study singled out *The Late
War* (Johnson and Johnson 2013). Each was criticised more for its setup than for its arithmetic:
closed candidate lists that force a pick, features that measure biblical register rather than
authorship, choices made after seeing the data, and comparison libraries too small to say what is
unusual.

This study is designed against those failures:

1. **Scale.** The comparison library is the surviving printed English of 1780-1830 (section 2), not
   a hand-picked set, and the language models are trained on that period only.
2. **Ranking and matching measured separately.** Every method may answer "none of these", and its
   rate of false matches is measured on known-answer tasks before it is used (section 4).
3. **King James masking.** Every span aligned to the King James Bible (6.8% of the text) is
   removed before attribution and dating.
4. **Pre-registration.** Thresholds, features, seeds and model choices were fixed publicly before
   scoring; every later change is a dated amendment, and those made after seeing results are
   labelled post hoc (section 7).
5. **No leakage, one blind run.** The text was kept out of every model's training and calibration
   until a single blind run (a gap in this rule, found after unblinding, is reported and corrected
   in section 7).
6. **A whole-library sweep** of every author in the period corpus, not only named suspects.

What stylometry can see is the English on the page and whoever produced it; it cannot see how that
English came to be, and in particular cannot separate a composer from a dictator or a translator.
The study therefore makes no claim about translation, inspiration or the truth of the book's
contents.

**How the paper is ordered.** Section 2 describes the scale of the test and how the text and
library were prepared; section 3 reruns the five earlier studies; section 4 measures every method
on known answers, including how large the models should be; section 5 gives each test on the Book
of Mormon with its preparation first; section 6 takes the books named in the CES Letter one by
one; section 7 lists what was corrected along the way; section 8 judges seventeen public claims;
section 9 says what held; section 10 takes the candidates one by one; sections 11-13 give the
limitations, what is public, and what comes next. The detailed methods are in Appendix A.


## 2. The scale and preparation of the test

### 2.0 At a glance

| | Larsen et al. 1980 | Holmes 1992 | Jockers et al. 2008 | Schaalje et al. 2011 | Johnson and Johnson 2013 | This study |
| --- | --- | --- | --- | --- | --- | --- |
| Question | do the narrators differ; does a candidate fit | do the prophets differ | which candidate | which candidate, or none | which books share rare phrases | who, what was borrowed, when |
| Comparison library | candidate samples | candidate and biblical samples | candidate samples | candidate samples | about 100,000 books (unpublished) | 202,816 period volumes for the models; 204,520 for rare phrases; 163 million passages for paraphrase |
| "None of these" allowed | no | no attribution made | no (closed set) | yes | n/a | yes, every method |
| Error rate on known answers | no | no | cross-validated among candidates | partly | no | ranking and false-match rate per method, 110 held-out tests |
| King James text removed | no | no | no | no | no | yes, 6.8% of the text |
| Pre-registered, blind | no | no | no | no | no | yes; blinding simulated |
| Models and data public | no | no | data deposited | no | no | yes, all models and derived tables |

### 2.1 Gathering

The catalog holds 695,021 items from five sources: for the period, the Internet Archive
(307,567), HathiTrust (135,035), Harvard Institutional Books 1.0 (31,958 volumes; released 2025 and
used here for the first time on this question) and Chronicling America (159,146 newspaper pages);
and, for dating, 61,315 early modern English texts (1473-1700, EEBO-TCP). The national newspaper
set holds almost nothing from western New York (47 New York pages); the *Wayne Sentinel* (Palmyra,
1,429 pages 1823-30) and *Lake Light* were added from the New York State Historic Newspapers, and
the *Ontario Phoenix*, which W. W. Phelps edited before 1830, is not digitized anywhere. About 1.1 TB on
disk. Harvard's and HathiTrust's texts and the Joseph Smith Papers transcripts are licensed and
are not redistributed; derived tables, checksums and the steps to obtain each are
(`docs/replication.md`).

### 2.2 Cleaning

**Dates.** Catalog dates were audited against each volume's own text: of 366,580 volumes scanned,
23,859 name a later year and 19,463 were moved past 1830 (BOM-64, Amendment 12); a model-read check
of 100 flagged volumes found 81 truly later, so the correction errs toward exclusion, and moved
volumes are kept in a separate column. Another 11,494 volumes carried a placeholder date of 1800;
1,502 of them were printed after 1830. This mattered directly: 17 "pre-1830" volumes, among them
Congressional serial-set volumes catalogued 1817 and an "1830" *Millennial Harbinger*, quote the
Book of Mormon, and without the audit they would have looked like sources.

**Duplicates.** Reprints and copies were grouped by MinHash similarity (5-gram shingles, threshold
0.8; 19,920 groups) and by title, author and year across sources (4,697 groups; Amendment 6).
Nothing is deleted; duplicates are flagged (`data/catalog/DEDUP.md`). The text method cannot see the
same book OCR'd twice by different sources (median similarity 0.12-0.18 on 300 such pairs), which
is why the metadata pass exists; copies within one source with different metadata can still escape.

**OCR.** Measured against 1,883 hand-keyed twins, the median character error rate is 0.083 after
cleaning, and 38% of volumes remain above 0.10; above that cut are 2.5% of Harvard's volumes,
11.9% of HathiTrust's, 24.9% of the Internet Archive's and 27.8% of the newspaper pages (BOM-14).
At about 80% word accuracy a 4-gram survives OCR about 41% of the time, so the wording searches
miss more than half of any real shared phrasing in poor scans (an unmeasured share of false
negatives). Language-model OCR correction was tried and rejected because it invented text.

### 2.3 Labelling

Every item carries a genre label from a local language model (sermon, history, fiction, scripture
imitation and so on), used to build genre-matched comparison groups and nulls
(`data/catalog/genre.parquet`; about 40 hours of local model time). A 300-record validation sample
is drawn; its hand adjudication is deferred until a perturbation test shows the labels matter
(BOM-53).

### 2.4 Sealing and masking

The Book of Mormon was excluded from every model's training, tuning, threshold and feature
selection until the blind run, except the replications of section 3. Catalogued copies were sealed
by title, and any volume holding 20 or more of the text's original 12-token strings was removed
from training (in practice later texts quoting it under early catalog dates).

Every span of the text aligned to the King James Bible was masked (18,336 of 268,811 words, 6.8%;
2 Nephi 32.7%, 3 Nephi 15.0%). On planted quotations the mask finds 78% of King James words with
95% precision, so some King James wording remains in the "original" text;
the same masking was applied to candidates (3.7%) and to 1.55 billion words of controls (1.8%).
The mask uses the 1769 King James text; the Smith family's 1828 Phinney Bible is consistent with
it (66.9% of verses found word for word even in its noisy OCR).
Attribution and dating read only the remaining text. Candidate samples were later found to contain
Book of Mormon quotations; Amendment 43 removed passages of 20 or more words copied after the
matching passage existed (section 7).

### 2.5 Segmentation

The text is cut by internal narrator (Nephi, Jacob, Mormon, Moroni and others), dictation order and
scribe, into 2,000- and 5,000-word chunks (756 in all). The 5,000-word chunks were split into a
discovery and a confirmation half by a seeded draw stratified by narrator (22 and 25 chunks). The
blind run scored the narrator scheme's 168 whole chunks.

### 2.6 Candidate samples

Eight candidates, each sample tagged by provenance tier (handwritten, dictated, printed by the
author, posthumous; Amendment 5) and by date. Masked word counts: Ethan Smith 277,391; Gilbert J.
Hunt 56,956; Solomon Spalding 41,833; Joseph Smith dictated before 1830 2,720 (his 1828-29
revelations; 2,844 words before King James masking, 3,039 model tokens), dictated after 1830 5,039, handwritten after 1830 6,363; Oliver Cowdery handwritten
before 1830 1,310 (after Amendment 43, 844 tokens), printed after 1830 44,338; Parley P. Pratt
91,478; Sidney Rigdon 21,516; W. W. Phelps 28,479. Samples under 10,000 words carry an
"unreliable sample" flag fixed before scoring: a power analysis on known authors put the minimum
reference sample at about 10,000 masked words (BOM-43). A registered check of whether later writing
can stand in for earlier (30 period authors with a gap of seven or more years) passed for no method
(37-60% against an 80% gate; BOM-48), so no candidate's post-1830 writing may stand in for his
pre-1830 style. Samples written after 1830 come from people who had
read the book and form a secondary set. Joseph Smith's documents come from the Joseph Smith Papers
manuscripts (copyrighted transcripts, held privately; steps to obtain them are published).

### 2.7 Controls and the benchmark

Four control groups stand for writers who are not candidates: pseudo-biblical texts (a published
curation, 1774-1827), 1820s sermons and tracts, histories including Native American origin texts,
and general prose. Each method is first measured on known-author tasks (the Federalist papers,
imitation scripture with known authors, dictated text) with the true author present and removed
(section 4).

### 2.8 The time-locked language models

GPT-style models trained from scratch on 1780-1830 English only, with the Book of Mormon and
post-1830 text excluded: 202,816 volumes, 25.7 billion tokens, one pass over the data. Why each size:

| Size | Why it was trained | Outcome |
| --- | --- | --- |
| 125M | pilot: cheap, to test the whole pipeline end to end | validation loss 2.515 |
| 297M | the registered model, the largest the original budget allowed | 2.325 |
| 1B | to test whether size helps (Amendment 26) | abandoned after a loss spike at step ~15,800 (Amendment 38) |
| 590M | the 1B's replacement with QK-norm, the standard fix for that instability (Amendment 39) | 2.192 |

Every model-based test runs at every size and is reported side by side, with none treated as the
headline (Amendment 37). The models are public on Hugging Face (`etherfuse/timelocked-1830-*`),
with every fine-tuned candidate, benchmark, style-encoder and dating model
(`etherfuse/bom-authorship-*`).


## 3. Prior work, replicated

Before any of our own methods touched the Book of Mormon, each earlier study's published method was
run on our texts (the one exception to the seal; `paper/replication-report.md`, designs fixed in
`docs/prior-studies.md`). Nothing here feeds a calibration or a threshold.

| Study | Published | Replication | Reproduces? |
| --- | --- | --- | --- |
| Larsen, Rencher and Layton 1980 | the speakers differ; no block resembles a candidate | 17 speakers differ (p 8e-38); 4 of 215 blocks classified to a candidate | yes, both findings |
| Holmes 1992 | Joseph Smith's own writing separates; the prophets do not cluster by prophet; revelations sit with the prophets | Joseph Smith 3 of 3 alone; prophets mixed; the 1835 revelations 3 of 3 with the prophets | yes |
| Jockers, Witten and Criddle 2008 | Rigdon first or second for 197 of 239 chapters | on their deposited data, the same method and error (8.8%), Rigdon 169; on our candidate texts, Pratt 193, Rigdon 29 | **method yes, result no** |
| Schaalje, Fields, Roper and Snow 2011 | 175 of 239 chapters to an unobserved author | 225 of 239 to an unobserved author | yes, but the answer moves with sample length and kind |
| Johnson and Johnson 2013 | *The Late War* has the densest shared rare phrasing after *The First Book of Napoleon* | *The Late War* in the top 0.05% (p 0.0004), but 30 books of 10,000+ words are denser, mostly other imitation scripture | **partly** |

**What this shows.** The earlier studies agree where the question is whether texts *differ*
(narrators differ in function words; Joseph Smith's own writing differs from the prophets'). They
disagree where the question is *who wrote it*, and the reason is the candidate texts: a method
that must name someone names whoever's samples sit nearest, so Jockers et al.'s Rigdon (mostly
from 1864) becomes Pratt when other genuine texts stand for each man. The open-set answer
("none") returns but moves with sample choices. The rare-phrase signal is real but shared by a
genre. Three limits recur: forced choice, register mistaken for style, and answers that follow the
texts chosen. The rest of the design answers those three.


## 4. Measuring every method on known answers

Every method answers two different questions, and they are measured separately:

- **Ranking:** "whose sample is closest?" With the true author among the candidates, how often is
  the true author ranked first (closed-set accuracy)?
- **Matching:** "is it confidently this person?" With the true author removed, how often does the
  method still say "match" to someone (the false-match rate)? The registered bar is 5%.

A method can be excellent at the first and poor at the second. Section 6.1 of the pre-registration
calls a match only on the second.

### 4.1 The benchmark (110 held-out tests; `data/benchmark/open_set.json`)

The candidate models (one copy of a time-locked model fine-tuned per author, scored by how much
better it predicts a text than the base model) were tested on held-out text of known authors:
Federalist papers, imitation scripture with known authors, and dictated text.

| Method | Size | Ranking (true author first) | False matches | Passes (>= 0.90 and <= 0.05) |
| --- | --- | --- | --- | --- |
| Candidate models (primary) | 125M | 0.936 | 0.473 | no |
| Candidate models (primary) | 297M | **0.991** | 0.382 | no |
| Candidate models (primary) | 590M | 0.982 | **0.218** | no |
| Burrows' Delta, same held-out tests | - | 0.955 | (no match score) | no |
| Cosine Delta, same tests | - | 0.818 | (no match score) | no |
| General Imposters, same tests | - | 0.745 | 0.827 | no |
| ENSC (Schaalje et al.), same tests | - | 0.964 | 0.782 | no |
| GPT-2 (modern training), primary method | 124M / 355M | 0.900 / 0.945 | 0.918 / 0.855 | no |
| V1 (learning rate 1e-4, registered) | 125M / 297M / 590M | 0.936 / 0.936 / 0.627 | 0.455 / 0.473 / 0.818 | no |
| V2 (classifier head, registered seed) | 125M / 297M / 590M | 0.900 / 0.909 / 0.764 | 0.282 / 0.136 / 0.391 | no |
| V2, five further seeds (range) | 125M / 297M / 590M | 0.66-0.93 / 0.51-0.76 / 0.40-0.78 | 0.09-0.93 / 0.53-0.98 / 0.32-0.93 | no |
| V3 (hidden states into classical trials) | 125M / 297M / 590M | 0.839 / 0.844 / 0.844 | 0.689 / 0.717 / 0.706 | no |

The classical methods and style encoders were also scored on the 180 classical trials (General
Imposters 0.833 / 0.617; ENSC 1.000 / 0.661; style encoder 0.839 / 0.500), compared within that
set, not across.

On the same 110 tests the 297M model ranks better than General Imposters (27 tests to 0) and
Cosine Delta (19 to 0), but not significantly better than Burrows' Delta (4 to 0, p 0.13) or ENSC
(paired exact McNemar tests): the language models' gain is mainly in matching, not in ranking.

**Benchmark accuracy overstates accuracy on a wider field.** On 30 fresh period authors, every
classical method falls to about 55-60% (Burrows' Delta 57.0%, Cosine 60.3%, General Imposters
56.5%, ENSC 54-55%), and none of three attempted repairs helped (BOM-58, BOM-60). Our General
Imposters reproduces the published method's results on its own benchmark (11 of 12 rows within 4
points), so its failure is the method's, not an implementation slip; our first ENSC was not the
published method and was replaced. The classical verdicts are stable across 54 alternative
settings, except General Imposters' (BOM-40).

**Three findings.**

1. **Period training matters for matching.** The same method with GPT-2, trained on modern text,
   ranks nearly as well but says "match" to the wrong author 86-92% of the time; the period models
   do so 22-47%.
2. **False matches fall with size** (47%, 38%, 22%) while ranking was already at its ceiling.
3. **Some variants are unstable.** V1's registered learning rate broke the 590M (its fine-tuned
   models raised the loss on new text); at a rate chosen on held-out training text it equals the
   primary method (Amendment 41, post hoc). V2's single registered numbers were one lucky seed:
   five more seeds range from 9% to 98% false matches (Amendment 42), so V2 carries no weight.

### 4.2 Robustness to deliberate imitation (`data/benchmark/imitation.json`)

Three authors who wrote both imitation scripture and ordinary prose (Snowden, Dodsley, Kenrick):
can a method trained on their ordinary prose recognise their imitation scripture among 13
candidates?

| Method | Imitation text to its real author | Weight in the synthesis |
| --- | --- | --- |
| Burrows' / Cosine Delta | 13 of 18 each (0.72) | half |
| General Imposters | 11 of 18 (0.61) | half |
| ENSC | 7 of 18 (0.39) | none |
| Style encoders 297M / 590M | 7 / 10 of 18 | none |
| Candidate models 125M / 297M / 590M | 5 / 7 / 6 of 17 | none |

Writing in a biblical register hides the author from the model-based methods more than from the
classical ones, and size does not help. This is why the registered synthesis rests on the
classical family alone (section 5.4).

### 4.3 Which method is best at what

Judged on known answers only, never on the Book of Mormon:

| Task | Best | Its figure | Next |
| --- | --- | --- | --- |
| Ranking the true author first | candidate models, 297M | 99.1% | 590M 98.2% |
| Fewest false matches | candidate models, 590M | 21.8% | 297M 38.2% |
| Recognising candidates' own held-out text in the blind run (decoys called "match") | candidate models, 125M | 20 of 22 (91%), at 47% false matches | 297M 15 of 22, 590M 11 of 22 |
| Seeing through deliberate imitation | Burrows' and Cosine Delta | 72% | General Imposters 61% |
| Reproducible across machines and seeds | candidate models (primary), classical methods | identical reruns | V2 unstable |

No method passes the registered bar, so every attribution in this paper is graded evidence: a
ranking can say who is closest; no method can yet say "not this person" with a known error below
5%.

### 4.4 How big should the model be?

**Why size matters.** From 125M to 297M to 590M parameters, false matches fell from 47% to 38% to
22%; ranking was already 94-99%. Matching is the weak half, and size is the one lever that has
moved it.

**What limits size is the data.** The training text is 25.7 billion tokens of 1780-1830 English,
close to all that survives digitally. A common rule of thumb from modern large-model research is
about 20 training tokens per parameter for the best use of a fixed compute budget (a guideline,
not a law). By it the best fit for this data is about 1.3B parameters. The 590M had 43 tokens per
parameter, the 297M 86, the 125M 205. Beyond about 1.3B the text must be repeated; up to about four
passes still helps a little, so 2-4B is the practical outer limit, with sharply diminishing
returns.

**Ways to more data, and their costs.** The period's newspapers (catalogued, not yet used for
training); Google-digitized volumes not in the public sets (BOM-71); or a wider window (for example
1700-1830), which weakens the time lock that makes "ordinary" mean ordinary for 1830. With the
Google volumes the period text would be about 32-33 billion tokens, a best fit near 1.6B.

**When to stop.** Grow only while the last step cut false matches meaningfully and the data
supports the next size at about 20 tokens per parameter or more; stop when gains flatten or the
data would have to repeat. By that rule a model of about 1.3B with QK-norm is justified and is the
logical last step on the present data; beyond about 2B is not. Whether any size reaches 5% false
matches is unknown: a straight extension of the trend would reach it only around 1.6-2B, and
trends of this kind usually flatten. Section 13 gives the staged plan.


## 5. The tests on the Book of Mormon

Each test is preceded by how it was prepared. The registered run is the main record (git tag
`blind-registered-2026-11-10`); where a later correction changes a number, both are shown
(section 7).

### 5.1 The blind procedure and its decoys

**Preparation.** The 168 whole chunks of the narrator scheme (121 of 2,000 words, 47 of 5,000) were
sealed with 43 decoys: 22 held-out passages by the candidates themselves and 21 control passages
by nobody in the set, which no model trained on. Ids were opaque, the key was written outside the
repository, and hashes of key and sealed set were committed before scoring. The scoring was run by
a new AI session given only the scoring script, without the key: this is **simulated blinding**,
since one person designed and runs the study. Outputs were hashed and committed before unblinding
on 2026-11-10.

**The sanity check.**

| Method | Candidate decoys: right candidate first (of 22) | Control decoys called a match (of 21) | Candidate decoys called a match to their author (of 22) |
| --- | --- | --- | --- |
| Burrows' / Cosine Delta | 20 / 15 | (no match call) | |
| General Imposters | 19 | 0 | 0 (cannot reach "match" at its registered threshold) |
| Style encoders 297M / 590M | 16 / 18 | 0 | 0 |
| Candidate models 125M / 297M / 590M | 20 / 21 / 19 | **0 at every size** | 20 / 14 / 11 |

Every method found real candidate text most of the time, and no method called a stranger's text
a match. The run is valid by section 8's rule. Two methods did worse on the decoys than on the
benchmark (Cosine Delta 15 of 22, the 297M style encoder 16 of 22): accuracy measured on the
benchmark does not fully carry over to new text.

### 5.2 Wording

**Preparation.** Four searches, each against the period library with the text's King James spans
labelled: exact reuse (passim alignment against every volume printed before it); rare phrases
(4-grams found in at most 5 period texts, scored per 10,000 words against 204,520 volumes); paraphrase
(163 million 128-word passages embedded and searched, each source compared with 500 genre- and
length-matched volumes); and triage of every surfaced pair as biblical, common or specific by one
model with a blind second pass by another (simulated review).

**Results.**

- **Exact reuse.** 58 short passages in 47 earlier-catalogued volumes, 0.52% of the text; 17 of the
  volumes are later texts quoting it under wrong early dates, and without them 0.16% remains, all
  loose stock phrasing (9-46 tokens). For comparison, *The Late War* shares 8.92% with earlier
  books.
- **Rare phrases.** *The First Book of Napoleon* (rank 63 of 204,520, p 0.0003) and *The Late War*
  (rank 131, p 0.0006) pass the registered rule; *View of the Hebrews* (rank 9,496) and Spalding do
  not. The 1829 reprint of Ilive's *Book of Jasher*, another imitation scripture, shares more than
  either; the shared phrases are battle and chronicle formulas, and 2,044 volumes pass the rule.
- **Paraphrase.** No named source stands out from its genre: *View of the Hebrews* leads the
  Indian-origins group but 77 of 500 matched religious volumes score higher. In the whole-library
  search editions of Josephus take 14 of the top 20 places, and the registered rule flags 622
  sources, which mostly measures biblical register.
- **Proposed parallels (exploratory).** Of the 500 parallels proposed in Rick Grunder's *Mormon
  Parallels*, 139 are in the catalog; their sources score slightly closer than matched volumes
  (median percentile 91.0 against 87.4, p 0.087), as expected from how they were chosen, and only
  Josephus stands out. Josephus, the leading paraphrase source, was on sale in Palmyra and nearby
  from 1822 and in E. B. Grandin's own stock from late 1828 into spring 1829 (Appendix B).
- **Triage.** Of 1,069 surfaced pairs, 382 are King James wording, 685 period stock phrasing, and 2
  were called specific on the first pass; the second pass called both common. **No pair is
  specific under both passes** (agreement 0.74, kappa 0.51).

**Known-answer check.** None of these searches separates genuine translations of ancient texts from
compositions presented as ancient (Amendment 9; exact reuse p 0.96, rare phrases 0.93, paraphrase
0.50). They describe which period books share the text's wording; they cannot speak to the
translation question.

### 5.3 Story structure

**Preparation.** Each 2,000-word block of the text, and of each source, was reduced by a hosted
model to at most 12 role-named events (checked on 20 King James chapters read twice: median
agreement 0.92), giving 1,421 events for the Book of Mormon. Sequences were aligned
(Smith-Waterman) and each alignment tested against 1,000 shuffles of the source's order.

**Positive control.** Josephus retelling Genesis-Judges shares 108 events in order with the Bible
(p 0.001): the test finds a retold story when there is one.

**Results.** One book meets the registered level (order p at most 0.01): Benjamin Church's *History
of Philip's War*, first of 49 in its group, p 0.008. The shared run is six events from one stretch of
each book (Alma 60-61: a commander writes angrily to the governor, the governor replies that rebels
have driven him out, the commander marches to help; in Church, a governor sends a captain with a
letter to raise troops): the common shape of military correspondence, not a shared episode. With 49
books tested, one such p-value arises by chance about 4 times in 10, so it is reported as it came
out and read as chance. Among the 20 leading sources of the paraphrase search the longest shared run
is 9 events (Josephus, p 0.24). Named sources: *View of the Hebrews* 1823, 3 events (p 0.97) and 1825, 2 (p
1.0); Spalding, 4 (p 0.67); *The Late War*, 2 (p 1.0); *Napoleon*, 3 (p 1.0).

### 5.4 Authorship

**Preparation.** Every method in section 4 scored every chunk against every candidate sample:
the classical methods (Burrows' and Cosine Delta, General Imposters), the style encoders (297M and
590M), and the candidate models (125M, 297M, 590M). Each method's "match" threshold was fixed on
the benchmark before the run.

**Matches.** Under the registered rule, General Imposters and the style encoders call no chunk a
match; the candidate models call 10, 5 and 3 of 168 (125M, 297M, 590M), and 2, 2 and 0 after Book of
Mormon quotations were removed from the candidate samples (Amendment 43). These counts are below
what the models' false-match rates would give for text by no candidate. **No candidate is matched
by two independent families on both halves (H1a not supported).**

**Ranking.** After Amendment 43, every method ranks a Joseph Smith sample first at least as often
as any other candidate: Cosine Delta 148 of 168 chunks, Burrows' Delta 91, General Imposters 66 (tied
with Pratt), style encoders 151 and 99, candidate models 159, 168 and 131. In seven of eight
methods it is his 1828-29 revelations; Burrows' Delta prefers his later ordinary prose (section
10.1). The full table per candidate, method and size is in section 10 and
`data/blind/a43/per_candidate.json`.

**The synthesis (6.7).** The registered Bayesian synthesis weights each family by its benchmark
accuracy times its imitation weight. Both model-based families earned zero imitation weight
(section 4.2), so only General Imposters enters, and the posterior is the same at every size. It
covers only the three candidates with pre-1830 samples of at least 10,000 words: "not in set" 0.744
(prior 0.5), Hunt 0.089, Spalding 0.085, Ethan Smith 0.082; across priors 0.2-0.8, 0.42-0.92.
A placebo run after unblinding showed the synthesis leans to "not in set" even on these
candidates' own held-out passages (Ethan Smith 0.59, Hunt 0.56, Spalding 0.51; controls 0.63), so
**0.744 carries little information**: General Imposters cannot say "match" at its registered
threshold, and the synthesis inherits that (section 7). Joseph Smith and Cowdery are outside it,
untested by it rather than ruled out.

**The whole-library sweep (descriptive).** 23,872 period authors were compared with the text. The
sweep failed its own usability test (true author first for 27-35% of 200 held-out books against a
required 70%), so its result is descriptive. No author passed both lead thresholds (0.035
expected by chance); the nearest are writers in the scriptural and prophetic register (John Wroe,
George Fox, William Sewel), none near a threshold.

### 5.5 Dating

**Preparation.** Three models placed each segment on a scale from 1473 to 1830: a grammar model on
61 grammatical features from the early modern English literature (decides H3), a lexical model on
word frequencies with grammar words removed, and a transformer cross-check on the 297M model's
hidden states. Validated on held-out authors: mean errors 23, 13 and 10 years. King James imitation
moves the grammar model about 53 years early and the transformer not at all.

**Results.** The grammar model places 78% of the 215 segments' median years before 1700 and 7% in
1780-1830 (median 1661): **H3b**. The lexical model (median 1736) and transformer (1755) place the
majority in neither window. **H3c is rejected:** the text dates earlier than the 25 pseudo-biblical
control volumes of 1780-1830 (grammar 1661 vs 1734; lexical 1738 vs 1794; p 0.0001), and with each
book of the text as one unit (12 books) the result stands (p 0.0025 and 0.0001). Part of the early
date is the biblical register, but the text is more archaic than the period's other biblical
imitations, and the transformer, which imitation did not move, still dates it before them (1755
vs 1805). Seven of the 25 period imitations are themselves placed in the
early modern window by the grammar model, so the genre can reach it. Three cautions: an
early-modern placement is predicted by an early-modern source, by imitation of one, and by the King
James register alike; the models learned 1780-1830 English from edited print, so unedited New York
and New England vernacular may read to them as archaic; and hand-keyed text reaches the period
window less often than OCR text of the same years (55% against 83% of 1780-1809 segments), and the
Book of Mormon text is keyed, which alone could pull its dates earlier.

### 5.6 Internal voices

**Preparation.** The same classical classifier that separates real authors at 0.96 on the benchmark
was asked to separate the chunks by narrator, by dictation order, and by scribe.

| Grouping | Accuracy | By chance | p |
| --- | --- | --- | --- |
| Narrator (Nephi, Jacob, Mormon, Moroni; 121 chunks) | 0.744 | 0.277 | 0.001 |
| Dictation order (first or last dictated; 124 chunks) | 0.758 | 0.502 | 0.001 |
| Scribe | not testable: only Oliver Cowdery's hand fills three or more continuous chunks | | |

The narrators differ above chance but well below the level that separates different real
authors: **not separable as different authors**. Raw accuracy is about the same for dictation
order; corrected for chance, narrator separates somewhat better (0.645 against 0.514), so the
differences follow both who narrates and when a passage was dictated. The manuscript evidence (Appendix B) shows the original was taken down by ear:
sound-alike corrections are 6 to 12 times more common in the dictated original than in the copied
printer's manuscript, with the same scribe in both (Fisher p 2e-9; a simulated check of the page photographs confirms the ratio, and the tests
treat corrections on one page as independent, which overstates certainty). That bears on how the words
reached the page, not on whether they were composed, recited or read aloud.


## 6. The books in the CES Letter, one by one

The *Letter to a CES Director* (Jeremy Runnells, 2013; https://read.cesletter.org/bom/) is the
most widely read critical compilation. Its Book of Mormon section names three books as sources or
parallels: *View of the Hebrews*, *The Late War* and *The First Book of Napoleon*
(`docs/ces-letter-books.md`). Spalding's *Manuscript Story*, named by other critics but not by the
Letter, gets the same treatment beside them. Of the Letter's King James arguments, the italics are tested
(section 6.5); which edition's errors the text follows is not (the study masks King James text
rather than asking which printing it follows), and place names are outside its methods.

Every claim was registered with its decision rule before any result (`data/claims/register.yaml`).
Access scores run from 3 (documented within Joseph Smith's reach before mid-1829) to 0 (no
evidence of circulation); availability is not use. The individual books were not dated separately;
section 5.5 dates the pseudo-biblical genre as a group.

### 6.1 *View of the Hebrews* (Ethan Smith, 1823; 2nd edition 1825)

**The claim.** B. H. Roberts' parallels, presented chart by chart: Hebrew origin of the American
Indians, buried records, the scattering and gathering of Israel.

| Test | Result |
| --- | --- |
| Rare phrases | 2 shared (0.37 per 10,000 words), rank 9,496 of 204,520, p 0.046 (interval 0.017-1.0): does not pass |
| Paraphrase | first of 49 in its genre group (29.6), but 77 of 500 matched religious volumes score higher (percentile 84.6 and 94.0 for the two editions): does not stand out |
| Shared passages after triage | none specific |
| Story structure | 1823: 3 events in order, p 0.97; 1825: 2 events, p 1.0 |
| Ethan Smith as author | never matched; mean rank 6-10 among 10-11 candidate samples, last for the candidate models |
| Access | 1825 edition 2 (advertised in Utica, 1826); 1823 edition 1 |
| Verdict (claim c02) | **contradicted**: the shared themes are real but common to the period's writing on Indian origins, and no wording, passage or plot is shared beyond the genre |

### 6.2 *The Late War between the United States and Great Britain* (Gilbert J. Hunt, 1816)

**The claim.** Shared rare phrasing (the Letter dates the book 1819; the first edition is 1816; a
school text).

| Test | Result |
| --- | --- |
| Rare phrases | 22 shared (3.86 per 10,000 words), rank 131 of 204,520, p 0.0006: **passes**; but the 1829 *Book of Jasher* shares more, the phrases are battle and chronicle formulas, and 2,044 volumes pass. Under Johnson and Johnson's own looser rule it shares 183 phrases: 6 occur in no other book, 17 in one to four, 135 in twenty or more. Rarity had to be counted by text, not by volume: nine printings of *The Late War* in the library had made its own phrases look common (counted by volume it shares none; by text, 22; Amendment 8) |
| Paraphrase | rank 6 of 18 in its group, percentile 79.8: does not stand out |
| Shared passages after triage | none specific |
| Story structure | 2 events in order, p 1.0 |
| Hunt as author | never matched; mean rank 3.9-5.5 among 10-11 candidate samples; a 3,039-token slice of *The Late War* outranks Joseph Smith's revelations in 63% of chunks for the 590M at equal dose (section 10.1), a register effect |
| Access | 1 (Palmyra "Historical Reader" advertisements of 1827-1830 do not name the author) |
| Verdict (claim c01) | **mixed**: the rare-phrase signal is real, as Johnson and Johnson found, and it is a genre signal shared with other imitation scripture; no passage or plot is shared |

### 6.3 *The First Book of Napoleon* (1809)

| Test | Result |
| --- | --- |
| Rare phrases | 12 shared (5.45 per 10,000 words), rank 63 of 204,520, p 0.0003: **passes** |
| Paraphrase | rank 3 of 18 in its group (7.9), percentile 98.4, below the null's 99th percentile: does not stand out |
| Shared passages after triage | none specific |
| Story structure | 3 events in order, p 1.0 |
| Access | 0 (no evidence of circulation in the region) |
| Verdict | **mixed**: dense rare phrasing of the same chronicle kind, nothing else |

### 6.4 Beside the Letter: Spalding's *Manuscript Story*

| Test | Result |
| --- | --- |
| Rare phrases | 1 shared (0.24 per 10,000 words), p 0.068: does not pass |
| Paraphrase | rank 12 of 49: does not stand out |
| Shared passages after triage | one first-pass "specific" pair (the elephant-like "Mammoons"), re-labelled common by the second pass |
| Story structure | 4 events in order, p 0.67 |
| Spalding as author | never matched; mean rank 3.7-10.6 among 10-11 candidate samples |
| Access | 0 |
| Verdict | **contradicted** as a source |

## 6.5 The King James italics

**The claim.** The text reproduces King James passages including the words the 1611 translators
printed in italics (supplied words with no Hebrew or Greek behind them), which a translation from
an ancient record would not be expected to carry.

**The test (BOM-62).** In every passage that parallels the King James text, the share of italic
words kept against the share of ordinary words kept. The Smith family's 1828 Bible printed the
italics (88 of 100 checked words). Genuine translations and period sermons that quote the King
James Bible keep italic words almost as often as other words (0.903 and 0.904). The Book of Mormon
keeps 0.645 of italic words (interval 0.576-0.716) against 0.946 of other words: it drops italic
words far more often than other users of the King James text. In Isaiah it drops 37.3%, matching
earlier counts (Spencer 2020, 37%; Wright 1998, about 40%). The registered test's own validation
check failed, so by its rule the result is reported without an interpretation: the measurement
reproduces, but the test cannot say why the italic words differ.

**Reading.** Of the three books the Letter names, two share an unusual density of rare phrases with
the text, and so does much of the imitation-scripture genre they belong to. None shares a copied
passage, a sequence of events, or a passage that two independent reviews judged specific.


## 7. Corrections and robustness

The registered run is the main record. Everything below was found or decided later, is labelled,
and is reported beside it, not in place of it.

### 7.1 Book of Mormon quotations in candidate samples (Amendment 43, post hoc)

After unblinding, the 590M candidate models ranked Oliver Cowdery's pre-1830 sample closest to 119
of 168 chunks. That sample, his "Articles of the Church of Christ" (June 1829), is 40% word-for-word
Book of Mormon text: it copies the sacrament prayers and baptismal instructions. Parley P. Pratt's
books quote it too (3.6%). The seal had been enforced on training data but not on candidate
samples.

Every run of words a candidate sample shares with the text was classed by a rule fixed before the
matches were read: biblical; period stock phrasing; written before the matching passage was
dictated; written in the same weeks; or written after it (`docs/bom-overlap-analysis.md`). Only
**quotations** were dropped: passages of 20 or more words written after the matching passage
existed. Masking every shared run was rejected, since it would also remove genuine shared idiom,
above all from Joseph Smith's 1828-29 revelations, which contain no quotation (one shared phrase
predates the passage it matches; the rest were dictated in the same weeks); they are unchanged.
The candidate models were retrained and the sealed set rescored by every method that reads
candidate samples.

| Method | Registered: ranked closest (of 168) | Without quotations | Matches |
| --- | --- | --- | --- |
| Cosine Delta | Joseph Smith 131, Hunt 31 | Joseph Smith 148, Hunt 20 | 0 -> 0 |
| Burrows' Delta | Joseph Smith 77, Hunt 47, Pratt 37 | Joseph Smith 91, Hunt 49, Pratt 25 | 0 -> 0 |
| General Imposters | Pratt 74, Joseph Smith 48 | Joseph Smith 66, Pratt 66 | 0 -> 0 |
| Style encoders 297M / 590M | Joseph Smith 150 / Cowdery 102 | Joseph Smith 151 / 99 | 0 -> 0 |
| Candidate models 125M / 297M / 590M | Joseph Smith 82 / 133 / 46; Cowdery 29 / 34 / 119 | Joseph Smith 159 / 168 / 131 | 10 / 5 / 3 -> 2 / 2 / 0 |

The Cowdery ranking was leakage and disappears. One consequence: without its quotations
Cowdery's 1829 sample is 844 tokens, shorter than one 1,024-token training sequence, so his
pre-1830 candidate model received no training step and is reported as not scorable by the
candidate models (the style encoders, which need no training on the sample, still score it).

### 7.2 Equal training dose (Amendment 45, post hoc)

Joseph Smith's revelations are the smallest sample (3,039 training tokens), and a model trained on
less text moves less from the base model, which could favour it. Every candidate sample was cut into
two seeded slices of exactly that size, 20 equal-dose models trained per model size, and the
revelations model ranked against them.

| Size | Revelations ranked first (of 168) | Mean rank among 21 |
| --- | --- | --- |
| 125M | 168 | 1.0 |
| 297M | 168 | 1.0 |
| 590M | 62 | 1.6 |

At 125M and 297M sample size does not explain the ranking. At 590M one slice of Hunt's *The Late
War*, written in the same chronicle-scripture register, outranks the revelations in 63% of chunks
(the other Hunt slice never does): the larger model's closeness follows register.

### 7.3 The synthesis placebo (post hoc)

Run on the candidates' own held-out decoys, the registered synthesis still leans to "not in set":
Ethan Smith 0.59, Hunt 0.56, Spalding 0.51, controls 0.63. The method cannot recognise an author's
own text as that author's, because its one contributing family (General Imposters) cannot reach
"match" at its registered threshold. The Book of Mormon's 0.744 is therefore reported, but carries
little information. It is also driven by modelling choices: across priors of 0.2-0.8 it runs
0.42-0.92; with equal family weights it is about 0.99, treating chunks as independent about
0.99999, and dropping General Imposters returns the prior.

### 7.4 Every decision made after results existed

| Amendment | Decided after | What it changed | Effect on the results |
| --- | --- | --- | --- |
| 19 | dating validation | H3a/H3b decided on segment medians | none on Book of Mormon results (fixed before scoring) |
| 25 | the benchmark | open-set threshold corrected to the 5th percentile of true authors | the false-match rates of section 4 |
| 33 | the benchmark | both readings of 6.1 and a false-match ladder reported | none (both shown) |
| 38-39 | the 1B's loss spike | 590M with QK-norm replaces the 1B | one model size |
| 41-42 | the 590M benchmark | V1/V2 learning rate; V2 seeds | V2 given no weight |
| 43 | unblinding | Book of Mormon quotations dropped from candidate samples | Cowdery ranking removed; synthesis unchanged |
| 44 | unblinding | Joseph Smith's ordinary prose scored | register stated (section 10.1) |
| 45 | the simulated reviews | ranking rechecked at equal training dose | ranking holds at 125M/297M; register at 590M |
| 8 | the benchmark | rarity counted by text, not volume; Delta as closed-set evidence only | *The Late War* visible to the rare-phrase rule |
| 20-21 | the semantic positive control | an own-copy exclusion; named sources tested against matched nulls | one control passes |
| 31 | a smoke test | one Cosine Delta imitation figure was seen before the imitation rule was registered (disclosed) | none |
| (none) | unblinding | synthesis placebo | the synthesis read as uninformative |

Every amendment, with its reason and date, is in section 11 of the pre-registration and on OSF.

### 7.5 Process failures

Reported because the study's guarantee is that everything can be checked:

- **Source data deleted.** The newspaper extractor deleted the archives it read, losing the per-word
  OCR confidence and word positions for all 158,960 pages; a build test now fails on any
  destructive call in the pipeline (BOM-50; recovery is open).
- **Licensed text nearly published.** A 117 MB results file holding fresh-author text was caught
  by the repository's size limit before it was pushed; results files now hold names and numbers
  only. Earlier, validation excerpts from Harvard's texts and a personal email and IP address were
  committed and removed by rewriting history.
- **Models discarded.** The benchmark's fine-tuned models were scored and then deleted to save
  disk, and the abandoned 1B's checkpoints were deleted without asking; every fine-tune is now kept
  and published, and the discarded ones are being rebuilt (BOM-72).
- **Wrong results caught later.** A first genre-agreement figure (7.4%) counted 3,027 outage
  failures as answers; a paraphrase write-up said no named source ranked first when one did; a
  rare-phrase count came from the wrong book; a closed catalog issue had left out HathiTrust. Each
  was corrected in the open, with the issue reopened.


## 8. Public claims

Seventeen public claims, from critical, apologetic and academic sources, were registered with their
decision rules before any result (`data/claims/register.yaml`); the verdicts apply those rules
(`docs/claims-verdicts.md`). An untestable claim is not a contradicted one.

| Claim | Source | Verdict |
| --- | --- | --- |
| c01 *The Late War* shares unusual rare phrases | CES Letter; Johnson and Johnson 2013 | mixed: passes its null, but a same-genre control scores higher |
| c02 *View of the Hebrews* shares themes closely enough to suggest dependence | CES Letter | contradicted |
| c03 Cowdery's link to Ethan Smith's congregation | CES Letter | untestable (biography) |
| c04 About 80 early-modern word uses obsolete by 1830 | Skousen and Carmack | not addressed (the forms were not tested one by one) |
| c05 Early-modern syntax that King James imitation cannot explain | Skousen and Carmack | mixed: grammar model yes, transformer cross-check about 1755 |
| c06 Dictation under "tight control" | Skousen and Carmack | untestable (production) |
| c07 Rigdon and Spalding contributed | Jockers et al. 2008 | contradicted |
| c08 Narrators distinct from each other and from the candidates | Larsen et al. 1980 | contradicted |
| c09 With "none of the above" allowed, no nineteenth-century candidate is the author | Fields et al. 2011 | supported by the rule, with caveats: the synthesis covers three candidates and its placebo shows little information (section 7.3) |
| c10 The text belongs to the American pseudo-biblical genre | Shalev | mixed: shares its stock phrasing, separates on grammar |
| c11 DNA cannot settle population questions | Gospel Topics | untestable (genetics) |
| c12 Dictated without notes or manuscripts | Gospel Topics | untestable (production) |
| c13 Spalding's manuscript supplied the story or text | Howe 1834 | contradicted |
| c14 *The First Book of Napoleon* suggests dependence | named sources | mixed |
| c15 Cowdery or Rigdon wrote or shaped the text | named sources | contradicted (Cowdery's high ranking was quotation, section 7.1) |
| c16 The language reflects its 1820s environment | Brodie 1945 | contradicted (language only; themes are separate) |
| c17 Narrators not distinct, and close to Joseph Smith's revelations | Holmes 1992 | supported |

**Totals:** supported 2, contradicted 6, mixed 4, not addressed 1, untestable 4.


## 9. What held

Read in the order of trust fixed before unblinding (`docs/method-reliability.md`):

1. **Ranking is the models' strength; matching is their weakness.** On known answers the candidate
   models rank the true author first 94-99% of the time, and wrongly say "match" 22-47% of the
   time. Every attribution here is graded evidence.
2. **No candidate is matched.** Of 168 chunks, 3-10 reach "match" in the registered run and 0-2 without
   Book of Mormon quotations in the samples, fewer than chance alone would give; no candidate is
   matched by two independent families; no control passage was ever called a match.
3. **If the author is one of the candidates, the strongest ranking points to Joseph Smith.** Every
   method ranks a Joseph Smith sample closest at least as often as any other (General Imposters
   ties him with Pratt), in seven of eight methods
   his 1828-29 revelations. This holds when every candidate model gets the same amount of training
   text at 125M and 297M. It runs through the scriptural register: his ordinary prose sits
   mid-pack, and at 590M an equal-sized slice of *The Late War* competes. Whether the author is
   one of the candidates at all, the tools cannot settle: none passes the 5% false-match bar, and
   the registered synthesis cannot tell an author's own text from a stranger's.
4. **Nothing copied, no plot shared.** No proposed source shares a copied passage, a sequence of
   events or a passage judged specific by two reviews; the story-structure test finds Josephus
   retelling Genesis when the story is there. Its one registered hit (Church's *Philip's War*, six
   generic military-letter events) is what chance gives among 49 books. Rare-phrase overlap with *The Late War* and *The First
   Book of Napoleon* is real and genre-wide.
5. **The language is earlier than its period and than period imitations.** The grammar dates
   mostly before 1700 (median 1661); the text is more archaic than the 1780-1830 pseudo-biblical
   books (p 0.0001), also counting each book of it as one unit.
6. **The narrators are not separable as different authors**, and dictation order explains their
   differences about as well.
7. **Period training matters.** The same method on a modern model makes false matches 86-92% of
   the time; on the period models 22-47%, falling with size.

None of this bears on how the text was produced, whether it is a translation, or whether it is
inspired: no borrowing or dating test separates genuine translations from compositions presented
as ancient, and no stylometric method separates the person who dictated a text from the person who
composed it.


## 10. The people, one by one

For each candidate: the samples, how the methods rank them, whether any chunk is called a match,
and the context. Numbers are from the run without Book of Mormon quotations (Amendment 43;
`data/blind/a43/per_candidate.json`), with the registered run (`data/blind/per_candidate.json`)
where it differs. "Mean rank" is among the 10-11 candidate samples on the 168 chunks (1 =
closest); "first" is the number of chunks ranking that sample first; "match" counts registered
match calls.

**Every candidate sample, every method** (mean rank / first / match where the method calls
matches; "-" = not scored):

| Sample | Burrows | Cosine | Gen. Imposters | Style 297M | Style 590M | Models 125M | Models 297M | Models 590M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Joseph Smith, revelations 1828-29 (2,720 words) | 6.7 / 29 | **1.1 / 148** | 3.9 / 59 / 0 | **1.1 / 149 / 0** | **1.5 / 99 / 0** | **1.1 / 159 / 2** | **1.0 / 168 / 2** | **1.3 / 131 / 0** |
| Joseph Smith, dictated after 1830 (5,039) | 3.4 / 41 | 3.0 / 0 | 6.0 / 3 / 0 | 3.8 / 2 / 0 | 3.9 / 0 / 0 | 8.6 / 0 / 0 | 7.6 / 0 / 0 | 6.2 / 0 / 0 |
| Joseph Smith, handwritten after 1830 (6,363) | 4.5 / 21 | 3.8 / 0 | 6.1 / 4 / 0 | 5.5 / 0 / 0 | 7.4 / 0 / 0 | 7.0 / 0 / 0 | 3.0 / 0 / 0 | 3.9 / 0 / 0 |
| Oliver Cowdery, 1829 Articles (844 tokens after A43) | - | - | - | 2.3 / 12 / 0 | 1.8 / 58 / 0 | not scorable | not scorable | not scorable |
| Oliver Cowdery, printed after 1830 (44,338) | 5.9 / 0 | 7.8 / 0 | 6.3 / 0 / 0 | 7.7 / 0 / 0 | 6.6 / 0 / 0 | 3.0 / 7 / 0 | 5.0 / 0 / 0 | 4.0 / 0 / 0 |
| Sidney Rigdon, after 1830 (21,516) | 8.3 / 0 | 5.7 / 0 | 5.6 / 1 / 0 | 6.3 / 0 / 0 | 7.4 / 0 / 0 | 8.2 / 0 / 0 | 9.0 / 0 / 0 | 7.3 / 0 / 0 |
| Solomon Spalding (41,833) | 5.5 / 0 | 8.6 / 0 | 6.7 / 0 / 0 | 10.0 / 0 / 0 | 10.6 / 0 / 0 | 3.7 / 0 / 0 | 4.4 / 0 / 0 | 6.5 / 0 / 0 |
| Ethan Smith (277,391) | 6.2 / 2 | 9.9 / 0 | 7.0 / 0 / 0 | 9.3 / 2 / 0 | 9.0 / 0 / 0 | 10.0 / 0 / 0 | 10.0 / 0 / 0 | 10.0 / 0 / 0 |
| Gilbert J. Hunt (56,956) | 5.5 / 49 | 4.4 / 20 | 5.1 / 35 / 0 | 5.4 / 2 / 0 | 3.9 / 11 / 0 | 4.5 / 0 / 0 | 4.7 / 0 / 0 | 5.0 / 11 / 0 |
| Parley P. Pratt, after 1830 (91,478) | 3.0 / 25 | 3.9 / 0 | **2.2 / 66 / 0** | 4.9 / 1 / 0 | 4.5 / 0 / 0 | 4.4 / 2 / 0 | 7.0 / 0 / 0 | 8.8 / 0 / 0 |
| W. W. Phelps, after 1830 (28,479) | 6.1 / 1 | 6.7 / 0 | 6.1 / 0 / 0 | 9.8 / 0 / 0 | 9.4 / 0 / 0 | 4.6 / 0 / 0 | 3.3 / 0 / 0 | 2.1 / 26 / 0 |

Every sample written after 1830 is by someone who had read the book; its closeness is
uninformative and its distance is the informative direction. **No sample written after 1830 is
called a match by any method at any size.**

### 10.1 Joseph Smith

**Samples.** His only surviving writing from before 1830 is the revelations of 1828-29 (2,720
words), dictated in a scriptural voice in the same months as the text. After 1830: dictated letters
and documents (5,039 words) and his own handwriting (6,363), from the Joseph Smith Papers
manuscripts; pooled non-revelatory prose of 1831-33 (letters and the 1832 history, about 11,600
tokens, Amendment 44). All are under or near the 10,000-word floor, and the registered check of whether later writing
can stand in for earlier failed for every method (section 2.6), so none of the post-1830 samples
can stand in for his pre-1830 style.

**Revelations: closest, everywhere but Burrows' Delta.** Seven of eight methods rank the revelations
closest, at every model size, and the candidate models call 2, 2 and 0 chunks a match (125M, 297M,
590M). Burrows' Delta, which rests most on function words, prefers his later dictated prose.

**Equal dose.** With every candidate model trained on exactly as much text as the revelations
(Amendment 45), the revelations rank first in 168 of 168 chunks at 125M and 297M; at 590M in 62,
with one slice of *The Late War* ahead in 63% of chunks (section 7.2).

**Register.** Mean rank of his two kinds of writing among 12 samples (Amendment 44):

| Method | Revelations, 1828-29 | Ordinary prose, 1831-33 |
| --- | --- | --- |
| Candidate models 125M / 297M / 590M | 1.1 / 1.0 / 1.3 | 6.1 / 6.3 / 5.4 |
| Style encoders 297M / 590M | 1.1 / 1.5 | 4.7 / 5.7 |
| Cosine Delta | 1.2 | 3.3 |
| General Imposters | 3.6 | 6.1 |
| Burrows' Delta | 7.7 | 2.7 |

Seven of eight methods place the revelations closest and his ordinary prose in the middle; Burrows'
Delta reverses them. The closeness runs mainly through the revelatory register, which is the
register of the text.

**Revelation as a register of its own.** One might argue that revelation, on any account of it,
would share the voice of scripture, so that a revelation and a book presented as scripture would
resemble each other whoever wrote them. The data cannot separate that reading from shared
authorship. What they do show is that his non-revelatory prose, measured the same way, is not
close, and that at the largest size another writer's chronicle scripture competes with his
revelations.

**Dictation.** The text was dictated by Joseph Smith on every account of its origin, and the
manuscript evidence shows it was taken down by ear (section 5.6). No stylometric method separates
the person who dictated a text from the person who composed it.

**His prose over time (BOM-73, in progress).** Did his ordinary writing, and that of others who
read the book, move toward its style after 1830? The attribution rule and the measures are fixed
in advance (`docs/js-over-time-plan.md`): 21 Joseph Smith Papers documents of 1833-1844 in his
hand or recorded as dictated, revelations excluded; three groups measured alike by period (1831-33,
1834-36, 1837-39, 1840-44): Joseph Smith; others who read the book (Cowdery, Pratt, Phelps,
Rigdon); and religious writers of the same years with no tie to the movement (Alexander Campbell,
Barton Stone, Methodist and Baptist periodicals, Finney, Beecher). Influence is supported only if
his line and the readers' move toward the book while the unexposed writers' does not. No ordinary
prose of his survives from before 1830, so his style before the book cannot be tested. The result
will be added here when measured.

### 10.2 Oliver Cowdery

**Samples.** His 1829 "Articles of the Church of Christ" (1,310 words, 40% Book of Mormon quotation;
844 tokens after Amendment 43) and his printed writing after 1830 (44,338 words, mostly the
*Messenger and Advocate*). He was the principal scribe of the text.

**Results.** In the registered run the 590M candidate models ranked his 1829 sample closest to 119
chunks, which was the quotation (section 7.1). Without it the candidate models cannot score the
sample (too short to train on). The style encoders, which need no training, still rank what
remains second closest (mean rank 2.3 and 1.8; first in 12 and 58 chunks), with no match: that
remainder still shares 7.8% of its words with the text in short phrases, much of it written in the
same weeks. His post-1830 writing is mid-pack (mean rank 3.0-7.8) and never matched. Claim c15
(Cowdery or Rigdon wrote the text): contradicted.

### 10.3 Sidney Rigdon

**Sample.** Printed writing after 1830 (21,516 words); the candidate set holds no pre-1830 Rigdon text.
**Results.** Mean rank 5.6-9.0, near the bottom for most methods; never matched. Jockers et al.'s
Rigdon lead does not return on our texts (section 3; claim c07 contradicted).

### 10.4 Solomon Spalding

**Sample.** The surviving *Manuscript Story* (41,833 words; posthumous). **Results.** Mean rank
3.7-10.6, never matched; synthesis 0.085. As a source, no passage, phrase density or plot is shared
(section 6.4; claim c13 contradicted). Access 0. Only the surviving manuscript can be tested.

### 10.5 Ethan Smith

**Sample.** *View of the Hebrews* and his other books (277,391 words). **Results.** Last or near last
for every method (mean rank 6.2-10.0), never matched; synthesis 0.082. As a source, section 6.1
(claim c02 contradicted).

### 10.6 Gilbert J. Hunt

**Sample.** *The Late War* and his other writing (56,956 words). **Results.** Mid-pack by most
methods (mean rank 3.9-5.5), first for 49 chunks by Burrows' Delta and 35 by General Imposters, never
matched; synthesis 0.089. At equal dose at 590M, one slice of *The Late War* outranks Joseph Smith's
revelations in most chunks (section 7.2). As a source, section 6.2 (claim c01 mixed).

### 10.7 Parley P. Pratt

**Sample.** Printed books after 1830 (91,478 words; 3.6% Book of Mormon quotation before
Amendment 43). **Results.** General Imposters ranks him first as often as Joseph Smith (66 chunks
each) and Burrows' Delta ranks him third; the models rank him low (mean rank 4.4-8.8). Never
matched. He wrote after reading the book.

### 10.8 W. W. Phelps

**Sample.** Printed writing after 1830 (28,479 words). His pre-1830 newspaper, the *Ontario
Phoenix*, is not digitized anywhere, and his signed items in the *Lake Light* (1827-28) were too few
to extract. **Results.** The 590M candidate models rank
him second (mean rank 2.1, first in 26 chunks, 22 inconclusive, no match); other methods rank him
low (6.1-9.8). Never matched. He wrote after reading the book.


## 11. Limitations

**No method passes the benchmark.** Every method ranks well (up to 0.991) but none keeps false
matches at or below the registered 5% (best stable result 0.218, the candidate models at 590M).
Under the registered thresholds General Imposters and the style encoders cannot return "match" at
all, so section 6.2's two-family rule could not have supported any candidate, and the registered
synthesis cannot recognise an author's own text (section 7.3). "No match" therefore cannot be read
as "not this person".

**Methods differ in stability.** The primary language-model method reproduces exactly across
machines and improves with size; V1's registered learning rate broke at 590M; V2 swings from 9% to
98% false matches across seeds and carries no weight; the model-based methods are weaker than the
classical ones on deliberate imitation.

**Closest is confounded with register.** Joseph Smith's revelations are the only candidate sample
in the text's own scriptural register; his ordinary prose is not close, and at 590M another
writer's chronicle scripture competes. The methods cannot separate shared register from shared
authorship, nor the person who dictated a text from the person who composed it.

**Small and uneven samples.** Joseph Smith's pre-1830 writing is 2,720 words and Cowdery's 1,310
(844 tokens without quotations); both are under the 10,000-word floor. Rigdon, Pratt and Phelps are
represented only by writing after 1830, by which time they had read the book. Samples mix
provenance (dictated, edited, posthumous); each tier is recorded.

**The borrowing and dating tests cannot speak to translation.** None separates genuine translations
of ancient texts from compositions presented as ancient (Amendment 9). The dating models learned
1780-1830 English from edited print; unedited vernacular may read to them as archaic.

**One person, simulated review and simulated blinding.** The study is designed and run by one person
with AI assistance. Every review step (adversarial, draft, peer) and the second triage pass are
simulated by AI models; the blind run's "fresh session" is a new AI session without the key, not
an independent analyst. None of this is independent scrutiny.

**The corpus.** OCR quality is uneven, and the wording searches miss an unmeasured but probably
large share of real shared phrasing in poor scans (a 4-gram survives about 41% of the time at 80%
word accuracy); a negative from poor OCR is not evidence of absence, as the 26 June 1829 *Wayne
Sentinel* title-page notice shows (present on the page image, 0 of 10 search terms found in its
OCR). Training volumes holding 1 to 19 of the text's 12-token strings (below the removal threshold
of 20) were kept and not reported; some catalog dates are wrong (corrected where the text names
later years); author names conflate namesakes and split variants; 72% of the original manuscript
is lost. Writers whose work did not survive in print, or is outside the 23,872 swept authors, are
not covered. The sweep failed its own usability test and is descriptive only.

**The models.** The time-locked models were trained on the period corpus, which includes held-out
authors' volumes used later for calibration (language modelling, not authorship supervision). The
fine-tuning settings were fixed for all sizes in advance and may not suit the largest. GPT-2 is
used on the benchmark only, since it read modern text possibly including the Book of Mormon.

**Post hoc decisions.** Every decision made after results existed is listed with its effect in
section 7.4 and labelled in the pre-registration.

**Access is not use.** The access table records documented availability, not reading.

**Planned and not run.** The hand validation of the genre labels and the 100-run perturbation that
would show whether label errors matter (BOM-53); thematic dating, whether the text's themes track
the 1820s (BOM-63); the register placebo (BOM-76); and Joseph Smith's prose over time (BOM-73,
in progress). Genre labels agree moderately between two model passes (84.9% on either label, 50.8%
exactly) and worst on early modern text.


## 12. Everything is public

The study is meant to be checked and redone. Mistakes are possible; what makes up for them is that
every step can be found and rerun.

- **Pre-registration and amendments:** https://osf.io/6ugxc/ (frozen 2026-10-15; 45 dated
  amendments, each post hoc one labelled), mirrored in `paper/preregistration.md`.
- **Code and configuration:** https://github.com/lifehug/book-of-mormon-authorship. Every analytic
  value comes from `config/preregistered.yaml`, and every output records that file's SHA-256 and
  the git commit. Every command, what it needs and writes, and how long it takes, is in
  `eval/README.md`.
- **Models:** every trained model is on Hugging Face: the time-locked base models
  (`etherfuse/timelocked-1830-125m`, `-297m`, `-590m`) and every fine-tuned candidate, benchmark,
  style-encoder and dating model (`etherfuse/bom-authorship-*`), with checksums in
  `data/manifests/`.
- **Data:** the catalog, genre labels, derived tables and every result file (numbers and names,
  never licensed text) are in `data/`.
- **Simulated reviews:** three simulated peer reviews and the responses (`paper/review/`).
- **What is held back, and how to get it:** Harvard Institutional Books (noncommercial terms, no
  redistribution), the HathiTrust researcher dataset, the Joseph Smith Papers transcripts
  (copyrighted) and one purchased book. For each, `docs/replication.md` gives numbered steps to get
  the same access we had.


## 13. What comes next (Part 2)

Three reasons to go further: false matches fell from 47% to 38% to 22% between 125M and 590M, and
the best-fit size for this data is about 1.3B; a source older than 1780 could have been used, and the
library covers 1780-1830; and only a method under 5% false matches lets "no match" mean "not this
person". Part 2 asks two questions: do the conclusions hold with a larger model and library, and
can any candidate be confidently excluded?

| Stage | What | Gate |
| --- | --- | --- |
| 0 | Pre-register success criteria and gates; grow the benchmark from 110 to about 400 tests; cross-work decoys and a register placebo (writers who died before 1827, and writers born after 1830 with no exposure, reported separately); several seeds per candidate model; larger candidate samples where they exist | the owner reviews Stage 0's results before any larger model |
| 1 | A 1.3B time-locked model with QK-norm on the present data; every test rerun | continue only if false matches fall by the pre-registered margin |
| 2 | More 1780-1830 text (Google-digitized volumes, the period's newspapers); a ~1.7B model; borrowing and sweep over the larger library | as above |
| 3 | All English before 1830 (1700-1780 and 1473-1700), year-tagged; a 2-3B model; borrowing, story structure and dating against all of it | as above |

Each gate can stop the sequence; if a stage does not cut false matches meaningfully, the next model
is not trained and the effort goes to data and methods. Only Stage 0 is committed. The plan, costs
and issues are in `docs/part2-plan.md` (BOM-74 to BOM-86).

**What each outcome would change.** If a larger model passes 5% false matches with useful
sensitivity, "no match" becomes "not this person" for the candidates with adequate samples, and
the registered synthesis can be replaced by one that can recognise an author. If the
register placebo ranks a writer who died before 1827 as close as Joseph Smith's revelations, the
ranking in section 10.1 measures register rather than person. If the wider library turns up a
source older than 1780, the borrowing tests will show it.


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

Units: 23,875 named, non-corporate authors in the training set's volumes with at least 10,000
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
| *The Late War* (1816, 9 printings) | 22 | 3.86 | 131 | 0.0006 (0.0004-0.0017) |
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
