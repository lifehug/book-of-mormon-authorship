# Control sets (BOM-18)

Built by `python -m metadata.controls build` from the catalog, genre pass 1, the dedup run on
cleaned and normalised text (`duplicates_normalized.parquet`), Amendment 6's combined flag
(`duplicates_combined.parquet`: within each set one member per duplicate group, applied after
sampling so the pool samples and their KJV masks are unchanged; pseudo_biblical 55, sermons_1820s 179, history 14, general_prose 1 removed), BOM-14's OCR flags
(`data/ocr_quality/volumes.parquet`) and 4.2's sealing check. The module docstring holds the
rules; config stamp `f0bb58079083b860…`.

| File | What it is |
| --- | --- |
| `<set>.txt` | the membership list: one work id per line, sorted. Its SHA-256 is the published hash (Amendment 2) |
| `<set>.jsonl` | the same members with source, year, words, named work, origins flag, candidate overlap |
| `controls.json` | sizes, words, sources, hashes, what was dropped and why, and the 12-token contamination result |

| Set | Volumes | Words | Native American origins subset | SHA-256 of id list |
| --- | --- | --- | --- | --- |
| `pseudo_biblical` | 3,522 | 348,172,265 | - | `a9c819fe7f36a3bb…` |
| `sermons_1820s` | 6,151 | 641,925,943 | - | `77527d086a7b97ee…` |
| `history` | 2,911 | 368,772,915 | 46 | `a327ea52b5054c5d…` |
| `general_prose` | 4,947 | 227,329,739 | - | `6c6f65fe15f47208…` |
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

**Placeholder dates (BOM-56, 2026-10-28).** Undated reprints catalogued as 1800 include post-1830
books. Each control member's year is now its title-page year where one was found
(`metadata.dates`, `data/catalog/date_check.parquet`); members whose corrected year falls outside
1780-1830, or that cannot be dated, are removed (276 in all). The pool samples are drawn
exactly as before, from the catalog year, and then filtered, so no member changes and every KJV
mask carries over; eight volumes corrected to the 1820s joined the 1820s sermons and were masked.

**The curated pseudo-biblical list (BOM-54, Amendment 6, 2026-10-30).**
`pseudo_biblical_curated.txt` is the confirmatory pseudo-biblical control: 18 works, one id per
work. Build: `python -m metadata.pseudo_biblical markers`, `candidates`, `judge`, `build`
(files in `pseudo_biblical/`). 1,349 candidates passed the marker rule set from the named
editions; each was judged by two models (Sonnet and Opus, with a third breaking ties: 97.7%
agreement; simulated reading, not a human check) in `judgments.jsonl`. The known-answer gate
passed (all 15 named editions admitted, all 25 rejection-set works refused). 49 judged yes; the
build then drops what a judgment cannot see, and collapses copies, all recorded in `build.json`:

- `internet_archive:book_of_morman`, a modern Book of Mormon catalogued as "Book of Morman"
  (the sealing regex, `metadata.sealed.TITLE`, now accepts that spelling);
- `institutional_books:HNQRCW` (*Oahspe*, 1882, catalogued 1800), by its BOM-56 title-page year;
- 29 copies folded into their work (`copies_collapsed`): editions of Hunt's *Late War* and his
  *Historical Reader*, Dodsley's *Oeconomy* / *Economy of Human Life*, Snowden's 1793 and 1802
  *American Revolution*, *Jasher*. The earliest copy is kept. *The Acts*, Chap. I and Chap. II
  (1790), are separate pamphlets of one series and both stay.
