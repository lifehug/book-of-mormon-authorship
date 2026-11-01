# Rare phrases: the plan (BOM-24)

Committed 2026-11-01. **Not written blind.** The Book of Mormon's 4-grams were already counted in
every period volume for BOM-22's replication of Johnson and Johnson (2013), a published-method
replication the seal allows (`data/reuse/bom/hits.parquet`, scanned before BOM-64), and its
ranking under the registered rule was seen there: by text, *The Late War* ranks 177th, p =
0.0008 (`data/benchmark/replication_johnson.json`, `paper/replication-report.md` section 5). So
every choice below that is not already registered (points 2-5) is made after that result and is
**post hoc**; none of them changes the registered score, threshold or significance rule. The
known-answer scans (below) have not been run.

## What is already registered

- **5.5:** for each 4-gram of the target, its document frequency across the corpus; a source's
  score is the length-normalised count of the 4-grams it shares with the target whose document
  frequency is at most `borrowing.max_df` (5): rare shared 4-grams per `borrowing.per_words`
  (10,000) words of the source.
- **6.5 and Amendment 7, Change 6:** a source is a significant parallel if its score is above the
  99th percentile (`borrowing.null_percentile`) of the null, and the null is the whole eligible
  period population, not a sample (BOM-45: a 500-volume sample's 99th percentile is mostly
  noise); significance by empirical p-value at most 0.01, ties counted against the source; the
  target's own copies (the sealed copies, 4.2) are left out of every document frequency.
- **Amendment 8, Change 3 (post hoc):** document frequency counts texts, copies found by content
  (`reuse.rare.copy_clusters`, shared-gram Jaccard at least 0.8), so a reprinted source can still
  share a rare phrase; the registered by-volume count is reported beside it.
- **The target:** the 1830 text with BOM-16's King James spans removed (`reuse.rare.bom_text`), as
  the Johnsons removed biblical matches.
- **The corpus:** every eligible period volume (1780-1830 by `metadata.dates.effective_year`, so
  with BOM-64's corrections; text; deduplication keepers; OCR exclusions; no newspapers).

## Fixed here

1. **The scan.** BOM-22's scan is reused: it covered every volume then dated 1780-1830, so after
   BOM-64 (which only moves volumes later) it holds the whole current population and the moved
   volumes too. **Volumes BOM-64 moved out of the period** are not in the population, the null or
   the document frequencies, but they are scored with the same document frequencies and
   listed in their own table with catalog and corrected years (decided in BOM-64 before this
   test, because about one moved volume in five may truly be pre-1830).
2. **Genre.** The issue asks for genre normalisation. The registered significance is against the
   whole population. Each source also gets its percentile within its own primary genre label
   (`data/catalog/genre.parquet`; "uncertain" and parse failures as one stratum), reported beside
   it. Length is already normalised by the per-10,000-words score. A source is reported as
   significant by the registered rule only.
3. **Confidence intervals.** By bootstrap over the target: its masked text cut into
   `borrowing.block_words` (1,000) word blocks, resampled with replacement
   `borrowing.bootstrap` (1,000) times with seed `bom24-boot`; each resample re-counts every
   source's rare shared 4-grams with the resampled blocks' multiplicities (document frequencies
   unchanged), and each source's percentile in the population is recomputed. Reported: 95%
   percentile intervals of the score and of the percentile.
4. **Imitation scripture as a group** (owner, 2026-10-30). *The Late War* (Hunt, 1816; every
   printing as one text) and *The First Book of Napoleon* (1809) are each placed against the
   curated pseudo-biblical list of Amendment 6 (18 works, `data/controls/pseudo_biblical_curated.txt`;
   *Napoleon* is one of them and is compared with the other 17), so the question is whether they
   share more rare phrases with the Book of Mormon than other books in the same style do. Reported:
   score, rank in the group, and the shared phrases (as phrases, they are the published finding,
   not corpus text: at most 4 words each).
5. **Named sources.** *The Late War*, *View of the Hebrews* (1823, 1825), *The First Book of
   Napoleon*, and Spalding's *Manuscript Story* (not in the corpus; scored with the same
   document frequencies and placed in the population) are reported whatever they score. Luke, which
   the issue names, is King James text that masking removes from the target; the King James
   Gospel of Luke (`data/kjv/kjv.jsonl`) is scored as a source against the masked text and placed in
   the population, and reported as such.

## The known-answer score (Amendment 9)

Committed to `docs/known-answer-plan.md` now: per text, **the strongest source's rare shared
4-grams per 10,000 words** in each of BOM-23's three matched-window draws (2,000 volumes from the
70 years before the text's English, `data/reuse/exact/searches.json`, dates re-read through
`effective_year`), with document frequency counted within that draw (Amendment 10's rule:
frequency at the scale of the search, and by text), mean over the draws. Each text's own copies
left out. Higher means drawing on its own time. Separation by Amendment 9's rule; if it fails,
the rare-phrase list is reported as uninformative on the translation question.

## Known weaknesses, stated now

- **OCR errors** make some common phrases look rare (a misread word turns a common 4-gram into a
  unique one). They also remove real matches. Not corrected; the CER of each listed source is
  reported.
- **The null is the corpus itself.** A source is significant against period books in general;
  point 4 is the comparison with books in the same style.
