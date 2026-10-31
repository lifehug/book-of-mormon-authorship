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
| Larsen, Rencher and Layton 1980 | speakers differ (odds of one author < 1 in 100 billion); no BoM block resembles a candidate | by speaker (relabelled, 16 of 24 speaker counts within 10% of theirs): 17 speakers differ, p = 8e-38; 4 of 215 blocks classified to a candidate | yes, both findings, with the same caveat on the p-value |
| Holmes 1992 | Joseph Smith's own writing and Isaiah separate; prophets do not cluster by prophet; revelations sit with the prophets | all five variables: Joseph Smith 3 of 3 alone; prophets mixed; D&C 1835 3 of 3 with the prophets; Isaiah 2 of 3 apart | yes (his 10,000-equivalent conversion does not reproduce from his formulas) |
| Jockers, Witten and Criddle 2008 | NSC: Rigdon first or second for 197 of 239 chapters, Spalding 110, Isaiah-Malachi 101 | On their published data: same 110 words, cross-validated error 8.76% (8.8%), Rigdon 169. On our texts: Pratt 193, Rigdon 29 | **method yes, result no**: the leading candidate follows the texts chosen for each candidate |
| Schaalje, Fields, Roper and Snow 2011 (ENSC) | 175 of 239 chapters to an unobserved author | published method, our texts: 225 of 239 to an unobserved author, 13 Isaiah | yes, at the level of the conclusion; the method's answer depends on candidate sample length and kind (BOM-57) |
| Johnson and Johnson 2013 | *The Late War* has the densest shared rare 4-grams after *The First Book of Napoleon* | *The Late War* in the top 0.05% (174 shared, p = 0.0004), but 30 books of 10,000+ words are denser, mostly other imitation scripture | **partly**: the two books stand out; the claim that nothing else approaches them does not hold |

## 1. Larsen, Rencher and Layton (1980)

**Run, by speaker as published.** Larsen et al. assigned every quoted segment of the book to its
originator by hand and published only each speaker's word count (their Appendix B). We rebuilt
that labelling with a model (`eval/speakers.py`, Sonnet, simulated; labels in
`replication/larsen_speakers.jsonl`): each chapter in 15-word units, every unit given to whoever
originally speaks it, a quotation within a quotation to the innermost speaker, and a parable's
characters to its teller. **Checked against their published counts**
(`replication/larsen_speakers_check.txt`): 16 of their 24 speakers within 10%, 20 within 20%
(Mormon 97,555 against 97,777; Benjamin 4,244 against 4,204; Zenos 4,282 against 4,230). The
four outside 20% are "the Lord quoted by Isaiah" (0.79), Nephi son of Helaman (1.23), the
angel (1.74: they count one particular angel, our label every angel) and the Father (1.42). One
convention was corrected after the first check: Jacob 5, Zenos's allegory, had gone to "the
Lord" inside it; Larsen evidently gave the whole allegory to Zenos, its teller, and the chapter
was relabelled with that rule.

Then their analysis: the 10 most frequent of their 38 function words, arcsine-transformed
relative frequencies, 1,000-word blocks; Jesus, Isaiah and the Lord quoted by Isaiah left out as
in their first analyses; speakers with at least two blocks (17; they had 21, four with about one
block). Candidates: Joseph Smith, Cowdery, Ethan Smith, Hunt, Phelps, Rigdon, Pratt, Spalding and
the *Lectures on Faith*, Book of Mormon-quoting samples left out (section 3).

**Result.** MANOVA across the 17 speakers, 215 blocks: Wilks' lambda 0.079, p = 8e-38. Leave-one-
out discriminant analysis put 4 of 215 speaker blocks with a nineteenth-century candidate.

**Also at narrator level** (Nephi 43, Jacob 9, Mormon 169, Moroni 25 blocks of the masked text):
Wilks' lambda 0.575, p = 1e-14; 11 of 246 blocks classified to a candidate.

**Comparison.** Both headline findings return, more strongly by speaker than by narrator: the
speakers differ in function-word use ("less than 1 in 100 billion", p. 232), and almost no
block resembles a nineteenth-century candidate (p. 234). The critique stands as well: blocks
from one book are not independent random samples, so the p-value overstates certainty by an
unknown amount, and differences between speakers may track genre (sermon, war narrative,
prophecy) as much as authorship.

## 2. Holmes (1992)

