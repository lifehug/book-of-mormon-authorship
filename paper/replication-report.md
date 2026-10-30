# Replication of prior Book of Mormon stylometry (BOM-22)

Written 2026-10-30. The designs were fixed in `docs/prior-studies.md` before anything ran. Each
study's *published* method runs on the 1830 text (the one exception to the seal of 4.2); the
project's own methods are not used and nothing here feeds a calibration or a threshold. Outputs:
`data/benchmark/replication_*.json`; code `eval/replicate.py`. Reproduce with
`python -m eval.replicate {chapters,jockers,larsen,holmes,ensc,johnson}`.

The question each section answers is the same: does the published result come back when the
published method is run on our texts, and where it does not, why.

## Summary

| Study | Published | Replication | Matches? |
| --- | --- | --- | --- |
| Larsen, Rencher and Layton 1980 | narrators differ (odds of one author < 1 in 100 billion); no BoM block resembles a candidate | 4 narrators differ, MANOVA p = 1e-14; 11 of 246 BoM blocks classified to a candidate | yes, both findings, with the same caveat on the p-value |
| Holmes 1992 | Joseph Smith's own writing and Isaiah separate; prophets do not cluster by prophet; revelations sit with the prophets | Joseph Smith 3 of 3 alone; prophets mixed; D&C 1835 3 of 3 with the prophets; Isaiah 2 of 3 apart | yes |
| Jockers, Witten and Criddle 2008 | NSC: Rigdon first or second for 197 of 239 chapters, Spalding 110, Isaiah-Malachi 101 | On their published data: same 110 words, cross-validated error 8.76% (8.8%), Rigdon 169. On our texts: Pratt 193, Rigdon 29 | **method yes, result no**: the leading candidate follows the texts chosen for each candidate |
| Schaalje, Fields, Roper and Snow 2011 (ENSC) | most chapters fit none of the candidates | 235 of 239 chapters "none", 4 Isaiah-Malachi | yes at the level of the published conclusion, with a validation caveat |
| Johnson and Johnson 2013 | *The Late War* has the densest shared rare 4-grams after *The First Book of Napoleon* | *The Late War* in the top 0.05% (174 shared, p = 0.0004), but 30 books of 10,000+ words are denser, mostly other imitation scripture | **partly**: the two books stand out; the claim that nothing else approaches them does not hold |

## 1. Larsen, Rencher and Layton (1980)

**Run.** The 10 most frequent of their 38 function words, arcsine-transformed relative frequency,
1,000-word blocks. Book of Mormon blocks by narrator from BOM-17's segments: Nephi 43, Jacob 9,
Mormon 169, Moroni 25. Candidate blocks: Joseph Smith 33, Cowdery 50, Ethan Smith 239, Hunt 57,
Phelps 30, Rigdon 22, Pratt 69, Spalding 43, *Lectures on Faith* 24.

