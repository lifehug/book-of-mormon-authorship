# Text reuse and rare-phrase scoring (Phase 3-4)

## `null_sizing/` (BOM-45)

Built by `python -m reuse.rare scan` (about 45 minutes, 8 workers) then `python -m reuse.rare size`
(seconds). Sizes the null that 6.5's borrowing test is judged against, using a stand-in target,
Gilbert Hunt's *The Late War* (KJV-masked), so the Book of Mormon is not touched.

| File | What it is |
| --- | --- |
| `target_grams.txt` | the stand-in's 49,091 distinct hashed 4-grams (Amendment 2's tokenisation) |
| `hits.parquet` | for every eligible period volume (226,798), its word count and which stand-in 4-grams it contains: hashes and counts only, no text |
| `sizing.json` | the scores' distribution and the 99th percentile's spread when the null is a genre-stratified sample of 500 to 20,000 volumes (1,000 draws each) |

Score (5.5): shared 4-grams with document frequency at most 5, per 10,000 words of the volume.
The target's own copies and editions (105) are excluded from document frequencies and from
the null; volumes whose corrected date (BOM-56) is outside 1780-1830 count towards document
frequency but are not in the null. 3.9% of null volumes score above zero.

| Null size | 99th percentile | 95% interval | +/- |
| --- | --- | --- | --- |
| 500 | 0.130 | 0.056-0.366 | 119% |
| 1,000 | 0.137 | 0.074-0.287 | 78% |
| 2,000 | 0.142 | 0.092-0.240 | 52% |
| 5,000 | 0.142 | 0.108-0.196 | 31% |
| 10,000 | 0.144 | 0.118-0.183 | 23% |
| 20,000 | 0.143 | 0.125-0.171 | 16% |

Whole population: 0.144. No sample size reaches the registered +/-10% tolerance, so the
null is the whole eligible population (proposed in the Amendment 7 draft, Change 6).

## `bom/` (BOM-22, 2026-10-30)

`python -m reuse.rare scan --target bom --workers 4`: the Book of Mormon with the KJV masked
(250,486 words) as target, every eligible period volume scanned (221,344; the 13 sealed copies of
the target left out of every document frequency, BOM-45). `target_grams.txt` is the target's
4-gram ids; `hits.parquet` (237 MB, not in git, rebuilt in about an hour, checksummed in
`data/manifests/reuse.jsonl`) holds each volume's shared 4-grams. Read by
`python -m eval.replicate johnson` (the Johnson and Johnson 2013 replication), which writes
`data/benchmark/replication_johnson.json`. This is the published-method replication allowed by 4.2;
nothing here feeds BOM-24's registered test.