**Run.** All five of Holmes's variables on 10,000-word samples (Nephi 4, Mormon 16, Moroni 2),
three 1835 Doctrine and Covenants revelation samples (Joseph Smith Papers transcripts, private
repo), KJV Isaiah 3, Joseph Smith's own writing 3: Honoré's R, V2/V and Yule's K on all words,
and Sichel's alpha and theta on the spectrum of nouns, as he did (nouns tagged and lemmatised by
MorphAdorner's distributed nineteenth-century model; median 1,790 nouns and 381 noun types per
sample, against his roughly 1,900 and 360). Average-linkage clustering into three groups and
principal components, on the standardised variables.

**The Sichel fit, checked first on his own numbers.** `classic/sichel.py` fits alpha and theta by
minimum chi-square, as Holmes describes. On his own published noun spectra (Table 3) it returns
alpha 1.152 and theta 0.9613 for Moroni 1 (his 1.142 and 0.9618) and 1.015 and 0.9726 for Mormon
5 (his 1.006 and 0.9731); the small gap follows from cell pooling, which he does not specify (he
reports 10 degrees of freedom where ours has 13). His "10,000-equivalent" values do **not**
reproduce from the invariants he gives (b = alpha sqrt(1 - theta), c = theta / ((1 - theta) N)):
applied to his own alpha and theta they give 2.54 for Moroni 1, not his 2.97, and no single
choice of N recovers his values across samples. Ours applies the invariants as described; the
gap is stated, not fitted away.

**Result.** With all five variables, Joseph Smith's three samples form one cluster, Isaiah 1
and 2 a second, and every Book of Mormon narrator sample with all three revelation samples and
Isaiah 3 the third. With the three non-Sichel variables only, the grouping is the same except
that Nephi 1 and 2 join Isaiah 1 and 2.

**Comparison.** Matches all three of Holmes's findings: Joseph Smith's personal writing stands
apart, the prophets do not separate by prophet, and the revelations cannot be told from the
prophets. The critique also stands: these are vocabulary-richness measures, and Holmes's own
result shows their limit, since samples by the same prophet do not group together. (Hoover 2003,
https://doi.org/10.1023/a:1022673822140, is the usual citation for this critique; not yet read
here.) Our samples are cut from the 1830 text, where Holmes used a modern edited text, and the
finding survived the change.

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

