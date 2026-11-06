# Access evidence (BOM-33)

**The ceiling, stated once and applied everywhere below.** This file records what was
*demonstrably available in the area* — what a newspaper printed, what a bookseller advertised.
It never says, and may never be quoted as saying, that Joseph Smith or anyone else read any of
it. Nobody wrote down what he borrowed, and no lending register for a village rental library is
likely to survive. That limit is historical, not a consequence of working from digitized
sources, and the paper states it in those terms.

Status (2026-11-06): all three parts drafted. The *Wayne Sentinel* index is done (below); the
Manchester library holdings, the Palmyra bookseller findings and the per-source availability
table follow the Lake Light section. The table is `data/access/access_table.csv` (33 rows); its
sources are in `data/access/SOURCES.md`. Follow-up the same day: the Josephus and "Historical
Reader" ads were checked on the page images, and the *Palmyra Register* (1817-1821) and
*Palmyra Herald* (1822-1823) were pulled and searched (see "Follow-up"). The *Ontario
Repository* is still unsearched (NYSHN only).

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
It is **not** earlier than the 26 June 1829 title page, which was already on record. Whether it
is new to the published scholarship on the printing has not been checked and is not claimed: this
is a statement about this project's records, nothing more.

**Checked 2026-11-02 (BOM-51): already documented.** BYU Library's *19th-Century Publications
about the Book of Mormon* master list carries it as "[We are requested to announce.] The Wayne
Sentinel (19 March 1830)"
(https://lib.byu.edu/collections/19th-century-publications-about-the-book-of-mormon/about/master-list-of-documents/).
Status `established` in `data/claims/novelty.yaml`.

### The 26 June 1829 title page: CONFIRMED from the page scan

**Resolved 2026-10-21.** The owner obtained the page image from NYS Historic Newspapers and it
settles the question: the *Wayne Sentinel* of Friday 26 June 1829, **page 3, column 2**, carries
an editorial notice followed by the Book of Mormon title page in full, set in clear type and
entirely legible. The scan is at `data/newspapers/wayne_sentinel/scans/wayne_sentinel_18290626_p3.pdf`
(committed; checksum in `data/manifests/wayne_sentinel_scans.jsonl`).

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

## Availability scoring (BOM-33, 2026-11-06)

### Method

The question is narrow: **was a given text documented as available where Joseph Smith lived,
before the Book of Mormon was dictated?** The dictation ran roughly April to June 1829 (Harmony,
Pennsylvania, then Fayette, New York). The Smith family lived in Palmyra from early 1817 and
then on the farm on the Palmyra-Farmington (later Manchester) town line, Ontario County.

Evidence was taken only from public sources, in this order:

1. The Manchester (Farmington) library holdings as published by Robert Paul (1982), read in full
   from the free PDF.
2. The project's own *Wayne Sentinel* OCR (1,429 pages, 1823-1830), searched for every candidate
   title and author with the same squeeze-whitespace matching as the access index. **Positive hits
   only count. A miss is not evidence of absence** (see the 26 June 1829 correction above).
3. Imprints (place and publisher) of every candidate edition, from the title page of the local
   text (Harvard Institutional Books), the Internet Archive metadata API, or the TCP header.
4. Sourced secondary compilations, used only where they cite a dated primary document that could
   be opened (for *View of the Hebrews*, the B. H. Roberts Foundation timeline, formerly
   mormonr.org; the cited *Western Recorder* page was then read on the Internet Archive scan).

**Scores attach to the text, not the physical copy.** Fourteen of the twenty top search sources
are editions of Whiston's translation of Josephus. They are one text, and an advertisement for
"Josephus' Works" in Palmyra is evidence for all of them, though the edition advertised is not
named. An edition printed in 1829 or 1830 could not itself have been read before the dictation,
but the text could; each row gives its edition's imprint so the reader can see this.

### The scale

| Score | Meaning |
| --- | --- |
| **3** | Documented within Smith's reach before mid-1829: held by the Manchester library, sold or advertised in Palmyra or Canandaigua, published there, or documented as owned or read by him |
| **2** | Documented in the region before mid-1829: sold, advertised, reviewed or published in western or central New York (about 150 miles of Palmyra), but not in Palmyra, Manchester or Canandaigua |
| **1** | In print in the United States before 1829, with no regional evidence found |
| **0** | No evidence found that it circulated in the United States before mid-1829 (unpublished, foreign imprint only, or US printing not shown to predate the dictation) |

The ceiling stated at the top of this file applies to every score. A 3 says a book was on a
shelf or in an advertisement near the Smith farm. It does not say anyone in the household
read it, and **Paul's own reading of the library's records is that no one connected with the
later church was a member** (below).

### The Manchester (Farmington) library

Source: Robert Paul, "Joseph Smith and the Manchester (New York) Library," *BYU Studies* 22,
no. 3 (1982), beginning p. 333. Free:
https://scholarsarchive.byu.edu/byusq/vol22/iss3/6 (the PDF link there sits behind a browser
check); the same PDF at Book of Mormon Central,
https://archive.bookofmormoncentral.org/sites/default/files/Robert%20Paul%2C%20Joseph%20Smith%20and%20the%20Manchester%20%28New%20York%29%20Library%2C%201982_0.pdf.

