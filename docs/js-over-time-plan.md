# Plan and attribution rule: prose over time against the Book of Mormon's style (BOM-73)

Written 2026-11-10, before any document for this study is fetched or scored. Owner's question:
did Joseph Smith's writing, and that of other people of the period, grow closer to the Book of
Mormon's style after 1830? Sources and attribution evidence: `docs/js-over-time-research.md`.
Post hoc with respect to the registration (filed as an amendment before scoring), and reported as
its own study beside the paper, not as a test of authorship: everyone measured here had read the
book or wrote after it.

## 1. What counts as Joseph Smith's own words

Decided from the Joseph Smith Papers (JSP) source notes and handwriting marks, never from what a
document says:

| Tier | Admitted | Source of the decision |
| --- | --- | --- |
| **H, holograph** | documents JSP lists as "written wholly or largely" in his hand; in mixed documents (journals 1832-34, 1835-36) only the passages JSP marks in his hand | JSP, *Documents in Joseph Smith's Handwriting* (34 documents, fetched 2026-11-10) and each transcript's handwriting marks |
| **D, dictated** | documents whose JSP source note says he dictated them, with the scribe recorded | JSP source notes |

**Excluded** before any scoring: revelations and other texts in a scriptural register (the
question is his ordinary prose; revelations are reported as their own line), the Book of Mormon
manuscripts, the Bible revision; documents composed by clerks or editors (the 1838 journal after
its dictated opening, the 1839 Memorandum, the 1841-44 journals of Richards and Clayton, the
History 1838-56 beyond Mulholland's dictated pages, *Times and Seasons* editorials, *Appeal to the
Green Mountain Boys*, *Views of the Powers and Policy*, the Wentworth letter); reports of sermons;
legal and financial forms (pay orders, warrants, agreements, authorizations), which are formulaic;
and every Book of Mormon quotation (Amendment 43's rule). H and D are kept as separate lines and
also pooled.

## 2. Comparison groups

- **Exposed:** Oliver Cowdery, Parley P. Pratt, W. W. Phelps, Sidney Rigdon: signed items only
  (rules 11-17 of `docs/candidates.md`), from the Internet Archive and JSP; pieces ghost-written for
  Joseph Smith go to their author.
- **Unexposed:** American religious prose by writers with no documented reading of the book,
  1829-44: Barton Stone's *Christian Messenger*, the *Methodist Magazine and Quarterly Review*, the
  *Religious Intelligencer*, the *Evangelical Magazine and Gospel Advocate*, Charles Finney, Lyman
  Beecher; any piece about Mormonism excluded.
- **Read it, not a follower (reported separately; changed 2026-11-10, before any fetch or
  measurement):** the *Millennial Harbinger* (Alexander Campbell). Campbell read the book and
  reviewed it in print ("Delusions", February 1831), and Rigdon had been his associate, so he cannot
  stand for the unexposed. His line shows what reading the book without adopting it does; it is
  never pooled with either other group.

## 3. Time bins and floor

1829-30, 1831-33, 1834-36, 1837-39, 1840-44 (by date written). A writer-bin needs at least 2,000
words after masking; thinner bins are reported as empty, never padded from a neighbour.

## 4. Measures (fixed now)

The Book of Mormon narrative, King James spans masked, as the reference. For each writer-bin, its
distance to the Book of Mormon by Burrows' and Cosine Delta (300 most frequent words, z-scores
from all bins of all groups pooled) and by the 297M and 590M style encoders (cosine). Each
writer-bin is cut into 2,000-word blocks; a bin's value is the mean over its blocks, with a
bootstrap interval over blocks.

## 5. Reading (fixed now)

- **Influence** is supported only if Joseph Smith's line, and the exposed group's, move toward
  the book over the bins while the unexposed group's does not (Campbell's line is reported beside
  them and does not enter the rule) (slope compared by permutation of
  bin labels within writer, 10,000 permutations).
- **No pre-1830 baseline** of his ordinary prose exists (1829-30 holds under 1,500 words), so a
  drift cannot show that his style was not already close to the book's before 1830.
- Register, topic (church affairs) and scribes can each move a line; the H-only line is the check
  on scribes.

## 6. Steps

1. Inventory: the JSP documents by the rule above, with tier, date, scribe (`data/js_time/sources.json`).
2. Fetch (private repo; the fetcher's JSP settings, owner's decision of 2026-10-25).
3. Exposed and unexposed texts from the Internet Archive (public).
4. Clean, mask, bin; report the words per writer-bin before measuring.
5. Measure and plot; file the result beside the paper.
