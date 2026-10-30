# Prior Book of Mormon stylometry: designs to replicate (BOM-22)

Written 2026-10-30, before any replication is run, so the replications cannot be fitted to an
expected answer. For each study: what it did, what it found, what reproducing it needs, and what
could not be recovered. BOM-22 runs these *published* methods on the Book of Mormon (the one
exception to the seal of 4.2); the project's own methods are not used here.

Sources were read in full where available. Paper texts are not copied into the repository
(copyright); figures below are cited to page or section.

## 1. Larsen, Rencher and Layton (1980), "Who Wrote the Book of Mormon? An Analysis of Wordprints"

*BYU Studies* 20(3): 225-251.

- **Units.** 24 Book of Mormon "authors" (narrators and quoted speakers) in 251 blocks of about
  1,000 words (Mormon 98 blocks; three speakers one block each). In the first analyses Jesus,
  Isaiah and "the Lord quoted by Isaiah" were dropped as too close to the Bible, leaving 21.
- **Features.** Non-contextual function words, Appendix C: the **38 frequent words** (and, the, of,
  that, to, unto, in, it, for, be, which, a, not, came, pass, behold, all, this, now, with, yea,
  should, by, as, upon, but, also, from, there, because, these, therefore, when, if, even, into,
  would, forth) and **42 infrequent** (out, after, among, against, thus, according, again, may, no,
  wherefore, before, might, or, on, at, away, an, so, over, O, could, about, must, then, every,
  what, nevertheless, until, exceeding, thereof, through, towards, verily, notwithstanding,
  whatsoever, lest, whether, nay, ever, whereby, thereby, between). The headline MANOVA used the
  10 most frequent; arcsine-transformed relative frequencies.
- **Comparison authors.** 90 blocks from Joseph Smith, W. W. Phelps, Oliver Cowdery, Parley P.
  Pratt, Sidney Rigdon, Solomon Spalding, the article "Paracletes" and the *Lectures on Faith*.
- **Methods.** MANOVA (RUMMAGE), cluster analysis, and discriminant/classification analysis on
  2,000-word blocks.
- **Findings.** "The statistical odds that a single author wrote the book are less than 1 in 100
  billion" (p. 232; the authors note this assumes random samples); "none of the Book of Mormon
  selections resembled the writing of any of the suggested nineteenth century authors" (p. 234).
- **Replication needs.** Narrator labels per passage (BOM-17 has narrators, not quoted speakers
  such as Jesus or Isaiah), candidate texts (ours, plus Lectures on Faith and "Paracletes").
- **Critique to test.** Blocks from one book are not independent random samples, so the MANOVA
  p-value overstates; differences between narrators may track genre (sermon, war narrative,
  quotation) rather than authorship.

## 2. Holmes (1992), "A Stylometric Analysis of Mormon Scripture and Related Texts"

*Journal of the Royal Statistical Society A* 155(1): 91-120.

- **Units.** 14 "pure" prophet samples of about 10,000 words, hand-separated from BYU's scripture
  database (a modern edited text, not the 1830 edition): Nephi x3, Jacob, Lehi (4,606), Moroni x2,
  Mormon x5, Alma x2 (section 4.1). Controls: Joseph Smith's personal writings (from Jesse 1984),
  three Doctrine and Covenants samples (D1 = 1828-1829 revelations), KJV Isaiah, Book of Abraham.
- **Features.** Five vocabulary-richness variables: Honoré's R (hapax legomena), V2/V (hapax
  dislegomena), Yule's K, and the 10,000-word-equivalent Sichel parameters alpha and theta.