**Result.** MANOVA across the four narrators: Wilks' lambda 0.575, F(30, 685) = 4.74,
p = 1.0e-14. Leave-one-out discriminant analysis put 11 of 246 Book of Mormon blocks with a
nineteenth-century candidate (Joseph Smith 5, Phelps 2, Rigdon 2, *Lectures on Faith* 2); the rest went to a Book of Mormon narrator, though often the wrong one
(Mormon's blocks: 95 to Mormon, 29 Moroni, 26 Nephi, 9 Jacob).

**Comparison.** Both headline findings return. The critique stands as well: blocks from one book
are not independent, so the p-value overstates certainty by an unknown amount, and the
narrator-to-narrator confusion above is large enough that "the narrators differ" is a statement
about group means, not about blocks being recognisable. The replication has 4 narrators, not
their 21 speakers (BOM-17 labels narrators, not quoted speakers), so it tests the weaker claim.

## 2. Holmes (1992)

**Run.** Honoré's R, V2/V and Yule's K on 10,000-word samples (Nephi 4, Mormon 16, Moroni 2), three
1835 Doctrine and Covenants revelation samples (Joseph Smith Papers transcripts, private repo),
KJV Isaiah 3, Joseph Smith's own writing 3; three-group hierarchical clustering and principal
components. Sichel's alpha and theta are omitted because Holmes does not specify the fit.

**Result.** Joseph Smith's three samples form their own cluster (1). Isaiah 1 and 2 cluster with
Nephi 1 and 2 (cluster 3), Isaiah 3 with the rest. Every Mormon and Moroni sample, Nephi 3 and 4,
and all three revelation samples fall in one cluster (2).

**Comparison.** Matches all three of Holmes's findings: Joseph Smith's personal writing stands
apart, the prophets do not separate by prophet, and the revelations cannot be told from the
prophets. The critique also stands: these are vocabulary-richness measures, and Holmes's own
result shows their limit, since samples by the same prophet do not group together. (Hoover 2003,
https://doi.org/10.1023/a:1022673822140, is the usual citation for this critique; not yet read
here.) Our samples are cut from the 1830 text, where Holmes used a modern
edited text, and the finding survived the change.

## 3. Jockers, Witten and Criddle (2008)

Run three ways (`python -m eval.replicate jockers` and `jockers-data`; outputs
`replication_jockers.json`, `replication_jockers_data.json`).

**(a) Our code on their data.** The authors deposited their word counts for all 456 samples
(Stanford Digital Repository, https://purl.stanford.edu/rs276tc2764, CC BY 3.0; copy in
`data/benchmark/replication/jockers2008/`). Applying the published selection rule to it gives
exactly the 110 words of their Appendix B. Nearest shrunken centroids, shrinkage chosen by
cross-validation, has a cross-validated error of **8.76% (published 8.8%)**. Chapter counts
reproduce in shape, not exactly:

| First choice (ours / published) | Rigdon | Spalding | Isaiah-Malachi | Cowdery | Pratt | Longfellow | Barlow |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NSC | 70 / 93 | 40 / 52 | 89 / 63 | 24 / 20 | 15 / 9 | 1 / 2 | 0 / 0 |
| Delta (90 words, as published) | 53 / 63 | 61 / 47 | 80 / 112 | 12 / 5 | 13 / 7 | 6 / 5 | 14 / 0 |

Rigdon is first or second for 169 chapters (published 197). The remaining gap is in how scores
become probabilities (their NSC ran in R's `pamr`; their Delta "probability assignments" are not
described), so Delta matches less well.

**(b) Our texts.** Our candidate samples (BOM-13), Bible text left in as they did, samples that
quote the Book of Mormon left out (see below): Cowdery 24, Pratt 30, Rigdon 11, Spalding 22.
NSC cross-validated error 12.5%. First or second choice: Pratt 193, Isaiah-Malachi 112,
Cowdery 69, Spalding 64, Rigdon 29 (Delta: Pratt 147, Isaiah-Malachi 99, Spalding 95, Rigdon
52). The published result does not return.

**(c) Which texts move the answer.** On their data, one candidate's samples at a time replaced
with ours (NSC, chapters where that candidate is first or second):

| Replaced | Rigdon | Pratt | Cowdery | Spalding | Isaiah-Malachi |
| --- | --- | --- | --- | --- | --- |
| none (their data) | 169 | 42 | 36 | 89 | 133 |
| Rigdon | **92** | 91 | 37 | 84 | 156 |
| Pratt | 163 | **137** | 21 | 34 | 116 |
| Cowdery | 164 | 30 | **81** | 70 | 125 |
| Spalding | 173 | 46 | 36 | **80** | 133 |

Their Rigdon is mostly his *Book of the Revelations of Jesus Christ to the Children of Zion*,
written in 1864, more than thirty years after the Book of Mormon (their Appendix A); with our
Rigdon (signed print) his count roughly halves. Pratt's and Cowdery's counts rise severalfold
with our samples of them. Spalding, the one candidate whose text is the same in both (the
Oberlin manuscript), barely moves.

**Comparison.** Our implementation reproduces the published method on the published data; the
published *result* depends on which writings were chosen to stand for each candidate. A
closed-set method must give every chapter to someone, so the candidate whose samples happen to
sit nearest the Book of Mormon wins, and that is a property of sample selection, not evidence
of authorship. This is Schaalje et al.'s (2011) critique, here measured.

**Found and fixed during this run.** Five of our 35 Pratt samples and 1 of 25 Cowdery samples
quote the Book of Mormon (4.2's 12-token check); both men quoted it in print after 1830. Matching
the Book of Mormon to such samples is circular, so they are now left out of every replication
that uses our candidate texts (`eval/replicate.py`, `_clean`; counts recorded in each output).
With them in, Pratt's count above was 186 rather than 137. The published study did not screen
for this either.

## 4. Schaalje, Fields, Roper and Snow (2011): ENSC

**Run.** The project's ENSC (`classic/ensc.py`, after Fields et al.) with BOM-21's calibrated
settings (shrinkage 0.5, alpha 0.5), Jockers' features and candidates plus Joseph Smith
(17 samples; Book of Mormon-quoting candidate samples left out as in section 3). The exact published open-set rule and per-chapter results were not recovered
(`docs/prior-studies.md`).

**Result.** 235 of 239 chapters "none of the above"; 4 to Isaiah-Malachi.

**Comparison.** Matches the published conclusion that most chapters fit none of the candidates.
**Caveat:** this ENSC failed BOM-21's benchmark (open-set false-positive rate 66% at this alpha).
Its failure was naming an author when it should say "none", the opposite of what happens here,
so the "none" answers are not the method being over-cautious; but a method that failed
validation does not count as evidence in this study, and this result is a replication only.

## 5. Johnson and Johnson (2013)

**Run.** The Book of Mormon with the KJV masked (250,486 words) against every eligible period
volume (221,344, the 13 sealed copies of the target left out, BOM-45). Their rarity rule: a
4-gram is rare if it occurs in fewer than one book per thousand (81,175 rare 4-grams shared with
the Book of Mormon). Density = rare shared 4-grams per 10,000 words; empirical p-value against the
whole corpus.

**Result.** *The Late War* (best copy) ranks 97th of 221,344 with 174 rare shared 4-grams,
p = 0.0004; *The First Book of Napoleon* ranks 44th (100 shared, p = 0.0002). The top of the raw
ranking is one-page broadsides, where a single shared 4-gram gives a huge density. Among documents
of at least 10,000 words (168,622; a descriptive cut, not a registered test), *The Late War* ranks
31st and Napoleon 8th, behind *The Book of Nullification* (1830), two copies of *The Book of
Jasher* (1829), *The Chronicle of the Kings of England*, *Prophetical Extracts* and similar works
(at 2,000 words: 54th and 18th).

**Comparison.** The core observation returns: both books share far more rare phrasing with the
Book of Mormon than chance gives. The stronger claim, that "no other book, aside from The First
Book of Napoleon, approaches the density", does not: in a corpus about twice the size of theirs,
some thirty longer books are denser, and most of them are themselves written in imitation of
scripture. The shared rare phrases track that register, which is the critique the study received,
and a single-source ranking cannot separate borrowing from shared style. That separation is what
BOM-24 and BOM-26 are for.

**A limit of the registered rule, found here.** Under the pre-registered rarity rule (a 4-gram
in at most 5 documents) *The Late War* shares just 1 rare 4-gram, because the corpus holds about
eleven printings of it: anything it shares with the Book of Mormon is in at least eleven
documents and so is never rare. Rarity counted by volume penalises reprinted sources. Recorded on
BOM-24 to be resolved there; it does not change this replication, which uses Johnson's rule.

## What this says about the methods, not the book

The two results that replicate cleanly (Larsen, Holmes) ask whether texts *differ*, not *who
wrote* them. The one closed-set attribution
(Jockers) reproduces as a method on its own data, but its answer is a property of the candidate
samples. The open-set
method returns the published "none", but has not passed validation. The rare-phrase result returns
in part: the named sources are real outliers, but not unique ones. These are the reasons the
pre-registered study requires an open-set method that passes section 7 before any attribution is
reported.

Every review step in this project is simulated by an AI model and labelled as such.
