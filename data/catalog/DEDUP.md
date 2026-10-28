# Deduplication: what this pass does and does not catch (BOM-12)

Built by `python -m metadata.dedup signatures && python -m metadata.dedup pairs`, against
`corpus.dedup` in the config (minhash, 5-gram shingles, threshold 0.8, keep earliest).
**Nothing is deleted.** `duplicates.parquet` flags members and marks the earliest as `is_keeper`;
stages wanting one row per work filter on it themselves.

| | before HathiTrust (2026-10-25) | with HathiTrust (2026-10-27) |
| --- | --- | --- |
| Works with text | 502,134 | 533,328 |
| Duplicate groups | 3,336 | 19,697 |
| Works in a group | 7,413 | 40,566 |
| Non-keepers flagged | 4,077 | 20,869 |
| Groups spanning more than one source | **6** | 16,573 |

**Read the second column carefully.** HathiTrust was left out of the first catalog merge by
mistake and added on 2026-10-27. 16,555 of the 16,573 cross-source groups pair a HathiTrust
volume with an Internet Archive item, and their best similarity has median **1.000** (p10 0.930;
86% at 0.95 or above): for Archive-digitized volumes HathiTrust redistributes the Archive's own
scan *and its OCR*. These are the same text twice, which is exactly what the method catches.
They are not independent OCR passes, and they do not change the finding below, which is about
genuinely different OCR of the same work. Excluding them, cross-source groups number 18.

## The limitation, measured 2026-10-25

The first column's last row is the finding. This pass catches **same-source near-identical copies** and
essentially no cross-source duplicates — yet 28,303 Internet Archive items are flagged in the
catalog as overlapping Harvard's collection.

Measured on 300 pairs that share an identical normalised title and author across two sources,
spot-checked by eye to confirm they are genuinely the same work:

| | |
| --- | --- |
| Median MinHash similarity | **0.164** |
| Reaching the registered 0.8 threshold | **0.0%** |
| Reaching even 0.5 | 5.3% |

**This is not bad data.** Corpus OCR is sound: lexicon rates run 0.79-0.87 by source with under
3.2% of documents below 0.5. It is that 5-grams are brittle. At roughly 80% token accuracy a
5-gram survives two independent OCR passes at about 0.8^5 = 33%, which is the whole explanation.
Some pairs are worse still: TCP is hand-keyed while the Internet Archive is OCR, so the same 1780
poem appears once as clean transcription and once as `2222 4 1 £41. v 1319 l | * a G`.

No threshold tuning fixes this. The dedup is being run on raw text, before BOM-14 cleans OCR and
BOM-15 normalises orthography, and on raw text cross-source matching cannot work.

**The fix needs no amendment.** Pre-registration 4.3 registers the method, not its position in
the pipeline, so dedup is re-run after BOM-14 and BOM-15 and both figures are published. This
pass stands as the same-source result.

## After cleaning and normalisation (BOM-15, 2026-10-27)

The same method re-run on BOM-14's cleaned and BOM-15's normalised text
(`python -m metadata.dedup signatures|pairs|authors --text normalized`; outputs
`duplicates_normalized.parquet`, `author_words_normalized.parquet`). The control sets read these.

| | raw text | cleaned and normalised |
| --- | --- | --- |
| Duplicate groups | 19,697 | 19,916 |
| Works in a group | 40,566 | 41,131 |
| Non-keepers flagged | 20,869 | 21,215 |
| Authors with 10,000+ words | 46,649 | 46,441 |

**The cross-source limitation is not fixed by it.** 300 pairs drawn with a seed
(`20261017:dedup-cross`) from the 599 pairs sharing an identical normalised title and author
across two sources (HathiTrust left out, as in the first measurement, because its Archive copies
are the same OCR), each scored on both signature sets (`dedup_cross_source_check.json`):

| | raw | cleaned and normalised |
| --- | --- | --- |
| Median similarity | 0.117 | 0.180 |
| Reaching 0.5 | 7.3% | 12.0% |
| Reaching the registered 0.8 | **0.0%** | **0.0%** |

Cleaning raised the similarity of 196 of the 300 pairs, and no pair reaches the threshold. Unlike
the first sample these pairs were not checked by eye, so some are different editions or volumes
of one title and belong apart; that lowers both columns equally and does not explain a zero.
What this means downstream: a work printed in two sources can be counted twice in a null or
control sample. A second, metadata-based pass (same title, author and year across sources) would
catch these, but it is a different method from 4.3's and so an owner decision, not a fix made
here. Recorded for BOM-45, which builds the null.

## The second pass, by title, author and year (Amendment 6, BOM-55)

Amendment 6 registers a second pass because MinHash cannot see the same work read by two OCR
engines (above). `python -m metadata.dedup metadata` groups works in more than one source sharing
the catalog's normalised title, normalised author and year; every member of such a group joins
it, the earliest (year, then catalog order) is kept, and nothing is deleted. Newspaper pages
(Chronicling America) are left out: every page of a title in a year shares those keys and they
are not copies. `python -m metadata.dedup combine` unites these groups with the MinHash groups on
normalised text into one keeper flag, `duplicates_combined.parquet`, which the control sets read.

| | groups | works | non-keepers |
| --- | --- | --- | --- |
| MinHash, normalised text | 19,916 | 41,131 | 21,215 |
| metadata pass | 4,697 | 12,966 | 8,269 |
| combined | 19,688 | 44,464 | 24,776 |

**Checked against the text** (`python -m metadata.dedup check-metadata`, seeded sample of
200 groups, 352 keeper-member pairs, `dedup_metadata_check.json`): word counts within 1.5x
in 341 pairs, beyond in 11; median vocabulary overlap 0.95. Most of what the pass
merges is the same text. The pairs that differ in length are different volumes or extents of one
work (two volumes of *Sketches of Persia* against a copy with both), which the amendment counts
as one work: they are not independent draws for a control or null sample. Vocabulary overlap
cannot tell two volumes of a work (about 0.45) from two OCR readings of one volume (0.44-0.61),
so no text threshold was added.

What the pass does not catch: copies within one source (three Archive scans of Hunt's 1816 *Late
War*) and editions catalogued under different titles. The curated pseudo-biblical list (BOM-54)
collapses those by hand.

## A second caveat, the other direction

One group holds 173 members and appears to be volumes of *The Public Statutes at Large*. Distinct
volumes of a serial share enough boilerplate to collapse together, so the threshold is loose for
serials while being far too strict across sources. Worth checking before any count treats a group
as one work.

## Consequence beyond dedup

The same arithmetic hits borrowing detection. A 4-gram shared between the Book of Mormon and a
source survives OCR at about 0.8^4 = 41%, so 5.5 will miss over half of real matches. That
largely cancels because 6.5 builds its null from the same noisy corpus — **but only if OCR
quality is even across sources, and it is not.** A candidate source with cleaner OCR than the
null volumes will look like a stronger match than it is. OCR quality should be a matching
variable for the null alongside genre, length and period; recorded against BOM-45.
