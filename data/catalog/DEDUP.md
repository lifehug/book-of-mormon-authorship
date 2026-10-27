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
