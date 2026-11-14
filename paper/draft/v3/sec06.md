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
shared passages, the longest 14 words, were kept, as for every candidate
(`data/blind/a54/shared_runs.json`). The
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
