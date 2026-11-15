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
any lead was seen) would pass about one random author in ten (10 of 100 drawn at random;
`data/sweep/gate_sample.csv`), so about 0.0035 false leads per query
would survive it.

**Result.** No lead: 0, against 0.035 expected by chance (`data/blind/unblinded.json`,
`data/sweep/calibration.json`). The twenty nearest authors (`nearest_20` in the first file)
include writers of prophecy and Quaker testimony (John Wroe, George Fox, William
Sewel), none near either threshold.

**What that is worth.** On the 200 known books the true author came first 27% of the time by
Cosine Delta and 30% by the style encoder (35% by either), against the 70% bar. The sweep failed
its own usability test. It cannot name anyone, and its silence cannot rule anyone out: on
this evidence an author of the Book of Mormon sitting in the library would usually not have come
first. It
says only that no unproposed author stands out by these two signals. The language models, the best
tool at picking an author from a list (section 5.1), were not run here: they need one fine-tuned
model per author, 23,872 models.

Section 14 returns to the whole library with better tools.
