# Wayne Sentinel (Palmyra, N.Y.), 1823-1830

The Smiths' local weekly, published at Palmyra from 1 October 1823 (E. B. Grandin from 1827,
the printer of the Book of Mormon). LCCN `sn84024337`. BOM-41; feeds BOM-33 (what was printed
and advertised near Palmyra: the "Golden Bible" items, the Book of Mormon title page on
26 June 1829, the sale notice on 26 March 1830) and BOM-10's New York coverage.

| File | Built by | Contents |
| --- | --- | --- |
| `pages.jsonl` | `scripts/nyshn_browser_pull.py pull --title "Wayne Sentinel" --start 1823-10-01 --end 1830-12-31` (2026-10-20) | one row per page: name, date, edition, page number, the site's page id (`oid`), word count of the OCR text. 1,429 pages, 376 issues, 1823-10-01 to 1830-12-31 |
| `text/<name>.txt` | same (the site's per-page OCR text view, one line per OCR paragraph) | NYSHN's OCR as delivered; 11,268,461 "words", much of it OCR noise. Microfilm OCR, poor: goes through BOM-14 before any measurement |

Source: NYS Historic Newspapers (Northern New York Library Network, Veridian platform),
https://nyshistoricnewspapers.org/, title code `ws`. The text is public domain (1823-1830).
The site is Cloudflare-fronted and blocks scripts; the pull drove a browser the owner had
unlocked, over the DevTools protocol (mechanics in the script's docstring). No page PDFs were
taken: each PDF sits behind a per-page Cloudflare Turnstile that solves itself only
sometimes, so `--pdf` is best-effort and was left off. Checksums of the text files are in
`data/manifests/wayne_sentinel_text.jsonl`.

Coverage: a near-complete weekly run. Issues per year: 1823 (Oct-Dec) 14; 1824 52; 1825 52;
1826 50; 1827 51; 1828 52; 1829 52; 1830 53. Four single-week gaps (the issues of 10 Jan
1826, 9 Jun 1826, 20 Jul 1827 and 18 Dec 1829 are absent). 317 issues have four pages; 47 have
two (half sheets or incomplete filming); 12 run to five, six or nine pages (supplements or
pages filed twice). Nine pages have no OCR text on the site at all (the text view shows the
OCR disclaimer and nothing after it); they are kept as zero-word rows:
`18250913_p3`, `18260901_p2`, `18270119_p1`, `18270713_p4`, `18270824_p4`, `18280627_p2`,
`18280822_p2`, `18300423_p2`, `18300820_p4`.

NYSHN holds the Sentinel to 1859; only 1823-1830 was pulled (the Book of Mormon was on sale
from March 1830). Rebuild or extend: start a browser with remote debugging, pass the
Cloudflare check by hand, then run the command above (resumable, about 2 hours for this
range; change `--end` to extend).
