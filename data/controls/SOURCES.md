# Control sets (BOM-18)

Built by `python -m metadata.controls build` from the catalog, genre pass 1, the dedup run on
cleaned and normalised text (`duplicates_normalized.parquet`), Amendment 6's combined flag
(`duplicates_combined.parquet`: within each set one member per duplicate group, applied after
sampling so the pool samples and their KJV masks are unchanged; pseudo_biblical 55, sermons_1820s 179, history 14, general_prose 1 removed), BOM-14's OCR flags
(`data/ocr_quality/volumes.parquet`) and 4.2's sealing check. The module docstring holds the
rules; config stamp `89a86f470bed232c…`.

| File | What it is |
| --- | --- |
| `<set>.txt` | the membership list: one work id per line, sorted. Its SHA-256 is the published hash (Amendment 2) |
| `<set>.jsonl` | the same members with source, year, words, named work, origins flag, candidate overlap |
| `controls.json` | sizes, words, sources, hashes, what was dropped and why, and the 12-token contamination result |

| Set | Volumes | Words | Native American origins subset | SHA-256 of id list |
| --- | --- | --- | --- | --- |
| `pseudo_biblical` | 3,672 | 364,442,037 | - | `8f6ae2a0ad71a7fd…` |
| `sermons_1820s` | 6,143 | 640,991,183 | - | `c7b7381f919864f2…` |
| `history` | 2,986 | 376,264,091 | 47 | `94559f412673a88c…` |
| `general_prose` | 4,998 | 231,227,527 | - | `2d75b03ce8beeed2…` |
| `pseudo_biblical_primary` | 29 | 1,858,828 | - | `c82a1a54efe12199…` |

Dropped before membership: ocr_excluded 101,340, duplicate 17,926, candidate_work 67, no_text 41,469, sealed_title 5, out_of_window 41,764.
Members failing 4.2's 12-token check: 0.

**Two lists for pseudo-biblical.** `pseudo_biblical` is the registered list (Amendment 3: either
genre label). Read by title, most of it is ordinary religious prose; `pseudo_biblical_primary`
holds the works whose primary label is pseudo-biblical plus the works section 3 names. Amendment 6 replaces both, for the
confirmatory test, with a curated list (BOM-54); these two remain as sensitivity analyses.

**Sampled pools.** History and general prose are seeded samples, stratified by source and
decade, of 39,112 and 268,246 eligible volumes
(registered by Amendment 6).

**Checked against the pre-1700 redo (BOM-15).** On 2026-10-27 no dedup group mixed a pre-1700
text with a 1780-1830 work, so redoing the pre-1700 spelling cannot change membership through
dedup; the count is re-checked once that redo lands.

KJV masks of the members: `data/kjv_mask/controls/` (`python -m kjv_mask.run controls`).
