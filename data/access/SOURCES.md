# Access evidence index (BOM-33)

| File | Built by | What |
| --- | --- | --- |
| `wayne_sentinel_access.jsonl` | `python -m ingest.access_index build data/newspapers/wayne_sentinel --name wayne_sentinel` (2026-10-21) | 4,831 OCR-derived hits over 1,429 pages: date, page id, term group, matched term, raw snippet |
| `wayne_sentinel_verified.jsonl` | human reading of page scans (2026-10-21) | items confirmed by eye on the image. Separate file on purpose: these are *not* OCR-derived and must not be mixed into recall or precision figures for the index |
| `access_table.csv` | compiled by hand, 2026-11-06 (BOM-33), from the sources listed under "Sources of the access table" below | 33 rows, one per candidate text: `source_id, title, author, year, kind, score, evidence, citation_url`. Scale and method in `docs/access-evidence.md`, "Availability scoring" |

**The ceiling:** this records what was *demonstrably available in the area*, never that any
person read it. See `docs/access-evidence.md`, which states the limit and must be read with the
data.

**The index cannot support negative findings on this source.** The 26 June 1829 page carries the
Book of Mormon title page in clear print, and the OCR of that page returns zero for all ten
diagnostic terms — `Golden Bible` survives extraction as `gattlmbible`. The OCR hits are a
floor, not a census. Any claim about what a paper did *not* print must be made against page
images. Full reasoning in `docs/access-evidence.md`.

Matching squeezes whitespace and punctuation out of each page so NYSHN's fragmented OCR
(`t h e b o o k`) still matches. That trades word boundaries for recall, so every row carries
its snippet and the file is meant to be read, not counted.

## Sources of the access table

All read 2026-11-06, public, no login. Every row of `access_table.csv` also carries its own
`citation_url`.

**How to rebuild.** The table is a research record, not a pipeline output. To check it, open
each source below. The candidate lists come from `data/semantic/corpus_bom.json`
(`top_search_sources`, looked up in `data/catalog/catalog.parquet`) and `docs/candidates.md`.
The *Wayne Sentinel* searches can be re-run against `data/newspapers/wayne_sentinel/text/`:
lower-case each page, strip everything but a-z, and search for `josephus`, `historicalreader`,
`viewofthehebrews`, `ethansmith`, `latewar`, `bookofnapoleon`, `spalding|spaulding`,
`georgefox`, `naylor|nayler`, `biblicalreader`, `sacredliterature`.

| What | Where |
| --- | --- |
| Robert Paul, "Joseph Smith and the Manchester (New York) Library," *BYU Studies* 22, no. 3 (1982): article and appendix of all 421 accessions | https://scholarsarchive.byu.edu/byusq/vol22/iss3/6 ; PDF: https://archive.bookofmormoncentral.org/sites/default/files/Robert%20Paul%2C%20Joseph%20Smith%20and%20the%20Manchester%20%28New%20York%29%20Library%2C%201982_0.pdf |
| *Wayne Sentinel* OCR, 1823-1830 (this repo) | `data/newspapers/wayne_sentinel/text/`; source NYS Historic Newspapers, https://nyshistoricnewspapers.org/ (LCCN sn84024337) |
| *Western Recorder*, Utica, 7 Feb 1826, p. 23, "New Books" (*View of the Hebrews*, 2nd-ed. title, sold by Merrell & Hastings) | https://archive.org/details/sim_western-recorder_western-recorder_1826-02-07_3_84 ; record: https://bhroberts.org/records/0rGxg3-p7Cq4c |
| *View of the Hebrews* circulation timeline, 1823-1829 (B. H. Roberts Foundation, formerly mormonr.org) | https://bhroberts.org/qnas/vFzgdj/the_book_of_mormon_and_view_of_the_hebrews/research (redirect from https://mormonr.org/qnas/vFzgdj/the_book_of_mormon_and_view_of_the_hebrews/research) |
| Imprints, Internet Archive items | `https://archive.org/metadata/<identifier>/metadata`, for each IA identifier in the table |
| Imprints, Harvard Institutional Books items | title pages of the local texts (`data/corpus/institutional_books/text_gen/<id>.txt`, licensed, not in git); public catalogue records at `https://hdl.handle.net/2027/hvd.<id lower-case>` |
| Imprint, Fox *Journal* (TCP N28090, Evans 37441) | https://raw.githubusercontent.com/textcreationpartnership/N28090/master/N28090.xml |
| *The Historical Reader*: Hunt (New York 1817, 1819) and Blake (Concord, N.H., 1824-1825) | https://archive.org/details/historicalreader00huntgil ; https://archive.org/details/readercontain00hunt ; https://archive.org/details/historicalreader00blakrich ; https://archive.org/details/historicalreade02blakgoog |
| *The First Book of Napoleon* (London 1809) | https://archive.org/details/firstbooknapole00gruagoog ; https://en.wikisource.org/wiki/The_First_Book_of_Napoleon |
| Spalding holograph; 1885 edition; Howe 1834 | https://oberlin.libraryhost.com/repositories/2/resources/455 ; https://archive.org/details/themanuscriptsto00spauuoft ; https://archive.org/details/mormonismunvaile00howe |
| *Ontario Phoenix* holdings (NYS Library union list) | https://nysl.nysed.gov/nysnp/all/435 |
| *Lake Light* (Ulysses Philomathic Library) | https://trumansburg.advantage-preservation.com/ |
| Ontario County Historical Society (holds the Manchester library volumes and record books) | https://ochs.org/ |
| Grunder, *Mormon Parallels*: review giving format and price (not used as evidence) | https://interpreterfoundation.org/journal/finding-parallels-some-cautions-and-criticisms-part-one |

