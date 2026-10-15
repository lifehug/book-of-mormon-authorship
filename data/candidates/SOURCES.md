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

## What is on disk now

Only a fetch test (`--limit 2`, public items) has been run:

- `text/sr-1838-oration.txt`: IA `orationdelivered01rigd`, 37,034 bytes, 5,621 OCR tokens.
- `text/ss-manuscript-story-1885.txt`: IA `themanuscriptsto00spauuoft`, 294,440 bytes,
  44,279 OCR tokens (includes the 1885 publisher's correspondence, to be stripped).

Raw OCR is kept as delivered; cleaning, quotation stripping and KJV masking are later steps
(BOM-14 to BOM-16).

## Rebuild

```
uv run python -m ingest.candidates --public-only          # all public texts
uv run python -m ingest.candidates                        # also private (needs data/private)
uv run python -m metadata.manifest build data/candidates -o data/manifests/candidates.jsonl
```

The fetcher sends a `bom-authorship-research` user agent, waits 2 seconds between requests
(`--delay`), and skips any output file already on disk. `--id` picks single sources;
`--max-pages N` caps Joseph Smith Papers documents while testing.
