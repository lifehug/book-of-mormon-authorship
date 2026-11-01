# The King James italics test: the plan, written before any measurement (BOM-62)

Committed 2026-10-31, before any italic word has been counted in any text's King James passages.

## The question

The King James translators printed in italics the English words they supplied to make sense,
words with no counterpart in the Hebrew or Greek ("darkness *was* upon the face of the deep"). A
translation made from a Hebrew or Greek source has no reason to reproduce those particular
English choices. A text that draws on the King James English will reproduce them, or, if its
author knew they were supplied, may change them more often than the rest. The Book of Mormon
runs parallel to the King James text for long stretches, mostly Isaiah (about 12,650 aligned
tokens in BOM-16's masks), with Matthew 5-7, Malachi 3-4 and others.

## Data

- **Italics**: `data/kjv/kjv.jsonl`, `text_marked`: eBible.org's 1769 Oxford text, translators'
  words in brackets (1,477 italic words of 37,203 in Isaiah). Period American printings varied
  somewhat in their italics; the 1828 Phinney edition (the Smith family's Bible, `data/kjv/raw/`)
  survives only as OCR, which does not record italics. **Check before measuring:** 100 italic
  words drawn with seed `"bom62-italics"` from the chapters the Book of Mormon parallels are
  looked up in the scanned pages of the 1828 Phinney edition (Internet Archive
  `holybiblecontain00cann`) and the agreement rate is reported. The check is model-assisted from
  page images and labelled simulated (Amendment 1).
- **Passages**: every King James span in each text as BOM-16 masked it (registered alignment,
  identity at least 0.60 over at least 8 tokens). The same rule applies to every text, so the
  passages chosen are chosen the same way everywhere.

## The measurement

Inside each span, the text's tokens are re-aligned word by word to the King James verse text
with its italics (`difflib`, as in masking). Each King James word in the span's range is
**kept** (the text has the same word at that place), **changed** (replaced) or **dropped**. Two
rates follow:

- `R_i`: the share of italic words kept;
- `R_r`: the share of roman (non-italic) words kept;
- `D = R_r - R_i`: how much more often the supplied words are changed than the rest.

Uncertainty: 95% intervals by bootstrap over spans (10,000 resamples, seed `"bom62-boot"`), since
words within a span are not independent.

## The reference texts (this test's known answer)

Amendment 9's known-answer set rarely runs parallel to the King James text (*Ossian*, Rowley,
Homer and *Sacontala* have no masked spans at all), so it cannot carry this test. The question here
is narrower and has its own known answer:

- **(a) independent translations** of the same books from the Hebrew or Greek, made in the
  period: Lowth's *Isaiah* (1795; `internet_archive:isaiahnewtransla01lowt`, `...02lowt`),
  *A New Translation of Isaiah* "by a layman" (1790;
  `internet_archive:bim_eighteenth-century_a-new-translation-of-isa_1790`), *A New Translation
  of the Book of Psalms* (1807; `institutional_books:AH5KIN`) and Gilbert Wakefield's *Matthew*
  (1782; `internet_archive:bim_eighteenth-century_a-new-translation-of-the_1782`). **Only the
  translation text is measured.** Their notes and dissertations quote the King James text to
  compare with it, and would make an independent translation look dependent. The character
  ranges of each volume's translation are recorded from its layout (chapter headings, the start
  of the notes), committed before any italic word in it is counted, and published;
- **(b) texts that quote the King James Bible**: the King James spans in the registered 1820s
  sermons control.

Expected: (b) near `D = 0` and `R_i` near `R_r`; (a) `D` well above 0 and `R_i` low. The test is
**shown to work** if (a)'s pooled `R_i` interval lies below (b)'s and their `D` intervals do
not overlap. If not, the test is reported as unable to separate independent translation from
King James dependence, and the Book of Mormon's rates are reported without interpretation.
Amendment 9's set is also scored where a text has at least 50 italic words inside its spans; the
counts are reported, and if fewer than two presented-as-ancient texts qualify, Amendment 9's
separation is reported as not computable for this test.

## Reading the Book of Mormon's result

Decided now, before any count:

1. If the Book of Mormon's `R_i` interval lies above the independent translations' pooled
   interval, it **reproduces the King James translators' supplied words more often than an
   independent translation does**: dependence on the King James English, including its
   additions.
2. Its `D` is then placed against (a) and (b): `D` within (b)'s interval means it keeps the
   supplied words as often as the rest, like a quotation; `D` above (b)'s interval means it
   changes supplied words more often than other words, which needs a reader who could tell
   which words were supplied (the italics are printed), and is reported as **selective revision
   at the italics**. Both outcomes under (1) are dependence on the King James English.
3. If its `R_i` interval overlaps the independent translations', the test does not show
   dependence on the added words.

The project draws no conclusion about inspiration from any of these.

## Scholarship

The result is reported beside the published work on this question, critical and apologetic, each
cited by link (gathered after the plan is registered and before the result is written up, so the
reading cannot shape the rule).

## Registration

Registered as Amendment 11 (OSF revision 6ae62f2ca50d25933c296d01, 2026-10-31), before any
italic word was counted.

## Deviations before counting (2026-10-31, no italic word counted yet)

- **Wakefield's *Matthew* (1782) is left out.** Its OCR interleaves translation, Greek notes and
  scrambled columns line by line, so no recorded range holds translation alone. The independent
  group is Lowth's *Isaiah*, the 1790 *Isaiah* and the 1807 *Psalms*; the Book of Mormon's
  parallels are mostly Isaiah, which this group covers twice.
