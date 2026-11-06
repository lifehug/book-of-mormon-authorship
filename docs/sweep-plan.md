# The author sweep: units, index, calibration, expected false leads (BOM-39, BOM-47)

Pre-registration 5.6 and 6.6 name the sweep and its lead rule; Amendment 28
(`paper/amendment-028-osf-text.md`) fixes what they leave open. Written 2026-11-06, before any
author is indexed or any calibration query is scored.

## What the sweep is for

Every author in the 1780-1830 corpus with enough text is compared with the Book of Mormon, so a
writer nobody has proposed can surface as a *lead*. A lead is a reason to look, never an
attribution. The sweep itself runs on the sealed text only in BOM-32; this issue builds the index
and measures, on known authors, how well it finds the right one and how many false leads it
throws up by chance.

## Units (who is swept)

- Every normalised catalog author (`author_norm`) with text, in the period window, a personal
  name (the style embeddings' `_named` rule) and not corporate (`style_embed.corporate`), with
  at least 10,000 words across non-duplicate volumes (the section 7 reference floor,
  `candidates.min_masked_words`). About 46,000 authors pass the word floor before the name
  filters (`data/catalog/author_words_normalized.parquet`).
- Each author's profile text is a sample: up to 20 blocks of 1,000 words (20,000 words), spread
  round-robin over the author's works (title groups, as BOM-30) and drawn at seeded positions
  from non-duplicate volumes. A cap keeps the 240-million-word government authors from costing
  more than everyone else, and equal-sized samples keep profiles comparably noisy.
- Blocks are BOM-15 normalised text with KJV quotation masked by BOM-16's frozen passim settings
  (a new `sweep` group; volumes already masked as controls reuse their spans). The Book of
  Mormon is masked the same way, so a scripture-heavy author cannot look close merely by quoting
  the Bible the Book of Mormon also quotes.

## Two signals, each on its own

- **Classical (BOM-20):** Cosine Delta on the 300 most frequent words (the registered middle MFW
  value), vocabulary from the swept author profiles (mean relative frequency, present in at least
  20% of them), z-scores fitted on the author profiles. Smaller is closer.
- **Style embeddings (BOM-30):** the trained encoder's vector of the text as one episode; cosine
  distance. Smaller is closer.

## The query

The Book of Mormon query is its discovery half: the 5,000-word chunks BOM-17 assigned to
discovery. An author's distance under a signal is the mean of its distances to each chunk.
Calibration queries are built the same way: a held-out book cut into 5,000-word chunks (at most as
many as the discovery half has), the distance averaged over chunks.

## Calibration (6.6)

- **Books:** 200 books by 200 different authors, drawn (seed `bom39-calibration`) from authors the
  style encoder never trained on (BOM-30's held-out 10%) who are swept and who still have 10,000
  words outside that book. The book is one title group (all its volumes and editions), at least
  5,000 words. The author's profile for these queries is rebuilt from their other works only.
- **Rank of the true author** under each signal among all swept authors.
- **Best false match:** with the true author removed, the smallest distance under each signal.
- **Usable** (6.6): the true author ranks first in at least 70% of queries. Read strictly: under
  each signal separately. The lenient reading (under either) is reported beside it.
- **Lead threshold:** the 5th percentile of best-false-match distances under each signal (closer
  than 95% of best false matches). A lead beats both.

## Expected false leads (BOM-47), written down before the sweep

- Leave-one-out on the 200 queries: thresholds from the other 199; count the authors other than
  the true one that beat both. The mean count is the expected number of false leads for a query
  whose author is not in the corpus; the counts' 50th and 95th percentiles are recorded.
- **Unremarkable:** an observed lead count at or below that 95th percentile. **Surprising:**
  above it. Observed leads are reported against this, never alone.
- **Signal correlation:** Spearman correlation of the two signals' distances over all authors
  (mean over queries), and of the best-false-match scores across queries. The expected count is
  measured, not derived from an independence assumption.
- **Chance survival of the plausibility gate:** the section 3 gate is also applied, blind to
  scores, to 100 swept authors drawn at random (seed `bom47-gate`). Their pass rate times the
  expected false-lead count is how many leads would survive by chance.

## Cost

Mac mini only. Sampling and reading: hours. Masking about 900 million words with passim: about
a day (the controls' 1.55 billion took most of a day). Style vectors for about 46,000 authors and
the calibration chunks on the M4 GPU: about half a day. Calibration: minutes.

## Limits

The base model under the style encoder was pretrained on the whole training set, held-out authors'
volumes included (language modelling, not style supervision). Catalog author names conflate
namesakes and split variant spellings; both make an author look less like themself. The sweep
makes no claim beyond the corpus: no leads means nobody in it is close.
