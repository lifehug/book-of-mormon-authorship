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

