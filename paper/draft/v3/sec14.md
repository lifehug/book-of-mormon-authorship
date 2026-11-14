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

*The accuracy figures in 14.1 and 14.5 rest on 200 known books; a test on 727 is running and
these figures will be replaced by it.* [CHECK: replace with the 727-book numbers]

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

**Known-answer test.** For each of 200 authors held out of both encoders, one book is withheld,
the author's profile is rebuilt from their other works, and the book is searched against every
author. Coverage is the share of books whose true author is among the K closest.

| Books | n | Encoder | first | top 10 | top 100 | top 1,000 |
| --- | --- | --- | --- | --- | --- | --- |
| all | 200 | first (whole profile, all 23,872 authors) | 30.0% | 58.0% | 71.5% | 86.0% |
| all | 200 | second (closest episode) | 38.0% | 66.0% | 80.5% | 90.0% |
| author's other writing in the book's genre | 101 | second | 47.5% | 73.3% | 84.2% | 93.1% |
| none of it in the book's genre (cross-genre) | 62 | second | 29.0% | 51.6% | 67.7% | 82.3% |

The second encoder's rows are over the 18,288 authors not known to have been dead or under age in
1829 (14.2); `data/sweep/coverage_episodes_v2.json`. Book by book against the first encoder
scored the same way, the second gains 13 books and loses 4 at a shortlist of 100 and gains 4 and
loses 4 at 1,000: it is better at the head of the list and no different at depth. About one known
author in ten is not in the top 2,000 under either encoder. The cross-genre row is the one that
applies to the Book of Mormon.

Profile size matters, so the test was repeated with every profile cut to an equal size:

| Profile | first | top 10 | top 100 | cross-genre: first | top 10 | top 100 |
| --- | --- | --- | --- | --- | --- | --- |
| full (about 20 episodes) | 38.0% | 66.0% | 80.5% | 29.0% | 51.6% | 67.7% |
| 11 episodes | 34.5% | 63.0% | 80.0% | 27.4% | 53.2% | 67.7% |
| 2 episodes (the 1828-29 revelation sample's size) | 21.5% | 45.5% | 72.0% | 19.4% | 32.3% | 59.7% |

(`data/sweep/coverage_episodes_v2_11.json`, `coverage_episodes_v2_2.json`.)

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
search places the true author first 38% of the time and in the top ten 66% of the time; for a
book unlike its author's other writing, 29% and 52%; at the small profile size that admits the
1828-29 sample, 19% and 32%.

What it cannot do is the same as in section 6.7. It does not separate one man from a kind of
writing, and the decoy check shows the kind of writing is a large part of what it follows. It
searches only authors with 10,000 printed words in this library; a person who published nothing
is out of its reach. Half the authors have no recorded dates. The later revelations were written
after the book, and its influence on them cannot be excluded. And the section is exploratory
throughout.

Not run: the author models at 297M and 590M on the library, and the encoder on a 590M backbone.
