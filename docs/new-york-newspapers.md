# The New York newspapers Chronicling America does not have (BOM-41)

Chronicling America holds **47 New York pages** for the whole of 1800-1830. BOM-10 read that
as a hole where Palmyra should be. It is a hole in Chronicling America, not in digitization:
New York's period press was digitized by the state's own program, NYS Historic Newspapers
(NYSHN, Northern New York Library Network, Veridian platform since 2023), and by small
libraries on Advantage Archives. This note records what each of the three titles that
matter most turned out to be, and what else NYSHN holds for the period.

Status 2026-10-20, after the owner's browser check of NYSHN's full title list and scripted
checks of every other route.

## The three titles

| Title | LCCN | Place, years | Why it matters | Digitized? |
| --- | --- | --- | --- | --- |
| **Wayne Sentinel** | `sn84024337` | Palmyra, 1823-1859 | The Smiths' local paper. Reported the "Golden Bible" rumour and printed the Book of Mormon title page on 26 June 1829, nine months before publication; carried the 26 March 1830 sale advertisement | **Yes**, NYSHN (title index confirmed; about 1,400 issues) |
| **Lake Light** | `sn84031024` | Trumansburg, 1827-1829 | Phelps's first paper, publishers Phelps & Bloomer 1827-1828 | **Yes**: Ulysses Philomathic Library, `trumansburg.advantage-preservation.com`: 168 pages, 42 issues, 10 Oct 1827 to 19 Nov 1828, the New York State Library microfilm run (the site's "336 pages" counts the same pages twice, see below). **Pulled** by `ingest.advantage_archive` (`data/newspapers/lake_light/`) |
| **Ontario Phoenix** | `sn84031006` | Canandaigua, 1828-1832 | Anti-Masonic weekly. Publisher line: **W. W. Phelps & R. M. Bloomer (1828-1829), W. W. Phelps (1829-1830)** | **No.** Not on NYSHN (title index, O section), not on Chronicling America (0 pages), not on HathiTrust or the Internet Archive. Recorded as not digitized; out of scope |

### What survives of the Ontario Phoenix at all

The New York State Library's union list (https://nysl.nysed.gov/nysnp/all/435, OCLC
06586477) records every known holding. F = microfilm, P = paper:

| Holder | Format | Issues held |
| --- | --- | --- |
| Ontario County Historical Society | F | 1830-07-07 to 1832-08-29 (gaps) |
| Ontario County Historical Society | P | 1828-08-27; 1829-12-16; 1830-02-24; 1830-07-07 to 1832-08-29 |
| Rochester Public Library | P | 1828-07-16 to 1829-01-07 (about 15 issues); 1831-05 to 1832-04 (gaps) |
| New York State Library | P | one 1828 issue; 1831-03-02, 06-08, 11-16 |
| Livonia Public Library; New York Public Library; Watertown Daily Times | P | one issue each: 1831-01-05; 1831-10-05; 1829-02-04 |

The only continuous run starts **7 July 1830**, after the Book of Mormon went on sale and
after Phelps had bought a copy (April 1830). Pre-1830 survival is about twenty scattered paper
issues, none from March-June 1828 and three from all of 1829. So the earlier hope in this
file, "a weekly edited for roughly two years is on the order of tens of thousands of words",
does not hold for the surviving record in any form. Under the scope rule (digitized sources
only) the Phoenix is recorded as unavailable and the cause is reported in the paper.

## What NYSHN holds for 1800-1830 beyond the three

From NYSHN's title index (read 2026-10-20). Dates in the index are shown; where the index is
undated the Library of Congress catalogue date is given and marked LoC, to confirm on the site.

