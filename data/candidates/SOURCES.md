# Candidate author texts: sources and how to recreate `data/candidates/`

BOM-13. The full inventory, with provenance and the texts deliberately left out, is in
`docs/candidates.md`. This file covers what is on disk and how to rebuild it.

## The manifest

`sources.json` lists 38 sources for the eight candidates of preregistration section 3. Each
entry has `id`, `candidate`, `title`, `url`, `kind`, `provenance`, `license`, `private`, plus
`date_written`, `date_published`, `pre1830`, `est_words` and `notes` (and `file` when an
Internet Archive item's OCR file is not named `<identifier>_djvu.txt`).
`uv run python -m ingest.candidates --check` validates it.

| Kind | Count | Fetched by `ingest.candidates` | Written to |
| --- | --- | --- | --- |
| `ia_djvu`, public | 17 | yes | `data/candidates/text/<id>.txt` (committed) |
| `ia_djvu`, private | 2 | yes | `data/private/candidates/<id>.txt` (private repo) |
| `jsp_page` | 16 | yes, all private | `data/private/candidates/<id>.jsonl`, raw pages in `data/private/candidates/raw/<id>/` |
| `wikisource` | 2 | no (inventory only) | - |
| `other` | 1 | no (Oberlin holograph, not digitized) | - |

## The public/private split

- **Public:** Internet Archive OCR of books and periodicals printed before 1927, with no
  rights claim on the item. These are public domain and are committed here, like `data/kjv/`.
- **Private, Joseph Smith Papers:** every `jsp_page` source. The transcripts are copyright
  Intellectual Reserve, Inc. They live only under `data/private/` (the private data repo
  `lifehug/bom-authorship-data`), never in this repo; only checksums are public.
- **Private, Internet Archive with a rights claim:** `sr-1840-appeal` and
  `ppp-1840-late-persecution`. The 1840 texts are public domain, but the Internet Archive
  rights field on these Church History Library scans says "Copyright by Intellectual Reserve".
  They are kept private to be safe; this can be revisited.

## What is on disk now (2026-10-25)

- **Internet Archive, all 19** (17 public in `text/`, 2 private): fetched 2026-10-15 (two) and
  2026-10-25 (the rest), 0 retries. 1,669,363 raw OCR tokens in all; per-file counts are in
  `docs/candidates.md` once the candidate table is built. The two periodical runs
  (`oc-messenger-advocate`, `wwp-evening-morning-star`) are whole runs; only signed items will
  enter a sample.
- **Joseph Smith Papers, 10 of 16 complete** (private repo): Revelation Book 1 (201 pages), the
  1832 history and all eight letters. Journal 1832-1834 has 16 of 106 pages; Letterbook 1 and
  the three Cowdery 1829 documents are not yet fetched; `oc-1834-history-jsp` (witness copy)
  is deferred. The fetch stopped when the site blocked this machine (see below) and resumes
  from the raw pages on disk.

Raw OCR is kept as delivered; cleaning, quotation stripping and KJV masking are later steps
(BOM-14 to BOM-16).

## Rebuild

```
uv run python -m ingest.candidates --public-only          # all public texts
uv run python -m ingest.candidates                        # also private (needs data/private)
uv run python -m metadata.manifest build data/candidates -o data/manifests/candidates.jsonl
```

Internet Archive requests send a `bom-authorship-research` user agent with a fixed delay
(`--delay`). Joseph Smith Papers requests send a browser user agent with a random delay
averaging `ingest.jsp.JSP_DELAY` and retries that back off by minutes; why, and the site terms
involved, are in `docs/candidates.md` (Joseph Smith, "How these were obtained"). Measured on
2026-10-25: at a 1 s average the site refused pages after about 26 and 66 requests; at 5 s it
blocked the address after about 165 requests (roughly 14 minutes), longer than six minutes of
retries. The block began about 11:20 PDT and hourly probes still got 404 at 12:35, 13:35,
14:35 and 15:35, so it lasts more than four hours. Expect to resume a full rebuild across several sittings. The fetcher skips any output already on disk.
`--id` picks single sources; `--max-pages N` caps Joseph Smith Papers documents while testing.
