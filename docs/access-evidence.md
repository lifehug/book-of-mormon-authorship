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

### The 26 June 1829 title page: CONFIRMED from the page scan

**Resolved 2026-10-21.** The owner obtained the page image from NYS Historic Newspapers and it
settles the question: the *Wayne Sentinel* of Friday 26 June 1829, **page 3, column 2**, carries
an editorial notice followed by the Book of Mormon title page in full, set in clear type and
entirely legible. The scan is at `data/corpus/nyshn/wayne_sentinel/wayne_sentinel_18290626_p3.pdf`
(outside git; checksum in `data/manifests/wayne_sentinel_pdf.jsonl`).

Transcribed from the scan. Square brackets mark readings the film leaves uncertain:

> Just about in this particular region, for some time past, much speculation has existed,
> concerning a pretended discovery, through superhuman means, of an ancient record, of a
> religious and divine nature and origin, written in characters, impossible to be interpreted by
> any to whom the special gift has not been imparted by inspiration. It is generally known and
> spoken of as the **"Golden Bible."** M[ost who] entertain an idea that the whole matter is the
> result of a gross imposition, and a grosser superstition. It is pretended that it will be
> published as soon as the translation is completed.
>
> Meanwhile we have been furnished with the following, which is represented to us as **intended
> for the title page of the work** — we give it as a curiosity: —
>
> "**The Book of Mormon**, an account written by the hand of Mormon upon plates, taken from the
> plates of Nephi —
>
> "Wherefore it is an abridgment of the record of the people of Nephi, and also of the
> Lamanites, written to the Lamanites, which are a remnant of the house of Israel; and also to
> Jew and Gentile — written by way of commandment, and also by the spirit of prophecy and of
> revelation. Written and sealed and hid up unto the Lord, that they might not be destroyed — to
> come forth by the gift and power of God unto the interpretation thereof — sealed up by the hand
> of Moroni, and hid up unto the Lord, to come forth in due time by the way of Gentile — the
> interpretation thereof by the gift of God — an abridgment taken from the book of Ether.
>
> "Also, which is a record of the people of Jared, which were scattered at the time the Lord
> confounded the language of the people, when they were building a tower to get to Heaven; which
> is to shew unto the remnant of the house of Israel how great things the Lord hath done for
> their fathers; and that they may know the covenants of the Lord, that they are not cast off
> forever — and also to the convincing of the Jew and Gentile that Jesus is the Christ, the
> Eternal God, manifesting himself unto all nations. And now, if there be fault, it be the
> mistake of men; wherefore condemn not the things of God, that ye may be found spotless at the
> judgment seat of Christ. — by **JOSEPH SMITH, Junior, Author and Proprietor**."

The item sits in the news column; the apothecary and dry-goods advertisements that the OCR
spliced it with are in columns 4 to 7, physically distant. The interleaving was never on the
page — it was introduced by the text extraction.

### What this does to every negative finding on this source

This is the more important result, and it is a correction to the section that follows.

The page above contains, in clear print: *Golden Bible*, *Book of Mormon*, *hand of Mormon*,
*plates of Nephi*, *Lamanites*, *Moroni*, *abridgment*, *Joseph Smith*, *Author and Proprietor*.
Searching the OCR of that same page for all ten returns **zero**. Not one. The phrase "spoken of
as the 'Golden Bible'" survives extraction as:

    ...llisgenorallyunowntlnirhiils11mmdspulciitdfsijoiegattlmbiblemistcxniiild...

`Golden Bible` has become `gattlmbible`.

So the index's recall on this source is far worse than its six confirmed hits suggest, and
**no negative statement about the Wayne Sentinel may be made from the OCR at all.** The six
items found are a floor, not a census: they are the occasions when the film happened to be
legible, not the occasions when the paper mentioned the book. Earlier wording here called the
Golden Bible zero "a real negative" and offered an explanation for it — that the coverage
belonged to the Palmyra *Freeman* and the Rochester papers. That explanation was wrong and is
withdrawn. The *Sentinel* printed the phrase; the OCR lost it.

Practically: BOM-14 cleaning is now a hard prerequisite for this source rather than an
improvement, and any claim about what the *Sentinel* did **not** carry has to be made against
page images, not against this text layer.

### Terms deliberately not used

Bare `nephi` and bare `mormon` were dropped after validation. The index squeezes whitespace and
punctuation out of every page so that fragmented OCR (`t h e b o o k`) still matches, and that
squeezing makes `ne Philadelphia` into `nephiladelphia` — five of eight `nephi` hits were that
word. Only distinctive multi-word forms are searched: `bookofmormon`, `ofnephi`, `handofmoroni`.

`goldenbible`, `goldbible`, `goldenplates` and `goldplates` returned zero hits across the whole
run. **That zero means nothing**, for the reason given above: the one page we have independently
verified to carry the phrase also returns zero.

## Lake Light, Trumansburg, 1827-1828

Not indexed for access evidence. It is 50 miles from Palmyra and enters the project as W. W.
Phelps's writing sample (BOM-13), not as evidence of what was available near the Smiths.
