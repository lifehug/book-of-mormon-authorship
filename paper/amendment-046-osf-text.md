# Amendment 46: Joseph Smith's prose over time against the Book of Mormon's style (BOM-73)

*Filed 2026-11-10. Post hoc: after unblinding, on the owner's question; filed before any text for
this study is scored.*

---

**Amendment 46, filed 2026-11-10, post hoc: after unblinding, before any BOM-73 scoring.** A study
added beside the paper, not a test of authorship (everyone measured read the book or wrote after
it): did Joseph Smith's ordinary prose, and that of others who read the Book of Mormon, move toward
its style after 1830, while religious writers who had not read it did not?

*Groups.* (1) Joseph Smith: Joseph Smith Papers documents of 1833-1844 in his own hand (only the
passages the edition marks in his hand, in mixed documents) or recorded in the source notes as
dictated by him, kept as separate lines and pooled; revelations, reports of sermons, clerk- or
editor-composed texts and formulaic legal and financial forms excluded (`data/js_time/sources.json`,
`docs/js-over-time-plan.md` section 1). (2) Readers who followed it: Oliver Cowdery, Parley P. Pratt,
W. W. Phelps and Sidney Rigdon, signed or otherwise attributed items only, each item dated by its
issue or imprint; an item that cannot be placed in one period is dropped. (3) Unexposed: the
*Methodist Magazine and Quarterly Review*, the *Evangelical Magazine and Gospel Advocate*, the
*Religious Intelligencer* (the first issue of each quarter on the Internet Archive), and books by
Charles Finney and Lyman Beecher (`data/js_time/controls.json`, 158 items with Alexander Campbell's).
(4) Alexander Campbell's *Millennial Harbinger*, 1831-44, reported as a line of its own and never
pooled: he read and reviewed the book in 1831.

*Preparation.* Every text is King James masked at the frozen settings of section 4.4 and has Book of
Mormon quotations removed by Amendment 43's rule; in groups 3 and 4 any block mentioning Mormonism
is dropped. The Book of Mormon narrative, King James masked, is the reference.

*Periods and floor.* Written 1829-30, 1831-33, 1834-36, 1837-39 and 1840-44. A writer-period with
fewer than 2,000 masked words is reported empty, never padded from a neighbouring period.

*Measures.* For each writer-period, cut into 2,000-word blocks: distance to the Book of Mormon by
Burrows' and Cosine Delta (300 most frequent words, z-scores over all blocks of all groups) and by
the 297M and 590M style encoders (cosine); the period's value is the mean over its blocks with a
1,000-resample bootstrap interval over blocks. Each measure is reported separately; none is
combined.

*Reading.* Influence is supported only if Joseph Smith's line and the readers' move toward the
book across periods while the unexposed group's does not: each group's slope of distance on
period is compared with the unexposed group's by permuting period labels within writer (10,000
permutations, seed `bom73`); Campbell's line is reported beside them and does not enter the rule.
No ordinary prose of Joseph Smith survives from before 1830, so a drift cannot show that his style
was not already close to the book's. Register, topic and scribes can each move a line; the
own-hand line is the check on scribes. Values in `config/preregistered.yaml` `js_time`.
