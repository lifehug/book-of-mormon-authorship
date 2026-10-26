# Candidate author texts: sources and how to recreate `data/candidates/`

BOM-13. The full inventory, with provenance and the texts deliberately left out, is in
`docs/candidates.md`. This file covers what is on disk and how to rebuild it.

## The manifest

`sources.json` lists 38 sources for the eight candidates of preregistration section 3. Each
entry has `id`, `candidate`, `title`, `url`, `kind`, `provenance`, `license`, `private`, plus
`date_written`, `date_published`, `pre1830`, `est_words` and `notes` (and `file` when an
Internet Archive item's OCR file is not named `<identifier>_djvu.txt`, and `edition_of` when the
entry is a later edition or transcription of another entry's work, counted once at the earliest).
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

## What is on disk now (2026-10-26)

- **Internet Archive, all 19** (17 public in `text/`, 2 private): fetched 2026-10-15 (two) and
  2026-10-25 (the rest), 0 retries. 1,669,363 raw OCR tokens in all; per-file counts are in
  `docs/candidates.md` once the candidate table is built. The two periodical runs
  (`oc-messenger-advocate`, `wwp-evening-morning-star`) are whole runs; only signed items will
  enter a sample.
- **Joseph Smith Papers, 15 of 16 complete** (private repo), finished 2026-10-25 22:23 PDT at a
  30 s average: Revelation Book 1, the 1832 history, all eight letters, Journal 1832-1834 (106
  pages), Letterbook 1 (108) and the three Cowdery 1829 documents. `oc-1834-history-jsp`
  (witness copy) is deferred.
- **Derived (2026-10-26):** `units.csv` (one row per counted unit: source, TOC entry, author,
  sample, period, words, the rule that decided it) and `word_counts.json` (totals per candidate,
  sample and period, with the section 3 floor flag and the config hash), both public: titles and
  counts only. `signed_items.json` lists every signature line found in the two periodical runs
  with its decision under rules 11-17 and, for admitted items, the line span in the OCR file
  (proposed by `ingest.signed_items`, checked by hand). The assembled sample texts are private, in
  `data/private/candidates/samples/<candidate>__<sample>__<period>.txt`. The JSP `<id>.jsonl`
  files were rebuilt offline on 2026-10-26 with `--rebuild` after the transcript reader was
  fixed (it had counted editorial notes as text and dropped glossed words).

Raw OCR is kept as delivered; cleaning, quotation stripping and KJV masking are later steps
(BOM-14 to BOM-16).

## Rebuild

```
uv run python -m ingest.candidates --public-only          # all public texts
uv run python -m ingest.candidates                        # also private (needs data/private)
uv run python -m ingest.candidates --rebuild --id <jsp id>  # re-extract JSP text from raw pages, offline
uv run python -m ingest.signed_items                      # propose signed periodical items (keeps checked ones)
uv run python -m ingest.candidate_words                   # units.csv, word_counts.json, private samples
uv run python -m metadata.manifest build data/candidates -o data/manifests/candidates.jsonl
uv run python -m metadata.manifest build data/private/candidates -o data/manifests/candidates-private.jsonl
```

Internet Archive requests send a `bom-authorship-research` user agent with a fixed delay
(`--delay`). Joseph Smith Papers requests send a browser user agent with a random delay
averaging `ingest.jsp.JSP_DELAY` and retries that back off by minutes; why, and the site terms
involved, are in `docs/candidates.md` (Joseph Smith, "How these were obtained"). Measured on
2026-10-25: at a 1 s average the site refused pages after about 26 and 66 requests; at 5 s it
blocked the address after about 165 requests (roughly 14 minutes), longer than six minutes of
retries. Hourly probes still got 404 at 12:35, 13:35, 14:35 and 15:35 PDT, but at about
15:50 a second network got the same 404, and the page's own data showed why: the shell and
table of contents load, while the transcript service answers `{"status": 500, "error": true}`.
So from some point the 404 was a server-side fault, not a block on this address; when that
point was is not known, and the earlier short refusals may still have been throttling. A
future fetcher should read `summary.status` before treating a 404 as a block. Expect to resume a full rebuild across several sittings. The fetcher skips any output already on disk.
`--id` picks single sources; `--max-pages N` caps Joseph Smith Papers documents while testing.
