# Access evidence (BOM-33)

**The ceiling, stated once and applied everywhere below.** This file records what was
*demonstrably available in the area* — what a newspaper printed, what a bookseller advertised.
It never says, and may never be quoted as saying, that Joseph Smith or anyone else read any of
it. Nobody wrote down what he borrowed, and no lending register for a village rental library is
likely to survive. That limit is historical, not a consequence of working from digitized
sources, and the paper states it in those terms.

Status: the *Wayne Sentinel* index below is done. The Manchester rental library holdings and the
per-source availability scoring (which depend on BOM-26) are not started.

## Wayne Sentinel, Palmyra, 1823-1830

1,429 pages, 376 issues, 1 Oct 1823 to 31 Dec 1830. Palmyra's weekly; printed by E. B. Grandin
from 1827, who printed the Book of Mormon itself. Index built by
`python -m ingest.access_index build data/newspapers/wayne_sentinel --name wayne_sentinel`
into `data/access/wayne_sentinel_access.jsonl`, one row per hit with its date, page and the raw
snippet that produced it.

### Book of Mormon items found

Six hits on four dates, every one inspected and genuine:

| Date | What the page carries |
| --- | --- |
| 1830-03-19 | `"B ook o f M ormon" w ill b e re a d y for s a l[e]` — the forthcoming-publication notice |
| 1830-03-26 | `by the hand Tof Moroni ... hid up nnto` and `BY JO S E P H S M IT H , JU N IO R` — title-page text with its byline |
| 1830-04-02 | `of^he P eople of Nephi., and also.of` and `by theTinnH of Moroni` — the title page again |
| 1830-05-07 | `THE BOOK OF MORMON` in capitals, with `the Pco.le of Nephi; and also of tbe La[manites]` — the sale advertisement |

The title-page advertisement with its `BY JOSEPH SMITH, JUNIOR` byline recurs on 26 Mar,
2 Apr, 9 Apr, 16 Apr and 7 May 1830 — a five-week run, not a single insertion.

**One item is earlier than the project had recorded.** `data/newspapers/wayne_sentinel/SOURCES.md`
names 26 June 1829 and 26 March 1830. The notice of 19 March 1830 — the book "will be ready for
sale" — is a week before the earliest 1830 date on record here and was not previously noted.

### The 26 June 1829 title page could not be confirmed from this OCR

This is the single most-cited page in the whole corpus, and it is the one page the index cannot
verify. All four pages of that issue were checked directly. Page 3 contains the only candidates,
and both are false:

- `mormon` occurs inside a garbled apothecary advertisement
  (`...4cld stinctures and essences ihelnmlyrmormonupnnplutoslukeii...`), a coincidental
  substring, not a reference.
- `titlepage` occurs in `...anditnntmshavebeenannndedforthetitlepageoftheworkwegive...`, which
  reads as genuine title-page language — but the OCR has **interleaved two columns**, splicing it
  with a cloves-and-pepper advertisement, so no phrase can be read with confidence.

The content is very likely present and the microfilm OCR has destroyed it. Confirming it needs
the page image or an independent transcription, neither of which this index can supply. It is
recorded here as *unconfirmed from OCR*, not as absent, and it must not be counted either way
until a human reads the scan.

### Printed matter advertised

| Group | Hits | Pages |
| --- | --- | --- |
| bookselling (`bookstore`, `books for sale`, `just received`, `new books`, `bookbindery`) | 2,869 | 826 |
| Grandin imprint | 1,932 | 544 |
| sermons and tracts (`sermon delivered`, `discourse delivered`, `religious tract`) | 6 | 6 |

Bookselling language appears on 826 of 1,429 pages — 58% — which establishes that printed matter
was continuously advertised for sale in Palmyra across the whole run. It does not yet establish
*which* books; extracting titles from advertisement columns is defeated by the same column
interleaving shown above, and is left to BOM-33's later work against the page images.

The Grandin count is dominated by the masthead and imprint line and should be read as
"Grandin printed this paper", not as 1,932 distinct mentions.

### Hits that look relevant and are not

`josephsmith` fires on 3 Nov 1824, 21 Jul 1826, 11 Aug 1826 and 18 Aug 1826, in subscription
and jury lists. Joseph Smith was a common name; these are other men. They are kept in the index
with their snippets precisely so the 1830 byline hits can be distinguished from them by reading
rather than by counting.

### Terms deliberately not used

Bare `nephi` and bare `mormon` were dropped after validation. The index squeezes whitespace and
punctuation out of every page so that fragmented OCR (`t h e b o o k`) still matches, and that
squeezing makes `ne Philadelphia` into `nephiladelphia` — five of eight `nephi` hits were that
word. Only distinctive multi-word forms are searched: `bookofmormon`, `ofnephi`, `handofmoroni`.

`goldenbible`, `goldbible`, `goldenplates` and `goldplates` returned **zero hits** across the
whole run. This is a real negative and worth stating: the "Golden Bible" press coverage of 1829
that is usually cited belongs to the Palmyra *Freeman* and the Rochester papers, not to the
*Sentinel*. Given the OCR quality demonstrated above, a zero here is weak evidence of absence,
and should be treated as "not found", not "not printed".

## Lake Light, Trumansburg, 1827-1828

Not indexed for access evidence. It is 50 miles from Palmyra and enters the project as W. W.
Phelps's writing sample (BOM-13), not as evidence of what was available near the Smiths.
