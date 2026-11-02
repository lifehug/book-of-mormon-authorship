# data/derived

Derived tables an outsider can re-run the statistics with, without the corpus (BOM-44;
Amendment 18, OSF revision 6ae8143cd1f5f0174dd84c7c). Built by `python -m eval.derived export`;
every table passes `python -m eval.derived check` (no text, no word positions, vocabularies at
most 1,000). Terms per source: `docs/derived-data-terms.md`.

| File | What | Where |
| --- | --- | --- |
| `benchmark_blocks.parquet` | the validation benchmark (BOM-21): every 1,000-token reference block, test sample (with the reference blocks it was cut from) and imposter-pool sample of each task, as counts over the task's 1,000 most frequent words. All 180 tests' vocabularies fall inside the published ones, so Delta, General Imposters and ENSC rerun exactly | here |
| `benchmark_vocabulary.json` | the words, per task | here |
| `target_grams_bom.txt`, `target_grams_known_*.txt` | each target's 4-gram hashes (`reuse.rare.gram_ids`, blake2b 8 bytes), recomputable from its public text | here |
| `rare_hits_bom.parquet` (237 MB) | BOM-22/24's scan: every period volume's id, word count and the Book of Mormon 4-gram hashes it contains; 221,344 volumes | GitHub release `derived-v1.0` |
| `rare_hits_known.parquet` (~110 MB) | Amendment 9's known-answer scans, same form, per target; Enoch and Josephus withheld (their copies are HathiTrust and Harvard text, and a full hash list can be unrolled into the text) | GitHub release `derived-v1.0` |
| `export.json` | what was exported, row counts, vocabulary coverage, the check result | here |

Elsewhere and already public: the catalog with genre, dates, OCR estimates and deduplication
(`data/catalog/`), the dating segments' grammar rates (`data/dating/segments.parquet`).

**Attribution.** Rows derived from Harvard Institutional Books volumes: "Institutional Books 1.0,
Harvard Law School Library Innovation Lab / Institutional Data Initiative", used under its terms
(clause 3: summary statistics that cannot substitute for the original). Rows derived from
HathiTrust volumes: HathiTrust Digital Library, public-domain open-access set. Nothing derived from
the Joseph Smith Papers transcripts is here.

Checksums: `data/manifests/derived.jsonl` (both the files here and the release assets). Archived on Zenodo with the repository at the release tag: DOI [10.5281/zenodo.23875959](https://doi.org/10.5281/zenodo.23875959).
