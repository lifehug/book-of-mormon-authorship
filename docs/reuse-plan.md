# Exact text reuse: the plan, written before any run (BOM-23)

Committed 2026-10-31, before passim has been run for reuse on any text. 5.5 registers "exact and
near-exact reuse by passim over the masked text against the deduplicated corpus"; it does not fix
how a corpus of 221,351 volumes is searched, what counts as a reused passage, or the score the
known-answer test needs (Amendment 9). Those are fixed here and registered before the Book of
Mormon is run.

## Two outputs

1. **The reuse table** (5.5, as registered). The KJV-masked 1830 Book of Mormon against every
   eligible period volume (1780-1830, deduplicated, OCR exclusions applied), its sealed copies
   (4.2) left out. Every aligned passage: source volume, offsets in both texts, length in tokens,
   token identity. No text. Two reference tables are built the same way: Hunt's *The Late War*
   (1816), against volumes printed before 1816, and one 1820s sermon collection drawn with seed
   `"bom23-sermon"` from the registered sermons control, against volumes printed before it. The
   issue's other suggested control, Luke, is the King James text, which masking removes.
2. **The known-answer score** (Amendment 9). A whole-corpus search cannot be the score, because
   texts differ in how many earlier volumes the corpus holds: the Book of Mormon has 203,717
   eligible volumes in the 70 years behind it, *Ossian* (1760) has 10,333, and a text with more earlier books
   to search finds more matches whatever its origin. So every text, the Book of Mormon included,
   is searched against the same number of volumes from the same span of years before it:

   - **sample:** `reuse.matched_volumes` (2,000) English volumes with text, drawn with a seed
     derived from the text's key, from those dated in the `reuse.window_years` (70) years before
     the year its English was written (`metadata.dates.effective_year`); one copy per text
     (deduplication keepers), OCR exclusions applied, Chronicling America newspapers left out as
     in every corpus search, Bibles and New Testaments left out (the target is already KJV-masked), and the
     target's own copies and editions left out (by author and title);
   - **draws:** `reuse.matched_draws` (3), each with its own seed; the score is the mean;
   - **score:** the share of the text's masked tokens covered by at least one aligned passage
     from the sample; higher means it draws more on writing of its own time.

   The year a text's English was written, and the source of each date:

   | Text | Year | Basis |
   | --- | --- | --- |
   | Book of Mormon | 1829 | dictated April-June 1829 |
   | *Testaments of the Twelve Patriarchs* | 1581 | the English text is Arthur Golding's translation of Grosseteste's Latin |
   | *Book of Enoch* | 1821 | Laurence's first edition |
   | *Apocryphal New Testament* | 1726 | Hone (1820) reprints the translations of Jeremiah Jones (1726) and William Wake (1693); the later date |
   | Josephus | 1737 | Whiston's translation |
   | Koran | 1734 | Sale's translation |
   | Herodotus | 1791 | Beloe's translation |
   | Homer | 1715 | Pope's *Iliad* began appearing |
   | Hesiod | 1812 | Elton's first edition |
   | *Sacontala* | 1789 | Jones's translation |
   | *Ossian* | 1760 | *Fragments of Ancient Poetry*; *Fingal* followed in 1761-62 |
   | Rowley poems | 1768 | written by Chatterton 1764-70 |
   | *Book of Jasher* | 1751 | Ilive's first edition |
   | Ireland's Shakespeare papers (secondary) | 1795 | forged 1794-95 |
   | *Castle of Otranto* (secondary) | 1764 | first edition |

   Eligible volumes in each window, and the share printed before 1700 (old spelling; see below):

   | Text | Window | Volumes | Before 1700 |
   | --- | --- | --- | --- |
   | Book of Mormon | 1759-1828 | 203,717 | 0% |
   | *Twelve Patriarchs* | 1511-1580 | 2,670 | 100% |
   | *Enoch* | 1751-1820 | 141,798 | 0% |
   | *Apocryphal New Testament* | 1656-1725 | 29,550 | 94% |
   | Josephus | 1667-1736 | 23,212 | 90% |
   | Koran | 1664-1733 | 24,143 | 91% |
   | Herodotus | 1721-1790 | 25,579 | 0% |
   | Homer | 1645-1714 | 36,895 | 96% |
   | Hesiod | 1742-1811 | 93,809 | 0% |
   | *Sacontala* | 1719-1788 | 20,292 | 0% |
   | *Ossian* | 1690-1759 | 10,333 | 69% |
   | Rowley | 1698-1767 | 5,151 | 27% |
   | *Jasher* | 1681-1750 | 17,139 | 84% |
   | Ireland papers | 1725-1794 | 37,735 | 0% |
   | *Otranto* | 1694-1763 | 7,644 | 55% |

   The smallest window holds 2,670, so 2,000 can be drawn for every text.

