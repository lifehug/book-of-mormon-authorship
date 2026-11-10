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
and, for dating, 61,315 early modern English texts (1473-1700, EEBO-TCP). About 1.1 TB on
disk. Harvard's and HathiTrust's texts and the Joseph Smith Papers transcripts are licensed and
are not redistributed; derived tables, checksums and the steps to obtain each are
(`docs/replication.md`).

### 2.2 Cleaning

Catalog dates were audited against the text itself; volumes whose pages name later years were
re-dated (BOM-64, Amendment 12), which mattered: some "1817" Congressional volumes and an "1830"
*Millennial Harbinger* quote the Book of Mormon. Reprints and later editions were grouped by
MinHash similarity (5-gram shingles, threshold 0.8) and a second pass by title, author and year;
nothing is deleted, duplicates are flagged (`data/catalog/DEDUP.md`). OCR quality was measured
and is uneven (BOM-14, BOM-50).

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

Every span of the text aligned to the King James Bible was masked (18,336 of 268,811 words, 6.8%);
the same masking was applied to candidates (3.7%) and to 1.55 billion words of controls (1.8%).
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
revelations), dictated after 1830 5,039, handwritten after 1830 6,363; Oliver Cowdery handwritten
before 1830 1,310 (after Amendment 43, 844 tokens), printed after 1830 44,338; Parley P. Pratt
91,478; Sidney Rigdon 21,516; W. W. Phelps 28,479. Samples under 10,000 words carry an
"unreliable sample" flag fixed before scoring. Samples written after 1830 come from people who had
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
