# Palmyra Herald, and Canal Advertiser (Palmyra, N.Y.), 1822-1823

Palmyra's paper between the *Register* and the *Wayne Sentinel*. Carries E. Peck & Co. (Rochester) book lists, July-September 1822, including "Josephus' Work, 6 vols." BOM-33 (access evidence).

| File | Built by | Contents |
| --- | --- | --- |
| `pages.jsonl` | `ingest.advantage_archive.pull` with this title added to `TITLES` at runtime (2026-11-06; see "Rebuild") | one row per page: name, date, page number, the archive's PubdateId, PDF sha256 and size, word count of the text layer. 157 pages, 39 issues, 859,338 words of text layer, 1822-06-19 to 1823-03-12 |
| `text/<name>.txt` | same (poppler `pdftotext -layout` on each PDF) | the PDF's own OCR text layer as delivered by the archive. Microfilm OCR, poor: a miss in it is not evidence of absence |
| `probed_misses.txt` | same | page names probed and absent (resume state; not tracked) |

Source: Digital Archives of the Pioneer Library System,
https://pioneerlibrarysystem.advantage-preservation.com/ (Advantage Archives), title id `33159`,
page names `palmyra_herald_and_canal_advertiser_usa_new_york_palmyra_<YYYYMMDD>_english_<n>`, resolved through
`https://pioneerlibrarysystem.advantage-preservation.com/viewer/?t=33159&i=t&fn=<name>&df=1&dt=10&cid=`
(no collection id needed on this site). Not Cloudflare-fronted. The text is public domain. The
page count matches the archive's own figure for the title.

The page PDFs are in `data/corpus/advantage/pioneerlibrarysystem/`, outside git, with checksums
in `data/manifests/pioneerlibrarysystem_pdf.jsonl`. The text files are checksummed in
`data/manifests/palmyra_herald_text.jsonl`.

Rebuild (resumable; about an hour for the *Register*, twenty minutes for the *Herald*, at one
request a second; one SSL timeout on 2026-11-06 needed a restart, which resumed cleanly):

```
uv run python -m ingest.advantage_archive pull --title "Palmyra Herald"
```

Both titles are now in `TITLES` in `ingest/advantage_archive.py`, so this is a plain
`python -m ingest.advantage_archive pull --title "Palmyra Register"` (or `"Palmyra Herald"`).
