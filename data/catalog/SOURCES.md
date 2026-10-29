# Corpus catalogs

Small, committed indexes of the large corpora. The corpora themselves live under
`data/corpus/` on the data machine (gitignored, not a git repo) and are tracked by checksum
manifests in `data/manifests/`.

| File | Built by | What it is |
| --- | --- | --- |
| `institutional_books.jsonl` | `python -m ingest.institutional_books catalog` | Harvard Institutional Books 1.0, English volumes dated 1780-1830: 31,958 rows (publication year 1780-1830, English) from the public metadata dataset `institutional/institutional-books-hl-metadata` (fetched 2026-10-15). Fields: barcode, title, author, dates, page and token counts, language, subject, OCR scores, likely duplicates, identifiers, HathiTrust link. |
| `institutional_books_summary.md` | same | counts and tokens by year |
| `tcp.jsonl` | `python -m ingest.eebo_tcp catalog` | Text Creation Partnership index: 61,315 texts (EEBO 1473-1700, Evans American imprints to 1800, ECCO 18th century) with id, date, author, title, pages, raw-file URL (fetched 2026-10-15). |
| `tcp_summary.md` | same | counts by collection, status, decade |
| `hathitrust.jsonl.gz` | `python -m ingest.hathitrust catalog --hathifile hathi_full_20261001.txt.gz` | HathiTrust public-domain English volumes with rights date 1780-1830: 135,035 rows (gzipped JSON Lines; read with `gzip.open`) from the monthly hathifile (https://www.hathitrust.org/files/hathifiles/, 2026-10-01 edition), each flagged `in_harvard` by `hvd.` id prefix or OCLC match against the Harvard catalog. 107,178 are not in the Harvard slice. |
| `hathitrust_summary.md` | same | overlap, contributors, decades |
| `hathitrust_ids_not_in_harvard.txt` | same catalog | the 107,178 HathiTrust ids (one per line) to request as a public-domain dataset from HathiTrust |
| `hathitrust_ia_map.jsonl`, `hathitrust_ia_ids.txt` | `python -m ingest.hathitrust map-ia` | the Archive-digitized HathiTrust volumes resolved to Internet Archive identifiers by ark id, and the id list for `ingest.internet_archive pull --ids` |
| `internet_archive.jsonl.gz` | `python -m ingest.internet_archive catalog` | Internet Archive scrape API, `mediatype:texts`, English, dated 1780-1830: 307,567 items with identifier, title, creator, year, publisher, language, subject (first 8), collection, imagecount, downloads, plus `has_text_likely` and `harvard_overlap` flags (fetched 2026-10-15). Gzipped because the plain JSONL is over GitHub's file limit. |
| `internet_archive_summary.md` | same | counts by year, top collections, Harvard overlap |
| `chronicling_america.jsonl.gz` | `python -m ingest.chronicling_america catalog` | Chronicling America newspaper pages dated 1800-1830 from the loc.gov JSON API (no key; fetched 2026-10-15). One row per page: page url, lccn, title, date, state, city, edition, sequence, OCR text-service url. Built from the issue list (`fa=type:issue`); pages are derived from each issue's page count and first scan number. |
| `chronicling_america_summary.md` | same | counts by state and decade, top titles, priority-state (NY, PA, OH) counts |

## Pulling the text (data machine)

```
python -m ingest.institutional_books pull      # 73 GiB on disk (two OCR versions), ~700 GB of transfer; needs a Hugging Face token whose account accepted the dataset terms
python -m ingest.eebo_tcp pull                  # ~25 GB of TEI XML plus extracted text; no account needed
python -m ingest.internet_archive pull --skip-harvard-overlap   # IA OCR (_djvu.txt), roughly 80 GB; no account needed
python -m ingest.chronicling_america pull        # OCR text of ~158,000 newspaper pages; no account; ~120 requests/minute
```

The New York, Pennsylvania, and Ohio pages (`pull --states NY,PA,OH`, 3,472 pages, 7 titles)
were pulled on 2026-10-15; their checksums are `data/manifests/chronicling_america_nypaoh.jsonl`.
Re-running the same command on another machine reproduces them.

**HathiTrust (BOM-08) completed 2026-10-20.** 31,194 volumes of 107,178 requested, 19 GiB on
disk (10.1 GiB of zipped page text plus METS). Pulled by rsync from
`datasets.hathitrust.org::ht_text_pd_open_access` under ticket GS-17502, approved 2026-10-20
with a dynamic IP allow-listed; **rsync access is removed 2026-11-30**. Manifest:
`data/manifests/hathitrust.jsonl` (62,394 records: one `.zip` and one `.mets.xml` per volume).
Each volume is `<pairtree>/<encoded id>.zip` holding one OCR text file per page. Rebuild:
`python3 ingest/hathitrust_rsync/ht_pull.py`; resumable, exit 23 expected (about 76,000 of the ids are Google-digitized and absent from this dataset). Access procedure: `docs/hathitrust-request.md`; rsync details: `docs/hathitrust-rsync-instructions.md`.

The 75,984 missing ids are Google-digitized and not in this dataset. Obtaining them needs a
separate Distribution Agreement with Google, which has not been pursued.

**What it actually added** (`data/catalog/hathitrust_overlap.json`): of the 31,194 received,
**21,810 were already held** from the Internet Archive pull, leaving **9,384 genuinely new**
volumes — under 2% of the corpus. **Corrected 2026-10-27:** this file said the 21,810 gave two
independent OCR passes of each book. They do not: for Archive-digitized volumes HathiTrust
redistributes the Archive's own OCR, and 16,555 of them match their Archive copy at a median
MinHash similarity of 1.000 (`DEDUP.md`). BOM-14 measures OCR error against TCP's hand-keyed
text instead (`data/ocr_quality/`). HathiTrust entered the merged catalog only on 2026-10-27;
the first merge left it out by mistake.

Terms, from the signed researcher agreement: the text stays on this machine, is never committed
or redistributed, and only manifests are public. Deletion notices from HathiTrust must be
honoured and logged here. Models trained on it must not reproduce it.

**Internet Archive (BOM-09) completed 2026-10-20.** 249,906 of 251,204 items (99.48%), 99 GiB,
one `.txt` per item in `data/corpus/internet_archive/text/<identifier>.txt`. Manifest:
`data/manifests/internet_archive.jsonl`.

4,822 distinct items were not obtained, recorded in `data/corpus/internet_archive/failed.txt`:
4,703 HTTP 500 (the Archive could not serve them), 1,550 bare 404 (left over from a run that
predated the filename recovery below, and not retired), 1,188 `no_ocr` (the item was asked and
genuinely has no OCR file: maps, manuscripts, image-only scans), 221 HTTP 401 and 30 HTTP 403
(restricted), the rest transient. The 500s are server-side and may clear; the pull is resumable,
so a later pass costs one command.

**Two things worth knowing about this source.** First, the download URL assumes
`<identifier>_djvu.txt`, which is wrong for a large minority of items whose OCR file is named
for an internal barcode (`39999063871220_djvu.txt`) or a stripped prefix (`jstor-30074678` ->
`30074678_djvu.txt`). Of 30 sampled 404s, 28 had an OCR file under another name. `ocr_filename()`
asks the item and recovers them; 404s fell from 9,127 to 1,550 once it was running. Second, the
Archive returns HTTP 500 on individual items frequently and unpredictably, and those are its own
faults rather than rate limiting -- across 250,000 requests over four days it never once returned
429.

**TCP (BOM-11) completed 2026-10-17.** 61,310 of 61,315 texts, 22 GiB: 8.5 GiB of extracted
text in `data/corpus/tcp/text` and 13 GiB of TEI XML in `data/corpus/tcp/xml`, one file each per
text. By collection: EEBO 53,830, Evans 5,012, ECCO 2,473. Manifest:
`data/manifests/tcp.jsonl` (122,621 records, both versions). The 5 missing are 404s listed in
`data/corpus/tcp/failed.txt`; those identifiers are in the index but have no file at the TCP
GitHub repositories. Note this source ships two versions per text, like Institutional Books.

**Chronicling America (BOM-10) completed 2026-10-17.** 158,960 of 159,146 pages, 4.4 GiB,
extracted from the bulk batch archives rather than the per-page API (see
`docs/chronam-bulk-download.md`). Manifest: `data/manifests/chronicling_america.jsonl`.
The 258 failures in `data/corpus/chronicling_america/failed.txt` are 257 HTTP 500s and one 520
from `tile.loc.gov`; those pages are absent from the batch archives and could not be recovered
from the live service either. 99.88% of the catalogued pages are on disk.

The Institutional Books pull completed 2026-10-16 05:38 on the Mac mini: all 9,831 shards read,
**31,958 volumes**, no failures. Two OCR versions are kept, one file per volume, 37 GiB each:

| Directory | What | Manifest |
| --- | --- | --- |
| `data/corpus/institutional_books/text_src` | Harvard's raw OCR (`text_by_page_src`) | `data/manifests/institutional_books_src.jsonl` |
| `data/corpus/institutional_books/text_gen` | Harvard's cleaned OCR (`text_by_page_gen`) | `data/manifests/institutional_books_gen.jsonl` |

31,958 records in each manifest. The pull is resumable from
`data/corpus/institutional_books/pull_progress.json`, which records completed shards by name;
rerunning the same command after any interruption skips what is already on disk.

## Terms

- Institutional Books: noncommercial use, no redistribution, attribution required:
  *Institutional Books* provided by the Institutional Data Initiative with source material
  contributed by Harvard Library, https://institutional.org/institutional-books. The text is
  never published by this project; corpus v1.0 (BOM-19) ships the catalog, manifests, and
  derived statistics for it.
- Internet Archive: items are mostly public-domain imprints; rights vary by item and are not
  re-checked here. The text stays on local disk; only the catalog and manifests are committed.
- TCP: Phase I texts are CC0; later texts carry their terms in the TEI header. Evans and ECCO
  texts are public-domain source material.

## The merged catalog and its labels (BOM-12)

All built from the per-source catalogs above and the corpus text on the data machine. Every
parquet carries the config hash it was built under in its schema metadata (`config_sha256`).

| File | Built by | What it is |
| --- | --- | --- |
| `catalog.parquet` | `python -m metadata.catalog merge` | one row per work from every source: 695,021 rows, 533,328 with text (HathiTrust added 2026-10-26 as the last source; the 559,986 earlier rows are unchanged); normalised author and year, and the path of the text file on disk |
| `genre.parquet` | `python -m metadata.genre rules`, then `label` (llama3.1:8b, about 82 h), then `resolve-no-text` | genre pass 1 for all 695,021 rows: 389,532 decided by rule (including 103,841 HathiTrust rows with no text, `rule:no_text`), 305,489 by the model; 290 `PARSE_FAIL` kept and reported. HathiTrust was added with `rules --append` and `label`, leaving earlier labels as they were |
| `genre_pass2.parquet` | `python -m metadata.genre_pass2 redraw` (after HathiTrust), `run`, then `adjudicate`; figures from `agreement` | genre pass 2 on the Amendment 4 sample of 5,000 (Sonnet, a different model family), with Opus adjudication of disagreements reported separately. Drawn again 2026-10-27 with HathiTrust: agreement with pass 1 84.9% on either label, 50.8% exact, 15.1% contradictions (no shared label); HathiTrust 83.9% on either label. The 757 contradictions were adjudicated by Opus: it sided with Sonnet in 553, with Llama in 62, both in 87, neither in 55 (simulated adjudication, not a human judgement). Full table: `python -m metadata.genre_pass2 agreement` |
| `genre_pass2_pre_hathitrust.parquet` | copied by `redraw` before redrawing | the pass-2 sample as drawn before HathiTrust joined the catalog, kept for comparison |
| `genre_benchmark_300.json` | interactive session of 2026-10-20 (commit a733bf6); no build script | the model-choice benchmark: 300 records with Sonnet and llama3.1:8b labels; the 60 rule-decided rows serve as ground truth |
| `signatures/` | `python -m metadata.dedup signatures` (about 2.6 h; gitignored, 524 MB) | MinHash signatures, one shard per parquet; resumable from the shards on disk |
| `duplicates.parquet` | `python -m metadata.dedup pairs` | on the text as fetched: 19,697 near-duplicate groups, 40,566 works, earliest marked `is_keeper`; nothing deleted. Read `DEDUP.md` |
| `duplicates_normalized.parquet`, `author_words_normalized.parquet`, `signatures_normalized/` | the same commands with `--text normalized` (BOM-15) | the same, on BOM-14's cleaned and BOM-15's normalised text; the control sets (BOM-18) read these |
| `duplicates_metadata.parquet`, `duplicates_combined.parquet` | `python -m metadata.dedup metadata`, then `combine` (Amendment 6, BOM-55) | the second pass by normalised title, author and year across sources, and its union with the MinHash groups: 19,692 groups, 24,779 non-keepers. The control sets read the combined flag. Read `DEDUP.md` |
| `dedup_metadata_check.json`, `dedup_cross_source_check.json` | `python -m metadata.dedup check-metadata`; the cross-source check of BOM-15 | the text checks behind DEDUP.md, with every pair scored |
| `author_words.parquet` | `python -m metadata.dedup authors` (word counts computed in the signatures pass) | word counts per normalised author: 65,432 authors |
| `date_check.parquet` | `python -m metadata.dates check` (seconds) | BOM-56: every volume catalogued as 1800 with a placeholder-shaped date (11,494), checked against the years on its own title page: confirmed 1800, corrected to another 1780-1830 year, post-1830, or undated. `metadata.dates.effective_year` is what date-window selections read; the catalog itself is unchanged |
| `DEDUP.md` | written by hand from the dedup outputs | the dedup report, and the measured limitation that cross-source duplicates are not caught on raw OCR |
| `validation_index.json` | `python -m metadata.validation build` (seeded; redraws byte-identical) | the 300-record genre validation sample: ids, strata, both pass labels; no text |
| `validation.html`, `validation_sample.json` | same command (gitignored here) | the review page and the sample with 700-char excerpts; restricted (30 Harvard volumes), so committed only to the private repo, `data/private/validation/` |
| `validation_draft.json`, `validation_draft_rules.md` | interactive session of 2026-10-27 (commit 03fddeb) | an AI-drafted label and reason per sample record, under the rule sheet; a drafting aid for BOM-53, not a judgement |

Checksums: `data/manifests/catalog.jsonl` (everything here except the two restricted files) and
`data/manifests/validation-private.jsonl` (the private copies of those two).

## MorphAdorner spelling data (BOM-15)

`data/corpus/morphadorner/morphadorner-2.0.1.zip`, downloaded 2026-10-27 from
https://morphadorner.northwestern.edu/morphadorner/download/morphadorner-2.0.1.zip
(Northwestern University; NCSA-style licence, see the site's Licenses page), with its
`data/eme*`, `standardspellings.txt` and `spellingsbywordclass.txt` extracted beside it.
`ememergedspellingpairs.tab` is the Early Modern English spelling table registered as
`corpus.spelling_normalization.pre_1700`. Local only (under `data/corpus/`); checksums in
`data/manifests/morphadorner.jsonl`. Rebuild: download the same zip and `unzip 'data/eme*'`.