| Title | Place | Dates | Why it matters |
| --- | --- | --- | --- |
| Palmyra Register | Palmyra | 1817-1821 (LoC) | The Smiths' local paper before the Sentinel; the family arrived 1816-17 |
| Palmyra Herald, and Canal Advertiser | Palmyra | 1822-1823 (LoC) | The gap years before the Sentinel |
| Ontario Repository | Canandaigua | 1824-1829; 1809-1826 | Eleven miles from the Smiths, through the dictation years |
| Ontario Repository and Freeman; Ontario Messenger and Repository | Canandaigua | 1836-1839 (LoC); undated | Successors of the Phoenix line |
| Rochester Antimasonic Inquirer | Rochester | 1828-1830; 1831-1833 | The anti-Masonic organ Phelps's papers echoed; reprinted Phoenix matter plausible |
| Rochester Telegraph; Rochester Observer | Rochester | 1818- ; 1827- (LoC) | Nearest city press; the Observer is the religious weekly |
| The Lyons Countryman, and Anti-Masonic Recorder; Western Argus | Lyons (Wayne Co.) | c.1829- (LoC) | County-seat papers next to Palmyra |
| Anti-Masonic Telegraph | Norwich | 1829- (LoC) | Anti-Masonic press |
| Geneva Gazette; Geneva Palladium | Geneva | 1809-1825; 1816- (LoC) | Ontario County |
| The People's Press | Batavia | 1825-1830 | Genesee County, where the Morgan affair began |
| Livingston Journal; Ovid Gazette; Oswego Palladium; Onondaga Register; Freeman's Journal (Cooperstown) | western and central NY | 1823-1831; 1821-1824; 1819-1828; undated; 1807- | Period regional press |
| Catskill Recorder; Schenectady Cabinet; Lansingburgh Gazette; Commercial Advertiser and New-York Evening Post (NYC); Long Island Farmer | eastern NY | 1829-1845; 1824-1837; 1798-1825, 1827-1883; 1797-1820; 1821-1825 | Period state press beyond the region |

Together these put the Palmyra press from 1817, Canandaigua from 1824 and the Rochester
anti-Masonic press from 1828 within reach, which is most of what BOM-10 and BOM-33 wanted
from New York. Whether to pull them is a scope decision recorded on BOM-41.

## Getting them

**Lake Light** is done: `python -m ingest.advantage_archive pull`. The Advantage site is not
Cloudflare-fronted; each page is a PDF resolved by probing page names through the viewer (the
module's docstring has the mechanics). The archive holds the run twice: collection 3142, a
400 dpi greyscale scan with a Tesseract 5 text layer, and collection 2734, an older, smaller
ABBYY FineReader 9 scan of the same 168 pages that files four issues under the wrong date
(3 Dec 1827 as pages 5-8 of 26 Nov; 24 Dec under 17 Dec; 7 Jan 1828 as 6 Jan; 1 Mar as 5 Mar).
The pull takes collection 3142 only. 42 issues over 58 weeks: the microfilm lacks 14 stretches
of two or three weeks, so about 16 issues never survived to be filmed. PDFs (1.0 GB) live in
`data/corpus/advantage/trumansburg/`, manifests in `data/manifests/lake_light_*.jsonl`; the
text layer (565,630 words, 14 MB) and page index are in `data/newspapers/lake_light/` and in git.

**NYSHN** blocks scripts (Cloudflare 403 on HTML, JSON and text endpoints alike) but not a
browser. `scripts/nyshn_browser_pull.py` drives a browser the owner has already unlocked, over
the DevTools protocol: start Brave with `--remote-debugging-port=9222`, pass the challenge by
hand, then `probe` a title page to confirm the Veridian URL shapes and `pull` the title. The
Veridian layout in that script was written from other Veridian sites, not a live NYSHN
session; its two link regexes may need one adjustment after the first probe.

## What it does not fix

Even complete, this is availability evidence, not readership evidence. That a paper printed
something near Palmyra does not establish that anyone in the Smith household read it. The
ceiling stays where `docs/backlog.md` puts it for BOM-33: *demonstrably available in the area*,
never *he read it*.

For Phelps the Lake Light is his own paper, but a weekly carries reprinted matter and the
masthead names two publishers (Phelps & Bloomer). Unsigned editorial matter is not
automatically one man's writing; attribution within the paper needs its own rule before the
text enters his candidate sample (BOM-13). The OCR on this microfilm is poor (the
Tesseract layer on the first page of the first issue yields six words), so the text goes
through BOM-14's OCR correction before any measurement.