## Finding reused passages

Settings are 5.5's passim, with Amendment 2's registered values: word 5-grams, a passage of at
least 8 tokens, gaps of at most 100 characters, relative overlap 0.5, passim's default
document-frequency cap of 100, at least 4 shared 5-grams to seed an alignment (the value chosen
under Amendment 2 for masking). Two implementation steps make a corpus-wide run feasible without
changing what it finds:

1. **Prefilter (lossless).** One pass over every volume records which of each target's 5-grams it
   contains. passim cannot align a pair sharing fewer than 4 seed 5-grams, so volumes with fewer
   are not passed to it. This cuts an estimated 9 days of alignment to hours.
2. **Document frequency at the scale of the search.** passim counts document frequency within its
   own input, so batching would change which 5-grams can seed an alignment. passim is therefore
   run with its cap off, and an alignment is kept only if it contains at least 4 distinct 5-grams
   whose document frequency in the whole search (the corpus for output 1, the 2,000-volume sample
   for output 2) is at most 100: the alignments a single passim run over the whole search would
   have seeded.

A kept passage is reported with its token identity (the share of the target's tokens in the
passage matching the source, as in masking). No identity floor beyond passim's own alignment is
applied; the table reports identity so a reader can set one.

## Known weaknesses, stated now

- **OCR.** Period volumes after 1780 are mostly OCR; earlier ones are mostly hand-keyed (TCP).
  OCR errors break 5-grams, so windows before 1780 can find more matches than windows after it.
  The Book of Mormon's window (1759-1829) is mostly OCR, which works against finding reuse in it.
- **Spelling.** Volumes before 1700 keep their own spelling ("vnto"), which breaks matches; this
  falls unevenly: five of the nine genuine translations have 90-100% of their window before 1700,
  the three presented-as-ancient texts 27-84%. Old spelling lowers a score, so it can make the
  genuine texts look less like their own time and the groups look more separate than they are.
  Each score is reported beside its window's pre-1700 share, and a separation under Amendment 9
  counts only if it also holds among the texts whose windows are mostly before 1700: *Ossian* and
  *Jasher* must each score above the median of the *Twelve Patriarchs*, *Apocryphal New
  Testament*, Josephus, Koran and Homer. Otherwise the test is reported as not shown to separate
  the groups.
- **A copy found by author and title can be missed**; an edition missed this way inflates the
  score. Any sample volume aligned to more than half the target is listed for inspection, and the
  score is reported with and without such volumes.

## Registration

Registered as Amendment 10 (OSF revision 6ae620454ae19487e2bde267, 2026-10-31), before passim was
run for reuse on any text.

## Implementation notes (after registration, before any Book of Mormon result)

**2026-10-31, the stretch margin is not neutral.** To keep passim's input small, each candidate
volume is passed as the stretches around its seed 5-grams with a margin of tokens either side
(250, widened to 2,000 and then the whole volume for any passage that reaches a stretch's edge).
On the *Jasher* test draw, a 1,000-token margin found 5 passages and the 250-token margin 7; the
two extra (a blessing on Ashur echoing Deuteronomy 33:24, and another copy of 1 Peter 1:4) are
genuine. passim's candidate step depends on how text is packaged, as BOM-16 found for batches
(Amendment 6), so the margin changes which passages are found, not only how much is read. The
prefilter itself stays lossless (a volume it drops cannot be aligned). Every search, the Book of
Mormon's included, runs with the same margins, so the comparison stays like for like; the margin
is reported with every passage.


## Known-answer result (2026-11-01; `python -m reuse.exact separation`)

**The test does not separate the groups: uninformative on the translation question.** Mean share
over three draws of 2,000 matched-window volumes; higher was declared to mean "its own time".

| Group | Text | Score |
| --- | --- | --- |
| presented as ancient | *Ossian*, Rowley, *Jasher* | 0.0000, 0.0000, 0.0028 |
| genuine | Hesiod, Herodotus, *Enoch*, *Apocryphal NT* | 0.0203, 0.0090, 0.0044, 0.0041 |
| genuine | *Sacontala*, Koran, Homer, Josephus | 0.0006, 0.0004, 0.0003, 0.0002 |
| genuine | *Twelve Patriarchs* | 0.2287 (0.0045 without a missed own copy) |
| secondary | Ireland papers, *Otranto* | 0.0080, 0.0000 |
| target | Book of Mormon | 0.0005 |

U = 4 of 27, exact p = 0.964 (rule: p <= 0.01), the same with the missed copy left out. The
spelling-era check passes for *Jasher* and fails for *Ossian*. The texts presented as ancient
quote their own century's books *less* than genuine translations quote earlier English: a
forger writing in an invented ancient voice avoids verbatim borrowing, while a genuine
translation shares wording with earlier translations and commentaries on the same work. Exact
reuse therefore stays in the study as a description of the Book of Mormon's sources (the reuse
table), not as evidence on whether it is a translation.

