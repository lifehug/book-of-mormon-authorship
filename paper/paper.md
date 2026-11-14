# Authorship, borrowing and dating of the earliest Book of Mormon text: an open, pre-registered computational study

*Draft on outline version 3, 2026-11-14. Dave Taylor, with analysis by an AI model (Claude). Every
review step is simulated by an AI model and labelled so; the blinding was simulated (the scoring
ran without the key; the analyst is an AI model). Sections 1-13 were drafted by an AI model from
the previous draft and the results files and are under review; items marked [CHECK] are not yet
verified. Repository: https://github.com/lifehug/book-of-mormon-authorship; pre-registration:
https://osf.io/6ugxc/ (frozen 2026-10-15; amendments 1-46 filed there, 47-58 recorded in the
repository; the post hoc ones labelled). Section 14 is exploratory and says so.*

## Abstract

We ask three questions of the earliest English text of the Book of Mormon (1830): who writes like
it, what it borrows, and when its language belongs. The tools are language models trained only on
text printed before 1830 (25.7 billion tokens; 125M, 297M and 590M parameters), the older
stylometric methods beside them, and a library of 695,021 catalogued items of 1780-1830. Every
method was first measured on texts of known authorship, the plan was registered before the
results, and each later change is dated and labelled.

**Borrowing.** With King James quotation set aside, 0.16% of the book matches earlier print, all
of it stock religious phrasing. Two of the three books most often named as sources pass the registered rare-phrase
rule, but do not stand out from other imitation scripture (a post hoc comparison), and no book
shares its plot. These tests cannot tell a translation from a
period book written to sound ancient, so the finding describes the text and not its origin.

**Authorship among named candidates.** On 55 authors of known work our models pick the right
author more often than every older method at every size. Among eight proposed candidates the
closest writing is Joseph Smith's revelations of 1828-29, in six of eight rankings (five method families at their several sizes); his
ordinary prose does not stand out under the language models. At the largest model size, writers
who could not have written the book score as close, so register explains part of the result. No
method can reliably answer "none of these".

**The whole library (exploratory).** A style encoder that places the true author of a known book
in its top ten 59% of the time among the 18,288 authors not known to have been dead (38% for a
book unlike its author's other writing; 727 known books) was run on all 23,872 authors with the candidates
beside them, at three profile sizes. A sample of Joseph Smith's revelations is first at two
sizes and second at the third, behind one library author, John Wroe, who also published
revelations. The rest of the head of the list is religious testimony, and dead authors are
over-represented in it: it is a kind of writing, not a set of possible authors.

The study does not argue for or against inspiration. Everything is public and rerunnable.

## 1. Introduction

The Book of Mormon was published in 1830. Three questions about its English text have been argued
ever since: **who** produced the wording, **what** in it was borrowed from books already in print,
and **when** its language belongs. This paper puts all three to the earliest text with computational
tools, and reports what those tools can and cannot answer.

Two centuries of argument have not settled the questions, and four decades of computer studies have
reached opposite conclusions. Wordprint studies found the book's narrators distinct from each other
and from nineteenth-century candidates (Larsen, Rencher and Layton 1980). A classification study
pointed to Sidney Rigdon and Solomon Spalding (Jockers, Witten and Criddle 2008). A reanalysis that
allowed the answer "none of these" sent most chapters to an unobserved author (Schaalje, Fields,
Roper and Snow 2011). A rare-phrase study singled out Gilbert Hunt's *The Late War* (Johnson and
Johnson 2013). Each was criticised more for its setup than for its arithmetic: candidate lists that
force a pick; features that measure biblical register (the King James manner of writing) rather
than a person; choices made after seeing the data; and comparison libraries too small to say what
is unusual for the period. Section 4 reruns five of these studies and shows how far each answer
follows such choices.

What is new here:

1. **Models trained only on text printed before 1830.** A modern language model has read the Book
   of Mormon and everything written about it. Ours were trained from nothing on 25.7 billion tokens
   of English printed from 1780 to 1830, with the Book of Mormon and all later text kept out, in
   three sizes (125M, 297M and 590M parameters). To such a model, "ordinary English" means ordinary
   for 1830 (section 2.8).
2. **The largest corpus and candidate set.** The comparison library is the surviving digitized
   print of 1780-1830, 695,021 catalogued items, rather than a hand-picked shelf. Eight named
   candidates are tested, and afterwards every one of 23,872 authors in the library (sections 2,
   7.8 and 14).
3. **Every method tested on known answers first.** Before a method is read on the Book of Mormon it
   is scored on texts whose authors are known: how often it picks the right author from a list, and
   how often it wrongly says "match" when the true author is not on the list. Our own models and
   the methods of the earlier studies take the same tests and are reported side by side, at every
   model size. The earlier methods are baselines to compare against; they are not votes to be
   averaged with ours (section 5).
4. **A plan written in advance.** Thresholds, features, random seeds and model choices were fixed
   publicly before scoring (`paper/preregistration.md`). Every later change is a dated amendment,
   and each one made after results were seen is labelled post hoc wherever it is used (section 9).
   Every span of the text that follows the King James Bible, 6.8% of it, is set aside before
   authorship and dating are measured.
5. **Everything public and rerunnable.** The code, the result tables, the base models and the
   candidate models are public. The licensed source texts are not ours to give, so the steps to
   obtain each are published instead (section 13). One person ran this study with AI models; every
   review step in it (blinding, second readings, the reviews of the plan and the draft) was
   performed by an AI model and is labelled *simulated* where it appears.

What methods of this kind can see is the English on the page. They cannot see how that English came
to be, and in particular cannot separate a writer who composed a text from one who dictated or
translated it. The study therefore takes no position on the book's origin, on translation or on
inspiration.

**The result, stated once.** If the author is among the candidates, the closest writing is Joseph
Smith's revelations. Whether the author is among them, these tools cannot settle. Section 5.4 shows
why the second sentence is needed: no method tested here, ours included, can reliably answer "none
of these".

**How the paper is ordered.** Section 2 describes the scale of the test and how the library and the
text were prepared. Section 3 leads the results with borrowing, including the three books named in
the *CES Letter*. Section 4 reruns the earlier authorship studies. Section 5 scores every method on
known answers. Section 6 examines Joseph Smith's writing in depth, and section 7 takes the other
candidates one by one, then everyone else in the library. Section 8 covers dating and the book's
internal voices. Section 9 lists every correction and every post hoc step. Section 10 judges
seventeen public claims by rules written beforehand. Sections 11 to 13 give what held, the
limitations, and what is public. Section 14 puts the same question to the whole library.

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

