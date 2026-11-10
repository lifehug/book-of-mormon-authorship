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
little information.

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
| (none) | unblinding | synthesis placebo | the synthesis read as uninformative |

Every amendment, with its reason and date, is in section 11 of the pre-registration and on OSF.