- **Hashed 4-grams** (64-bit) may collide; at this corpus size the expected number of collisions
  among the target's grams is far below one.

## Registration

Registered as Amendment 13 (OSF revision 6ae7978847ce2102d62394f9, 2026-11-01), before the known-answer scans and before the scores above were computed.

## Known-answer result (2026-11-01; `python -m reuse.rare known`, `data/reuse/rare_known/known_answer.json`)

62,967 volumes scanned for the 4-grams of the 15 texts in BOM-23's 45 matched draws.

| Text | Group | Score (strongest source, per 10,000 words) |
| --- | --- | --- |
| *Twelve Patriarchs* | genuine | 1,104.2 (26.4 with its missed own copy out) |
| *Apocryphal New Testament* | genuine | 273.4 |
| Josephus | genuine | 214.4 |
| Koran | genuine | 148.9 |
| Homer | genuine | 124.3 |
| Hesiod | genuine | 53.8 |
| Herodotus | genuine | 49.9 |
| *Enoch* | genuine | 49.5 |
| *Sacontala* | genuine | 24.4 |
| *Jasher* | presented as ancient | 57.9 |
| Rowley | presented as ancient | 36.4 |
| *Ossian* | presented as ancient | 33.4 |
| Book of Mormon (not in the verdict) | target | 84.3 |

**The test does not separate the groups:** U = 6 of 27, p = 0.927 (with the missed own copy
`tcp:A09151` out, as in BOM-23: U = 9, p = 0.814; the Rowley check fails too). Under Amendment 9
the rare-phrase list is therefore **uninformative on the translation question**; it can still say
which period books share the Book of Mormon's rare wording.

**Why, as far as can be seen (post hoc).** The score divides by the source's length, so the
strongest source in a draw is usually a very short piece: the median winning volume is 728 words,
and 29 of 51 are under 1,000 (a 156-word advertisement, a 177-word proclamation). One or two
shared rare phrases in a broadside outscore dozens in a book. The registered score measures that
more than it measures borrowing.

## The Book of Mormon's source list (2026-11-01; `python -m reuse.rare score`, `data/reuse/bom/rare.json`)

204,520 volumes dated 1780-1830 after BOM-64; 16,813 moved volumes listed separately; 11
volumes held out by the registered seal (4.2: 20 or more 12-word Book of Mormon strings), all
later texts quoting it (*Monthly Review* "1826", 337 strings; five Congressional serial-set
volumes "1817"; three *Millennial Harbingers* "1830"; *Herald of Gospel Liberty* "1808"; an
*Eclectic Review* "1805"). Running the seal here was missed in the first run of this command and
added before anything was written up. 25,814 rare 4-grams (document frequency at most 5, by text).

- **The registered rule calls 2,044 volumes significant** (density above the population's 99th
  percentile, 1.089). As in the known-answer draws, the top of the list is short pieces: 53 of the
  top 100 share a single rare phrase, and their bootstrap p-intervals run from 0 to 1. Only 11 of
  the top 100 share five or more.
- **Named sources:**

| Source | Rare shared 4-grams | Per 10,000 words | Rank | p (95% interval) | Genre percentile p |
| --- | --- | --- | --- | --- | --- |
| *The First Book of Napoleon* (1809) | 12 | 5.45 | 63 | 0.0003 (0.0002-0.0031) | 0.0003 |
| *The Late War* (1816, 9 printings as one text) | 22 | 3.86 | 131 | 0.0006 (0.0004-0.0017) | 0.0004 |
| *View of the Hebrews* (1825) | 2 | 0.37 | 9,496 | 0.046 (0.017-1.0) | 0.18 |
| Spalding, *Manuscript Story* | 1 | 0.24 | - | 0.068 | - |
| Luke (King James), against the masked text | 0 | 0 | - | 1.0 | - |

  *The Late War* and *Napoleon* are significant by the registered rule and their intervals stay
  under 0.01; *View of the Hebrews* and Spalding are not. Counted by volume (the registered count
  without Amendment 8), *The Late War* shares none, because its nine printings put every phrase in
  nine documents.
- **Imitation scripture as a group (post hoc).** Ranked within the curated pseudo-biblical list:
  Ilive's *Book of Jasher* (its 1829 reprint) 7.99 (31 shared), then two one-phrase pamphlets, then
  *Napoleon* 5.45 (12), then *The Late War* 3.86 (22). So *The Late War* shares rare wording with
  the Book of Mormon at a rate typical of books written in the same imitation-biblical style, not
  above them; the 1829 *Jasher* shares more. Its shared phrases are battle and chronicle formulas
  ("the thirty and sixth year", "took their weapons of war", "was their chief captain", "and they
  pitched").
- **Books sharing the most** (five or more phrases, from the top of the list): John Wroe's *Life
  and Journal; with Divine Communications* (1829, 62: "baptize in my name", "gather my people
  together"), the two 1829 *Jasher* printings (31, 30), the Oriental Translation Fund's 1829
  publications (61), *The Testament of the Twelve Patriarchs* (1791, 19), *The Harmony of the
  Three Commissions* (1822, 19 and 18). All are religious or biblical-register prose.

**Reading.** The test cannot tell translations from compositions presented as ancient, so none of
this bears on the translation question. As a description: the Book of Mormon's rare 4-grams are
shared most with period books written in biblical English, imitation scripture among them, and no
named proposed source stands out from that group.