- **Methods.** Hierarchical cluster analysis, principal components, two-variable plots.
- **Findings.** Joseph Smith's personal writings and Isaiah form separate clusters; the prophets
  do not cluster by prophet ("variation within samples from the same prophet is generally as
  great as any variation between the prophets", section 6); two of three revelation samples are
  indistinguishable from the prophets.
- **Replication needs.** The same prophet samples from the 1830 text (BOM-17 narrators), Joseph
  Smith's holograph writing (BOM-13), D&C revelations (Joseph Smith Papers), KJV Isaiah (BOM-06).
- **Critique to test.** Vocabulary richness is weak for attribution (Hoover 2003); the samples come
  from an edited modern text.
- **Recovered 2026-10-30.** The Sichel fit: minimum chi-square on each sample's *noun* frequency
  distribution, then 10,000-word-equivalent alpha and theta (section 2.4, Tables 3-4). Full text
  in the private repo; https://doi.org/10.2307/2982671.

## 3. Jockers, Witten and Criddle (2008), "Reassessing Authorship of the Book of Mormon Using Delta and Nearest Shrunken Centroid Classification"

*Literary and Linguistic Computing* 23(4): 465-491. Design from the paper as reproduced at
solomonspalding.com (Tables 1-2 and Appendix A not reproduced there).

- **Known samples (217).** Cowdery 19, Pratt 53, Rigdon 23 (all post-1830), Spalding 17 (Manuscript
  Story), KJV Isaiah-Malachi 70, controls Joel Barlow 12 (*Columbiad*, 1825) and Henry W.
  Longfellow 23 (*Song of Hiawatha*, 1855). Joseph Smith excluded for want of a reliable corpus.
- **Units.** 239 Book of Mormon chapters (modern LDS divisions) of the 1830 text, chapter headings
  removed, **biblical passages left in** deliberately.
- **Features.** 110 words: in every author's samples and in the Book of Mormon (521), mean relative
  frequency at least 0.1% (114), minus god, ye, thy, behold.
- **Methods.** Delta; nearest shrunken centroids (R `pamr`), columns centred and scaled, tuned by
  repeated random train/test cross-validation (NSC error 8.8%, Delta 11.1%).
- **Findings.** Rigdon first or second for 197 of 239 chapters, Spalding 110, Isaiah-Malachi 101,
  Cowdery 37, Pratt 24; 85% of the text attributed to Rigdon, Isaiah-Malachi or Spalding by NSC.
- **Replication needs.** Barlow's *Columbiad* (in the corpus or Gutenberg) and Longfellow's
  *Hiawatha* (Gutenberg; post-1830, outside the corpus); our candidate texts.
- **Critique to test.** Closed set: every chapter must go to one of the listed authors, so the
  result cannot say "none of these" (Schaalje et al. 2011); quotation left in.
- **Recovered 2026-10-30 (the paper, Appendices A and B; https://doi.org/10.1093/llc/fqn040).**
  Candidate sources, with Old and New Testament passages removed from every one: Rigdon, his
  *Book of the Revelations of Jesus Christ to the Children of Zion* (written 1864; transcription
  of the Stephen Post Collection, University of Utah), the revelations to Phebe Rigdon, and 14
  *Millennium* articles (1833-35); Cowdery, *Messenger and Advocate* writings; Pratt, the
  *Autobiography*, *Mormonism Unveiled* (1838), *Plain Facts* (1840) and *The Angel of the
  Prairies* (1880); Spalding, the Oberlin manuscript with its appended letter. Book of Mormon:
  1830 text with modern chapters, prefaces excluded. The 110 words are listed (Appendix B); ours
  differ by five (we add s, thee, thou; they add hand, pass). Our first replication used the
  candidates' text unmasked, which is not what they did.

## 4. Schaalje, Fields, Roper and Snow (2011), extended nearest shrunken centroids (ENSC)

*Literary and Linguistic Computing* 26(1): 71-88; companion review *Mormon Studies Review* 23(1):
87-111; restated in *Journal of Book of Mormon Studies* 21(1), 2012.

- **Design (known).** Open-set NSC: a chapter is assigned to "none of the above" when no candidate
  centroid fits; candidates as in Jockers et al. plus Joseph Smith; texts of varying size.
- **Findings (as reported in the secondary literature).** Most chapters fit none of the
  candidates; the authors conclude no nineteenth-century candidate is supported.
- **Not recovered.** The per-chapter assignments and the exact open-set rule (BYU ScholarsArchive
  refused automated access, and the LLC paper is paywalled). The replication uses our ENSC
  (`classic/ensc.py`, after Fields et al., calibrated in BOM-21) and compares at the level of the
  published conclusion; the gap is stated in the report.

## 5. Chris and Duane Johnson (2013), "A Comparison of The Book of Mormon and The Late War"

https://github.com/wordtreefoundation/thelatewar (site, October 2013).

- **Design.** The Book of Mormon compared with over 100,000 pre-1830 books; a 4-gram is *rare* if it
  occurs in fewer than one book per thousand; biblical matches removed; books ranked by the density
  of shared rare 4-grams.
- **Findings.** Over 100 rare 4-grams shared with *The Late War*; "no other book, aside from The
  First Book of Napoleon, approaches the density".
- **Replication needs.** Our corpus (226,798 period works), the KJV masks, rare = under 1 per 1,000
  books (theirs) and also 5.5's document frequency at most 5 (ours, for comparison), the target's
  own copies excluded (BOM-45).
- **Critique to test.** No null: how many books would show this density by chance (BOM-45's whole-
  corpus null answers that); shared phrases may be common outside their corpus (FAIR's critique).

## Data the replications need beyond what the project holds

| Item | For | Source |
| --- | --- | --- |
| Lectures on Faith (1835), "Paracletes" (1836) | Larsen | Joseph Smith Papers / Messenger and Advocate (public domain) |
| Doctrine and Covenants revelations, Book of Abraham | Holmes | Joseph Smith Papers |
| Barlow, *The Columbiad* (1807/1825) | Jockers | corpus or Project Gutenberg |
| Longfellow, *The Song of Hiawatha* (1855) | Jockers | Project Gutenberg |
| Quoted-speaker labels (Jesus, Isaiah, the Lord) | Larsen | to derive from the 1830 text and BOM-16's KJV masks |
