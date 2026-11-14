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
