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
