# data/newspapers/ontario_repository

The *Ontario Repository* (Canandaigua, N.Y.), the county-seat weekly about ten miles from the
Smith farm, pulled 2026-11-06 for BOM-33 (bookseller advertisements of candidate sources).

| File | Made by | What |
| --- | --- | --- |
| `pages.jsonl` | `scripts/nyshn_browser_pull.py pull --title "Ontario Repository" --code onrb --start 1824-01-01 --end 1829-12-31`, then `--code onr` (the six months held under the second code) | one row per page: name, date, edition, page number, the site's page id, OCR word count. 483 pages |
| `text/<name>.txt` | same | the site's per-page OCR text (public domain, 1824-1829). Microfilm OCR: a miss is not evidence of absence |

Source: NYS Historic Newspapers, https://nyshistoricnewspapers.org/, title codes `onrb` and `onr`,
read through an ordinary Chrome session on the Mac mini (the site is Cloudflare-fronted; the
browser passed its check by itself; nothing was bypassed), at the script's default pace.

Coverage: the site holds only part of the run: 124 issues in 1824-1829 (a full weekly run would
be about 300). The 1809-1823 years are not on the site, though secondary listings say so.
Checksums: `data/manifests/ontario_repository_text.jsonl`.