What Paul establishes (paraphrased; page numbers are the article's):

- Organised loosely about 1815-1816, formally January 1817, as the "Farmington Library"; kept in
  librarian John Pratt's Manchester house; about five miles from the Smith farm. Shares were two
  dollars, dues twenty-five cents a year.
- **275 books had been accessioned by 1830, about 421 by 1845.** The appendix lists all 421 by
  accession number. 222 original volumes went to the **Ontario County Historical Society
  (OCHS)**, Canandaigua, in 1943-44.
- Paul dates the list only by assuming that accession numbers were assigned in order. No. 276 is
  the first book published after 1830 (his note 7). He gives three circulation anchors:
  Humboldt (no. 119) circulating from January 1827; Thomas Dick (nos. 244-245) from early 1830;
  Josiah Priest's *Wonders of Nature and Providence* (no. 208) "by late 1836".
- Three record books survive at OCHS: the "Secretary's Record Book, 1817-1854" and two
  "Withdrawal Record Book[s]", 1826-1837 and 1838-1857. Paul reports that **none lists any patron
  who joined the new church.** BYU's photocopies of the OCHS material lack the 1826-1837
  withdrawal book (his note 17).
- Palmyra had bookstores from December 1817, and Grandin opened a circulating library there in
  1828. Paul argues that this made the Manchester library the less likely route.

**Candidate holdings found in the appendix:**

| Accession | Entry (Paul) | Relevance |
| --- | --- | --- |
| **181-186** | *The works of Flavius Josephus.* Translated by Wm. Whiston. London, 1806 | **Fourteen of the top twenty search sources are this text.** Harvard item `HXJ9AU` is a London 1806 Whiston edition. Not among the volumes surviving at OCHS (no asterisk) |
| 208 | Priest, *The wonders of nature and Providence, displayed*. Albany: J. Priest, 1825 | Reprints the argument of *View of the Hebrews* (1823) ch. 3 (Paul note 9). Circulation documented only by late 1836 |
| 142 | Tuke, *Memoirs of the life of George Fox*. Philadelphia | Not the Fox *Journal* (top-20 rank 12) |
| 98-100 | Clarkson, *Portraiture of Quakerism*, 3 vols. | Quaker background; not a candidate |
| 321 | Priest, *American Antiquities*, 3rd ed. (1833) | Postdates 1830 |

No entry for *View of the Hebrews*, *The Late War*/*Historical Reader*, *The First Book of
Napoleon*, Spalding, Blake, Simpson, Bayly or Nayler. Paul notes that nearly half the entries are
one-word identifications ("Capt. Lyon's Journey", "Durand's Journal"), so absence from the list is
weaker evidence than presence.

**Dating the Josephus accession.** Numbers 181-186 sit between 119 (circulating January 1827) and
244 (early 1830). On Paul's sequence assumption, the set was added about 1827-1830. Whether that
was before or after mid-1829 is **not established**. The 1826-1837 withdrawal book at OCHS
would settle it (see "Worth buying or requesting").

### Palmyra booksellers and the *Wayne Sentinel*

Paul's notes 21-27 give the dated advertisements for each Palmyra bookstore. Timothy C. Strong's
bookstore advertised about 250 titles in the *Palmyra Register* of 15 September 1818. Wescott's
store opened in December 1820 and E. F. Marshall's in October 1822. Tucker and Grandin ran the
Wayne County Bookstore from 1824, renamed the Palmyra Bookstore in 1826. In Canandaigua,
J. D. Bemis ran the Canandaigua Bookstore and H. Tyler the Ontario Bookstore. Book auctions were
held from 1819. A Palmyra library was formed in the winter of 1822-23, and Grandin opened a
circulating library in 1828 (*Wayne Sentinel* 27 June 1828, 23 January 1829, 10 September 1829).
The Smiths took the *Palmyra Register* and then the *Sentinel* (Paul note 28, citing the
*Sentinel* of 11 October 1825 and 6 October 1826; the OCR of those pages does not show the name,
which by the rule above means nothing).

Searching the project's *Sentinel* OCR (`data/newspapers/wayne_sentinel/text/`, raw and cleaned
layers agree) for every candidate title gives:

| Term | Pages | What it is |
| --- | --- | --- |
| **Josephus** | **38** | Bookstore title lists. "Works of Flavius Josephus" 7 Jul-18 Aug 1824 (Wayne County Bookstore). "Josephus' works" 8-29 Dec 1826, beside *Young's Night Thoughts* and *Jemima Wilkinson*. **"Josephus' Works" in the Palmyra Bookstore list 23 Jan-1 May 1829**, beside Heeren's *Ancient History*, Willard's *Republic of America*, *Junius*. The 20 Mar 1829 p4 copy ends "For sale at the Palm[y]ra Book[store]". Again 11 Dec 1829-4 Jun 1830 beside Rollin's *Ancient History*. One more mention, "subscription paper, for the works of Josephus" (27 Dec 1825 p1), has unclear context |
| Historical Reader | 22 | School-book lists 27 Jul 1827-28 May 1830, never with an author. **Two different books carried this title**: Hunt's reissue of *The Late War* (New York 1817, 1819) and J. L. Blake's *Historical Reader* (Concord, N.H., 1824-1825 onward). Not assignable |
| Blake's | 21 | "Blake's Nat. Philosophy" in the 1829 Palmyra Bookstore list: J. L. Blake's science text, not his *Biblical Reader* |
| Hebrews / lost tribes | 6 pages | Mordecai Noah's "Ararat" proclamation (27 Sep 1825 p2) calls the Indians descendants of the lost tribes. Lowth's *Poetry of the Hebrews* is in a Tucker & Gilbert list (20 Apr 1825). Neither is *View of the Hebrews* |
| View of the Hebrews, Ethan Smith, Late War (as a title), Gilbert Hunt, First Book of Napoleon, Spalding (as author), Fox's Journal, Nayler, Bayly, Biblical Reader, Sacred Literature | 0 | No hit. Not a negative. "Spalding" returns 27 pages, all the Palmyra merchants Marshall & Spalding |

**Checked on the page images, 2026-11-06.** The column interleaving that garbled the 26 June
1829 page could in principle have spliced a title from one advertisement into another. So the
three key items were read by eye on the Pioneer Library System scans (see "Follow-up" below):

| Date, page | What the image shows |
| --- | --- |
| 18 Aug 1824, p3 | A notice headed "Works of Flavius Josephus.": "A FEW Numbers for sale at the Wayne County Book-store." "Numbers" means a part-issue sold in instalments |
| 8 Dec 1826, p3 | "NEW BOOKS, AT THE Palmyra Book Store", with an alphabetical catalogue: "... Junius' letters / Josephus' works / Jemima Wilkinson ...". The "Woodstock" the OCR placed beside it is Scott's novel, further down the same list; the OCR's other "Woodstock" is a kind of glove in the dry-goods column |
| 20 Mar 1829, p4 | "NEW BOOKS. The subscriber has just received from New York, at his Bookstore, Printing-Office, and Bindery, (west end of Thayer & Grandin's Row,) an entire New Stock of Books & Stationary": "... Heeren's Ancient History / Josephus' Works / Junius ...", signed **"E. B. GRANDIN. Palmyra, Nov. 27, 1828."** |

All three are confirmed. The 1829 one is Grandin's own stock list: it was first set on 27
November 1828 and was still running on 20 March 1829, while the dictation was under way in
Harmony. The other dates in the table above (July 1824, December 1829-June 1830) are the same
standing lists, found in OCR and not each re-read.

### The access table

`data/access/access_table.csv`: 33 rows, one per text, with columns
`source_id, title, author, year, kind, score, evidence, citation_url`.

- `named`: the five proposed sources (*View of the Hebrews* 1823 and 1825, *The Late War*,
  *The First Book of Napoleon*, Spalding's manuscript).
- `search_top`: the 20 entries of `top_search_sources` in `data/semantic/corpus_bom.json`, in
  rank order, by `work_id`.
- `candidate_author`: the other pre-1830 printed works of the candidate authors in
  `docs/candidates.md` (five more Ethan Smith works, the 1819 *Late War*, and Phelps's two
  papers). Excluded, with reasons: everything first written or printed after 1830, which cannot
  bear on access before the dictation. Also excluded are the manuscripts of Joseph Smith and
  Oliver Cowdery, who were present at the dictation, so the access question does not apply to
  them in this form. Rigdon's pieces in Campbell's *Christian Baptist* (1823-1830) have not
  been identified item by item and are listed under gaps.

| Score | Rows | Which |
| --- | --- | --- |
| 3 | 15 | All 14 Josephus editions (one text) and the *Ontario Phoenix* (Phelps's paper, printed at Canandaigua from 1828; not digitized) |
| 2 | 3 | *View of the Hebrews* 1st ed. (1823), reviewed in the *Utica Christian Repository*, May 1825 (from Grunder, checked on the scan); 2nd ed. (1825), sold at Utica Feb 1826; the *Lake Light* (Trumansburg, 1827-28) |
| 1 | 9 | *The Late War* (1816, 1819), Blake's *Biblical Reader*, Fox's *Journal*, five other Ethan Smith works |
| 0 | 6 | *First Book of Napoleon* (London 1809 only), Spalding's manuscript (unpublished), Simpson's *Sacred Literature* (Birmingham 1788 only), Bayly (US reprint 1830), Nayler (Cincinnati 1829, month unknown; two copies) |

Collapsed to distinct texts, the twenty search sources are six texts (unchanged by Grunder): Josephus (3), Blake (1),
Fox (1), Simpson (0), Bayly (0), Nayler (0).

**Main finding, stated with its limit.** The top-ranked source of the whole-corpus search,
Whiston's Josephus, is also the one candidate with the strongest documented local
availability. It was advertised in Palmyra's paper by a Rochester bookseller in 1822 (the
earliest offer found), for sale in Palmyra's own bookstores in 1824 and 1826, and was in **E. B.
Grandin's own advertised stock from 27 November 1828 through at least spring 1829** (all three
confirmed on the page images). It was held by the Manchester library by about 1830. It was not
in T. C. Strong's Palmyra lists of 1818 and 1819. No proposed source in the named literature reaches
3. *View of the Hebrews* reaches 2 for both editions, on central New York evidence: a Utica review of
the 1823 edition (May 1825) and a Utica bookseller's list for the 1825 edition (February 1826).
This settles nothing about borrowing. Josephus was one of the most widely owned books in
America, so local availability is what one would expect of it on general grounds. The score
removes an objection (that the text could not have been to hand). It does not add evidence
that it was used.

### Gaps: what could not be established

- **Date of the Manchester Josephus accession** relative to mid-1829. Needs the OCHS withdrawal
  book, 1826-1837.
- ~~The Josephus items read only in OCR~~: **done**, confirmed on the images (above). Still
  unread on the image: Paul's subscription pages, 11 Oct 1825 and 6 Oct 1826.
- **Which "Historical Reader"** Palmyra sold, 1827-1830: Hunt's or Blake's. **The page images
  do not settle it.** Every entry checked (26 Oct 1827 p4, Palmyra Bookstore; 20 Mar 1829 p4
  and 11 Dec 1829 p3, Grandin) is a bare "Historical Reader" among school books, with no
  author, price or subtitle. It would need a Grandin or Tucker invoice, a school list naming
  the book, or a surviving Palmyra copy.
- ~~*Palmyra Register* and *Palmyra Herald* not searched~~: **done**, see "Follow-up" below.
- **The *Ontario Repository* (Canandaigua, 1809-1829)**, with the Bemis and Tyler bookstore
  ads, is still not searched. It is digitized only on NYSHN, which needs the owner's unlocked
  browser (`scripts/nyshn_browser_pull.py`). It is not on Chronicling America (no digitized
  pages under any Canandaigua LCCN) and was not found on an Advantage archive.
- **Grandin's 1828 circulating library**: no catalogue of it has been found.
- **Harmony, Pennsylvania, and Fayette, New York**, where the dictation took place, were not
  examined. Book of Mormon Central has a short note on whether Harmony had a library
  (https://archive.dev-bookofmormoncentral.org/sites/default/files/pressing_forward_65_-_was_there_a_library_in_harmony_pennsylvania.pdf),
  not read for this pass.
- ***The First Book of Napoleon***: no US printing was found in the Internet Archive or the web
  sources searched. A union-catalog check (WorldCat, *American Imprints* 1801-1819) was not
  possible without an account, so "no US edition" is unconfirmed.
- **Simpson's *Sacred Literature***: same limit. Only the Birmingham 1788 edition was found.
- **Nayler 1829 (Cincinnati)**: the month of printing was not found. If it was before April 1829
  the score would be 1.
- **Rigdon in the *Christian Baptist***: not identified item by item.
- **Quaker Farmington.** The Smith farm lay in Farmington township until 1821 (Paul, first page).
  Whether a Friends' meeting library there held Fox's *Journal* was not investigated. It is a
  lead, not a finding.

### Worth buying or requesting

- ~~Rick Grunder, *Mormon Parallels*~~: **bought by the owner 2026-11-06 (2014 PDF) and used**;
  see "Grunder" below. The description first given here overstated it. It is a bibliography of
  500 proposed parallels with occasional notes on local availability, not an item-by-item
  availability register. For the 33 texts in the table it added one regional fact.
- **Milton V. Backman Jr., *Joseph Smith's First Vision*, 2nd ed. (Bookcraft, 1980)**, pp. 48-49
  describes Strong's September 1818 stock. **No longer needed**: the 1818 page itself has been
  read on the scan (see "Follow-up").
- **Ontario County Historical Society, Manchester Library Collection File**: "Numbers of the
  Volumes in the Manchester Library", "Books from the old Manchester Library" and the
  "Manchester Rental Library Withdrawal Record Book, 1826-1837". This is not a purchase but a
  copy request to OCHS, 55 N. Main St., Canandaigua, NY (https://ochs.org/). Ask for scans of
  the withdrawal-book pages recording accessions 181-186 and their first loans. **This is the
  one document that would date the Josephus holding.** BYU L. Tom Perry Special Collections holds
  photocopies of the other two lists (Manchester Library Collection; M. Wilford Poulson
  Collection), but not the 1826-1837 book.

### Follow-up (2026-11-06): page images and the Palmyra papers

**Route.** The plan was to read the scans on NYS Historic Newspapers through
`scripts/nyshn_browser_pull.py`. That needs the owner's browser unlocked past Cloudflare, and none
was running. The same papers are public on the **Pioneer Library System's Advantage archive**
(https://pioneerlibrarysystem.advantage-preservation.com/), which has no Cloudflare: the *Wayne
Sentinel* 1823-1859, the *Palmyra Register* 1817-1821 (648 pages) and the *Palmyra Herald*
1822-1823 (157 pages). These are the same microfilm page images, so this answers the same
question without the browser step. Pages were fetched with the helpers in
`ingest/advantage_archive.py`. Each target was located with the PDF's own text layer and then
**read by eye on the rendered image**.

**1. Josephus in the *Wayne Sentinel*: confirmed.** See the table under "Palmyra booksellers"
above (18 Aug 1824, 8 Dec 1826, and Grandin's list of 27 Nov 1828, read on 20 Mar 1829).

**2. "Historical Reader": not settled by the images.** Read on 26 Oct 1827 p4 ("NEW BOOKS, JUST
RECEIVED AND FOR SALE AT THE PALMYRA BOOKSTORE": "Ryan's Algebra and Key; Historical Reader;
Large Methodist Hymns"), 20 Mar 1829 p4 (Grandin, "School and Classical Books") and 11 Dec 1829
p3 (Grandin: "Historical Reader, Tytler's History"). None gives an author, price or subtitle.
*The Late War* stays at 1.

**3. *Palmyra Register*, 1817-1821: pulled in full (648 pages, 162 issues) and searched.**
- **T. C. Strong's list, 15 Sep 1818 p3** ("T. C. STRONG, Book-Seller & Printer, Has for sale
  a general assortment of Books, among which are the following Standard and Miscellaneous
  Works", dated "Palmyra, Sept. 16, 1818"). Read by eye in full, A to Y, plus the closing
  school-book note. **None of the 33 candidate texts is in it**: no Josephus, no Hunt (whose
  *Historical Reader* had been in print since 1817), no Fox *Journal*, no Simpson. (*View of
  the Hebrews* did not yet exist.) The "Fox's history of James the II." in the list is Charles
  James Fox, and "Cobbet's letters on the late war" is Cobbett, not Hunt.
- **Strong & Bradish, dated 13 Oct 1819 (27 Oct 1819 p4)**: the same list reset, also read in
  full. Same result; its school books (English Readers, Murray, Daboll, American Readers,
  Preceptors and Speakers, Willett's geography) include no *Historical Reader*.
- **Leonard Wescott's "New-Store", 27 Dec 1820 p4**: merchandise, hardware, drugs and glass. No
  book titles on this notice.
- OCR search of all 648 pages for every candidate title and author: **no genuine hit**. Each
  apparent hit was read on the image and is something else. "Josephus" on 5, 12 and 19 July 1820
  is "Josephus Warren", a name in the post-office list of uncollected letters. "Eliakim"
  (3 Jan 1821) is "Eliakim Thatcher" in a letter list. "History of the late war" (9 Aug 1820
  p3) is a satirical piece, "Connecticut Authors", about a history "published at Hartford in
  1815" and sold by pedlars; Hunt's is New York 1816, so this is a different book.

**4. *Palmyra Herald*, 1822-1823: pulled in full (157 pages, 39 issues) and searched.**
- **New: "Josephus' Work, 6 vols. D3."** (three dollars), confirmed on the image of 7 Aug 1822
  p4. It is in a book list signed **"E. Peck & Co. ... Rochester, July 25, 1822"** and runs in
  the OCR from 31 Jul to 11 Sep 1822 (six issues). Its neighbours include Enfield's *Natural
  Theology*, Bellamy's *History of all Religions*, Weems's *Washington* and "The whole of the
  Waverly Novels". A Rochester bookseller was advertising Josephus to Palmyra readers in
  Palmyra's own paper two years before the earliest *Sentinel* offer. **This is the earliest
  Josephus availability found.**
- No other candidate title or author appears. The one "Spalding" (12 Mar 1823) reads in the OCR
  as a personal name, "Frederick Spalding", in a news column; it was not checked on the image.

**Scores.** No score changes. The Josephus rows (3) now cite images rather than OCR, and their
earliest date moves back to July 1822. *The Late War* stays at 1: the Palmyra papers of
1817-1823 add nothing for it, and the 1827-1830 "Historical Reader" remains unassigned.
Everything else is unchanged, and the absences from the Register and Herald OCR are, as
always, not negatives. The two book lists read in full by eye (1818, 1819) are the exception:
for those two lists the absence is a real result.

**Data written.**
- `data/newspapers/palmyra_register/` and `data/newspapers/palmyra_herald/`: text layers,
  `pages.jsonl`, `SOURCES.md`.
- Page PDFs (257 MB, including the six *Sentinel* verification pages) in
  `data/corpus/advantage/pioneerlibrarysystem/`, outside git.
- Manifests: `data/manifests/palmyra_register_text.jsonl`,
  `data/manifests/palmyra_herald_text.jsonl`, `data/manifests/pioneerlibrarysystem_pdf.jsonl`.

**Still open.**
- The *Ontario Repository* (NYSHN only; needs the owner's unlocked browser).
- The *Western Farmer* (Palmyra, 1821-1822), which is listed for Fulton History, not on this
  archive.
- The *Palmyra Reflector* (1829-1830).
- The date of the Manchester Josephus accession (OCHS withdrawal book).

### Grunder, *Mormon Parallels* (2014 PDF), checked against the table (2026-11-06)

**Source and handling.** The owner bought Rick Grunder, *Mormon Parallels: A Bibliographic
Source* (2014 PDF, 2,307 pp.). It is held privately: `data/private/access/`, checksum in
`data/manifests/access-private.jsonl`. Its text was extracted to `data/corpus/grunder/` for
local searching only; that folder is outside git and is never published. Citations here use
Grunder's own form, *MP n* for entry n and *MP p. n* for a page; book pages equal PDF pages in
this edition. Nothing is quoted beyond a short phrase.

**Method.** The table's 33 texts and the five named sources were each looked up in his
"Bibliographic Table of Contents" (MP pp. 2091-2148, 500 entries). Each matching entry was then
searched for Palmyra, Manchester, Canandaigua, Harmony, Fayette, Grandin, the local papers,
bookstores, libraries and advertising. The whole book was also searched for every candidate
title within about 400 characters of a local place name. Where his primary citation is a paper
we hold, it was checked on our page image. Otherwise it was checked on a public scan where one
exists.

**What he covers, and what he adds.**

| Our text | Grunder | What he documents about local availability | Checked |
| --- | --- | --- | --- |
| *View of the Hebrews*, 1823 | MP 398 (pp. 1619-20) | **A long, favourable review in *The Utica Christian Repository* 4:5 (May 1825), pp. 143-49**, from William Williams's Utica press. He notes Utica was a canal trip from Palmyra | **Yes**, on the Internet Archive scan (https://archive.org/details/sim_utica-christian-repository_1825-05_4_5): the heading gives "12mo. pp. 183", i.e. the 1823 edition. **Rescored 1 to 2** |
| *View of the Hebrews*, 1825 | MP 399 (pp. 1621-29) | Edition history only; no New York sale. Our Utica notice of Feb 1826 is not in Grunder | n/a |
| Josephus (14 rows) | MP 203 (pp. 796-97), the Borradaile New York 1823-24 edition, which is our `institutional_books:HW3CRW` | The Manchester library set (from Paul, accessions 181-86). He judges it unlikely the Smiths used that set. Nothing on Palmyra sale | Same as ours. Our 1822-1829 newspaper offers go beyond him |
| *The Late War* (1816, 1819) | MP 193 (pp. 724-71) | Publishing history: 1816; 1817 as *The Historical Reader*; fourteen 1819 issues, eight of them titled *The Historical Reader*; none after 1819. Treated as a **stylistic** parallel. No copy, sale or ad near Palmyra | **Does not settle Hunt vs Blake.** "Historical Reader" occurs twice in the whole book, both on p. 724, and never with Palmyra |
| Spalding manuscript | MP 410 (pp. 1694-95) | Unpublished until 1885; the theory first printed by Hurlbut and Howe, 1834 | Agrees with our 0 |
| Ethan Smith, *Dissertation* (1811) | MP 395 (p. 1610) | Widely used; advertised by booksellers as "Smith on the Prophecies". No New York venue named | That short title returns no hit in our four local papers' OCR (not a negative) |
| Ethan Smith, *Treatise* | MP 397 (p. 1613) | Second edition advertised on the back board of *View of the Hebrews* (1823). No New York venue | n/a |
| Ethan Smith, *Death of God's Chosen* | MP 394 | None | n/a |
| Ethan Smith, *Episcopacy Examined*; Newburyport sermon | His short-list of Smith's works, MP pp. 1627-28, marked not analysed | None | n/a |
| Priest, *Wonders of Nature and Providence* (reprints *View of the Hebrews* ch. 3) | MP 341 (p. 1323) | The Manchester holding (Paul no. 208); he warns against reading it as evidence of use | Same as ours |
| *Ontario Phoenix*, *Lake Light* | MP p. 688 (in another entry) | Phelps & Bloomer's *Phoenix* at Canandaigua from 30 Apr 1828; Bloomer out 16 Dec 1829 | Consistent with our 3 and 2 |
| *First Book of Napoleon*, Fox *Journal*, Blake *Biblical Reader*, Simpson *Sacred Literature*, Nayler, Bayly | Not among his 500 entries (his only Simpson, MP 386, is another work) | n/a | n/a |

**His primary citations to papers we hold.** For our 33 texts, none of his citations is to the
*Wayne Sentinel*, *Palmyra Register*, *Palmyra Herald*, *Lake Light* or *Ontario Phoenix*. His
two *Herald* entries (MP 300, 30 Oct 1822; MP 301, 24 Sep 1823) describe local bookstore ads
that name no candidate text. MP 300 was checked on our image: the Canandaigua Book-Store of
J. D. Bemis & Co., 30 Oct 1822 p2, lists classes of books only. MP 301 falls after the end of
our *Herald* run (12 Mar 1823).

**Where we differ.**
- **Josephus.** Grunder treats Josephus mainly as a source of themes and notes the Manchester
  set. Our newspaper evidence shows Josephus *offered for sale to Palmyra readers* in 1822,
  1824, 1826 and 1828-29, including in Grandin's own stock. His remark that the Smiths
  probably did not see the library set is a judgement about use. The table makes no such
  judgement either way.
- **The Late War.** Grunder's treatment rests on style, not access. For access, we have only
  the unassigned Palmyra "Historical Reader" ads, so the score stays 1.

**Net change to the table:** one rescore, *View of the Hebrews* 1823 from 1 to 2. Counts are now
3: 15, 2: 3, 1: 9, 0: 6. Every row's `evidence` now says what Grunder adds, or that he does not
treat the text.

**The facts-only list of his sources: `data/access/grunder_sources.csv`.** One row per entry (500).
- Columns: entry number and citation, start page, author, a short title (at most about 15
  words), the year of the edition he describes, `imprint_region`, and the catalog match fields.
- `imprint_region` is a place among Palmyra, Canandaigua, Manchester, Geneva, Lyons and
  Rochester found in the imprint. It is approximate (39 entries).
- Catalog matching:
  - `in_catalog = yes` means an author surname plus title-word match in
    `data/catalog/catalog.parquet` (139 entries: 105 at the same year, 34 at another).
  - `possible` means a title-only phrase match, mostly periodicals and almanacs (32).
  - `no` means not found (329).
  - The catalog stops at 1830, and 170 entries are dated after 1830 or carry no year (330 are
    1830 or earlier, 124 of them firm catalog matches), so `no` often reflects that cutoff, or
    an item that was never a book, such as a manuscript letter.
- `in_access_table` links the 8 entries that correspond to rows of the access table.
- Titles and years are bibliographic facts. No commentary or quotation from Grunder is in the
  file. The parse and match code was run from a scratch script and is described in
  `data/access/SOURCES.md`; it is not yet in a pipeline package.
