# Palmyra Register (Palmyra, N.Y.), 1817-1821

T. C. Strong's weekly, the Smiths' local paper from their arrival in 1817 until the *Wayne Sentinel*. Carries Strong's bookstore lists (15 Sep 1818 p3; Strong & Bradish, dated 13 Oct 1819, in the 27 Oct 1819 issue p4). BOM-33 (access evidence).

| File | Built by | Contents |
| --- | --- | --- |
| `pages.jsonl` | `ingest.advantage_archive.pull` with this title added to `TITLES` at runtime (2026-11-06; see "Rebuild") | one row per page: name, date, page number, the archive's PubdateId, PDF sha256 and size, word count of the text layer. 648 pages, 162 issues, 3,102,226 words of text layer, 1817-11-26 to 1821-03-07 |
| `text/<name>.txt` | same (poppler `pdftotext -layout` on each PDF) | the PDF's own OCR text layer as delivered by the archive. Microfilm OCR, poor: a miss in it is not evidence of absence |
| `probed_misses.txt` | same | page names probed and absent (resume state; not tracked) |

Source: Digital Archives of the Pioneer Library System,
https://pioneerlibrarysystem.advantage-preservation.com/ (Advantage Archives), title id `33163`,
page names `palmyra_register_usa_new_york_palmyra_<YYYYMMDD>_english_<n>`, resolved through
`https://pioneerlibrarysystem.advantage-preservation.com/viewer/?t=33163&i=t&fn=<name>&df=1&dt=10&cid=`
(no collection id needed on this site). Not Cloudflare-fronted. The text is public domain. The
page count matches the archive's own figure for the title.

The page PDFs are in `data/corpus/advantage/pioneerlibrarysystem/`, outside git, with checksums
in `data/manifests/pioneerlibrarysystem_pdf.jsonl`. The text files are checksummed in
`data/manifests/palmyra_register_text.jsonl`.

Rebuild (resumable; about an hour for the *Register*, twenty minutes for the *Herald*, at one
request a second; one SSL timeout on 2026-11-06 needed a restart, which resumed cleanly):

```
uv run python -m ingest.advantage_archive pull --title "Palmyra Register"
```

Both titles are now in `TITLES` in `ingest/advantage_archive.py`, so this is a plain
`python -m ingest.advantage_archive pull --title "Palmyra Register"` (or `"Palmyra Herald"`).
