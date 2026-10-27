# Lake Light (Trumansburg, N.Y.), 1827-1828

W. W. Phelps's first newspaper. LCCN `sn84031024`. BOM-41; feeds BOM-13 and BOM-33.

**The imprint changes mid-run** (measured 2026-10-21, not assumed): `PHELPS & BLOOMER`
through 18 Feb 1828, then `CLARK & BLOOMER` from 19 Mar 1828, with the partnership
dissolved that May. Phelps had gone to the *Ontario Phoenix*; the issue of 3 Sep 1828
refers to it as another paper. Only 15 of the 42 issues are from his tenure. The
attribution rule in `docs/candidates.md` is written and governs what may be scored.

| File | Built by | Contents |
| --- | --- | --- |
| `pages.jsonl` | `python -m ingest.advantage_archive pull` (2026-10-20) | one row per page: name, date, page number, the archive's PubdateId, PDF sha256 and size, word count of the text layer. 168 pages, 42 issues, 1827-10-10 to 1828-11-19 |
| `text/<name>.txt` | same (poppler `pdftotext -layout` on each PDF) | the PDF's own OCR text layer, Tesseract 5.3.1 as delivered by the archive; 565,630 words. Microfilm OCR, poor: goes through BOM-14 before any measurement |
| `probed_misses.txt` | same | page names probed and absent (resume state; not tracked) |

Source: Digital Archives of the Ulysses Philomathic Library,
https://trumansburg.advantage-preservation.com/ (Advantage Archives), collection `cid=3142`,
title ids `34773,47247`. Terms of use: "made available to the community for the purpose of
research, study and to satisfy curiosity"; the text is public domain (1827-1828). The page PDFs
(400 dpi greyscale JPEG, 1.0 GB) are in `data/corpus/advantage/trumansburg/`, outside git,
with checksums in `data/manifests/lake_light_pdf.jsonl`; the text files are checksummed in
`data/manifests/lake_light_text.jsonl`.

Coverage: the New York State Library microfilm run `<1827:10:10,22-1828:11:19>` (OCLC
10995092). 42 issues in 58 weeks; the film lacks 14 stretches of two or three weeks. The site
advertises 336 pages because it also holds an older ABBYY scan of the same pages
(`cid=2734`) that misdates four issues; it is not used.

Rebuild: `uv run python -m ingest.advantage_archive pull` (resumable, about an hour).

## cleaned/ (BOM-14)

`cleaned/` holds one file per page of `text/`, built by
`python -m ocr_fix.defragment run data/newspapers/lake_light/text -o data/newspapers/lake_light/cleaned`:
lines with words broken apart (`h a s b een`) are re-segmented into words against the period
lexicon, then hyphens and long s are repaired (`ocr_fix.clean`, no header pass). `text/` is
untouched. Interleaved columns are not fixed here; that needs page layout (BOM-50).
Checksums: `data/manifests/lake_light_cleaned.jsonl`.
