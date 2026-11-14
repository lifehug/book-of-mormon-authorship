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