## Page-image checks and Palmyra pulls (2026-11-06, BOM-33 follow-up)

NYS Historic Newspapers needs the owner's unlocked browser (`scripts/nyshn_browser_pull.py`), and
none was running. The same papers turned out to be public, without Cloudflare, on the Pioneer
Library System's Advantage archive, so the scans were taken from there with the helpers in
`ingest/advantage_archive.py` (viewer probe, `GetPdfFile`, one request a second or slower).

| What | Where |
| --- | --- |
| Pioneer Library System digital archive (Wayne Sentinel title id 33165, 1823-1859; Palmyra Register 33163, 1817-1821, 648 pages; Palmyra Herald and Canal Advertiser 33159, 1822-1823, 157 pages) | https://pioneerlibrarysystem.advantage-preservation.com/ |
| A page's viewer (resolves the page name to its PDF) | `https://pioneerlibrarysystem.advantage-preservation.com/viewer/?t=<title id>&i=t&fn=<name>&df=1&dt=10&cid=` |
| Page names | `wayne_sentinel_usa_new_york_palmyra_<YYYYMMDD>_english_<n>`; `palmyra_register_usa_new_york_palmyra_<YYYYMMDD>_english_<n>`; `palmyra_herald_and_canal_advertiser_usa_new_york_palmyra_<YYYYMMDD>_english_<n>` |
| Wayne Sentinel scans read by eye | 18240818 p3, 18261208 p3, 18271026 p4, 18290313 p4, 18290320 p4, 18291211 p3; PDFs in `data/corpus/advantage/pioneerlibrarysystem/` (not in git; checksums below) |
| Palmyra Register pages read by eye | 15 Sep 1818 p3 (T. C. Strong's list), 27 Oct 1819 p4 (Strong & Bradish list), 27 Dec 1820 p4 (Wescott), 5 Jul 1820 p3, 9 Aug 1820 p3, 3 Jan 1821 p3 (false OCR leads) |
| Palmyra Herald page read by eye | 7 Aug 1822 p4 (E. Peck & Co., Rochester: "Josephus' Work, 6 vols. D3."); viewer `https://pioneerlibrarysystem.advantage-preservation.com/viewer/?t=33159&i=t&fn=palmyra_herald_and_canal_advertiser_usa_new_york_palmyra_18220807_english_4&df=1&dt=10&cid=` |
| Checksums | `data/manifests/palmyra_register_text.jsonl` (648), `data/manifests/palmyra_herald_text.jsonl` (157), `data/manifests/pioneerlibrarysystem_pdf.jsonl` (811 PDFs = 648 + 157 + 6 Sentinel pages) |
| Palmyra Register, 15 Sep 1818, pp. 1-4 (T. C. Strong's book list, p. 3) | same folder; viewer `...viewer/?t=33163&i=t&fn=palmyra_register_usa_new_york_palmyra_18180915_english_3&df=1&dt=10&cid=` |
| Palmyra Register 1817-1821 and Palmyra Herald 1822-1823, full runs | pulled by `ingest.advantage_archive.pull` with the two titles added at runtime (slugs `palmyra_register`, `palmyra_herald`): PDFs in `data/corpus/advantage/pioneerlibrarysystem/`, text layers and `pages.jsonl` in `data/newspapers/palmyra_register/` and `data/newspapers/palmyra_herald/` |
| Ontario Repository (Canandaigua), 1809-1829 | NYSHN only (title index in `docs/new-york-newspapers.md`); not on Chronicling America (LoC records sn85026151, sn85042109, sn83031526 show no digitized pages) and not found on an Advantage site. Not searched |
