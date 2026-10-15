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

## Pulling the text (data machine)

```
python -m ingest.institutional_books pull      # ~44 GB; needs a Hugging Face token whose account accepted the dataset terms
python -m ingest.eebo_tcp pull                  # ~25 GB of TEI XML plus extracted text; no account needed
```

## Terms

- Institutional Books: noncommercial use, no redistribution, attribution required:
  *Institutional Books* provided by the Institutional Data Initiative with source material
  contributed by Harvard Library, https://institutional.org/institutional-books. The text is
  never published by this project; corpus v1.0 (BOM-19) ships the catalog, manifests, and
  derived statistics for it.
- TCP: Phase I texts are CC0; later texts carry their terms in the TEI header. Evans and ECCO
  texts are public-domain source material.
