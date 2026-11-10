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