**A missed own copy.** One *Twelve Patriarchs* draw scored 0.677: almost all of it is
`tcp:A09151`, the 1576 printing of the same English translation (Gilby), whose old-spelling
title ("twelue patriarches") escaped the title rule. It is listed in `MISSED_OWN_COPIES` and
the score is reported both ways; leaving it out can only lower a genuine score, so it cannot
change a failed separation into a pass. The full tables are read for the same leak.

## The reuse table (2026-11-01; `python -m reuse.exact sources <search>`)

Each text against every eligible volume printed before its year, its own copies left out.
"Later" means the volume's own text names a year after the target's more than any other (and at
least 10 such mentions), against a catalog date before it; that rule and the kinds below were
written after seeing the table and are **post hoc**.

| Target | Passages | Volumes | Share covered | Volumes printed later by their own text | Share without them |
| --- | --- | --- | --- | --- | --- |
| *The Late War* (1816) | 1,680 | 401 | 8.92% | 73 | 8.87% |
| Newton's *Works* vol. 4 (1821, the sermons control) | 746 | 626 | 2.47% | 46 | 2.39% |
| Book of Mormon (1829) | 58 | 47 | 0.52% | 17 | 0.16% |

**The Book of Mormon's 47 volumes, by kind (post hoc):**

- **Later quotation, 17 volumes.** These are texts quoting the Book of Mormon whose catalog
  date is decades too early: Congressional serial set volumes catalogued 1817 whose text names
  1865-1905 most (Jacob 2 on one wife, Ether 12, the sacrament prayers); *The Millennial
  Harbinger* catalogued 1830 (1831, Campbell's review); *The Monthly Review* catalogued 1826
  (1842); *Herald of Gospel Liberty* catalogued 1808 (1909-1918); *The Bible Christian* and
  *Evangelical Magazine* catalogued 1830 (1840-1843). They hold all of the long, high-identity
  passages. The registered seal (4.2: at least 20 distinct original 12-token strings) catches 9
  of them; the other 8 quote too briefly to reach it. BOM-64 corrects their dates.
- **Missed Bible text, 0.** No passage is mostly King James wording (largest share 0.37).
- **Shared period phrase, 30 volumes, all printed before 1830 by their own text.** These are
  short (9-46 tokens) and loose (identity 0.27-0.67, one at 0.89 over 9 tokens) matches on
  religious stock phrases: "the Lord cannot look upon sin with the least degree of allowance"
  (Ravenscroft's *Works*); "I fear not what man can do ... perfect love casteth out all fear"
  (Job Scott's *Journal* in five printings, *Piety Promoted*); "healing the sick, raising the
  dead, causing the lame to walk" (Archibald M'Lean, *The Reformer*, Samuel Stanhope Smith's
  *Sermons*); "the distance of a day and a half's journey" (four magazines); "turn ye, turn
  ye, why will ye die" (Thomas Taylor); "if it so be that there is a devil and a hell"
  (*Christian Intelligencer*). Several sit at the edge of a King James chapter the Book of
  Mormon reproduces, where its own added words meet the biblical text (Isaiah 48 and 50 in
  commentaries and *The Jew*), so their King James share is low but their content is biblical. Volumes
  dated 1830 by their own text (Ravenscroft's *Works*) are flagged; they may postdate the
  Book of Mormon by months.

**The reference texts.** *The Late War*'s 8.9% is mostly the War of 1812's own documents, which
it retells: *British and Foreign State Papers*, *Niles' Weekly Register*, Congress's debates and
the treaties in the *Statutes at Large* (identity 0.88-0.93 over thousands of tokens). Newton's
sermons share 2.4% with the evangelical magazines and tracts of his circle; 128 of their 746
passages are mostly King James wording the mask missed.

**Reading.** On exact reuse the Book of Mormon, KJV masked, shares 0.16% of its text with books
printed before it, against 2.4% for an 1821 sermon collection and 8.9% for *The Late War*; its
pre-1830 matches are short stock phrases. Under Amendment 9 this test does not separate
translations from compositions presented as ancient, so the number describes the text and is not
evidence on the translation question.

**Rechecked under BOM-64's corrected dates** (`python -m reuse.exact redate`, `redated.json`;
details in `docs/date-audit-plan.md`). The Book of Mormon's table drops to 0.26% on dates alone
(16 of the 17 later quotations move past 1830; the seal takes the seventeenth, for 0.16%), the
sermons' to 2.28% and *The Late War*'s to 8.74%. The known-answer test is unchanged (U = 4 of 27,
p = 0.964). Nothing above changes.