**What can be redistributed.** Harvard's and HathiTrust's texts are licensed, and the Joseph Smith
Papers transcripts and one purchased book (Rick Grunder's *Mormon Parallels*) are copyrighted;
none is redistributed. Everything else is public, and for each
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

## 3. Borrowing: the CES Letter's books, and everything else

The question with the plainest answer comes first: what did the Book of Mormon take from books
already in print? Borrowing can happen at four depths, and each has its own test: copied wording
(3.1), unusual phrases in common (3.2), the same ideas in different words (3.3), and the same story
in the same order (3.4). Section 3.5 then takes the three books named in the *CES Letter* one by
one, and 3.6 states what none of these tests can show.

All four tests read the text with its King James spans labelled, so that Bible quotation is counted
separately from everything else. All were run against the period library, not against a chosen
shelf, so that each result can be set beside what is ordinary for a book of its kind.

### 3.1 Copied wording

**Preparation.** The masked text was aligned against every eligible volume printed before it, with
its own copies left out. The aligner (passim) finds passages that match word for word or nearly so,
allowing for OCR errors (`docs/reuse-plan.md`; Amendment 10).

**Result.** 58 short passages in 47 earlier-catalogued volumes align with the Book of Mormon,
covering 0.52% of it. Seventeen of those volumes are later texts that quote the book under catalog
dates decades too early (section 2.2). Without them **0.16%** of the text remains shared with
earlier books, in 30 volumes, and all of it is short, loose religious stock phrasing (9 to 46
tokens). None of the 30 is a book proposed as a source. For scale, the same search finds that *The
Late War* (1816) shares 8.92% of its text with earlier books, mostly the War of 1812's own
documents, which it retells, and an 1821 volume of sermons 2.47%.

Beyond its King James passages, then, the Book of Mormon copies almost nothing word for word from
any earlier book in the library.

### 3.2 Rare shared phrases

**Preparation.** This is the test of Johnson and Johnson (2013), rebuilt on a full library. A
four-word phrase counts as rare if it occurs in at most 5 of the period's texts. A source's score
is the number of rare phrases it shares with the Book of Mormon per 10,000 of its own words, placed
against all 204,520 period volumes (`data/reuse/bom/rare.json`; Amendments 12-13). One correction
was needed before the test worked: rarity is counted by distinct text, not by volume, because nine
printings of *The Late War* in the library had made its own phrases look common (Amendment 8).

**Result.**

| Source | Rare shared phrases | Per 10,000 words | Rank of 204,520 | p (95% interval) | Passes the registered rule |
| --- | --- | --- | --- | --- | --- |
| *The First Book of Napoleon* (1809) | 12 | 5.45 | 63 | 0.0003 (0.0002-0.0031) | yes |
| *The Late War* (1816) | 22 | 3.86 | 131 | 0.0006 (0.0004-0.0017) | yes |
| *View of the Hebrews* (the 1823 edition's text) | 2 | 0.37 | 9,496 | 0.046 (0.017-1.0) | no |
| Spalding, *Manuscript Story* | 1 | 0.24 | - | 0.068 | no |

*The Late War* and *Napoleon* pass, as Johnson and Johnson reported. But both are imitations of
scripture, books written on purpose in King James style, and within that group they are not
unusual. Set beside the curated imitation-scripture works (a post hoc comparison), an 1829 reprint
of Jacob Ilive's *Book of Jasher* shares more than either (31 phrases, 7.99 per 10,000 words). That
reprint was printed in Bristol, and its circulation in America is not established; nobody proposes
it as a source. The shared phrases are battle and chronicle formulas. In all, 2,044 volumes pass
the same rule, most of them short pieces sharing a single phrase.

The reading is that the signal is real and belongs to a genre. A book written in imitation of the
King James Bible shares rare King James-like phrasing with another such book, whether or not either
author saw the other.

### 3.3 Paraphrase

**Preparation.** To find the same ideas in different words, the eligible library (278,796 volumes)
was cut into 128-word passages, 163 million of them, and each was turned into a vector by an
embedding model (a model that places passages with similar meaning near each other), chosen
beforehand on a known-answer paraphrase test (Amendment 14). Each Book of Mormon passage was
searched against all of them. A named source is then scored two ways: by its rank within its
subject group, and against a null of 500 volumes matched to it in genre and length. The registered
bar is the top 1% of that null. The genre label for each source's null was chosen after the
sources' ranks had been seen (Amendment 21, post hoc).

**Result** (`data/semantic/named.json`, `data/semantic/named_null.json`).

| Source | Rank in its subject group | Score (95% interval) | Null median | Null 99th percentile | Percentile in null | Stands out |
| --- | --- | --- | --- | --- | --- | --- |
| *View of the Hebrews* (1825) | 1 of 49 | 29.6 (28.0-31.3) | 14.6 | 45.0 | 84.6 | no |
| *View of the Hebrews* (1823) | 2 of 49 | 29.5 (27.9-31.1) | 9.2 | 38.4 | 94.0 | no |
| *The First Book of Napoleon* | 3 of 18 | 7.9 (6.9-9.0) | 0.1 | 8.8 | 98.4 | no |
| *The Late War* | 6 of 18 | 1.9 (1.4-2.4) | 0.4 | 14.6 | 79.8 | no |
| Spalding, *Manuscript Story* | 12 of 49 | 5.5 | - | - | - | no (by rank) |

*View of the Hebrews* comes first of the 49 books on the origin of the American Indians. That is a
real result: on its subject it is the closest book in the library. But the Book of Mormon is a
religious book, and 77 of 500 equally religious volumes of similar length score higher than *View
of the Hebrews* does. It sits at the 85th percentile, short of the top-1% bar. The two rankings
answer different questions, and both are reported: closest on its subject, not unusual for a
religious book.

**The whole library.** In the search over every volume, editions of Josephus take 14 of the top 20
places, and the registered rule flags 622 sources (`data/semantic/corpus_bom.json`). A count that
large mostly measures biblical register: many period books retell or expound scripture.

**Proposed parallels (exploratory, not registered).** Of the 500 parallels proposed in Rick
Grunder's *Mormon Parallels*, 139 match firmly to works in the catalog. Their sources score
slightly closer than other volumes (median percentile 91.0 against 87.4, p 0.087), as would be
expected from how they were chosen, and two firmly matched entries stand out, Josephus and the Owen-Campbell *Debate on the
Evidences of Christianity* (4 of 99 volumes; `data/semantic/grunder_ranks.json`).

**Reading the surfaced pairs.** Every pair of passages the searches brought up, 1,069 in all, was
then read and labelled as King James wording, period stock phrasing, or specific to the two texts.
The first reading was by one AI model; a second AI model, not shown the first label, reread every
pair called specific and a seeded tenth of the rest. Both readings are simulated review, not human
judgment. The first pass labelled 382 pairs King James wording, 685 stock phrasing and 2 specific;
the second pass called both of those common. **No pair is specific under both readings**
(agreement on the 104 pairs read twice 0.74, Cohen's kappa 0.51; `data/semantic/triage.json`).

### 3.4 Story order

**Preparation.** Two books can tell the same story with no sentence in common. Each 2,000-word
block of the Book of Mormon, and of each source, was reduced by a hosted AI model to at most 12
events with the characters named by role ("a commander writes to the governor"), giving 1,421
events for the Book of Mormon. The reduction was checked on 20 King James chapters read twice
(median agreement 0.92; the check covers biblical narrative, not period prose, and no
chance-corrected figure was computed). Two event sequences are then aligned, and each alignment is
tested against 1,000 shuffles of the source's order (Amendment 15; `data/semantic/skeleton/`).

**Checked first on a known retelling.** Josephus's *Antiquities* retells Genesis to Judges. The
test finds 108 events in the same order as the Bible (p 0.001). The registered control had three texts: the test also finds the *Testaments of the
Twelve Patriarchs* (8 events, p 0.003) and does not find Ilive's *Book of Jasher* (4 events,
p 0.75; `data/semantic/skeleton/controls.json`). It can find a retold story when the retelling
is close; it missed one of three.

**Result.** No book shares the Book of Mormon's plot. Among the 20 leading sources of the
paraphrase search the longest shared run is 9 of its 1,421 events (an edition of Josephus, p 0.24).
The named sources share 2 to 4 events each, none in an order that differs from chance: *View of the
Hebrews* 1823, 3 events (p 0.97) and 1825, 2 (p 1.0); Spalding, 4 (p 0.67); *The Late War*, 2 (p
1.0); *Napoleon*, 3 (p 1.0).

One book of the 49 in the Indian-origins group does reach the registered level: Benjamin Church's
*History of Philip's War* (p 0.008). The shared run is six events from one stretch of each book,
the common shape of military correspondence: a commander writes angrily to a governor, the governor
replies, troops march. With 49 books tested, one p-value that small arises by chance about 1 time in 3. It is reported as it came out and read as chance.

### 3.5 The Letter's three books, one by one

The *Letter to a CES Director* (Jeremy Runnells, 2013) is the most widely read critical
compilation. Its Book of Mormon section names three books as sources or parallels: *View of the
Hebrews*, *The Late War* and *The First Book of Napoleon* (`docs/ces-letter-books.md`, checked
against the Letter's text). Each claim was registered with its decision rule (`data/claims/register.yaml`): claims c01-c12
on 2026-10-18, before any result; c13-c17, which include Spalding and *The First Book of
Napoleon*, on 2026-11-06, before the blind run and after the borrowing results existed. Access scores run from 3 (documented within Joseph Smith's reach
before mid-1829) to 0 (no evidence of circulation in the region); availability is not use
(`data/access/access_table.csv`).

**3.5.1 *View of the Hebrews*** (Ethan Smith, 1823; second edition 1825). *The claim:* B. H.
Roberts' parallels, shown chart by chart: a Hebrew origin for the American Indians, buried records,
the scattering and gathering of Israel.

| Test | Result |
| --- | --- |
| Copied wording (3.1) | none |
| Rare phrases (3.2) | 2 shared, rank 9,496 of 204,520, p 0.046: does not pass |
| Paraphrase (3.3) | first of 49 on its subject; 85th percentile against 500 matched religious volumes (94th for the 1823 edition): does not stand out |
| Surfaced pairs | none specific |
| Story order (3.4) | 1823: 3 events, p 0.97; 1825: 2 events, p 1.0 |
| Ethan Smith as author | the one candidate the models recognise across his books, and not the closest to the text (section 7.4) |
| Access | 2 for both editions: the first reviewed in Utica in 1825, the second advertised there in 1826; no Palmyra notice found |
| Verdict (claim c02) | **contradicted**: the shared themes are real and are common to the period's writing on Indian origins; no wording, passage or plot is shared beyond that genre |

**3.5.2 *The Late War between the United States and Great Britain*** (Gilbert J. Hunt, 1816; the
Letter gives 1819, the year of a reissue for schools). *The claim:* shared phrasing.

| Test | Result |
| --- | --- |
| Copied wording | none |
| Rare phrases | 22 shared, rank 131 of 204,520, p 0.0006: **passes**; an imitation-scripture reprint shares more, and the phrases are battle and chronicle formulas |
| Paraphrase | 6th of 18 in its group, 80th percentile: does not stand out |
| Surfaced pairs | none specific |
| Story order | 2 events, p 1.0 |
| Hunt as author | section 7.5; at equal training dose a slice of *The Late War* is ahead of Joseph Smith's revelations on 63% of chunks at 590M and not at the smaller sizes (section 6.2), an effect of shared register |
| Access | 1: Palmyra advertisements of 1827-30 for a "Historical Reader" do not name an author |
| Verdict (claim c01) | **mixed**: the rare-phrase signal is real, as Johnson and Johnson found, and it is shared with other imitation scripture; no passage or plot is shared |

**3.5.3 *The First Book of Napoleon*** (1809). *The claim:* shared phrasing.

| Test | Result |
| --- | --- |
| Copied wording | none |
| Rare phrases | 12 shared, rank 63 of 204,520, p 0.0003: **passes** |
| Paraphrase | 3rd of 18 in its group, percentile 98.4, just under the bar: does not stand out |
| Surfaced pairs | none specific |
| Story order | 3 events, p 1.0 |
| Access | 0: a London imprint; no American printing or advertisement found |
| Verdict (claim c14) | **mixed**: dense rare phrasing of the same chronicle kind, and nothing else |

**3.5.4 Beside the Letter: Spalding's *Manuscript Story*.** The Letter does not name it; other
critics do, from 1834 on, so it gets the same treatment, labelled as not from the Letter. Only the
surviving manuscript can be tested.

| Test | Result |
| --- | --- |
| Rare phrases | 1 shared, p 0.068: does not pass |
| Paraphrase | 12th of 49: does not stand out |
| Surfaced pairs | one pair called specific on the first reading (elephant-like "Mammoons"), called common on the second |
| Story order | 4 events, p 0.67 |
| Spalding as author | section 7.3 |
| Access | 0: unpublished until 1885 |
| Verdict (claim c13) | **contradicted** as a source |

**What the Letter argues that this study does not test.**

- *The King James arguments:* that the text follows the errors of the 1769 edition, carries the
  translators' italic words, and reproduces Isaiah and the Sermon on the Mount. This study sets
  every King James span aside and does not ask which printing the text follows. One measurement of
  the italic words was made, but its own validity check failed, so by its registered rule it is not
  offered as a test (`docs/italics-plan.md`).
- *The place-name and reading-environment arguments:* Captain Kidd stories, an 1808 map of Africa,
  Vernal Holley's table of place names. Names and biography are outside these methods.

**Summary.** Of the three books the Letter names, two share an unusual density of rare phrases with
the text, and so does much of the imitation-scripture genre they belong to. None shares a copied
passage, a sequence of events, or a passage that two readings judged specific.

### 3.6 Limit

A test is informative about a question only if it gives different answers when the truth differs.
So each borrowing test was first run on texts where the truth is known: nine genuine period
translations of ancient texts, and three period compositions presented as ancient (Amendment 9).

| Test | Does it separate genuine translations from period books written to sound ancient? |
| --- | --- |
| Copied wording | no (p 0.96) |
| Rare phrases | no (p 0.93) |
| Paraphrase | no (p 0.50) |

None of them does. A genuine translation made in the 1820s and a book written in the 1820s to sound
ancient look alike to these searches, because both are period English and both lean on the King
James Bible. "No borrowing found" therefore describes the text: which period books share its
wording, its ideas or its plot, and how unusual that sharing is. It says nothing about the text's
origin, in either direction.

A second limit is practical. In poorly scanned volumes more than half of any real shared phrasing
is lost to OCR error (section 2.2), so the wording searches can miss borrowing from a badly scanned
book.

## 4. Earlier authorship studies, re-run

**Preparation.** Before any of our own methods touched the Book of Mormon, the published method of
each of five earlier studies was run again: on the authors' own data where they deposited it, and
on our texts. This is the one registered exception to the seal of section 2.4, and nothing from it
feeds a threshold or a model. The designs were fixed beforehand (`docs/prior-studies.md`), and the
full account is in `paper/replication-report.md`. The purpose is twofold: to show that our versions
of the older methods are faithful before using them as baselines in section 5, and to see how far
each published answer depends on choices its authors did not test.

| Study | Published finding | Our rerun | Reproduces? |
| --- | --- | --- | --- |
| Larsen, Rencher and Layton 1980 | the book's speakers differ; no block resembles a candidate | 17 speakers differ (p 8e-38); 4 of 215 blocks classified to a candidate | yes, both findings |
| Holmes 1992 | Joseph Smith's own writing separates; the prophets do not cluster by prophet; his revelations sit with the prophets | Joseph Smith 3 of 3 samples apart; prophets mixed; the 1835 revelations 3 of 3 with the prophets | yes |
| Jockers, Witten and Criddle 2008 | Rigdon first or second choice for 197 of 239 chapters | on their deposited data, the same 110 words and the same error rate (8.8%), Rigdon 169; on our candidate texts, Pratt 193, Rigdon 29 | **method yes, result no** |
| Schaalje, Fields, Roper and Snow 2011 | 175 of 239 chapters to an unobserved author | 225 of 239 to an unobserved author | yes, but the answer moves with sample length |
| Johnson and Johnson 2013 | *The Late War* has the densest shared rare phrasing after *The First Book of Napoleon* | *The Late War* in the top 0.05% (p 0.0004), but 30 books of 10,000 words or more are denser, mostly other imitation scripture | **partly** |

Every study reproduces with its own method. Two of the answers follow choices that were never
tested.

**The 2008 study: the answer follows the texts chosen to stand for each man.** Jockers and
colleagues used a closed list: every chapter must go to someone on it. We replaced one candidate's
samples at a time on their own data, leaving everything else as they had it
(`data/benchmark/replication_jockers_data.json`). Chapters for which each candidate is the first or
second choice:

| Samples replaced with ours | Rigdon | Pratt | Cowdery | Spalding | Isaiah-Malachi |
| --- | --- | --- | --- | --- | --- |
| none (their data) | 169 | 42 | 36 | 89 | 133 |
| Rigdon's | **92** | 91 | 37 | 84 | 156 |
| Pratt's | 163 | **137** | 21 | 34 | 116 |
| Cowdery's | 164 | 30 | **81** | 70 | 125 |
| Spalding's | 173 | 46 | 36 | **80** | 133 |

Their Rigdon sample is mostly a book of his revelations written in 1864, more than thirty years
after the Book of Mormon was printed. With other genuine Rigdon text in its place (print he signed),
his count falls from 169 chapters to 92. Pratt's and Cowdery's counts rise severalfold with our
samples of them. Spalding, the one candidate whose text is the same manuscript in both, barely
moves. The Book of Mormon did not change between rows; the samples did. A method that must name
someone names whoever's samples happen to sit nearest. One further defect surfaced during this run:
some of our own Pratt and Cowdery samples quote the Book of Mormon, and matching the book to text
that quotes it is circular. They were left out of every rerun (with them in, Pratt's 137 would be
186). The published study did not screen for this either.

**The 2011 study: "none of these" moves with sample length.** Schaalje and colleagues extended the
same classifier so that it may answer "none of the candidates", which removes the forced choice.
Their conclusion returns, more strongly, on our texts: 225 of 239 chapters fit nobody on the list.
But the method's rate of saying "none" depends on how long the candidates' samples are. On a
known-answer test in which "none" is always the right answer, the published method was wrong 80% of
the time with 1,000-word samples and 0% of the time with 10,000-word samples
(`data/benchmark/fidelity/REPORT.md`). An answer that swings from one extreme to the other with a
setting is a replication of the published conclusion, not independent evidence for it.

**The 2013 study: a real signal that belongs to a genre.** The rare-phrase result returns and is
examined in section 3.2: *The Late War* does stand out against the library as a whole, and does not
stand out against other imitations of scripture.

**What the reruns show.** The earlier studies agree where the question is whether texts *differ*:
the narrators differ in their small common words, and Joseph Smith's ordinary writing differs from
the book's prophets. They disagree where the question is *who wrote it*, and the reruns show why.
Three weaknesses recur: a forced choice among the listed candidates; biblical register mistaken
for personal style; and answers that follow the sample texts and settings chosen. The rest of this
paper is designed against those three, and the same older methods are carried forward as
baselines, scored on known answers beside our own, in the next section.

## 5. How good is each method? A scorecard on known answers

A method's answer about the Book of Mormon is worth what the method scores on texts whose authors
are known. This section gives that score for every method and every model size, side by side. The
methods are judged here only on known answers, never on the Book of Mormon.

**The methods.**

- *Our models:* one copy of a time-locked model trained further on each author's sample, scored by
  how much better it predicts a passage than the untouched model does (section 2.8), at 125M, 297M
  and 590M.
- *Burrows' Delta* and *Cosine Delta:* distances between texts in the frequencies of their most
  common words (Burrows 2002; the family used by Jockers et al. 2008).
- *General Imposters:* asks whether a text is closer to a candidate than to a crowd of other
  writers, over many random subsets of words (Koppel and Winter 2014).
- *ENSC:* the classifier of Schaalje et al. (2011), which may answer "none of the candidates".

The older methods are baselines. They are not combined with ours or with each other.

**Two questions, scored separately.** *Picking:* with the true author on the list, how often is he
ranked first? *"None of these":* with the true author taken off the list, how often does the method
still declare a match (a false match)? A method can be good at the first and poor at the second,
and the second is the one a claim of authorship needs. The benchmark, its three steps (110, 430 and
1,070 held-out tests) and the registered bar are described in section 2.7.

### 5.1 Picking the right author from a list

**Preparation.** Every method takes exactly the same held-out tests: 5,000-word passages from the
last quarter of each author's text, attributed among the roughly four authors of the passage's
task. For the 430 tests the older methods were first scored on their own draws of test passages;
to make paired comparison possible they were rerun on the very passages our models took (Amendment
52, post hoc). All figures below are on those shared tests.

**Right author, share of tests** (`data/benchmark/prior_work.json`, `alm_*_p2.json`,
`alm_*_p3.json`, `prior_work_classic_tails_p3.json`):

| Method | Part 1: 110 tests, 7 authors | BOM-75: 430 tests, 23 authors | The 32 new authors: 640 tests | All 55 authors: 1,070 tests |
| --- | --- | --- | --- | --- |
| Our models, 125M | 93.6% | 91.6% | 93.6% | 92.8% |
| Our models, 297M | 99.1% | 93.3% | 92.5% | 92.8% |
| Our models, 590M | 98.2% | 93.3% | 90.6% | 91.7% |
| Burrows' Delta | 95.5% | 81.6% | 76.3% | 78.4% |
| Cosine Delta | 81.8% | 80.0% | 78.4% | 79.1% |
| General Imposters | 74.5% | 63.0% | 77.2% | 71.5% |
| ENSC | 96.4% | 76.0% | 76.9% | 76.5% |

The 430 include Part 1's 110, and the 1,070 are the 430 and the 640 together. On their own draws of
passages from the same 23 authors, which may come from anywhere in an author's text, the older
methods score higher (Burrows 93.0%, Cosine 93.6%, General Imposters 79.8%, ENSC 92.8%;
`data/benchmark/part2/open_set.json`). The shared tests are harder because they are held apart from
everything a method learns from, and both sides took them.

**The unit is the author, not the passage.** Up to 20 passages come from each author, and passages
by one author tend to go right or wrong together, so 430 tests are not 430 independent trials. The
first comparison we ran (Amendment 52) counted passages, and every one of its twelve head-to-heads
came out in our models' favour with a corrected p below 0.0001. That overstated the certainty. A
simulated research check (an AI agent reading the whole project) raised the point, and we recounted
by author (Amendment 55, post hoc): an author counts for a side when that side wins more of the
passages on which the two methods disagree; the test is an exact sign test over authors who are not
tied, with Holm's correction for making twelve comparisons; beside it stands the gap in accuracy
with a 95% range from resampling authors. One author shows why this matters: the sermon writer
Samuel Spring alone supplies 19 of the 297M's 59 passage-level wins over Burrows' Delta.

**23 authors were not enough.** Counted by author on BOM-75's 23, our models were clearly better
than General Imposters and ENSC, and ahead of the two Delta methods without that being shown
(`data/benchmark/clustered.json`; cells are authors where ours is ahead - authors where the older
method is ahead, at 125M / 297M / 590M):

| Our models against | Authors ahead - behind | Holm p | Reading by the rule |
| --- | --- | --- | --- |
| Burrows' Delta | 11-3 / 11-2 / 10-2 | 0.15 / 0.13 / 0.15 | no difference shown |
| Cosine Delta | 11-3 / 11-2 / 10-2 | 0.15 / 0.13 / 0.15 | no difference shown |
| General Imposters | 16-1 / 16-0 / 15-0 | 0.003 / 0.0004 / 0.0007 | ours better |
| ENSC | 14-2 / 14-1 / 14-1 | 0.03 / 0.009 / 0.009 | ours better |

**32 more authors, with a stopping rule (Amendment 56, post hoc).** A lead of 11 authors to 2 that
is not significant needs more authors, not a different test. Before any further author was drawn,
the rule was written down: continue down the same seeded order in each genre, by the same
selection rules, until eight more authors per genre are kept; apply the same by-author test to all
55 authors; and add no authors after that, whatever the result. The stopping rule is what prevents
drawing until the answer comes out one way. The screen turned down 17 authors on the way
(translations, two people under one name, anthologies, a state government).

**All 55 authors** (`data/benchmark/clustered.json`):

| Our models against | Authors ahead - behind (tied), 125M | 297M | 590M | Holm p, 125M / 297M / 590M | Accuracy gap in points (95% range), 125M / 297M / 590M |
| --- | --- | --- | --- | --- | --- |
| Burrows' Delta | 25-4 (26) | 25-3 (27) | 24-4 (27) | 0.0004 / 0.0002 / 0.0005 | +14 (8-22) / +14 (8-21) / +13 (7-20) |
| Cosine Delta | 26-5 (24) | 26-4 (25) | 24-6 (25) | 0.0005 / 0.0003 / 0.0014 | +14 (7-22) / +14 (7-21) / +13 (6-20) |
| General Imposters | 33-3 (19) | 32-2 (21) | 30-4 (21) | 0.000002 / 0.000001 / 0.00006 | +21 (14-29) / +21 (14-29) / +20 (13-27) |
| ENSC | 30-4 (21) | 30-3 (22) | 29-4 (22) | 0.00006 / 0.00001 / 0.00008 | +16 (9-24) / +16 (9-24) / +15 (8-23) |

All twelve comparisons read "ours better". The largest corrected p is 0.0014, and every accuracy
range lies above zero.

**The 32 new authors alone repeat it.** Nobody had looked at these authors before the rule was
written, so they are an independent check. On them alone all twelve comparisons are again "ours
better" (Holm p from 0.009 to 0.038): against Burrows' Delta 14 authors to 1-2, Cosine Delta 14-15
to 2-4, General Imposters 15-17 to 2-4, ENSC 15-16 to 2-3. On their 640 tests our models are right
91-94% of the time and the older methods 76-78%.

**Passage counts, reported beside** (Amendment 52's unit, not the test). On the 430 tests the
passages only one side got right split, ours to theirs: against Burrows' Delta 58-15 / 59-9 / 59-9
at 125M / 297M / 590M; Cosine Delta 66-16 / 67-10 / 67-10; General Imposters 130-7 / 131-1 / 132-2;
ENSC 76-9 / 77-3 / 77-3. Most of the gap comes from the new genres: on 1820s sermons the 297M wins
28 passages to 0 against Burrows' Delta, on fiction 8 to 0, while on the Federalist papers and the
dictated task the two barely disagree.

**Part 1's 110 tests could not decide it.** There the methods disagreed too rarely. The 297M was
right on 4 tests that Burrows' Delta missed and wrong on none that Delta got (p 0.13); the 590M, 3
to 0; the 125M, 4 to 6. Against ENSC: 3-0, 2-0 and 3-6. This is where the earlier draft of this
paper said our models "tie with the best older methods". On more authors that reading does not
hold.

**Variants and other methods on Part 1.** Three registered variants of our method and the style
encoders (models that turn a passage into a vector meant to capture its style) were scored on Part
1 only (`data/benchmark/prior_work.json`, `open_set.json`):

| Method | Right author, 125M / 297M / 590M | False matches |
| --- | --- | --- |
| V1 (a ten times larger learning rate, as registered) | 93.6% / 93.6% / 62.7% | 45% / 47% / 82% |
| V2 (a classifier on top of the model), registered seed | 90.0% / 90.9% / 76.4% | 28% / 14% / 39% |
| V2, five further seeds, range (Amendment 42, post hoc) | 66-93% / 51-76% / 40-78% | 9-93% / 53-98% / 32-93% |
| V3 (the untouched model's internal states fed to the older methods), on 180 trials | 83.9% / 84.4% / 84.4% | 69% / 72% / 71% |
| Style encoders, 297M / 590M backbone, on 180 trials | 83.9% / 83.9% | 50% / 63% |

V1's registered setting damaged the 590M; at a rate chosen on held-out training text it is the main
method again (Amendment 41, post hoc). V2's registered figures were one lucky seed: the same
settings give false-match rates from 9% to 98% depending only on the random seed, so V2 carries no
weight anywhere in this paper. V3 and the style encoders were scored on a different draw of 180
trials and are compared within that set, not with the rows above.

**Summary of 5.1.** At picking the right author from a short list, period-trained language models
are better than every older method tested, at every size, counted by author on 55 authors, and
again on 32 authors nobody had examined beforehand.

### 5.2 Period training matters

**Preparation.** Is the gain from training on the period's English, or would any language model do?
The same procedure was run with GPT-2, a public model of similar size trained on modern internet
text, in place of our base models: same samples, same settings, same 110 tests
(`data/benchmark/alm_gpt2.json`, `alm_gpt2_medium.json`).

| Base model | Trained on | Right author | False matches |
| --- | --- | --- | --- |
| GPT-2, 124M | modern text | 90.0% | 92% |
| GPT-2, 355M | modern text | 94.5% | 85% |
| Ours, 125M | 1780-1830 only | 93.6% | 47% |
| Ours, 297M | 1780-1830 only | 99.1% | 38% |
| Ours, 590M | 1780-1830 only | 98.2% | 22% |

GPT-2 picks the right author nearly as often. The difference is in false matches: 85-92% for GPT-2
against 22-47% for the period models. A modern model fine-tuned on any early nineteenth-century
author learns, first of all, what early nineteenth-century English looks like, and then finds that
every period text fits. A model that already knows the period's English has only the author left
to learn. This comparison was run on Part 1's 110 tests only; as 5.4 shows, the period models'
own false-match rates are higher on the wider benchmark.

### 5.3 Writing in biblical style

The Book of Mormon is written in a biblical register, so the test that matters most is whether a
method still recognises a writer when he puts that register on.

**Preparation.** The imitation test takes authors who wrote both imitation scripture and ordinary
prose, trains each method on the ordinary prose only, and asks it to find the author of the
imitation scripture among 13 candidates (the authors themselves and 10 others). Three authors
qualify: Richard Snowden, Robert Dodsley and William Kenrick (`data/benchmark/imitation.json`).

**Result, by passage and by author.**

| Method | Passages right | Dodsley | Kenrick | Snowden | Authors with most passages right |
| --- | --- | --- | --- | --- | --- |
| Burrows' Delta | 13 of 18 | 2 of 5 | 0 of 2 | 11 of 11 | 1 of 3 |
| Cosine Delta | 13 of 18 | 2 of 5 | 0 of 2 | 11 of 11 | 1 of 3 |
| General Imposters | 11 of 18 | 0 of 5 | 0 of 2 | 11 of 11 | 1 of 3 |
| ENSC | 7 of 18 | 2 of 5 | 0 of 2 | 5 of 11 | 0 of 3 |
| Our models, 125M | 5 of 17 | 5 of 5 | 0 of 2 | 0 of 10 | 1 of 3 |
| Our models, 297M | 7 of 17 | 5 of 5 | 2 of 2 | 0 of 10 | 2 of 3 |
| Our models, 590M | 6 of 17 | 4 of 5 | 2 of 2 | 0 of 10 | 2 of 3 |
| Style encoders, 297M / 590M | 7 / 10 of 18 | 5 / 4 of 5 | 1 / 2 of 2 | 1 / 4 of 11 | 1 / 2 of 3 |

(The language models' text preparation yields one passage fewer of Snowden.)

By passage the Delta methods lead, 13 of 18 against the 297M's 7 of 17. By author the order
reverses: Burrows' Delta 1 of 3, the 297M 2 of 3. Both figures describe the same data. Snowden
supplies 11 of the 18 passages; the word-count methods recognise him every time and the language
models never, while on the other two authors it is the other way round. Each family is fooled by a
different writer. An earlier draft read the passage count as "the older methods see through
imitation better"; counted by author there is no such finding (corrected 2026-11-12, section 9).

On the 430-test benchmark, the imitation-scripture task (24 tests, four authors, same-register
training and test) gives a few disagreements, all in our models' favour: against Burrows' Delta 2-0,
2-0 and 1-0 at 125M, 297M and 590M; against ENSC 3-0, 3-0 and 2-0. That is too few to weigh.

**The ceiling is real.** More authors would settle it, and the library does not hold them. The
corpus-wide search for imitation scripture judged 1,349 candidate works (by two AI models with a
third breaking ties; a simulated reading) and found 18 works under 10 author names. Only 3 of those
authors left 10,000 words or more of other prose in the library: the three above
(`data/benchmark/dual_register.json`). Outside 1780-1830 most imitation scripture is anonymous
satire [CHECK: no results file found for the search outside the period; stated as in the outline].

**Reading.** Three authors are too few to judge either way. This paper makes no claim that our
models, or the older methods, can or cannot see through biblical style on the strength of this
test. A larger test of the same worry, on 553 authors [CHECK: count as given in the outline; no
results file] who left both sermons and other prose, was considered and not run (owner's decision,
2026-11-12). The worry it addresses, that a model follows the biblical style and not the person, is
instead tested directly on the Book of Mormon in sections 6.2 and 6.3, with samples of equal size
and with writers who could not have written the book.

### 5.4 "None of these"

**Preparation.** Remove the true author from the list and score the same passages. A method with a
match score declares a match when its best candidate scores above a threshold. The registered bar
sets that threshold where 95% of true authors clear it, and allows at most 5% false matches there
(section 2.7). Burrows' and Cosine Delta produce a ranking only and have no match score.

**No method passes.** False matches at the registered threshold:

| Method | Part 1, 110 tests | BOM-75, 430 tests | 32 new authors, 640 tests | BOM-75, each author held out in turn (Amendment 55, post hoc) |
| --- | --- | --- | --- | --- |
| Our models, 125M | 47% | 75% | 56% | 57% |
| Our models, 297M | 38% | 67% | 58% | 52% |
| Our models, 590M | 22% | 63% | 62% | 51% |
| General Imposters | 83% | 100% | 100% | |
| ENSC (its own "none") | 78% | 83% | 83% | |

(`data/benchmark/open_set.json`, `part2/open_set.json`, `alm_*_p3.json`, `clustered.json`. `prior_work.json`, `prior_work_classic_tails_p3.json`. The older methods' figures are on the same
tests as our models'; on their own registered draw of 500 passages they are 79% and 76%.) In the first three columns the
threshold is set on one half of the tests and applied to the other. In the last, the threshold for
each author's tests is set only from other authors, which is the stricter version: 51-57%.

The bar is 5%. The best figure anywhere in the table is 22%, on the narrowest benchmark, and on the
wider ones every method wrongly declares a match for more than half of the passages whose author is
absent.

**The whole trade-off, not one failed bar.** A threshold can be moved: stricter, and fewer strangers
are matched but fewer true authors are confirmed. Reporting only the registered point hides how
good or bad the method is elsewhere, so the full curve was computed, each author held out in turn
(Amendment 55, post hoc; 430 tests, 23 authors; `data/benchmark/clustered.json`):

| | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Area under the curve (1.0 is perfect, 0.5 is chance) | 0.91 | 0.91 | 0.89 |
| Equal-error rate (where the two kinds of error are equal) | 16% | 14% | 16% |
| Aiming at 5% false matches: false matches actually obtained on held-out authors | 5.6% | 5.8% | 6.0% |
| ... and true authors confirmed there | 61% | 53% | 38% |
| Aiming at 10%: true authors confirmed | 74% | 74% | 73% |
| At the registered threshold: true authors confirmed | 86% | 87% | 87% |

Read the other way round from the registered bar: if false matches are held to about 5%, our models
confirm between 38% and 61% of true authors and miss the rest. A "match" at that setting would mean
something; a "no match" would not, because a true author is missed about half the time.

**The standard fix was tried and failed.** Speaker verification, the field that decides whether a
voice belongs to a claimed speaker, has a standard remedy for exactly this: score normalisation.
Each model's score is put on a common scale by how that model scores other people (z-norm), or the
top candidate's normalised score is compared with the runner-up's (z-margin). An exploratory look
by the simulated research agent, splitting the data by test passage, suggested a large gain: about
three in four true authors confirmed at about 2% false matches
(`docs/research/2026-11-12-easy-wins-and-sota.md`). We then ran it with the rule written down first and the
split made by author, so that no passage by a tested author informs his own threshold (Amendment
55, post hoc). It covers 344 tests from 20 authors: the dictated task has one test author and so nothing to
normalise on, as the amendment says, and the Federalist task, with two, dropped out by the same
rule, which the amendment had not named.

| Aiming at 5% false matches | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Plain score (all 430 tests): false matches on held-out authors | 5.6% | 5.8% | 6.0% |
| z-norm: false matches on held-out authors | 21% | 17% | 19% |
| z-margin: false matches on held-out authors | 22% | 20% | 26% |

Normalisation does not carry over to authors it has not seen: aimed at 5%, it delivers 17-26%. The
split by passage had let each author's quirks leak into his own threshold. The plain score at least
holds the rate it aims for. Normalisation is therefore not a better algorithm here, and it is not
used.

**What this means for the rest of the paper.** Every method can rank candidates. None can say
"none of these" with a known, low error. This is why the opening statement of section 1 has two
halves. The rankings of sections 6 and 7 say whose writing is closest among those tested. They
cannot say that the author is among those tested, and no result in this paper should be read as
doing so.

### 5.5 Model size

**Preparation.** The three sizes were trained on the same text and take the same tests, so the
only difference is the number of parameters. The 1B that would have extended the series failed in
training (section 2.8).

| Measure | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Right author, 110 tests | 93.6% | 99.1% | 98.2% |
| Right author, 430 tests | 91.6% | 93.3% | 93.3% |
| Right author, 640 tests (32 new authors) | 93.6% | 92.5% | 90.6% |
| Right author from a list of all 55 authors (Amendment 58, post hoc) | 86% | 86% | 82% |
| False matches, 110 tests | 47% | 38% | 22% |
| False matches, 430 tests | 75% | 67% | 63% |
| False matches, 430 tests, each author held out | 57% | 52% | 51% |
| False matches, 640 tests (32 new authors) | 56% | 58% | 62% |

**Picking the author: the sizes tie.** On 110 tests the 297M is ahead of the 125M (6 tests to 0, p
0.03) and level with the 590M. On the larger sets no size leads consistently, and on the 32 new
authors the order is the reverse of the order of size. The by-author comparisons of 5.1 come out the
same at every size.

**Longer lists (Amendment 58, post hoc).** The benchmark's lists have about four authors. To see
whether a bigger model holds up better as the list grows, each of the 55 authors' tests was
attributed among lists of 2 to 55 authors (`data/benchmark/list_size.json`). Accuracy, averaged by
author, on random lists:

| List size | 2 | 4 | 12 | 30 | 55 |
| --- | --- | --- | --- | --- | --- |
| Our models, 125M | 98% | 95% | 91% | 88% | 86% |
| Our models, 297M | 97% | 95% | 91% | 88% | 86% |
| Our models, 590M | 96% | 93% | 87% | 84% | 82% |
| Burrows' Delta | 93% | 85% | 75% | 67% | 62% |
| Cosine Delta | 91% | 85% | 73% | 66% | 59% |
| ENSC | 91% | 83% | 70% | 61% | 54% |
| General Imposters | 89% | 80% | 68% | 56% | 49% |

Our models lose about 10 points between a list of 4 and a list of 55; the older methods lose 23 to
31. A bigger model does not extend the list: the 590M is the weakest of the three at every length.

**"None of these": bigger was better on two benchmarks and not on the third.** On Part 1's tests
false matches fall with size, from 47% to 38% to 22%. On BOM-75's 430 they fall from 75% to 67% to
63%, and the ranges of the 125M (71-79%) and the 590M (59-68%) do not overlap; nearly all of that
gain is in the first step. On the 32 new authors the order reverses (56%, 58%, 62%), with
overlapping ranges. So the evidence that size helps at "none of these" is real on the first two
sets and is not repeated on the newest and largest one. At every size and on every set the rate is
many times the 5% bar.

**Summary of the scorecard.** Judged on known answers:

| Job | Best | How good |
| --- | --- | --- |
| Picking the author from a short list | our models, any size | 92-93% of 1,070 tests on 55 authors, against 72-79% for the older methods; better than each of them counted by author (5.1) |
| Picking from a list of 55 | our models, 125M or 297M | 86% |
| Not mistaking period English for a person | period-trained models over a modern one | 22-47% false matches against 85-92% on the same 110 tests (5.2) |
| Recognising a writer in biblical style | not known | three authors; too small to judge (5.3) |
| Saying "none of these" | no method | no method near the 5% bar; normalisation did not help (5.4) |

## 6. Joseph Smith, the deep dive

Section 5 measured what each method can do on known answers: pick the right author from a list
(well), and say "none of these" (not reliably). This section applies the first of those to the Book
of Mormon and follows the one result that every later check kept returning to.

**What is ranked.** The scored text is 168 sealed chunks of the Book of Mormon (section 2.4; they
are the book cut twice, see 6.4a). For each chunk, each method orders the candidate samples from
closest to farthest. Two figures are reported per sample: *first*, the number of chunks on which it
is the closest sample, and *mean rank* over the 168 chunks (1 is closest). A rank is always among a
stated list; the lists differ between checks and are named each time.

**Three kinds of Joseph Smith text.** They are kept apart throughout:

- **The 1828-29 revelations**: 2,720 words after King James masking (3,039 model tokens), dictated
  in a scriptural voice in the same months as the book. This is his only surviving writing from
  before 1830 and the only Joseph Smith sample in the registered, confirmatory comparison.
- **The 1830-34 revelations**: 95 sections of Revelation Book 1, 65,222 words (60,375 after
  masking; 64,501 tokens). They were written after the book was dictated and enter only in 6.4.
- **Ordinary prose**: his non-revelatory writing of 1831-33 (letters and the 1832 history), about
  11,300 words pooled. Its two parts also appear as separate samples: dictated after 1830 (5,039
  words) and handwritten after 1830 (6,363 words).

All of them are under or near the 10,000-word floor of section 2.6, and none of the later samples
may stand in for his style before 1830 (the registered check of that substitution failed for every
method). His texts come from the Joseph Smith Papers transcripts.

**The registered outcome.** Under the rule fixed in advance, a candidate is supported only if two
independent method families call the text a match to that candidate on both halves of it. That did
not happen for anyone (H1a not supported). General Imposters and the style encoders called no chunk
a match; the candidate models (one copy of the period language model fine-tuned on each candidate
sample) called 10, 5 and 3 of 168 chunks a match at 125M, 297M and 590M, and 2, 2 and 0 once Book of
Mormon quotations were removed from the candidate samples (Amendment 43, post hoc; section 9). The
remaining calls are to the 1828-29 revelations (`data/blind/per_candidate.json`,
`data/blind/a43/per_candidate.json`). Because no method passed the benchmark's "none of these" bar
(section 5.4), neither the match calls nor their absence carry weight. What follows is ranking
only, and every step beyond the registered ranking is post hoc and labelled with its amendment.

### 6.1 With and without the revelations

*Amendment 44 (post hoc, on the owner's question after unblinding) scored his ordinary prose beside
the 1828-29 revelations. Amendment 53 (post hoc, a reporting step with no new model) reports the
whole ranking of candidate samples for every method, once with the 1828-29 revelations in the list
and once with them taken out.* The list is candidate samples only, no control groups: 11 samples
for the three classical methods and 12 for the style encoders and language models, which also
carry Oliver Cowdery's 1829 sample (section 7.1). Joseph Smith's ordinary prose appears three
times, pooled and as its two parts (`data/blind/a44/people.json`).

**With the 1828-29 revelations in the list.**

| Method | 1828-29 revelations: mean rank / first | Pooled ordinary prose: mean rank / first | Closest sample by mean rank |
| --- | --- | --- | --- |
| Language models 125M | 1.08 / 159 | 6.07 / 0 | 1828-29 revelations |
| Language models 297M | 1.00 / 168 | 6.32 / 0 | 1828-29 revelations |
| Language models 590M | 1.26 / 131 | 5.42 / 0 | 1828-29 revelations (Phelps second, 2.11 / 26) |
| Style encoder 297M | 1.14 / 149 | 4.73 / 0 | 1828-29 revelations |
| Style encoder 590M | 1.46 / 99 | 5.70 / 0 | 1828-29 revelations (Cowdery's 1829 sample second, 1.82 / 58) |
| Cosine Delta | 1.20 / 135 | 3.32 / 0 | 1828-29 revelations |
| General Imposters | 3.60 / 57 | 6.10 / 3 | Pratt (2.46 / 60) |
| Burrows' Delta | 7.68 / 25 | 2.71 / 59 | his pooled ordinary prose (Hunt is first on 56 chunks) |

Six of the eight rankings put the 1828-29 revelations first, including the language models at every
size (159, 168 and 131 of 168 chunks). General Imposters puts Parley P. Pratt narrowly ahead.
Burrows' Delta, which rests most heavily on common function words, puts the revelations tenth of
eleven and his ordinary prose first. Burrows' and Cosine Delta did not pass the benchmark bar and
count only as "which listed sample is closest" (Amendment 8).

**With the 1828-29 revelations taken out.**

| Method | Closest sample (mean rank / first) | Next | Pooled ordinary prose (mean rank / first; place in list) |
| --- | --- | --- | --- |
| Language models 125M | Cowdery, printed after 1830 (2.08 / 63) | Spalding (2.85 / 33) | 5.07 / 3; 6th of 11 |
| Language models 297M | Joseph Smith, handwritten after 1830 (2.02 / 70) | Phelps (2.34 / 46) | 5.32 / 0; 6th of 11 |
| Language models 590M | Phelps (1.30 / 133) | Joseph Smith, handwritten after 1830 (2.95 / 11) | 4.42 / 2; 4th of 11 |
| Style encoder 297M | Cowdery's 1829 sample (1.43 / 132) | Joseph Smith, dictated after 1830 (3.14 / 20) | 3.73 / 1; 3rd of 11 |
| Style encoder 590M | Cowdery's 1829 sample (1.18 / 145) | Joseph Smith, dictated after 1830 (3.01 / 3) | 4.70 / 0; 5th of 11 |
| Cosine Delta | his pooled ordinary prose (2.32 / 47) | Joseph Smith, dictated after 1830 (2.43 / 39) | first of 10 by mean rank; Hunt is first on more chunks (77) |
| General Imposters | Pratt (2.04 / 81) | Hunt (4.71 / 40) | 5.20 / 23; 4th of 10 |
| Burrows' Delta | his pooled ordinary prose (2.55 / 82) | Pratt (3.30 / 16) | first of 10 |

Without the revelations the answer depends on the method. Burrows' and Cosine Delta put his
ordinary prose first. The language models put it in the middle of the list, and each size names a
different sample first: Cowdery's printed writing, Joseph Smith's own handwritten prose, W. W.
Phelps. The style encoders name what is left of Cowdery's 1829 sample, which still shares short
phrases with the book (section 7.1). General Imposters names Pratt. Two notes on reading the table:
Cowdery's 1829 sample is in the language-model lists but its model received no training step
(section 7.1), so its place there carries no information; and every sample written after 1830 is
by someone who had read the book.

So the closeness of Joseph Smith to the book, as the language models and style encoders see it, is
a closeness of his revelations. It does not extend to his ordinary prose. The two word-frequency
methods see it the other way round.

### 6.2 Equal training dose

*Amendment 45, post hoc, raised by the simulated reviews after unblinding.* The 1828-29 revelations
are the smallest sample. A model fine-tuned on little text moves little from the base model, and
that alone could make it look close. So every larger candidate sample, and the pooled ordinary
prose, was cut into two seeded slices of exactly the revelations' size (3,039 tokens), one model was
trained per slice at every size (20 equal-dose models), and the revelations model was ranked among
them (`data/blind/a45/report.json`).

| Size | 1828-29 revelations first (of 168) | Mean rank among 21 |
| --- | --- | --- |
| 125M | 168 | 1.00 |
| 297M | 168 | 1.00 |
| 590M | 62 | 1.63 |

At 125M and 297M the revelations beat every same-sized sample on every chunk, so sample size does
not explain the ranking there. At 590M one slice of Gilbert J. Hunt's *The Late War*, a history of
the War of 1812 written in imitation King James English, is ahead of the revelations on 63% of
chunks. The other *Late War* slice is never ahead, and no other slice is ahead on any chunk.

### 6.3 Writers who could not have written it

*Amendment 49 fixed the rule before any placebo model was trained (after unblinding); Amendment 51
(post hoc, after the first placebo results) replaced one pair of slices per writer with up to
twelve.* If "closest" follows biblical register and not a person, then writers in that register who
cannot be the author should rank as high as the revelations. Six such writers were taken: authors
of imitation scripture or prophecy who died before September 1827 (Richard Snowden, Ezra Stiles,
Jacob Ilive, Joanna Southcott, Richard Brothers, Thomas Reader). A seventh, Levi H. Dowling (born
1844; *The Aquarian Gospel*, 1908), is reported separately. Each was given the equal dose of 3,039
tokens and ranked on the 168 chunks in one pool with Amendment 45's models and the revelations
model. The rule written first: if any of the six has a median rank at or better than the
revelations', "ranked first" is read as measuring register, not person.

With one pair of slices per writer (35 models ranked; `data/benchmark/part2/decoys_report.json`):

| Size | 1828-29 revelations, median rank | Best placebo writer | Rule triggered |
| --- | --- | --- | --- |
| 125M | 1 | Jacob Ilive, 5 | no |
| 297M | 1 | Jacob Ilive, 2.5 | no |
| 590M | 4 | Jacob Ilive, 1.5 | yes |

Jacob Ilive died in 1763. His *Book of Jasher* (1751; the corpus copy is an 1829 printing)
presents itself as a lost book named in the Bible and is written in imitation King James English.

A 3,039-token sample fits in one training batch, so a new random seed cannot change such a model
(6.5). The chance element is which 3,039 tokens are taken. Amendment 51 therefore trained up to
twelve non-overlapping slices per writer, spread evenly through each text, and counted the slices
whose median rank is at or better than the revelations model's:

| Writer (died) | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Jacob Ilive (1763) | 0 of 12 | 0 of 12 | 8 of 12 |
| Joanna Southcott (1814) | 0 of 12 | 0 of 12 | 0 of 12 |
| Richard Brothers (1824) | 0 of 8 | 0 of 8 | 0 of 8 |
| Richard Snowden (1825) | 0 of 12 | 0 of 12 | 0 of 12 |
| Ezra Stiles (1795) | 0 of 12 | 0 of 12 | 0 of 12 |
| Thomas Reader (1794) | 0 of 11 | 0 of 11 | 0 of 11 |
| *Levi H. Dowling (born 1844; reported separately)* | 0 of 12 | 0 of 12 | 9 of 12 |

At 125M and 297M none of the 67 slices by the six writers reaches the revelations. Ilive's best
slice ranks second at both sizes; his slices range from 2nd to 22nd at 125M and 2nd to 24th at
297M. At 590M eight of his twelve slices are at or above the revelations (range 1st to 12th), and
so are nine of twelve by Dowling, who was born fourteen years after the book was printed. At 590M,
then, "ranked first" does not pick out a person. At the two smaller sizes no writer who could not
have written the book gets there.

No size has earned more trust than another on this question: on known answers the three sizes pick
the right author equally often (section 5.5). The result is reported as a split. One limit cannot
be removed: the revelations are the whole of his surviving pre-1830 text, so that side of the
comparison is one fixed model and cannot be resliced.

### 6.4 His later revelations

*Amendment 54, post hoc, on the owner's question after Amendments 44, 45, 51 and 53 had been seen;
the rule was recorded before any later revelation was masked, trained or scored.* The 1828-29
sample is a few pages. Is it those pages that sit close to the book, or his revelation voice in
general? The 1830-34 revelations are every section of Revelation Book 1 dated after March 1830
whose title begins "Revelation": 95 sections (23 from 1830, 42 from 1831, 16 from 1832, 10 from
1833, 4 from 1834; `data/blind/a54/plan.json`). They were masked like every candidate sample.
Amendment 43's rule found no Book of Mormon quotation of 20 or more words in them; 80 shorter
shared runs were kept, as for every candidate [CHECK: the count of 80 shorter runs, longest 14
words, is from the blog and outline; no results file under `data/blind/a54/` records it]. The
registered comparison is unchanged: it still uses only text from before the book was published.

**Equal dose.** Twelve non-overlapping slices of the 1830-34 revelations, each the size of the
1828-29 sample and spread through the book in order, were each ranked in the pool of 6.3 (36
models; `data/blind/a54/report.json`).

| Size | 1828-29 revelations, median rank | 1830-34 slices, median rank | Slices at or above the 1828-29 model | Placebo writers' slices (6.3) |
| --- | --- | --- | --- | --- |
| 125M | 1 | 2 for eleven slices; 1 for the last-but-one (1833-34), where the 1828-29 model is 2 | 1 of 12 | Ilive 2-22; Dowling 2-5 |
| 297M | 1 | 2 or 3 for every slice | 0 of 12 | Ilive 2-24; Dowling 3-13 |
| 590M | 5 (4 in two pools) | 1 to 5 | 10 of 12 | Ilive 1-12; Dowling 2-7 |

At the two smaller sizes every slice, from April 1830 to 1834, lands second or third (second at
125M, except one slice that is first; second or third at 297M), next to the 1828-29
pages, where the placebo writers' slices range widely. At 590M the pool compresses and ten of the
twelve slices are at or above the 1828-29 model, as Ilive's and Dowling's are there.

**Whole sample.** Added as one sample to the list of 6.1 (mean rank / first, with the 1828-29
revelations also in the list):

| Method | 1830-34 revelations | 1828-29 revelations | Place of the 1830-34 revelations |
| --- | --- | --- | --- |
| Language models 125M | 1.00 / 168 | 2.08 / 0 | first |
| Language models 297M | 1.00 / 168 | 2.00 / 0 | first |
| Language models 590M | 1.01 / 166 | 2.24 / 2 | first |
| Style encoder 297M | 1.83 / 66 | 1.54 / 94 | second, behind the 1828-29 revelations |
| Style encoder 590M | 1.28 / 124 | 2.33 / 22 | first |
| Cosine Delta | 2.07 / 48 | 1.55 / 83 | second, behind the 1828-29 revelations |
| Burrows' Delta | 3.19 / 93 | 9.15 / 3 | first (the 1828-29 revelations are 11th of 12) |
| General Imposters | 5.42 / 41 | 3.87 / 27 | third (Pratt first, 3.05 / 50) |

The language-model comparison here is not a fair one: the whole 1830-34 sample is 21 times the
training text of the 1828-29 sample. It is shown for completeness; the equal-dose table is the
comparison to read.

**Reading, as stated before the run.** His revelation voice in general, not only the 1828-29
pages, is the closest writing in the candidate set. This cannot separate "the same man" from "the
same revelatory medium". And because these texts were written after he dictated the book, its
influence on them is possible and cannot be excluded; the absence of long quotation limits that
worry, it does not remove it.

### 6.4a Chunk length

*Amendment 55(c), post hoc, a reporting correction.* The 168 chunks are the same text cut twice:
121 chunks of 2,000 words and 47 of 5,000. A count "of 168" is therefore not 168 separate passages,
and every count is also given per length (`data/blind/a55_by_length.json`). Chunks on which the
1828-29 revelations rank first, in the list of 6.1:

| Method | Of 121 (2,000 words) | Of 47 (5,000 words) |
| --- | --- | --- |
| Language models 125M | 113 (93%) | 46 (98%) |
| Language models 297M | 121 (100%) | 47 (100%) |
| Language models 590M | 90 (74%) | 41 (87%) |
| Style encoder 297M | 104 (86%) | 45 (96%) |
| Style encoder 590M | 67 (55%) | 32 (68%) |
| Cosine Delta | 97 (80%) | 38 (81%) |
| General Imposters | 41 (34%) | 16 (34%) |
| Burrows' Delta | 20 (17%) | 5 (11%) |

The two lengths agree for every method; the longer chunks give the revelations a somewhat larger
share for the encoders and the 590M language models. The same holds without the revelations (for
example the 590M language models put Phelps first on 92 of 121 and 41 of 47) and for the 1830-34
revelations as a whole sample (first for the language models on 121 and 47 at 125M and 297M, 119
and 47 at 590M). The equal-dose and placebo results of 6.2 to 6.4 are medians and counts over all
168 chunks and are not broken down by length in the results files.

### 6.5 Seeds

*Amendment 50, recorded before the run, after unblinding.* Every candidate model was trained once.
To see whether one random seed misled, every model of the Amendment 43 run was retrained with five
further seeds at every size and rescored (`data/benchmark/part2/seeds_report.json`). This ranking
is over 15 samples: the 11 candidate samples and the four control samples (pseudo-biblical works,
1820s sermons, history, general prose), which are much larger. It is therefore a different list
from 6.1. Share of the 168 chunks on which a sample ranks first:

| Size | Sample | Original run | Five new seeds | Inside the range |
| --- | --- | --- | --- | --- |
| 125M | 1828-29 revelations | 12.5% | 4.8-38.7% | yes |
| 125M | pseudo-biblical control | 87.5% | 58.3-95.2% | yes |
| 297M | 1828-29 revelations | 75.0% | 63.1-79.8% | yes |
| 297M | pseudo-biblical control | 25.0% | 20.2-36.9% | yes |
| 590M | 1828-29 revelations | 52.4% | 53.0-59.5% | no, by one chunk |
| 590M | pseudo-biblical control | 41.7% | 38.1-47.0% | yes |
| 590M | W. W. Phelps | 6.0% | 0-2.4% | no |

No other sample ranks first on more than 3% of chunks in any run at any size. The ranking is stable across
seeds, with two misses in opposite directions: the original 590M run slightly understated the
revelations (88 chunks against 89 to 100) and overstated Phelps.

Two things must be said beside this table. First, the caveat: each Joseph Smith sample is small
enough to fit in one training batch, and the seed only changes the order of batches, so his five
"new" models are identical to the original. The ranges above show the other models moving around a
fixed revelations model. For such samples the real source of chance is which text is taken, which
is what 6.3 and 6.4 vary. Second, the table shows something the candidates-only lists do not: when
the control samples are in the list, the pseudo-biblical control, a large collection of the
period's imitation scripture, shares first place with the revelations, and takes most of it at
125M. That comparison is not at equal dose, and 6.2 and 6.3 are the controlled versions of it. It
is reported here because it is in the registered run.

### 6.6 His prose over time

*BOM-73; Amendment 46, post hoc, on the owner's question after unblinding; the method was filed
before any scoring.* Did his ordinary writing, and that of others who read the book, move toward
its style after 1830? This is a study beside the authorship test. Fixed in advance
(`docs/js-over-time-plan.md`): 21 Joseph Smith Papers documents of 1833-1844, his own hand and
his dictated documents as separate lines, revelations excluded; readers who followed the book
(Cowdery, Pratt, Phelps, Rigdon; signed items dated by issue); religious writers of the same years
with no documented reading of it (the *Methodist Magazine and Quarterly Review*, the *Evangelical
Magazine and Gospel Advocate*, the *Religious Intelligencer*, Charles G. Finney, Lyman Beecher);
and Alexander Campbell, who reviewed the book in 1831, as a line of his own. All texts were King
James masked, Book of Mormon quotations removed, and comparison blocks about Mormonism dropped.
The measure is the distance of each 2,000-word block to the masked Book of Mormon, by Burrows'
Delta, Cosine Delta and the 297M and 590M style encoders, each reported separately
(`data/js_time/results.json`).

Mean distance by period, 590M style encoder (lower is closer):

| Line | 1831-33 | 1834-36 | 1837-39 | 1840-44 | Blocks |
| --- | --- | --- | --- | --- | --- |
| Joseph Smith, own hand | 0.43 | (under the 2,000-word floor) | 0.65 | (under the floor) | 2 |
| Joseph Smith, dictated | | | 0.31 | 0.42 | 18 |
| Cowdery / Phelps / Rigdon | | 0.65 / 0.66 / 0.61 | Rigdon 0.58 | | 44 |
| Pratt | | | 0.55 | | 44 |
| Unexposed (*Methodist Magazine*) | 0.85 | 0.83 | 0.81 | 0.80 | 1,963 |
| Campbell | 0.77 | 0.76 | 0.80 | 0.81 | 2,226 |

By the rule fixed in advance, influence would be supported only if Joseph Smith's lines and the
readers' moved toward the book while the unexposed writers' did not. It is not supported. Both
Joseph Smith lines move away from the book's style over time, by all four measures. The only
reader with two periods, Rigdon, moves in different directions by different measures. The
unexposed writers are nearly flat.

Three limits govern this. The data are thin: his own hand is two blocks, and his dictated line is
one long history and one further block. Topic and genre change with the documents. And no ordinary
prose of his survives from before 1830, so there is no "before" to compare with. His dictated
prose sits closer to the book than any other writer's here; his own-hand block of 1837-39 (0.65)
does not, with Pratt at 0.55 and Rigdon at 0.58 in the same period. Closeness of level, unlike
direction, can come from shared subject (the church and its history).

The registered permutation test cannot be read for these lines and is not used. With one block per
period, shuffling period labels within a writer can only swap a line's two values, while it erases
the unexposed group's trend. The p-values are in the results file, flagged; the reading above
rests on direction, as the rule states it.

### 6.7 Two readings, not decided

The results of this section, side by side:

| Check | 125M | 297M | 590M |
| --- | --- | --- | --- |
| 1828-29 revelations first among candidate samples (6.1) | 159 of 168 | 168 of 168 | 131 of 168 |
| His ordinary prose, with the revelations out (6.1) | 6th of 11 | 6th of 11 | 4th of 11 |
| Revelations first at equal dose (6.2) | 168 of 168 | 168 of 168 | 62 of 168 |
| Slices by writers who could not have written it, at or above the revelations (6.3) | 0 of 67 | 0 of 67 | 8 of 67 (all Ilive); Dowling 9 of 12 |
| 1830-34 revelation slices at or above the 1828-29 model (6.4) | 1 of 12 | 0 of 12 | 10 of 12 |

The older methods add: the style encoders agree with the language models; Cosine Delta puts the
1828-29 revelations first and, without them, his ordinary prose; Burrows' Delta puts his ordinary
prose first either way; General Imposters puts Pratt first.

Two readings fit these results, and the tools here cannot choose between them.

**The same man.** The closest writing to the book, among the candidates, is Joseph Smith's, and it
stays closest when sample size is equalised, at two of three model sizes, against every writer
tested who could not have written the book. It is not confined to a few pages of 1828-29: twelve
slices of his revelations from 1830 to 1834 land in the same place. Two word-frequency methods
also put his ordinary prose first.

**The same revelatory medium.** What is close is his revelations, not his letters or history: for
the language models and style encoders his ordinary prose is in the middle of the list. The
revelations share with the book more than a possible author. They share a register (scripture in
King James English), a channel (dictated by Joseph Smith in the same years, taken down by the same
circle of scribes, unedited) and, for the 1828-29 sample, the same months. At 590M, writing in
that register by a man who died in 1763 and a man born in 1844 ranks as high. A revelation and a
book presented as scripture might resemble each other whatever their source.

Neither reading is the study's conclusion. The text was dictated by Joseph Smith on every account
of its origin, and no stylometric method separates the person who dictated a text from the person
who composed it. A test that could separate the readings would need his ordinary prose from before
1830, which does not survive, or revelations in the same medium by other people; section 14 adds
the second of these from the whole library.

## 7. The other candidates, one by one

For each candidate: the samples, how each method ranks them, and whether the language models can
recognise that person at all in a work they were not trained on. Numbers are from the run without
Book of Mormon quotations in the candidate samples (Amendment 43, post hoc;
`data/blind/a43/per_candidate.json`), with the registered run (`data/blind/per_candidate.json`)
where it differs.

**Every candidate sample, every method.** Mean rank among the candidate samples on the 168 chunks
(1 is closest) / chunks on which the sample ranks first. This list has 10 samples for the
classical methods and 10 or 11 for the others; it does not include Joseph Smith's pooled ordinary
prose, which is why some counts differ slightly from section 6.1. In this run no sample other
than Joseph Smith's 1828-29 revelations is called a match by any method at any size. In the
registered run, before the quotation rule, the candidate models also called 4 chunks for Pratt
(125M) and 4, 3 and 3 for Cowdery's 1829 sample at the three sizes; all were quotation of the
book (`data/blind/per_candidate.json`). The word counts in the table are the registered samples',
before that rule removed quotations.

| Sample (words after King James masking) | Burrows | Cosine | Gen. Imposters | Style 297M | Style 590M | Models 125M | Models 297M | Models 590M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Joseph Smith, 1828-29 revelations (2,720) | 6.7 / 29 | 1.1 / 148 | 3.9 / 59 | 1.1 / 149 | 1.5 / 99 | 1.1 / 159 | 1.0 / 168 | 1.3 / 131 |
| Joseph Smith, dictated after 1830 (5,039) | 3.4 / 41 | 3.0 / 0 | 6.0 / 3 | 3.8 / 2 | 3.9 / 0 | 8.6 / 0 | 7.6 / 0 | 6.2 / 0 |
| Joseph Smith, handwritten after 1830 (6,363) | 4.5 / 21 | 3.8 / 0 | 6.1 / 4 | 5.5 / 0 | 7.4 / 0 | 7.0 / 0 | 3.0 / 0 | 3.9 / 0 |
| Oliver Cowdery, 1829 Articles (844 tokens after Amendment 43) | - | - | - | 2.3 / 12 | 1.8 / 58 | not scorable | not scorable | not scorable |
| Oliver Cowdery, printed after 1830 (44,338) | 5.9 / 0 | 7.8 / 0 | 6.3 / 0 | 7.7 / 0 | 6.6 / 0 | 3.0 / 7 | 5.0 / 0 | 4.0 / 0 |
| Sidney Rigdon, after 1830 (21,516) | 8.3 / 0 | 5.7 / 0 | 5.6 / 1 | 6.3 / 0 | 7.4 / 0 | 8.2 / 0 | 9.0 / 0 | 7.3 / 0 |
| Solomon Spalding (41,833) | 5.5 / 0 | 8.6 / 0 | 6.7 / 0 | 10.0 / 0 | 10.6 / 0 | 3.7 / 0 | 4.4 / 0 | 6.5 / 0 |
| Ethan Smith (277,391) | 6.2 / 2 | 9.9 / 0 | 7.0 / 0 | 9.3 / 2 | 9.0 / 0 | 10.0 / 0 | 10.0 / 0 | 10.0 / 0 |
| Gilbert J. Hunt (56,956) | 5.5 / 49 | 4.4 / 20 | 5.1 / 35 | 5.4 / 2 | 3.9 / 11 | 4.5 / 0 | 4.7 / 0 | 5.0 / 11 |
| Parley P. Pratt, after 1830 (91,478) | 3.0 / 25 | 3.9 / 0 | 2.2 / 66 | 4.9 / 1 | 4.5 / 0 | 4.4 / 2 | 7.0 / 0 | 8.8 / 0 |
| W. W. Phelps, after 1830 (28,479) | 6.1 / 1 | 6.7 / 0 | 6.1 / 0 | 9.8 / 0 | 9.4 / 0 | 4.6 / 0 | 3.3 / 0 | 2.1 / 26 |

Two cautions apply to every row. A sample written after 1830 is by someone who had read the book,
so closeness may come from reading it. And distance is not clean evidence either: letters, sermons
and histories differ in genre from a scriptural narrative, whoever wrote them.

**Can the models recognise the person in a different work?** *Amendment 49, recorded before any of
these models was trained, after unblinding.* Each candidate model had been trained on all of that
candidate's works together. For this check a model was trained on a candidate's works with one
left out, and passages from the work left out (up to twenty 5,000-word windows) were scored by
that model and by every other candidate's model. A window is *recognised* when its own author's
model scores closest. A candidate's rate is the share of recognised windows over all the works
left out in turn (`data/benchmark/part2/decoys_report.json`).

| Candidate | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Ethan Smith | 77 of 77 | 77 of 77 | 74 of 77 |
| Parley P. Pratt | 45 of 52 | 36 of 52 | 27 of 52 |
| Oliver Cowdery | 2 of 22 | 5 of 22 | 2 of 22 |
| Sidney Rigdon | 0 of 12 | 0 of 12 | 0 of 12 |
| W. W. Phelps | 0 of 20 | 0 of 20 | 0 of 20 |

Hunt and Spalding have one work each and cannot be tested this way; Joseph Smith's cross-sample
result is section 6.1. Only Ethan Smith is recognised across his books at the 90% the rule
required, and he is the candidate the methods place farthest from the Book of Mormon. For Cowdery,
Rigdon and Phelps the models learned a book or a periodical, not the person; for Pratt the result
falls with model size. So a low rank for those four does not show that the person is unlike the
text. Under the rule fixed in Amendment 47, a candidate can be reported as "not a match" only if a
method passes the benchmark, the candidate is recognised across works, and no chunk matches. No
method passes (section 5.4), so every candidate below is "not excluded"; this table adds that for
four of the five, even a passing method would not have been enough.

### 7.1 Oliver Cowdery

**Samples.** His 1829 "Articles of the Church of Christ" (1,310 words) and his printed writing
after 1830 (44,338 words, mostly the *Messenger and Advocate*). He was the principal scribe of the
text.

**The quotation leak.** In the registered run the 590M candidate models ranked his 1829 sample
closest on 119 of 168 chunks, and the 590M style encoder on 102. That sample is 40% word-for-word
Book of Mormon text: it copies the sacrament prayers and the instructions for baptism. The seal
that kept the book out of every model's training had not been applied to the candidate samples.
Amendment 43 (post hoc, found after unblinding) removed quotations from every candidate sample:
passages of 20 or more shared words written after the matching passage was dictated
(`docs/bom-overlap-analysis.md`; section 9). Without them the ranking disappears.

**Results after the correction.** What is left of the 1829 sample is 844 tokens, shorter than one
1,024-token training sequence, so its candidate model received no training step and the language
models cannot score it. The style encoders need no training on the sample and still rank the
remainder second (mean rank 2.3 and 1.8; first on 12 and 58 chunks), and first when Joseph
Smith's 1828-29 revelations are taken out (section 6.1). That remainder still shares 7.8% of its
words with the text in short phrases, much of it written in the same weeks, so the encoders'
ranking cannot be separated from shared wording. His printed writing after 1830 is mid-list for
most methods (mean rank 3.0 to 7.8); with the 1828-29 revelations out, the 125M language models
put it first (63 chunks), the 297M and 590M models do not (8 and 3). Cross-work recognition: 2, 5
and 2 of 22.

### 7.2 Sidney Rigdon

**Sample.** Printed writing after 1830 (21,516 words). The candidate set holds no Rigdon text from
before 1830.

**Results.** Mean rank 5.6 to 9.0, in the lower half for most methods; first on one chunk by
General Imposters and none otherwise. The Rigdon lead reported by Jockers and colleagues in 2008
does not return when their method is run on other genuine Rigdon text (section 4). Cross-work
recognition: 0 of 12 at every size, so the language models' low rank says little about him.

### 7.3 Solomon Spalding

**Sample.** The surviving *Manuscript Story* (41,833 words; published after his death).
Only this manuscript can be tested; the argument that a second, lost manuscript existed is
outside what text can settle.

**Results.** Mean rank 3.7 to 10.6. The 125M and 297M language models place him in the upper half
(3.7 and 4.4; with the revelations out, second at 125M with 33 chunks first), the style encoders
last or next to last. He has one work, so cross-work recognition is not testable. As a source, no
copied passage, phrase density or plot is shared (section 3.5).

### 7.4 Ethan Smith

**Sample.** *View of the Hebrews* and his other books (277,391 words), the largest sample.

**Results.** Last or near last for every method (mean rank 6.2 to 10.0; last for the language
models at every size). He is also the one candidate the language models demonstrably know: 77 of
77 windows from a book left out of training are recognised at 125M and 297M, 74 of 77 at 590M. His
is the only case in this section where "far from the text" rests on a model shown to recognise the
person. It is still not a registered exclusion, because no method passes the "none of these" bar.
As a source, section 3.3 and 3.5.

### 7.5 Gilbert J. Hunt

**Sample.** *The Late War between the United States and Great Britain* (1816) and his other
writing (56,956 words).

**Results.** Mid-list by most methods (mean rank 3.9 to 5.5); first on 49 chunks by Burrows'
Delta, 35 by General Imposters, 20 by Cosine Delta and 11 by the 590M language models and the 590M
style encoder. With Joseph Smith's 1828-29 revelations out, Cosine Delta puts him first on more
chunks than anyone (77). At equal training dose at 590M, one slice of *The Late War* is ahead of
the 1828-29 revelations on 63% of chunks (section 6.2). *The Late War* is imitation King James
prose, so Hunt's showing is the register effect of section 6.3 seen in a candidate. He has one
work, so cross-work recognition is not testable. As a source, section 3.2 and 3.5.

### 7.6 Parley P. Pratt

**Sample.** Printed books after 1830 (91,478 words). Before Amendment 43 his books carried long
Book of Mormon quotations (*A Voice of Warning* 4.8% shared, *Mormonism Unveiled* 3.1%). He had
no documented contact with Joseph Smith before September 1830, after the book was printed.

**Results.** General Imposters ranks him first more often than any other sample (66 chunks,
against 59 for the 1828-29 revelations and 66 for Joseph Smith's three samples together; 60
against 57 in section 6.1's list, and 81 with the revelations out). Burrows'
Delta has him closest by mean rank (3.0). The language models place him lower as they grow (mean
rank 4.4, 7.0, 8.8). Cross-work recognition falls the same way: 45, 36 and 27 of 52. In the
registered run, before his quotations were removed, the 125M models ranked him first on 57 chunks;
after, on 2.

### 7.7 W. W. Phelps

**Sample.** Printed writing after 1830 (28,479 words). His newspaper from before 1830, the
*Ontario Phoenix*, is not digitised anywhere we could find, and his signed items in the *Lake
Light* (1827-28) were too few to extract. He had no documented contact with Joseph Smith before
the text was finished.

**Results.** The 590M language models rank him second (mean rank 2.1; first on 26 chunks), and
first when the 1828-29 revelations are taken out (133 chunks). The other sizes and methods do not
agree (297M mean rank 3.3 and no chunk first; the encoders 9.4 to 9.8). The seed check qualifies
the 590M figure: five further seeds give him first place on 0 to 2% of chunks where the original
run gave 6% (section 6.5). Cross-work recognition: 0 of 20 at every size.

### 7.8 Everyone else in the library

The eight candidates are the people someone has proposed. The registered design also asked whether
any author nobody has proposed stands out (the author sweep; BOM-39 and BOM-47; Amendment 28,
recorded before any author was indexed).

**Preparation.** Every named, non-corporate author in the 1780-1830 library with at least 10,000
words: 23,872 authors. Each has a profile of up to twenty 1,000-word blocks drawn across their
works, King James masked. Two signals, kept separate: Cosine Delta on the 300 most frequent words,
and the style encoder's distance. The query is the 22 chunks of 5,000 words in the discovery half
of the text. A *lead* is an author closer than the 5th percentile of the best wrong author's
distance under both signals. Two things were measured before the Book of Mormon was scored. First,
on 200 books of known authorship, with each author's profile rebuilt without the book: how often
the true author comes first among all the authors, with a bar of 70% for the sweep to count as
usable. Second, how many false leads the rule produces on those 200 books: 0.035 per query. A
plausibility gate (right period, and right place or documented access; Amendment 40, fixed before
any lead was seen) would pass about one random author in ten, so about 0.0035 false leads per query
would survive it.

**Result.** No lead: 0, against 0.035 expected by chance (`data/blind/unblinded.json`,
`data/sweep/calibration.json`). The nearest authors are writers of prophecy and Quaker testimony
(John Wroe, George Fox, William Sewel), none near either threshold.

**What that is worth.** On the 200 known books the true author came first 27% of the time by
Cosine Delta and 30% by the style encoder (35% by either), against the 70% bar. The sweep failed
its own usability test. It cannot name anyone, and its silence cannot rule anyone out: on
this evidence an author of the Book of Mormon sitting in the library would usually not have come
first. It
says only that no unproposed author stands out by these two signals. The language models, the best
tool at picking an author from a list (section 5.1), were not run here: they need one fine-tuned
model per author, 23,872 models.

Section 14 returns to the whole library with better tools.

## 8. Dating and internal voices

Two questions about the text itself, apart from who wrote it. When does its language date from?
And do its narrators differ from one another the way different authors do?

### 8.1 Dating

**Preparation.** Three models place a passage on a scale from 1473 to 1830. A *grammar model*
reads 61 grammatical features taken from the scholarly literature on early modern English and
fixed before fitting; it alone decides the registered hypothesis (H3). A *lexical model* reads
word frequencies with grammar words removed. A *transformer cross-check* reads the 297M period
model's internal states. All three were trained on dated text from 1473 to 1830 and checked on
authors they had never seen: mean errors of 23, 13 and 10 years. Writing in imitation of the King
James Bible moves the grammar model about 53 years early and the transformer not at all. The
decision rule (Amendment 19, post hoc, fixed before any Book of Mormon text was scored) reads the
median year of each segment: H3a if more than half fall in 1780-1830, H3b if more than half fall
before 1700.

**Results.** The grammar model places 78% of the text's 215 segments before 1700 and 7% in
1780-1830 (median 1661): H3b. The lexical model (median 1736) and the transformer (median 1755)
place the majority in neither window (`data/blind/unblinded.json`).

The registered comparison H3c asked whether the text dates like the period's own imitation
scripture. It does not: the text dates earlier than the 25 pseudo-biblical control volumes of
1780-1830 (grammar model, mean 1661 against 1734; lexical model, 1738 against 1794; permutation
p 0.0001 for each). With each book of the text counted as one unit (12 books) the result stands
(p 0.0025 and 0.0001; `data/dating/h3c.json`). So part of the early date is biblical register, but
the text is more archaic than the period's other biblical imitations, and the transformer, which
imitation did not move in validation, still places it before them.

**Cautions.** Seven of the 25 period imitations are themselves placed in the early modern window
by the grammar model, so the genre can reach it. An early modern placement is predicted alike by
an early modern source, by imitation of one, and by the King James register. The models learned
the English of 1780-1830 from edited print, so unedited New York and New England vernacular may
read to them as archaic; we had no control sample of such vernacular. And hand-keyed text reaches
the 1780-1830 window less often than scanned text of the same years (55% against 83% of 1780-1809
segments); the Book of Mormon text is keyed, which alone could pull its dates earlier. On the
known-answer set of section 3.6 the dating models do not separate genuine translations of ancient
texts from period compositions presented as ancient, so an early date says nothing about which of
those the text is.

### 8.2 Internal voices

**Preparation.** The classical classifier that separates real authors with 0.96 accuracy on the
benchmark (leave-one-out Cosine Delta) was asked to sort the text's 2,000-word chunks by narrator,
by dictation order, and by scribe, each against shuffled labels (`data/benchmark/scribes.json`).

| Grouping | Accuracy | By chance | p |
| --- | --- | --- | --- |
| Narrator (Nephi, Jacob, Mormon, Moroni; 121 chunks) | 0.744 | 0.277 | 0.001 |
| Dictation order (first or last dictated; 124 chunks) | 0.758 | 0.502 | 0.001 |
| Scribe | not testable | | |

The narrators differ above chance and well below the level that separates different real authors:
by the registered rule they are **not separable as different authors** (H1c). Narrator and
dictation order are confounded in the text, since the books attributed to different narrators
were dictated at different times, and this test cannot pull them apart. Raw accuracy is about the
same for the two groupings; corrected for chance, narrator separates somewhat better (0.645
against 0.514). The differences therefore follow both who narrates and when a passage was
dictated.

Scribe could not be tested. The surviving original manuscript shows three hands in the scored
text (Oliver Cowdery, John Whitmer and an unidentified third scribe, the last two only in 1
Nephi); only Cowdery's fills three or more continuous 2,000-word chunks (11 of them), and most of
the original manuscript is lost.

**The manuscripts.** The corrections in the two manuscripts show how the text was taken down.
Corrections of one word to another that sounds the same are 6 to 12 times more common in the
dictated original than in the printer's copy made from it, with the same scribe in both (Fisher
p 2e-9; `data/manuscript/summary.json`). A simulated check of the page photographs by an AI model
confirms the ratio. The tests treat corrections on one page as independent, which overstates
their certainty. The original was written by ear and the copy by eye. Every account of the text's
production already holds that it was dictated, so this does not discriminate between accounts,
and it does not say whether the words were composed, recited or read aloud.

## 9. Corrections and robustness

The registered run is the main record (git tag `blind-registered-2026-11-10`). Everything in this
section was found or decided after some result existed. Each step is labelled, dated in section
11 of the pre-registration, and reported beside the registered result, not in place of it.
Amendments up to 46 were filed on OSF; from 47 on they are recorded in the repository only,
committed before the results they govern, so the commit time is the record.

### 9.1 Every post hoc step

"Post hoc" here means decided after a relevant result had been seen. Several of the later steps
had their rule written down before their own run (noted in the third column), but all of them
came after unblinding and were prompted by what the unblinded results showed.

**After unblinding (2026-11-10 onward).**

| Step | Amendment | Decided after | What changed | Effect |
| --- | --- | --- | --- | --- |
| The quotation leak | 43 | unblinding, and after seeing which samples were affected | Book of Mormon quotations (passages of 20+ shared words written after the matching passage was dictated) dropped from candidate samples; candidate models retrained, sealed set rescored | Cowdery's first-place ranking (119 of 168 chunks at 590M) removed; the 1828-29 revelations first for the language models on 159, 168, 131 chunks; match calls 10 / 5 / 3 become 2 / 2 / 0 (9.2) |
| Joseph Smith's ordinary prose scored | 44 | unblinding, on the owner's question | his non-revelatory writing of 1831-33 pooled and scored beside the 1828-29 revelations | ordinary prose mid-list for the language models and encoders, first for Burrows' Delta (6.1) |
| Equal dose | 45 | the simulated reviews | every candidate sample refitted on slices of exactly the revelations' 3,039 tokens | revelations first on 168 of 168 chunks at 125M and 297M; 62 at 590M, a *Late War* slice ahead on 63% (6.2) |
| His prose over time | 46 | unblinding, on the owner's question; method filed before scoring | distance of his 1833-44 prose, readers' and unexposed writers' to the book, by period | no movement toward the book's style; the registered permutation test unreadable and not used (6.6) |
| The synthesis placebo | none | the simulated reviews | the registered synthesis run on the candidates' own held-out passages | it leans to "not in set" on true authors' text; its 0.744 carries little information (9.3) |
| Registered feature sets not run | none (deviation D3) | the simulated reviews | found: character n-grams, part-of-speech n-grams and the content-word set were registered for the classical methods and never run on the benchmark or the sealed set; only most-frequent words were | not known; whether to run them post hoc is undecided (`paper/deviations.md`) |
| A larger benchmark and its pass rule | 47, 48 | unblinding; rule and draw fixed before scoring | 430 held-out tests on 23 authors in place of 110; pass rule and stopping rule for larger models | no method passes; the best false-match rate is 63% (590M) where the 110 tests had given 22% |
| Cross-work decoys and register placebo | 49 | unblinding; rule fixed before any model was trained | each candidate tested on a work left out of training; six writers who died before September 1827 ranked at equal dose | only Ethan Smith recognised across works (7); the register rule triggered at 590M only (6.3) |
| Seeds | 50 | unblinding; rule fixed before the run | every candidate and control model retrained with five further seeds | ranking stable; two misses at 590M in opposite directions; one-batch models cannot vary (6.5) |
| Slices | 51 | the first placebo results | up to 12 slices per placebo writer in place of one pair | 0 of 67 slices reach the revelations at 125M and 297M; Ilive 8 of 12 and Dowling 9 of 12 at 590M (6.3) |
| The 430-test head-to-head | 52 | Part 1's paired results and the 430-test totals | the four older methods run on exactly the 430 tests the language models took; McNemar test per pair, Holm-corrected | all 12 comparisons "ours better" by test (for example 297M against Burrows' Delta 59 to 9); corrected by Amendment 55 |
| The whole ranking with and without the revelations | 53 | the language-model rankings had been computed from saved scores | reporting only: every candidate sample's rank for every method, with the 1828-29 revelations in and out | section 6.1's two tables |
| The later revelations | 54 | Amendments 44, 45, 51, 53; rule fixed before any text was prepared | his 1830-34 revelations as a whole sample and as 12 equal-dose slices | every slice 2nd or 3rd behind the 1828-29 revelations at 125M and 297M; 10 of 12 at or above them at 590M (6.4) |
| Counting by author | 55(a) | Amendment 52, and a simulated research review by an AI agent that had already shown the by-author counts | the unit of the head-to-head becomes the author (sign test, Holm-corrected, intervals from resampling authors) | on 23 authors: ours better than General Imposters and ENSC; ahead of Burrows' and Cosine Delta on 10-11 authors to 2-3, not significant (Holm p 0.13-0.15) |
| The normalised curve | 55(b) | the same review, whose exploratory split by test had suggested a large gain | the whole trade-off curve reported; score normalisation (z-norm, z-margin) tested with each author held out | normalisation fails on new authors (17-26% false matches at a 5% target); the raw score holds its target (about 6%) and confirms 38-61% of true authors; the registered bar is unchanged and still failed (51-57% false matches) |
| Chunks by length | 55(c) | the same review | every count over the 168 chunks also given for the 121 and the 47 | the two lengths agree (6.4a) |
| 32 more benchmark authors | 56 | Amendment 55's by-author result; draw rule and stopping rule fixed first | 32 authors added by the original rules; the by-author test on all 55 | all 12 comparisons "ours better" (Holm p at most 0.0014); the 32 new authors alone repeat it (5.1) |
| The imitation-test correction | none (2026-11-12) | a by-author recount | the imitation test's passages come from three authors; counted by author, Burrows' Delta gets 1 of 3 and the 297M models 2 of 3, where by passage it was 13 of 18 against 7 of 17 | "the models are weaker under imitation" withdrawn; the test is too small to judge either way (5.3) |

**Before unblinding.**

| Step | Amendment | Decided after | What changed | Effect |
| --- | --- | --- | --- | --- |
| Delta as closed-set evidence; rarity by text | 8 | the benchmark | Burrows' and Cosine Delta kept only for "which listed candidate is closest"; rare phrases counted by distinct text, not by printed copy | *The Late War* becomes visible to the rare-phrase rule |
| Dating by segment medians | 19 | dating validation, before any Book of Mormon scoring | H3a and H3b decided on median years, since the registered interval rule passed only 14% of genuine period text | none on the Book of Mormon result |
| Semantic controls | 20, 21 | the semantic positive control | a known own-copy excluded; named sources tested against matched nulls | one control passes; *View of the Hebrews* placed at the 85th percentile |
| The open-set threshold | 25 | the benchmark | match threshold set at the 5th percentile of true authors | the false-match rates of section 5 (General Imposters 0% becomes 62%) |
| A disclosed leak | 31 | a smoke test | one Cosine Delta imitation figure was seen before the imitation rule was registered | none |
| Both match rules reported | 33 | the benchmark | both readings of the match rule and a false-match ladder reported | none (both shown) |
| The 1B model replaced | 38, 39 | an unrecoverable loss spike in training | a 590M model with QK-norm takes the 1B's place | one model size |
| The sweep's plausibility gate | 40 | the gate, read literally, passed 94% of random authors; before any lead was seen | gate read as period and (place or access) | none (no lead) |
| Variant learning rates | 41 | the 590M benchmark | variants V1 and V2 rerun at a rate chosen on held-out training text | V1 at that rate equals the primary method |
| The V2 seed fluke | 42 | V2 moved when rerun on another machine | V2, a variant of the language-model method, rerun with five further seeds per size | its registered 297M run had the lowest false-match rate of any method (14%) and was first reported as the best; across seeds it ranges 53-98% at 297M and 9-93% at 125M. V2 carries no weight |

### 9.2 The quotation leak in detail

After unblinding, the 590M candidate models ranked Oliver Cowdery's 1829 sample closest on 119 of
168 chunks. That sample, his "Articles of the Church of Christ", is 40% word-for-word Book of
Mormon text. Parley P. Pratt's books quote it at length too. The seal had been enforced on
training data and not on candidate samples.

Every run of words a candidate sample shares with the text was classed by a rule fixed before the
matches were read: biblical; period stock phrasing; written before the matching passage was
dictated; written in the same weeks; or written after it (`docs/bom-overlap-analysis.md`). Only
quotations were dropped. Masking every shared run was considered and rejected, because it would
also remove shared idiom that may be genuine evidence, above all from Joseph Smith's 1828-29
revelations. Those contain no quotation (one shared phrase predates the passage it matches; the
rest were dictated in the same weeks) and are unchanged. This decision was made after seeing
which samples it would affect, and it leaves the revelations' shared phrasing in; both facts
should be weighed by the reader.

| Method | Registered: first (of 168) | Without quotations | Match calls |
| --- | --- | --- | --- |
| Cosine Delta | Joseph Smith 131, Hunt 31 | Joseph Smith 148, Hunt 20 | none in either |
| Burrows' Delta | Joseph Smith 77, Hunt 47, Pratt 37 | Joseph Smith 91, Hunt 49, Pratt 25 | none in either |
| General Imposters | Pratt 74, Joseph Smith 48 | Joseph Smith 66, Pratt 66 | none in either |
| Style encoders 297M / 590M | Joseph Smith 150 / Cowdery 102 | Joseph Smith 151 / 99 | none in either |
| Candidate models 125M / 297M / 590M | Joseph Smith 82 / 133 / 46; Cowdery 29 / 34 / 119 | Joseph Smith 159 / 168 / 131 | 10 / 5 / 3 become 2 / 2 / 0 |

"Joseph Smith" in this table adds his three samples together (the 1828-29 revelations and his
dictated and handwritten writing after 1830). For Burrows' Delta most of his count is the later
prose (41 and 21 chunks against 29 for the revelations); for the other methods nearly all of it is
the revelations (`data/blind/per_candidate.json`, `data/blind/a43/per_candidate.json`).

### 9.3 The synthesis and its placebo

The registered plan combined the method families into one posterior probability for each
candidate and for "not in the set", weighting each family by its benchmark accuracy and by its
result on the imitation test. The model-based families received zero weight from the imitation
test, so only General Imposters entered, and the posterior is the same at every model size. It
covers only the three candidates with samples of at least 10,000 words from before 1830: "not in
set" 0.744 (prior 0.5), Hunt 0.089, Spalding 0.085, Ethan Smith 0.082. Joseph Smith and Cowdery
are outside it, untested by it, not ruled out.

*The placebo (post hoc, raised by the simulated reviews).* Run on the candidates' own held-out
passages, the same synthesis still leans to "not in set": Ethan Smith's passages 0.59, Hunt's
0.56, Spalding's 0.51, control passages 0.63 (`data/synthesis/placebo/decoys.json`). It cannot
recognise an author's own text, because General Imposters cannot reach "match" at its registered
threshold. The 0.744 is therefore reported as registered and carries little information. It also
moves with modelling choices: 0.42 to 0.92 across priors of 0.2 to 0.8, about 0.99 with equal
family weights, and back to the prior if General Imposters is dropped. Two later corrections
bear on it as well: the imitation test that set the family weights is too small to judge
(section 5.3), and read strictly the registered rule admits no family at all, since every one
failed the benchmark bar. H1b ("none of these") cannot be supported by it.

### 9.4 Process failures

Reported because the study's guarantee is that everything can be checked.

- **Source data deleted.** The newspaper extractor deleted the archives it read, losing the
  per-word OCR confidence and word positions for all 158,960 pages. A build test now fails on any
  destructive call in the pipeline (BOM-50; recovery is open).
- **Licensed text nearly published.** A 117 MB results file holding corpus text was caught by the
  repository's size limit before it was pushed; results files now hold names and numbers only.
  Earlier, validation excerpts from Harvard's texts and a personal email and IP address were
  committed and removed by rewriting history.
- **Models discarded.** The benchmark's fine-tuned models were scored and then deleted to save
  disk, and the abandoned 1B model's checkpoints were deleted without asking. They have not been
  rebuilt (BOM-72 was dropped on 2026-11-11): no result depends on the weights, their scores are
  saved, and they can be rebuilt from the published base models, code and seeds.
- **Wrong results caught later.** A first genre-agreement figure (7.4%) counted 3,027 outage
  failures as answers. A paraphrase write-up said no named source ranked first when one did. A
  rare-phrase count came from the wrong book. A closed catalog issue had left out HathiTrust. The
  430 benchmark tests were first analysed as 430 independent tests when they come from 23 authors
  (Amendment 55). The imitation test was first read by passage when it has three authors. A first
  write-up called the 590M "the size that sees style best" when the three sizes pick the right
  author equally often. Each was corrected in the open.
- **A check that looked like a win.** An exploratory split of the benchmark by test made score
  normalisation look like a large gain for "none of these"; split by author, as it should have
  been, the gain vanished (Amendment 55(b)). The quick version is in the record, labelled.

## 10. Public claims

Seventeen public claims about the Book of Mormon's text, taken from critical, apologetic and
academic sources, were written into a register together with the rule that would decide each one,
(`data/claims/register.yaml`): twelve on 2026-10-18, before any result existed, and five more
(c13-c17) on 2026-11-06, before the blind run and after the borrowing results. The verdicts below apply those rules
(`docs/claims-verdicts.md`). Four verdicts are allowed: supported, contradicted, mixed, and not
addressed. Four claims were marked untestable by text analysis from the start. The register takes
no side, and an untestable claim is not a contradicted one.

| Claim | Source | Verdict |
| --- | --- | --- |
| c01 *The Late War* shares unusual rare phrases | CES Letter; Johnson and Johnson 2013 | mixed: it passes its null, but a control of the same genre scores higher |
| c02 *View of the Hebrews* shares themes closely enough to suggest dependence | CES Letter | contradicted |
| c03 Cowdery's link to Ethan Smith's congregation | CES Letter | untestable (biography) |
| c04 About 80 early modern word uses that were obsolete by 1830 | Skousen and Carmack | not addressed (the forms were not tested one by one) |
| c05 Early modern syntax that King James imitation cannot explain | Skousen and Carmack | mixed: the grammar model agrees; the transformer cross-check dates the text to about 1755 |
| c06 Dictation under "tight control" | Skousen and Carmack | untestable (production) |
| c07 Rigdon and Spalding contributed | Jockers et al. 2008 | contradicted |
| c08 Narrators distinct from each other and from the candidates | Larsen et al. 1980 | contradicted |
| c09 With "none of the above" allowed, no nineteenth-century candidate is the author | Fields et al. 2011 | supported by the rule as written, with caveats (below) |
| c10 The text belongs to the American pseudo-biblical genre | Shalev | mixed: it shares the genre's stock phrasing and separates from it on grammar |
| c11 DNA cannot settle population questions | Gospel Topics essays | untestable (genetics) |
| c12 Dictated without notes or manuscripts | Gospel Topics essays | untestable (production) |
| c13 Spalding's manuscript supplied the story or text | Howe 1834 | contradicted (for the surviving manuscript) |
| c14 *The First Book of Napoleon* suggests dependence | named sources | mixed |
| c15 Cowdery or Rigdon wrote or shaped the text | named sources | contradicted, with a caveat (below) |
| c16 The language reflects its 1820s environment | Brodie 1945 | contradicted (language only; themes were not tested) |
| c17 Narrators not distinct, and close to Joseph Smith's revelations | Holmes 1992 | supported |

**Totals:** supported 2, contradicted 6, mixed 4, not addressed 1, untestable 4.

**When the verdicts were set, and what has changed since.** The owner set the verdicts from the
pre-written rules on 2026-11-10, the day of unblinding. They have not been re-graded. Several
later results bear on them, and are stated here so that no verdict reads as stronger than its
evidence.

- **c09.** The rule asks whether any candidate is supported under the registered procedure, and
  none is. But the registered synthesis it leans on covers three candidates and cannot recognise
  an author's own text (section 9.3), and no method can say "none of these" at the registered
  error rate (section 5.4). "Supported" here means the registered condition was met, not that
  the candidates are excluded. Whether to re-grade c09 is open and is the owner's decision before
  release.
- **c07 and c15.** "Contradicted" means neither Rigdon, Spalding nor Cowdery is supported under
  the registered rule, and that Cowdery's high ranking in the registered run was quotation
  (section 7.1). It does not mean excluded. The language models do not recognise Rigdon or
  Cowdery across their own works (section 7), and both are represented mainly by writing from
  after 1830.
- **c17.** The verdict cited the classical methods' rankings. The later checks sharpen what
  "close to Joseph Smith's revelations" means: it holds for his revelations of 1828-29 and of
  1830-34, not for his ordinary prose under the language models and style encoders, and at the
  590M size other writers of imitation scripture rank as high (section 6). Closest is not a
  match.
- **c05 and c16.** The dating results carry the cautions of section 8.1: an early date is
  predicted by an early source, by imitation, and by the King James register alike, and the text
  is hand-keyed where most comparison text is scanned.

## 11. What held

These are the results that survived every check in sections 3 to 9, in the order the paper
reached them. Each is stated with the limit that belongs to it.

1. **No copying and no borrowed plot.** With King James passages set aside, 0.16% of the Book of
   Mormon matches wording in earlier books, all of it stock religious phrasing; *The Late War*, by
   the same measure, shares 8.9% of its text with earlier books. No book in the library shares the
   Book of Mormon's sequence of events. The story-order test was shown to work first: it finds
   Josephus retelling Genesis to Judges, 108 events in order. Its one registered hit on the Book
   of Mormon (Church's *History of Philip's War*, six generic events of military correspondence,
   p 0.008) is about what chance gives among 49 books (section 3).

2. **The named books do not stand out within their genre (a post hoc comparison).** *The Late War* and *The First Book of Napoleon* pass the
   registered rare-phrase rule, and a reprint of Ilive's *Book of Jasher* shares more: the overlap
   belongs to the genre of imitation scripture, not to a source. *View of the Hebrews* ranks first
   of 49 books on its subject for paraphrase and at the 85th percentile against 500 equally
   religious books, short of the top-1% bar. Spalding's surviving manuscript shares no passage,
   phrase density or plot (section 3).

3. **Earlier authorship studies are fragile.** Five were reproduced with their own methods, one of
   them on its authors' own deposited data. Their answers follow choices that were not tested: the 2008 study's Rigdon attribution
   falls from 169 chapters to 92 when other genuine Rigdon text is used, and the error of the
   study that allowed "none of the candidates" swings from 80% to 0% with sample length
   (section 4).

4. **At picking the right author from a list, period-trained language models beat every older
   method we tested, at every size.** On 55 benchmark authors, counted by author, all twelve
   comparisons (three model sizes against Burrows' Delta, Cosine Delta, General Imposters and
   ENSC) favour the language models: ahead on 24 to 33 authors, behind on 2 to 6, with a gain of
   13 to 21 points of accuracy (Holm-corrected p at most 0.0014). The 32 authors added last
   repeat it on their own. This took a correction to establish: the first count, by test,
   overstated it, and 23 authors were not enough (Amendments 52, 55, 56). Training on the period
   matters: a modern model (GPT-2) used the same way makes false matches 85-92% of the time on
   the first benchmark, the period models 22-47% (section 5).

5. **Among the candidates, the closest writing is Joseph Smith's revelation voice.** His 1828-29
   revelations rank first for the language models at every size (159, 168 and 131 of 168 chunks),
   for both style encoders and for Cosine Delta. With every sample cut to the same size they
   still rank first at 125M and 297M, and no writer who could not have written the book reaches
   them there; twelve slices of his 1830-34 revelations land second or third, next to them. Three
   qualifications hold just as firmly. It is his revelations and not, for these methods, his
   ordinary prose. At 590M other imitation scripture ranks as high, including a writer born in
   1844. And Burrows' Delta and General Imposters order the candidates differently. Two readings
   fit, the same man or the same revelatory medium, and these tools do not decide between them
   (section 6).

**Also standing.** The text's grammar dates earlier than its period and earlier than the period's
own imitation scripture (median 1661; p 0.0001 against 25 control volumes), with the cautions of
section 8.1. Its narrators differ above chance but are not separable as different authors, and
dictation order explains their differences about as well. The corrections in the manuscripts are
those of a text taken down by ear. Joseph Smith's ordinary prose of 1833-44 does not move toward
the book's style, on very little text. And among the candidates other than Joseph Smith, only
Ethan Smith is recognised by the models across his own books, and he is the farthest from the
text (section 7).

**What did not hold, or could not be established.** No candidate is matched under the registered
rule, and no method can say "none of these" at the registered error rate, so neither a match nor
its absence was available as evidence (section 5.4). The registered synthesis carries little
information (section 9.3). The registered author sweep cannot name anyone (section 7.8). The
imitation test is too small to judge (section 5.3).

None of this bears on how the text was produced, whether it is a translation, or whether it is
inspired. No borrowing or dating test here separates a genuine translation from a composition
presented as ancient, and no stylometric method separates the person who dictated a text from the
person who composed it.

## 12. Limitations

The first four limits bound every conclusion in the paper. The rest are narrower.

**The tests cannot separate translation from imitation.** Each borrowing and dating test was
first run on texts whose nature is known: genuine period translations of ancient works, and
period compositions presented as ancient (Amendment 9). None of the tests tells the two groups
apart. So "no borrowing found" and "the language dates early" describe the text. They do not say
what it is or how it came to be.

**No method can say "none of these".** This is stated once, here, for the whole paper. The
registered bar for a usable verdict was at most 5% false matches while still recognising 95% of
true authors. No method passes it. At that point the language models call a stranger's text a
match 51 to 57% of the time on the 430-test benchmark when each author is held out in turn
(Amendment 55, post hoc), and 63 to 75% on the registered split. Read the other way round, at a 5%
false-match target they confirm only 38 to 61% of true authors. The standard remedy from speaker
verification, score normalisation, does not carry over to authors it has not seen (17 to 26%
false matches against a 5% target). General Imposters and the style encoders cannot return
"match" at all at their registered thresholds, and the registered synthesis cannot recognise an
author's own text (section 9.3). It follows that "no match" cannot be read as "not this person",
for any candidate, and that the study can rank the candidates it has but cannot say whether the
author is among them.

**Most candidates are not recognised across their own works.** Only Ethan Smith's model
recognises him in a book it was not trained on (96 to 100% of passages). For Cowdery, Rigdon and
Phelps the rate is 0 to 23%, and for Pratt 52 to 87%, falling as the model grows; Hunt and
Spalding have a single work and cannot be tested. For those candidates the models learned a book
or a periodical, and a low rank is weak evidence about the person. Rigdon, Pratt and Phelps are
also represented only by writing from after 1830, by which time they had read the book, and the
registered check of whether later writing can stand in for earlier failed for every method.

**The pre-1830 revelation sample is small, and it is the only one of its kind.** Joseph Smith's
1828-29 revelations are 2,720 words, under the 10,000-word floor, and they are the whole of his
surviving writing from before 1830, so that side of every comparison is one fixed model that
cannot be resampled. Section 6.4 addresses part of this with his 1830-34 revelations, which
behave the same way at equal dose; but those were written after the book and could echo it. No
ordinary prose of his survives from before 1830. Cowdery's 1829 sample is 844 tokens once its
quotations are removed, too short to train on.

**Closest is confounded with register and channel.** The revelations are the only candidate
samples in the text's own scriptural register, and they share its channel: dictated by the same
man in the same years to the same circle of scribes, unedited. Nearly every other comparison text
is edited print. The methods cannot separate shared register or channel from shared authorship,
nor the person who dictated a text from the person who composed it. King James masking removes
aligned biblical passages only; formulae such as "it came to pass" and "behold" remain, and how
much each method rests on them has not been measured.

**The model sizes disagree where it matters most.** The register placebo is clean at 125M and
297M and fails at 590M. On known answers no size picks authors better than another, so there is
no ground for preferring one, and the split is reported as a split.

**Methods differ in stability.** The primary language-model method reproduces closely across
machines and its ranking is stable across seeds (section 6.5); variant V1's registered learning rate broke at 590M; variant V2 swings from 9% to 98%
false matches across seeds and carries no weight. Whether the model-based methods hold up under
deliberate imitation is not known: the imitation test has three authors.

**The 168 chunks are not 168 passages.** They are the text cut twice, and chunks from one book
are not independent of each other. Counts are given per length (section 6.4a) and should not be
read as 168 independent observations. Where a test was run on chunks (the dating comparison of
section 8.1), the result is also given with each book of the text as one unit.

**Single authors only.** Every test asks whether one known writer's style fits. Composite or
collaborative authorship is a common historical hypothesis that this design cannot test.

**The corpus.** OCR quality is uneven, and the wording searches miss an unmeasured but probably
large share of real shared phrasing in poor scans (a four-word phrase survives about 41% of the
time at 80% word accuracy). A negative from poor OCR is not evidence of absence: the 26 June 1829
*Wayne Sentinel* notice of the book's title page is present on the page image, and none of ten
search terms is found in its OCR. Training volumes holding 1 to 19 of the text's 12-token strings
(below the removal threshold of 20) were kept. Some catalog dates are wrong, and were corrected
where the text names later years. Author names conflate namesakes and split variants. About 72%
of the original manuscript is lost. Writers whose work did not survive in print, or who fall
outside the 23,872 swept authors, are not covered, and the registered sweep failed its own
usability test (section 7.8).

**The local print environment.** How much of what was printed and sold in western New York before
1830 survives in the corpus is not measured. The national newspaper set holds almost nothing from
the region, and the access scores centre on Joseph Smith's documented reach. Access is not use:
the access table records documented availability, not reading.

**The models.** The period models were trained on the period corpus, which includes volumes by
benchmark authors used later for calibration (as language-model training text, not with author
labels). The fine-tuning settings were fixed for all sizes in advance and may not suit the
largest. GPT-2 is used on the benchmark only, since it has read modern text that may include the
Book of Mormon.

**Registered features not run.** The classical methods used only most-frequent-word features. The
registered character n-grams, part-of-speech n-grams and content-word set were not run on the
benchmark or the Book of Mormon (`paper/deviations.md`, D3).

**Post hoc decisions.** A large share of sections 5 and 6 was decided after unblinding. Each step
is listed with its amendment and effect in section 9.1. The registered results are those of the
run tagged `blind-registered-2026-11-10`; everything later is a check on them, not a replacement.

**One person, simulated review and simulated blinding.** The study is designed and run by one
person with AI assistance. Every review step (adversarial review, draft review, peer review, the
research review of 2026-11-12) and the second triage pass are simulated by AI models. The blind
run's "fresh session" was a new AI session without the key, not an independent analyst. None of
this is independent scrutiny, and the paper has had none.

**Planned and not run.** The hand validation of the genre labels and the perturbation run that
would show whether label errors matter (BOM-53); thematic dating, whether the text's themes track
the 1820s (BOM-63); a larger test of register shift on 553 authors' sermons against their other
prose (section 5.3). Genre labels agree moderately between two model passes (84.9% on either
label, 50.8% exactly) and worst on early modern text.

## 13. Everything is public

The study is meant to be checked and redone. It was designed and run by one person
with AI assistance, and mistakes are possible; section 9 lists the ones found so far.
What stands behind the results is that every step can be found and rerun.

- **The plan and every change to it.** The pre-registration was frozen on OSF on 2026-10-15
  (https://osf.io/6ugxc/) and is mirrored in `paper/preregistration.md`. Its section 11 holds
  every amendment, dated, with post hoc ones labelled. Amendments 1 to 46 were also filed on OSF.
  From Amendment 47 on (2026-11-11) they are recorded in the repository only, committed and
  pushed before the results they govern exist, so that the commit time is the record. Decisions
  made after results were seen are also listed in `paper/deviations.md` and in section 9.1.
- **Code and configuration.** https://github.com/lifehug/book-of-mormon-authorship. Every
  analytic value (threshold, cutoff, chunk size, seed, model choice) comes from
  `config/preregistered.yaml`, and every results file cited in this paper records that file's SHA-256 and the git
  commit that produced it. `eval/README.md` lists every command: what it does, what it needs,
  what it writes, and how long it takes.
- **Results and data tables.** The catalog, genre labels, derived tables and every results file
  are in `data/`, each directory with a `SOURCES.md` saying where its files came from and how to
  rebuild them, and with checksums in `data/manifests/`. Results files hold names and numbers,
  never licensed text. The derived tables that the analyses read (phrase frequencies, feature
  matrices, genre labels, OCR scores) are published so that the statistics can be rerun without
  obtaining any restricted source.
- **Models.** The three period base models and the candidate models are on Hugging Face:
  `etherfuse/timelocked-1830-125m`, `etherfuse/timelocked-1830-300m` (the 297M),
  `etherfuse/timelocked-1830-590m`, and `etherfuse/bom-authorship-candidate-models`. These two
  sets are enough to replicate. With the base models, every other fine-tune in the paper
  (benchmark, seeds, slices, placebo writers) can be rebuilt from the code, configuration and
  seeds for roughly $50 to $100 of rented GPU. With the candidate models, anyone can check the
  Book of Mormon ranking without any restricted text and without training anything. Other
  fine-tunes publish their scores, not their weights (owner's decision, 2026-11-11). The
  repository's README also lists a style-encoder, a dating-model and an earlier
  benchmark-fine-tune repository [CHECK: whether these three stay public after the planned
  clean-up to base and candidate models (BOM-87); not verifiable offline].
- **Simulated reviews.** Three simulated peer reviews (a historian, a statistician, a
  stylometrist), the response plan, the adversarial review and the research review of 2026-11-12
  are in `paper/review/`, `paper/adversarial-review.md` and `docs/research/`. All were written by
  AI models and are labelled as simulated. The study has had no independent human review.
- **The running account.** `paper/blog.md` is a dated, informal log of what was done and why,
  wrong turns included; `docs/method-improvements.md` records each change to the method and
  whether it worked.

**What is held back, and how to get it.** Four sources cannot be redistributed: the HathiTrust
researcher dataset (a signed agreement), Harvard's Institutional Books (accepted terms:
noncommercial, no redistribution), the Joseph Smith Papers transcripts (copyrighted), and one
purchased book, Rick Grunder's *Mormon Parallels*. For each, `docs/replication.md` gives numbered
steps to obtain the same access we had, and the public checksum manifests let a replicator
confirm they hold the same files. The large corpora themselves stay on local disk, covered by
those manifests. Nothing else is withheld. A replicator refused access to one of these sources
cannot check the results that depend on it from the raw text; the published derived tables are
there for that case.

## 14. The whole library

Sections 6 and 7 asked which of a small list of named candidates writes most like the Book of
Mormon. This section asks what happens when the same question is put to every author in the
library. It is exploratory: nothing in it was pre-registered, the choices were made in November
2026 with earlier results in view, and each is recorded in the configuration file before the
result it governs. Two safeguards stand in for registration. Every tool was tested on books of
known authorship before it was trusted, and the procedure for the Book of Mormon was fixed in a
single commit (`9ed5940`) before any Book of Mormon text was run through it.

The aim was a statement with a measured number in it: if the author left other writing in this
library, this search places them near the top X% of the time. And the candidates of sections 6 and
7 were to be ranked in the same list as everyone else, so that it could be seen whether any
author in the library rates closer than what the small list found.

### 14.1 The search, and how it was tested

The library's authors are the 23,872 catalogued authors of 1780-1830 with at least 10,000 words
of text (section 7.8). Each has a profile of up to twenty 1,000-word blocks drawn across their
works, with King James quotation masked.

The search uses a style encoder: a copy of the 297M period model trained so that passages by one
author land near each other. The encoder registered in Amendment 24 had a flaw that its own
training log shows. Its loss on its 7,673 training authors fell from 1.55 to 0.03 while its
accuracy on held-out authors stayed where it had been after 1,000 of 20,000 steps (0.27-0.42
throughout, `data/corpus/style_embed/runs/style/log.jsonl`): it had memorised 32 fixed passages
per work. And the sweep's misses on known books were concentrated where the author's other
writing was in a different genre from the book (`data/sweep/coverage.json`), which is the Book of
Mormon's situation.

A second encoder was therefore trained (`style_embed/v2.py`), changing three things, each after
the published literature on cross-genre authorship retrieval (Rivera-Soto et al. 2021; the
"Sadiri" data-selection results, 2024; the 2025 retrieve-and-rerank study): eight times the text
per work (256 passages), freshly drawn; on half the training steps, batches drawn from a single
genre with each author's paired passage taken from a different genre, so that the model must
separate authors within a genre and recognise one author across genres; and a validation split
of training authors that selects the kept weights. The held-out authors of Amendment 24, which
include every known book used below, were never trained on and never used to choose anything.
An author is scored by their closest stretch of text: each profile is embedded in consecutive
episodes of about 1,024 tokens, and for each episode of the questioned text the similarity to the
author's nearest episode is averaged (`sweep/episodes.py`).

A stopping rule was set before the second encoder's result was seen: take the better variant by
coverage of the cross-genre known books at a shortlist of 1,000 and stop work on the search
there, whatever the number.

**Known-answer test.** For each author held out of both encoders who has a book that can be
withheld (727 authors: the 200 of the registered sweep and 527 more, built the same way), one
book is withheld, the author's profile is rebuilt from their other works, and the book is
searched against every author. Coverage is the share of books whose true author is among the K
closest, over the 18,288 authors not known to have been dead or under age in 1829 (14.2). Ranges
are 95% intervals from resampling books (`data/sweep/coverage_episodes_v2.json`).

| Books | n | first | top 10 | top 100 | top 1,000 |
| --- | --- | --- | --- | --- | --- |
| all | 727 | 34% (31-38) | 59% (55-62) | 76.5% (73-80) | 89% (86-91) |
| author's other writing in the book's genre | 403 | 47% (42-52) | 71% (67-76) | 87% (83-90) | 95% (93-97) |
| partly in the book's genre | 112 | 20.5% | 54.5% | 79% | 94% |
| none of it in the book's genre (cross-genre) | 212 | 17% (12-22) | 38% (31-44) | 56% (49-62) | 74% (67-80) |
| identity confirmed by life dates | 204 | 34% | 65% | 84% | 95% |

The cross-genre row is the one that applies to the Book of Mormon. On the first 200 books alone
the figures were higher (first 38%, top ten 66%; cross-genre 29% and 52% on 62 books); the
larger set is the one to quote. On those 200 books the first encoder, scored on whole profiles
over all 23,872 authors, placed the true author first for 30% and in the top 100 for 71.5%; scored
the same way as the second, it is 13 books behind and 4 ahead at a shortlist of 100 and level at
1,000 (4 and 4). About one known author in nine is not in the top 1,000.

Profile size matters, so the test was repeated with every profile cut to an equal size
(`data/sweep/coverage_episodes_v2_11.json`, `coverage_episodes_v2_2.json`):

| Profile | first | top 10 | top 100 | cross-genre: first | top 10 | top 100 |
| --- | --- | --- | --- | --- | --- | --- |
| full (about 20 episodes) | 34% | 59% | 76.5% | 17% | 38% | 56% |
| 11 episodes | 31% | 57% | 75% | 16% | 39% | 55% |
| 2 episodes (the 1828-29 revelation sample's size) | 19% | 42% | 66% | 13% | 27% | 50% |

**In the Book of Mormon's own neighbourhood.** The head of the Book of Mormon's ranking (14.4) is
religious testimony, so the search was also scored on the known books closest to that
(`data/sweep/bom_genre_check.json`). For the 98 sermon and devotional books: first 34%, top ten
62%, top 100 81%. For known-book authors who are themselves among the 1,000 library authors
closest to the Book of Mormon (38 books): 39.5%, 66%, 79%; among the 500 closest (17 books): 53%,
76.5%, 88%. The search does no worse on writers of this kind than on the library at large; the
numbers of books are small.

### 14.2 Who could have written it

Life dates were taken from the catalog's author field where it carries them and, for the 12,929
authors it leaves undated, from the Library of Congress name authority file, accepting a match
only when exactly one person of that name was born early enough to have written the author's
earliest volume here (`sweep/people.py`). The rule was checked on 494 authors whose dates the
catalog does give: it dated 219, and 212 of those agree with the catalog. It dated only 13% of
the undated authors. The result: 6,016 authors alive and at least fifteen in 1829, 5,584 dead or
too young, 12,275 unknown (`data/sweep/people.json`).

No author was removed. The 18,288 not known to be dead or under age are the gallery the
accuracy figures are stated over; the dead remain in every ranking as decoys. An author who
died in 1706 cannot have written a book dictated in 1829, so the number of dead authors near the
top of a ranking measures how far it follows a kind of writing and not a person.

### 14.3 The author models on long lists

The plan had been for the search to hand a shortlist to the method that did best in section 5,
one fine-tuned period model per author. That method had been tested only on lists of four.
Amendment 58 measured it on lists of 2 to 55 authors: by author, it picks the right one from 55
candidates 86% of the time at 125M and 297M and 82% at 590M, against 49-62% for the four older
methods; from 12 candidates chosen to be similar, every model size is ahead of every older method
(36-48 authors ahead, 3-4 behind, Holm-corrected p < 10^-6); larger models do not lengthen the
list (`data/benchmark/list_size.json`). The errors on long lists come from a few models that
score low on every author's text.

Those figures are for models trained on all of an author's text and tested on later passages of
the same works. The library asks for something harder: a different book, and an equal amount of
text for every author, since larger samples otherwise win by size (section 6.2). So before any
run on the Book of Mormon the method was tested on that task (`eval/library_pool.py`): 1,000
library authors, 200 of them the known-book authors of 14.1 with the book withheld; for each
author one model on 11,264 tokens and three on 3,039-token slices, 3,982 models at 125M, each
scoring the known books.

| Method, on the same 1,000 authors | first of 55 | first of 1,000 | top 10 of 1,000 | cross-genre: first of 1,000 | top 10 |
| --- | --- | --- | --- | --- | --- |
| author models, 11,264 tokens | 62-64% | 42-44% | 61-64% | 29-32% | 47-55% |
| author models, 3,039 tokens (median of three slices) | 51-56% | 28-29% | 52-55% | 19% | 39-42% |
| second style encoder | - | 66% | 82% | 53% | 68% |
| encoder and author models combined | - | 65% | 84% | 53% | 74% |

Ranges are raw scores and scores put on each model's own scale; `data/sweep/pool_report_pilot.json`,
`pool_fusion_pilot.json`. Book by book, the encoder places the true author higher than the
larger-dose author models on 96 books and lower on 19; adding the models to the encoder helps 30
books and hurts 38. On this task the method that was best on the small benchmark is the weaker
one, and the plan was changed before the Book of Mormon was run: the encoder ranks the library,
and the author models are reported as a second opinion on its top 200. Caveats: only the 125M
size was run; the encoder used each author's full profile where the models had 11,264 tokens,
though the encoder at 11 episodes loses little (14.1); each known book was scored on about 3,000
tokens.

### 14.4 The Book of Mormon against 23,872 authors

The 168 sealed chunks of section 6 were embedded by the second encoder and scored against every
library author and against the candidate samples of sections 6 and 7, embedded the same way, at
three profile sizes. A candidate's place is the number of library authors scoring closer, plus
one (`eval/library_bom.py`, `data/sweep/bom_ranking.json`).

| Sample | 2 episodes | 11 episodes | full profile |
| --- | --- | --- | --- |
| Joseph Smith, 1828-29 revelations | 1 | too short | 13 |
| Joseph Smith, 1830-34 revelations | 1 | 2 | 1 |
| Joseph Smith, ordinary prose, pooled | 24 | 19 | 30 |
| Parley Pratt | 23 | 22 | 2 |
| Sidney Rigdon | 65 | 27 | 35 |
| Oliver Cowdery, printed after 1830 | 347 | 35 | 17 |
| Gilbert Hunt | 140 | 54 | 30 |
| W. W. Phelps | 1,082 | 170 | 132 |
| Solomon Spalding | 1,099 | 2,308 | 507 |
| Ethan Smith | 4,359 | 6,170 | 189 |

The 1828-29 sample has two episodes; its thirteenth place in the full ranking is two episodes
against other authors' twenty. Where a candidate has more text than the profile size, its other
slices were scored too: the 1830-34 revelations' 31 two-episode slices range from 1st to 67th
(median 1st); Pratt's 47 range from 1st to 2,998th (median 221st).

One library author places ahead of Joseph Smith's revelations at one of the three sizes: at 11
episodes John Wroe (0.630) is ahead of the 1830-34 revelations (0.615), which are second. At the
other two sizes a revelation sample is first, and no other library author is ahead of them at
any size. The library's own head of the list is the same at the two larger sizes: John Wroe
(1782-1863), then William Bayly (d. 1810), William Savery (d. 1804), John Field (d. 1723), David
Willson (1778-1866), Elizabeth Stirredge (d. 1706), James Backhouse (1794-1869), with several
names the catalog does not date. Read against outside biography, which this study did not
verify, these are an English prophet who published his own revelations in the 1820s, the leader
of a breakaway sect in Upper Canada, and Quaker ministers' journals and epistles. [CHECK:
biographical descriptions are from general knowledge, not from the corpus.]

### 14.5 The decoy check, and a second opinion

Dead authors are 23% of the library. They are 9, 7 and 6 of the top 20 at the three profile
sizes, where chance gives about 5, and 39, 35 and 36 of the top 100, where chance gives 23. The
head of the ranking is therefore a kind of writing, first-person religious testimony and
revelation, and not a set of people who could have written the book. This repeats, on the whole
library, what the writers who could not have written it showed at 590M in section 6.3.

As a second opinion the author models were run on the encoder's top 200 library authors and the
candidate samples (850 models at 125M, equal doses, the 168 sealed chunks;
`data/sweep/bom_second_opinion_pilot.json`). Joseph Smith's 1830-34 revelations are first at both
doses and the closest sample on 123 to 150 of the 168 chunks; the 1828-29 revelations are fourth
of 212 at the small dose. Behind them are John Wroe, David Willson, Joanna Southcott (d. 1814)
and John Reeve (d. 1658). Lower down the two methods disagree, and different slices of one author
place far apart, as in section 6. Given 14.3, this is the weaker of the two instruments here.

### 14.6 Reading and limits

The search of every author returns the finding of section 6 on a list three thousand times
longer: the writing closest to the Book of Mormon is Joseph Smith's revelations, first at two of
three profile sizes and second to one other writer of revelations at the third, and after them
the revelations and testimonies of other people, many of them long dead. On known books the same
search places the true author first 34% of the time and in the top ten 59% of the time; for a
book unlike its author's other writing, 17% and 38%; at the small profile size that admits the
1828-29 sample, 13% and 27%.

What it cannot do is the same as in section 6.7. It does not separate one man from a kind of
writing, and the decoy check shows the kind of writing is a large part of what it follows. It
searches only authors with 10,000 printed words in this library; a person who published nothing
is out of its reach. Half the authors have no recorded dates. The later revelations were written
after the book, and its influence on them cannot be excluded. And the section is exploratory
throughout.

Not run: the author models at 297M and 590M on the library, and the encoder on a 590M backbone.

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