- **Ranges** (`python -m eval.italics ranges`, `data/italics/translation_ranges.json`): Lowth
  volume 1 from the heading before "The Vision of Isaiah" to its end (263,226 characters); Lowth
  volume 2 is notes only and contributes nothing; the 1790 *Isaiah* from its first "SECTION I" to
  "NOTES on ISAIAH" (237,401 characters, its short page footnotes included); the 1807 *Psalms* as
  142 blocks from a "PSALM n." heading to the next "NOTES." (eight of 150 headings were lost to
  OCR, and those psalms are left out).

- **The check's page lookup (2026-10-31, before any measurement).** The first pass found 56 of
  62 located words italic but could not locate 38, 37 of them in the New Testament. The OCR page
  index counts all 892 scanned leaves; the image URL counts only the 884 shown to readers (leaf 0
  and the four leaves before the New Testament are hidden), so images were one leaf off in the
  Old Testament, which the neighbouring-page retry absorbed, and five off in the New, which it
  could not. Pages are now mapped through the scan's `scandata.xml`; the 38 were asked again;
  the answers that named their verse stand.

## Result (2026-11-01; `python -m eval.italics measure`, `data/italics/measure.json`)

**The italics check (Amendment 11):** 88 of 100 seeded italic words are italic in the 1828
Phinney Bible, 12 roman (model-assisted from page images, simulated).

| Group | Spans | Italic words | R_i (95% CI) | R_r | D (95% CI) |
| --- | --- | --- | --- | --- | --- |
| (a) independent translations, pooled | 1,306 | 806 | 0.903 (0.861-0.937) | 0.929 | 0.026 (-0.001 to 0.056) |
| (b) 1820s sermons | 498,225 | 480,072 | 0.904 (0.901-0.907) | 0.927 | 0.023 (0.021-0.026) |
| Book of Mormon | 337 | 493 | 0.645 (0.576-0.716) | 0.946 | 0.301 (0.235-0.361) |

Independent volumes: Lowth vol. 1, R_i 0.867 (128 italic words); the 1790 *Isaiah*, 0.912
(148); the 1807 *Psalms*, 0.909 (530).

**The test is not shown to work.** (a)'s R_i interval does not lie below (b)'s; the two groups
keep the supplied words at the same rate. Inside the passages where an independent translation
runs parallel to the King James text (the registered spans, identity at least 0.60), it supplies
the same small English words ("is", "was", "that") the King James translators did, because
English needs them. So under the rule fixed before counting, **the Book of Mormon's rates are
reported without interpretation** and readings (1)-(3) above do not apply. Amendment 9's
separation is not computable for this test: of its texts only the *Apocryphal New Testament*
(genuine, 60 italic words) reaches 50 italic words, and no text presented as ancient does.

**Descriptive, noticed after the result (post hoc):** the Book of Mormon keeps 95% of the King
James roman words in its spans and 64% of the italic ones, a gap (D = 0.30) more than ten times
that of either reference group, whose intervals it does not overlap. By book: Isaiah 394 italic
words, 62.7% kept (69 changed, 78 dropped); Matthew 30, 56.7%; Malachi 27, 66.7%; Exodus 15,
60.0%. This test cannot say what produces the gap.

**Beside the published work.** The pattern is known, and our count matches it:

- David P. Wright, "Joseph Smith's Interpretation of Isaiah in the Book of Mormon," *Dialogue*
  31, no. 4 (1998), https://www.dialoguejournal.com/articles/joseph-smiths-interpretation-of-isaiah-in-the-book-of-mormon/
  (critical): 3.6% of the words in the main Isaiah chapters are italic, and about 40% of them
  are missing from the Book of Mormon; read as work done directly on the KJV. Wright's 2002
  chapter in *American Apocrypha* and Stan Larson's work on the Sermon on the Mount (*Trinity
  Journal* 7, 1986, 23-45; cited by Spencer as the "italics revision" hypothesis) make the same
  argument (cited through Spencer and *Dialogue*, not yet read here).
- John A. Tvedtnes, "Isaiah Variants in the Book of Mormon," in *Isaiah and the Prophets*
  (1984), https://rsc.byu.edu/isaiah-prophets/isaiah-variants-book-mormon (apologetic): 59
  omissions and 37 changes of italic words, 35 of the changes neutral in meaning.
- Stan Spencer, "Missing Words: King James Bible Italics, the Translation of the Book of Mormon,
  and Joseph Smith as an Unlearned Reader," *Interpreter* 38 (2020): 45-106,
  https://interpreterfoundation.org/journal/missing-words-king-james-bible-italics-the-translation-of-the-book-of-mormon-and-joseph-smith-as-an-unlearned-reader
  (apologetic): about 37% of italic words omitted across the Isaiah chapters, 41% against about
  1% of other words in 2 Nephi 16-17; Royal Skousen attributes 29% of the Isaiah differences to
  italic words; explained as a prior translator's omission of the italic words, restored by
  Joseph Smith.

Our Isaiah figure, 37.3% of italic words not kept, agrees with Spencer's 37% and Wright's
about 40%. What this study adds is the comparison: independent translators and period
preachers both keep about 90% of the supplied words where they follow the King James text,
so the Book of Mormon's 64% sets it apart from both. That difference is consistent with
deliberate revision at the italics (Larson, Wright) and with Spencer's missing-words account
alike; this test does not separate those, and the project draws no conclusion about
inspiration.
