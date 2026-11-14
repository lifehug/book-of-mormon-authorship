## 2. The scale and preparation of the test

Each test in this paper is preceded by how it was prepared. This section gives the preparation
common to all of them: the library, its cleaning and labelling, the sealing of the Book of Mormon
text, the candidates' samples, the known-answer tests, and the language models.

### 2.0 At a glance

| | Larsen et al. 1980 | Holmes 1992 | Jockers et al. 2008 | Schaalje et al. 2011 | Johnson and Johnson 2013 | This study |
| --- | --- | --- | --- | --- | --- | --- |
| Question | do the narrators differ; does a candidate fit | do the prophets differ | which candidate | which candidate, or none | which books share rare phrases | who, what was borrowed, when |
| Comparison library | candidate samples | candidate and biblical samples | candidate samples | candidate samples | about 100,000 books (unpublished) | 202,816 period volumes for the models; 204,520 for rare phrases; 163 million passages for paraphrase |
| Candidates | nineteenth-century writers [CHECK: Larsen et al.'s own candidate list is not in our result files; our rerun used nine samples] | Joseph Smith's own writing and his revelations, beside the book's prophets | 4 (Rigdon, Spalding, Cowdery, Pratt) | 5 (the same, and Joseph Smith) | books, not people | 8 named people, then 23,872 library authors |
| Controls | none | none | Isaiah-Malachi, Barlow, Longfellow | Isaiah | none | four control groups, placebo writers, decoys |
| "None of these" allowed | no | no attribution made | no (closed set) | yes | not applicable | yes, every method that has a match score |
| Error rate on known answers | no | no | cross-validated among candidates | partly | no | right-author rate and false-match rate per method, on 110, 430 and 1,070 held-out tests |
| King James text removed | no | no | no | no | no | yes, 6.8% of the text |
| Pre-registered, blind | no | no | no | no | no | yes; blinding simulated |
| Models and data public | no | no | data deposited | no | no | yes: base and candidate models, code, derived tables |

The candidates and controls of the earlier studies are as recorded in our reruns of them (section
4; `paper/replication-report.md`).

### 2.1 Gathering

The catalog holds 695,021 items from five sources (`data/catalog/catalog.parquet`). Four cover the
period 1780-1830: the Internet Archive (307,567 items), HathiTrust (135,035), Harvard's
Institutional Books 1.0 (31,958 volumes; released in 2025 and, as far as we know, used here for the
first time on this question) and Chronicling America (159,146 newspaper pages). The fifth is the
Text Creation Partnership's 61,315 hand-keyed texts, chiefly early modern English of 1473-1700,
which give the dating models their earlier reference.

The national newspaper set holds almost nothing from western New York (47 New York pages), so the
*Wayne Sentinel* (Palmyra; 1,429 pages, 1823-30) and the *Lake Light* were added from the New York
State Historic Newspapers. The *Ontario Phoenix*, which W. W. Phelps edited before 1830, is not
digitized anywhere. The whole is about 1.1 TB on disk.

**What can be redistributed.** Harvard's and HathiTrust's texts are licensed and the Joseph Smith
Papers transcripts are copyrighted; none is redistributed. Everything else is public, and for each
restricted source the numbered steps to obtain the same access are published
(`docs/replication.md`). Derived tables, labels and a checksum for every file are public, so a
reader who obtains the sources can apply our labels without rerunning the pipeline. What is held,
used and set aside is listed folder by folder in `docs/holdings.md`.

### 2.2 Cleaning

**Dates.** A catalog date is a claim, and some are wrong. Dates were audited against each volume's
own text: of 366,580 volumes scanned, 23,859 name a later year and 19,463 were moved past 1830
(Amendment 12). A model-read check of 100 flagged volumes found 81 truly later, so the correction
errs toward exclusion; moved volumes are kept in a separate column, not deleted. Another 11,494
volumes carried a placeholder date of 1800, and 1,502 of them were printed after 1830. This
mattered directly: 17 "pre-1830" volumes, among them Congressional serial-set volumes catalogued
1817 and an "1830" *Millennial Harbinger*, quote the Book of Mormon. Without the audit they would
have looked like its sources.

**Duplicates.** Reprints and copies were grouped in two passes. The first compares texts by MinHash
similarity (a fast estimate of how many five-word sequences two texts share; threshold 0.8), giving
19,920 groups. The second compares title, author and year across sources, giving 4,697 groups
(Amendment 6). Nothing is deleted; duplicates are flagged (`data/catalog/DEDUP.md`). The text pass
cannot see one book scanned twice by different libraries, because two noisy scans of the same pages
share little exact text (median similarity 0.12-0.18 on 300 such pairs). That is why the second
pass exists, and copies inside one source with different catalog entries can still escape both.

**OCR.** The texts are machine readings of page scans (optical character recognition, OCR), and
their quality was measured, not assumed. Against 1,883 volumes that also exist in hand-keyed form,
the median character error rate after cleaning is 0.083, and 38% of volumes remain above 0.10.
Above that cut are 2.5% of Harvard's volumes, 11.9% of HathiTrust's, 24.9% of the Internet
Archive's and 27.8% of the newspaper pages. At about 80% word accuracy a four-word phrase survives
OCR about 41% of the time, so the wording searches of section 3 miss more than half of any real
shared phrasing in poor scans. Correction of OCR by a language model was tried and rejected because
it invented text.

### 2.3 Labelling

Every item carries a genre label (sermon, history, fiction, imitation of scripture and so on)
assigned by a local language model, about 40 hours of machine time (`data/catalog/genre.parquet`).
The labels build the genre-matched comparison groups used throughout, so that a religious book is
compared with religious books.

**Validation.** A second model relabelled a stratified sample of 5,000 records. The two agreed on
at least one label for 84.9% and exactly for 50.8%; they contradicted each other on 15.1%, and a
third model adjudicated those 757 records (`docs/results-inventory.md`). All three readings are by
AI models: this is a simulated check, with no human labeller. A 300-record sample for hand
adjudication is drawn but deferred until a perturbation test shows that the results depend on the
labels.

### 2.4 Sealing and masking

**The seal.** The Book of Mormon was kept out of every model's training, tuning, thresholds and
feature selection until a single blind run, with one registered exception: the replications of
earlier studies in section 4, which feed nothing else. Catalogued copies were sealed by title, and
any volume holding 20 or more of the text's original 12-token strings was removed from training. In
practice these were later texts quoting the book under early catalog dates.

**King James masking.** A passage quoted from the Bible says nothing about who wrote the passages
around it, and would read as shared style with every other writer who quotes the Bible. Every span
of the text aligned to the King James Bible was therefore masked: 18,336 of 268,811 words, 6.8%
(`data/kjv_mask/bom/report.json`); the share is 32.7% in 2 Nephi and 15.0% in 3 Nephi. On planted
quotations the mask finds 78% of King James words with 95% precision, so some King James wording
remains in the unmasked text. The same mask was applied to the candidates' samples (3.7% masked)
and to 1.55 billion words of control texts (1.8%). The mask uses the 1769 King James text; the
Smith family's 1828 Phinney Bible is consistent with it. Authorship and dating read only the
unmasked text. The borrowing searches read the whole text with the King James spans labelled.

**The quotation rule for candidate samples (Amendment 43, post hoc).** The seal covered training
data but, as first built, not the candidates' own samples. After unblinding, Oliver Cowdery's 1829
"Articles of the Church of Christ" was found to be 40% word-for-word Book of Mormon text, and
Parley P. Pratt's books quote it too (3.6%). Every run of words a sample shares with the text was
then classed by a rule fixed before the matches were read (`docs/bom-overlap-analysis.md`), and
only **quotations** were removed: passages of 20 or more words written after the matching passage
existed. Shorter shared idiom stays, for every candidate alike. Joseph Smith's 1828-29 revelations
contain no quotation by this rule and are unchanged. Results are reported with the rule applied,
and the registered results beside them where they differ (section 9).

### 2.5 Segmentation

The text is cut three ways: by internal narrator (Nephi, Jacob, Mormon, Moroni and others), by the
order in which it was dictated, and by scribe. Each scheme is cut into chunks of 2,000 and of 5,000
words, 756 chunks in all (`data/bom/segments/chunks.jsonl`). The blind run scored the narrator
scheme's 168 whole chunks. These are the book cut twice, 121 chunks of 2,000 words and 47 of 5,000,
not 168 separate passages, so every count over them is also given per length (Amendment 55, post
hoc). The 5,000-word chunks were split in advance into a discovery half and a confirmation half by
a seeded draw stratified by narrator (22 and 25 chunks).

### 2.6 Candidate samples

Eight people are tested. Each sample is tagged by date and by provenance tier, meaning how directly
the words are the person's own: handwritten, dictated, printed by the author, or published after
death (Amendment 5). Word counts after King James masking (`data/benchmark/alm_candidates_plan.json`):

| Candidate | Sample | Masked words |
| --- | --- | --- |
| Joseph Smith | dictated before 1830 (his 1828-29 revelations) | 2,720 (3,039 model tokens) |
| Joseph Smith | dictated after 1830 | 5,039 |
| Joseph Smith | handwritten after 1830 | 6,363 |
| Oliver Cowdery | handwritten before 1830 | 1,310 (844 tokens after Amendment 43) |
| Oliver Cowdery | printed after 1830 | 44,338 |
| Sidney Rigdon | printed | 21,516 |
| Parley P. Pratt | printed | 91,478 |
| W. W. Phelps | printed | 28,479 |
| Solomon Spalding | *Manuscript Story* | 41,833 |
| Ethan Smith | printed before 1830 | 277,391 |
| Gilbert J. Hunt | *The Late War* | 56,956 |

**Limits of these samples.** Three limits were fixed before scoring and govern how every later
result is read.

- *Size.* A power analysis on known authors put the smallest reliable reference sample at about
  10,000 masked words (`data/benchmark/power.json`). Samples below that carry an "unreliable
  sample" flag. Every pre-1830 sample of Joseph Smith and of Cowdery is below it. After the
  quotation rule Cowdery's 1829 sample is shorter than one training sequence, so the candidate
  language models cannot score it at all.
- *Date.* A registered check asked whether a writer's later prose can stand in for his earlier
  prose, on 30 period authors with a gap of seven or more years. No method passed (37-60% against a
  gate of 80%; `data/benchmark/timesplit.json`). Writing after 1830 is therefore a secondary set:
  it comes from people who had read the book, and it may not stand in for their earlier style.
- *Role.* Pratt and Phelps had no documented contact with Joseph Smith before the text was
  finished. Hunt, Ethan Smith and Spalding enter as authors of proposed sources as much as proposed
  authors.

Joseph Smith's documents come from the Joseph Smith Papers manuscripts. A later, post hoc addition
(Amendment 54) is the rest of his Revelation Book 1: 95 revelations of 1830-34, 65,222 words, used
only in the deep dive of section 6.4.

### 2.7 Controls and the benchmark

**Control groups.** Four groups stand for writers who are not candidates: imitations of scripture
(18 works of 1774-1827, selected by a published rule; section 5.3), 1820s sermons and tracts,
histories including books on the origin of the American Indians, and general prose. Candidates' own
works are kept out of the controls. One early defect is kept on record: the first benchmark run's
pool of comparison authors wrongly held a copy of *The Late War* (BOM-21). The pool used in the
blind run removes every candidate's works.

**The benchmark.** A benchmark here is a set of texts whose authors are known, on which a method is
scored before it is trusted on a text whose author is not. Ours was built in three steps, and the
rule for each was written before its tests were scored.

| Step | Tasks | Authors with tests | Held-out tests |
| --- | --- | --- | --- |
| Part 1 (registered) | the Federalist papers (26 tests); imitation scripture with known authors (24); dictated text by Walter Scott (60) | 7 | 110 |
| BOM-75 (Amendment 48) | Part 1's three tasks, plus four authors each in fiction, law and politics, sermons, and history | 23 | 430 |
| Amendment 56 (post hoc) | 32 more authors, eight per genre, by the same rules | 55 | 1,070 |

In every task a method learns from the first three quarters of each author's text and is tested on
5,000-word passages from the last quarter, so tests come mostly from works it did not learn from. A
task offers a list of about four authors. Authors for the new genres were taken in a seeded random
order from all period authors with at least four distinct works and 60,000 words, after a screen
for translations, repeated texts, anthologies and catalog entries that join two people. The screen
was made by an AI model from catalog titles and years, and every rejection is recorded with its
reason (`data/benchmark/part2/screen.json`). No Book of Mormon text is involved at any step.

Each method is asked two things. With the true author on the list, how often is he ranked first?
With the true author removed, how often does the method still say "match"? The registered bar is at
least 90% on the first and at most 5% false matches on the second, with the match threshold set so
that 95% of true authors clear it (Amendment 25, post hoc: as first built, the threshold would have
given about 5% for any method by construction). Section 5 reports the results.

### 2.8 The time-locked language models

A language model predicts the next word of a text; how well it predicts a passage is a measure of
how expected that passage's language is to the model. Ours are GPT-style models trained from
nothing on 1780-1830 English only, with the Book of Mormon and all post-1830 text excluded: 202,816
volumes, 25.7 billion tokens (word pieces), read once (`docs/timelocked-plan.md`). "Time-locked"
means the model knows no English later than 1830.

| Size (parameters) | Why it was trained | Outcome (validation loss; lower is better) |
| --- | --- | --- |
| 125M | pilot: cheap, to test the whole pipeline | 2.515 |
| 297M | the registered model, the largest the first budget allowed | 2.325 |
| 1B | to test whether size helps (Amendment 26) | failed: training became unstable at about step 15,800 and was abandoned (Amendment 38) |
| 590M | the 1B's replacement, with a standard fix for that instability (QK-norm; Amendment 39) | 2.192 |

To test a candidate, one copy of a model is trained further on that candidate's sample alone, and a
passage is scored by how much better the copy predicts it than the untouched model does (Amendment
22). We call these copies candidate models. Every model-based test runs at all three sizes and is
reported side by side, with no size treated as the headline (Amendment 37).

**What is public.** The three base models and the candidate models are on Hugging Face
(`etherfuse/timelocked-1830-*`, `etherfuse/bom-authorship-candidate-models`). With the base models
anyone can rebuild every other model in this paper for roughly $50-100 of rented computing; with
the candidate models anyone can check the Book of Mormon results without the copyrighted
manuscripts and without training anything. Other fine-tuned models publish their scores, not their
weights.
