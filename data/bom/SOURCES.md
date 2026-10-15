# Book of Mormon base texts: sources and how to recreate `data/bom/`

Only this file, the 1830 edition texts, and the checksum manifests are committed. The
manuscript transcripts are copyright Intellectual Reserve, Inc. (Joseph Smith Papers) and
are not redistributed here. Anyone can rebuild the full directory with the commands below.

## 1. Printer's manuscript (1829-1830)

- Source: Joseph Smith Papers, "Printer's Manuscript of the Book of Mormon, circa August
  1829–circa January 1830", 468 pages.
  https://www.josephsmithpapers.org/paper-summary/printers-manuscript-of-the-book-of-mormon-circa-august-1829-circa-january-1830/1
- Print edition: *Revelations and Translations, Volume 3, Parts 1-2* (2015), ed. Royal
  Skousen and Robin Scott Jensen.
- What the online transcript contains: the original inscriptions only. Later redactions made
  to prepare the text for printing are not in the online transcript (the site says so on
  every page); they are in the print facsimile edition.
- Scribe information: the page JSON carries `scribes` per page and inline notes such as
  "Oliver Cowdery handwriting begins", which the fetcher keeps in `editorial_notes`.
- Rebuild: `uv run python -m ingest.jsp printers` writes `raw/jsp/printers/NNNN.json` (one
  per page, the page's full embedded JSON) and `jsp_printers.jsonl` (one record per page:
  text, editorial page number, scribes, notes, table-of-contents entry).

## 2. Original manuscript (1828-1829)

- Source: Joseph Smith Papers, "Original Manuscript of the Book of Mormon, circa 12 April
  1828–circa 1 July 1829", 231 pages.
  https://www.josephsmithpapers.org/paper-summary/original-manuscript-of-the-book-of-mormon-circa-12-april-1828-circa-1-july-1829/1
- Print edition: *Revelations and Translations, Volume 5* (2021).
- Extent: about 28% of the original manuscript survives (Skousen), excluding the 116 lost
  pages. Missing stretches are marked in the transcript, for example "[ 2 pages not extant ]".
  The printer's manuscript fills the gaps for alignment.
- Rebuild: `uv run python -m ingest.jsp original`.

## 3. 1830 edition (Palmyra, E. B. Grandin)

Public domain. Both files are committed.

- `1830/jenson-reproduction-1830.pdf` and `.txt`: Thomas A. Jenson's 2012 typed
  reproduction of the first edition, checked against scans, preserving spelling, errors,
  page breaks, and numbering. Internet Archive item `book-of-mormon-1830-digital-replica`,
  Creative Commons Public Domain Mark. This is the primary 1830 text. The `.txt` is the
  PDF's own text layer extracted with `pdftotext -layout` (poppler), not the Internet
  Archive's `_djvu.txt`, which is a re-OCR of the PDF and contains errors. It keeps the
  running page headers (for example "FIRST BOOK OF NEPHI.  7") and soft hyphens (U+00AD) at
  line-end word breaks; downstream code removes both.
  https://archive.org/details/book-of-mormon-1830-digital-replica
- `1830/pittsburgh-scan-ocr-1830.txt`: raw OCR of a scanned first-edition copy, University of
  Pittsburgh Library System, Internet Archive item `bookofmormonacco1830smit`. Used only to
  cross-check the reproduction; expect OCR errors.
  https://archive.org/details/bookofmormonacco1830smit
- Rebuild: `scripts/fetch_1830.sh` (needs `pdftotext` from poppler).

## 4. Fetch etiquette

The Joseph Smith Papers site has no robots.txt and no bulk download. The fetcher identifies
itself, requests one page every 1.5 seconds, and resumes from the files already on disk.
Fetched 2026-10-15.

## 5. Derived outputs (committed; they contain numbers and references, not manuscript text)

| File | What it is |
| --- | --- |
| `1830/edition_1830.jsonl` | the 1830 text as books, chapters, paragraphs, pages (`ingest.edition_1830`) |
| `jsp_printers_toc.json`, `jsp_original_toc.json` | the Papers' page-level tables of contents with modern references |
| `align_printers.jsonl`, `align_original.jsonl` | per manuscript page: 1830 paragraphs it carries, scribes, anchor count (`ingest.align`) |
| `align_*_paragraphs.jsonl` | per 1830 paragraph: manuscript pages, scribes, coverage fraction |
| `diff_printers.jsonl`, `diff_original.jsonl` | per 1830 paragraph: word-level similarity to the manuscript (`ingest.diff_report`) |
| `reports/align_*.md`, `reports/diff_*.md` | summaries of the two above |
| `reports/original_extant.md` (+ `.jsonl`) | which pages of the original manuscript survive, with gap notes (`ingest.extant`) |

Rebuild all of them with `scripts/build_bom.sh`.

## 6. Manifests

After a rebuild, verify against the committed manifests:

```
uv run python -m metadata.manifest verify data/bom data/manifests/bom.jsonl
```