Rigdon is first or second for 169 chapters (published 197). **The NSC gap is not our code:** run
on their counts in their own tool, R's `pamr` (version 1.57, `python -m eval.replicate
jockers-pamr`, `replication_jockers_pamr.json`), NSC at Schaalje et al.'s threshold of 0.44
gives exactly our first-choice counts (Cowdery 23, Pratt 8, Rigdon 67, Spalding 68,
Isaiah-Malachi 72, Barlow 0, Longfellow 1), and `pamr`'s cross-validated threshold, which moves
with the random folds (0 to 0.52 here), gives Rigdon 65 to 81. The printed Table 1 (Rigdon 93)
does not come back from the deposited data with the authors' tool; the deposit records a
tokenising correction made after publication, and the exact threshold they used is not
reported. Delta matches less well; its "probability assignments" are not described.

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

**Run.** Two versions (`python -m eval.replicate ensc`; `replication_ensc.json`).

- *Published method* (`classic/ensc_published.py`, ported from the authors' code in Funai 2010
  and checked in BOM-57), in their Book of Mormon design (2011, section 6): candidates Joseph
  Smith, Rigdon, Spalding, Cowdery, Pratt and Isaiah, no Barlow or Longfellow; Jockers et al.'s
  110 words; training texts composited to 4,000 words (theirs 2,000-6,000); shrinkage 2,
  lambda 4, the text-size adjustment on. Our candidate texts, Book of Mormon-quoting samples
  left out (section 3).
- *Our BOM-20 reconstruction*, which BOM-57 found not faithful, kept for the record.

**Result.**

| Chapters assigned | Unobserved author | Isaiah | Rigdon | Smith | Spalding | Cowdery | Pratt |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Published (2011, section 6) | 175 | 35 | 17 | 8 | 2 | 2 | 0 |
| Published method, our texts | 225 | 13 | 0 | 0 | 1 | 0 | 0 |
| Our BOM-20 reconstruction | 235 | 4 (Isaiah-Malachi) | 0 | 0 | 0 | 0 | 0 |

**Comparison.** The published conclusion returns, more strongly: most chapters fit none of the
candidates. Two differences: they split Rigdon into early and late texts (we hold one Rigdon),
and their Joseph Smith texts were Jessee's holographs (ours are BOM-13's); together these likely
account for the chapters they gave to Rigdon and Smith. Fewer chapters go to Isaiah here (13
against 35).

**Caveat.** BOM-57 showed that this method's "none" answer moves with the length and kind of the
candidate texts, and the 2011 text-size adjustment narrows but does not remove that. So agreement
with the published conclusion is a replication of it, not independent evidence for it. ENSC is
not used as evidence in this study unless it passes the benchmark (BOM-58).

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

**A limit of the registered rule, found here (corrected 2026-10-30).** Under the pre-registered
rarity rule (a 4-gram in at most 5 documents) Hunt's *The Late War* shares 1 rare 4-gram
(p = 0.05), because the corpus holds nine printings of it: everything it shares with the Book of
Mormon sits in at least eight documents. (A first version of this paragraph quoted "1 rare
4-gram" from the wrong book: the name pattern matched any title about the late war, and under
the registered rule the best-ranked match was Thomas Brockway's 1784 sermon *America Saved*. The
pattern is now pinned to Hunt's title and his *Historical Reader*.) Counting document frequency
by *text*, with copies found by their content (BOM-60, `reuse.rare.copy_clusters`), Hunt's nine
printings fall into four groups and *The Late War* shares 15 rare 4-grams, rank 177 of 221,344,
p = 0.0008. This does not change the replication, which uses Johnson's rule.

## Gaps that cannot be closed

- **Johnson and Johnson's own collection.** They compared against over 100,000 books they
  assembled; that set is not published. We ran their rule on ours (221,344 period volumes), so
  the method replicates exactly and the collection does not.
- **Holmes's modern edited text.** He cut his samples from a later edited Book of Mormon; ours come
  from the 1830 text. This is deliberate (the project studies the 1830 text) and his findings
  survived it. His 10,000-equivalent Sichel values also do not reproduce from the formulas he
  gives (section 2).
- **Jockers et al.'s printed tables.** Their NSC reproduces as a method on their deposited data,
  in their own tool, to the same cross-validated error; their printed chapter counts do not come
  back from that data in that tool (section 3). The threshold they used is not reported.
- **Schaalje et al.'s candidate texts.** We hold one Rigdon, not their early and late corpora, and
  different Joseph Smith holographs; their smoothing across chapters is not reproduced (section 4).
- **Larsen et al.'s quoted speakers.** Rebuilt by model labelling (simulated) and checked
  against their published word counts: 16 of 24 within 10%; the exact segment boundaries they
  drew by hand cannot be recovered (section 1).

## Where the results match, where they differ, and why

- **They match where the question is whether texts differ.** Larsen's narrators differ in their
  function words, and Holmes's prophets do not separate from each other while Joseph Smith's own
  writing does. Both return on the 1830 text, with the same caveats the critics raised: blocks of
  one book are not independent samples, and vocabulary richness is a weak measure of authorship.
- **They differ where the question is who wrote it, and the reason is the candidate texts.**
  Jockers et al.'s method reproduces exactly on their own data, but the leading candidate moves
  with the writings chosen to stand for each man: their Rigdon is mostly from 1864, and swapping
  in other genuine Rigdon text halves his count. A method that must name someone from a list
  names whoever's samples sit nearest.
- **The open-set conclusion returns, but depends on choices.** ENSC as published sends most
  chapters to an unobserved author (theirs 73%, ours 94%), but BOM-57 showed its "none" answer
  moves with the length and kind of the candidate samples.
- **The rare-phrase signal is real but not unique.** *The Late War* shares far more rare phrasing
  than chance gives, and so do some thirty other books written in imitation of scripture.
- **Two things we got wrong first, and fixed.** Our first ENSC was not the published method
  (BOM-57), and some of our candidate samples quoted the Book of Mormon (section 3). Both are now
  corrected, and the first results are kept beside the corrected ones.

These are the reasons the pre-registered study requires an open-set method that passes the
section 7 benchmark before any attribution is reported, screens candidate texts for quotation of
the Book of Mormon, and reports how results move with the choice of candidate samples.

Every review step in this project is simulated by an AI model and labelled as such.
