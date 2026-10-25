# Candidate author corpora: source inventory (BOM-13)

This is the sourcing half of BOM-13: where a writing sample for each candidate in
preregistration section 3 can be found, who physically produced it, whether it predates the
1830 Book of Mormon, whether we may redistribute it, and how big it is. The machine-readable
version is `data/candidates/sources.json`; `ingest/candidates.py` fetches from it. Word counts
are estimates and are replaced by measured counts once texts are fetched and cleaned.

Inventory as of 2026-10-15. Every URL below was checked to resolve on that date (Joseph Smith
Papers pages through `ingest.jsp.page_props`, Internet Archive items through the metadata API).

## Conventions

- **Provenance:** *handwritten* (in the candidate's own hand), *dictated* (spoken by the
  candidate, written by a scribe), *scribal copy* (a later copy by someone else of a lost
  original), *mixed* (several hands; split using the JSP handwriting notes), *printed* (published
  under the candidate's name in their lifetime), *edited* (a periodical or work others shaped),
  *posthumous*.
- **Pre-1830** means written before the Book of Mormon went on sale (March 1830). Post-1830
  texts are still useful for a candidate's stable habits, but they were written after exposure
  to the Book of Mormon, and that exposure can pull style toward it. Results built on post-1830
  text carry that caveat.
- **Licence:** Joseph Smith Papers (JSP) transcripts are copyright Intellectual Reserve, Inc.
  and go only to `data/private/`. Pre-1927 printed books on the Internet Archive (IA) are public
  domain. Two IA scans from the Church History Library carry an Intellectual Reserve rights
  statement on the item; the text is public domain, but they are kept private to be safe.
- **Word estimates:** IA items use the OCR file size divided by 6. The two files fetched so far
  ran about 6.6 bytes per word, so these estimates are about 10% high and include front matter,
  headers and OCR noise. JSP figures are estimates from page counts and printed volumes, not
  measured.
- **How to fetch:** `uv run python -m ingest.candidates --id <id>`. For JSP items the fetcher
  walks every page of `https://www.josephsmithpapers.org/paper-summary/<slug>/<n>`; for IA it
  downloads `https://archive.org/download/<identifier>/<identifier>_djvu.txt`.

## Summary

| Candidate | Sources | Pre-1830 words (est.) | All words (est.) | Under 10,000 pre-1830? |
| --- | --- | --- | --- | --- |
| Joseph Smith | 12 JSP | about 11,500 dictated; 0 handwritten | about 20,000 own-text after removing others' hands | **yes for handwritten; borderline for dictated** |
| Oliver Cowdery | 3 JSP + 2 IA + 1 JSP witness | about 2,500 (much is Book of Mormon quotation) | about 25,000 plus signed periodical items | **yes** |
| Sidney Rigdon | 2 IA + Wikisource | 0 found | about 55,000 | **yes (none)** |
| Parley P. Pratt | 3 IA | 0 (first writing 1835) | about 98,000 | **yes (none)** |
| W. W. Phelps | 1 IA + Wikisource | 0 digitized | about 15,000 signed plus unsigned editorials | **yes (none)** |
| Solomon Spalding | 2 IA transcriptions + holograph | about 40,000 (one text) | about 40,000 | no |
| Ethan Smith | 7 IA | about 400,000 | about 400,000 | no |
| Gilbert J. Hunt | 2 IA | about 60,000 (one text) | about 60,000 | no |

Four of the eight candidates have no pre-1830 sample at all in any digitized source found, and
Joseph Smith has no pre-1830 sample in his own hand. Under section 3 of the preregistration
their pre-1830 results carry the "unreliable sample" flag. The usable comparison for them is
post-1830 text, with the exposure caveat above.

## Joseph Smith

Section 3 requires dictated and handwritten texts to be scored as separate samples. The
handwritten sample is small: everything in his own hand that survives from 1831-1834 is about
6,000-8,000 words, and nothing in his hand survives from before 1830.

| id | Text | Format / URL | Written; published | Provenance | Pre-1830 | Licence | Words (est.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| js-1828-1829-revelations | Revelation Book 1, revelations of July 1828 to 1829 (D&C 3-19) | JSP, 201 pp. [revelation-book-1](https://www.josephsmithpapers.org/paper-summary/revelation-book-1) | 1828-1829; copied 1831-1835; JSP facsimile 2009 | dictated; copies by John Whitmer and others | yes | JSP, private | about 11,000 pre-1830 (whole book much more) |
| js-1829-10-22-letter-cowdery | Letter to Oliver Cowdery | JSP, 1 p. [link](https://www.josephsmithpapers.org/paper-summary/letter-to-oliver-cowdery-22-october-1829) | 22 Oct 1829; JSP D1 2013 | scribal copy (F. G. Williams, 1832) | yes | JSP, private | 450 |
| js-1831-03-letter-hyrum | Letter to Hyrum Smith | JSP, 4 pp. [link](https://www.josephsmithpapers.org/paper-summary/letter-to-hyrum-smith-3-4-march-1831) | 3-4 Mar 1831; JSP D1 | handwritten | no | JSP, private | 1,100 |
| js-1832-history | History, circa Summer 1832 | JSP, 6 pp. [link](https://www.josephsmithpapers.org/paper-summary/history-circa-summer-1832) | 1832; first printed 1965 | mixed (JS and F. G. Williams) | no | JSP, private | 2,100 |
| js-1832-06-06-letter-emma | Letter to Emma Smith | JSP, 4 pp. [link](https://www.josephsmithpapers.org/paper-summary/letter-to-emma-smith-6-june-1832) | 6 Jun 1832; JSP D2 | handwritten | no | JSP, private | 800 |
| js-1832-10-13-letter-emma | Letter to Emma Smith | JSP, 4 pp. [link](https://www.josephsmithpapers.org/paper-summary/letter-to-emma-smith-13-october-1832) | 13 Oct 1832; JSP D2 | handwritten | no | JSP, private | 700 |
| js-1832-07-31-letter-phelps | Letter to W. W. Phelps | JSP, 8 pp. [link](https://www.josephsmithpapers.org/paper-summary/letter-to-william-w-phelps-31-july-1832) | 31 Jul 1832; JSP D2 | dictated (F. G. Williams) | no | JSP, private | 2,500 |
| js-1832-11-27-letter-phelps | Letter to W. W. Phelps | JSP, 4 pp. [link](https://www.josephsmithpapers.org/paper-summary/letter-to-william-w-phelps-27-november-1832) | 27 Nov 1832; JSP D2 | mixed (JS and F. G. Williams) | no | JSP, private | 1,300 |
| js-1833-01-04-letter-saxton | Letter to Noah C. Saxton | JSP, 5 pp. [link](https://www.josephsmithpapers.org/paper-summary/letter-to-noah-c-saxton-4-january-1833) | 4 Jan 1833; JSP D2 | dictated (F. G. Williams) | no | JSP, private | 1,300 |
| js-1833-01-11-letter-phelps | Letter to W. W. Phelps | JSP, 3 pp. [link](https://www.josephsmithpapers.org/paper-summary/letter-to-william-w-phelps-11-january-1833) | 11 Jan 1833; JSP D2 | dictated (F. G. Williams) | no | JSP, private | 1,200 |
| js-journal-1832-1834 | Journal, 1832-1834 | JSP, 106 pp. [link](https://www.josephsmithpapers.org/paper-summary/journal-1832-1834) | 1832-1834; JSP J1 2008 | mixed (JS, Cowdery, Williams, Pratt, Rigdon and others) | no | JSP, private | about 9,000 total; perhaps 2,000-3,000 in JS's hand |
| js-letterbook-1 | Letterbook 1 | JSP, 108 pp. [link](https://www.josephsmithpapers.org/paper-summary/letterbook-1) | 1829-1835 letters copied 1832-1835 | mixed; outgoing JS letters only | no | JSP, private | about 30,000 total; JS outgoing a fraction |

How to fetch: `uv run python -m ingest.candidates --id <id>` (writes
`data/private/candidates/<id>.jsonl`; needs `data/private/`).

**How these were obtained (recorded 2026-10-25).** By October 2026 josephsmithpapers.org
answered 404 to the project's self-identifying User-Agent and served pages normally to a
browser. The site publishes no rate-limit policy and no robots.txt; its footer's Terms of Use
link is the Church's general terms
(<https://www.churchofjesuschrist.org/legal/terms-of-use>, updated 2021-04-13), which say not to
"use any robot, spider, or other automatic device, process, or means to access this site for any
purpose" and permit downloading "for your own personal, noncommercial use". Having read those
terms, the owner chose to fetch with a browser User-Agent at one request every 20
seconds. The transcripts stay in the private repository and are never redistributed. The
BOM-05 manuscript transcripts were fetched by script from the same site, under the same terms,
before the filter appeared. A written request for research permission to the Church History
Department would put both on a firmer footing; that is the owner's to send.

**Do not use:**

- *Preface to the Book of Mormon* (1829, JSP `preface-to-book-of-mormon-circa-august-1829`) and
  the witness statements: part of the 1830 book under test, so they are sealed with it.
- *Lectures on Faith* (1835): authorship disputed; some stylometric studies attribute much of it to
  Sidney Rigdon.
- Revelations as printed in the *Book of Commandments* (1833) and *Doctrine and Covenants*
  (1835): edited by committee (JS, Cowdery, Rigdon, Williams); use the manuscript copies.
- *History, 1838-1856* ("Manuscript History"): compiled and written largely by clerks and
  later editors, mostly after 1838.
- Joseph Smith Translation of the Bible: revisions of KJV text, not free composition.
- Wentworth letter (1842) and *Times and Seasons* editorials: commonly ghost-written or
  co-written by editors such as John Taylor and W. W. Phelps.
- Lucy Mack Smith's history (1845, printed 1853): her text, with Joseph quoted from memory.
- Dean Jessee, *Personal Writings of Joseph Smith*: a modern copyrighted edition; use JSP.

## Oliver Cowdery

| id | Text | Format / URL | Written; published | Provenance | Pre-1830 | Licence | Words (est.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| oc-1829-06-articles | "Articles of the Church of Christ" | JSP, 4 pp. [link](https://www.josephsmithpapers.org/paper-summary/appendix-3-articles-of-the-church-of-christ-june-1829) | Jun 1829; JSP D1 appendix | handwritten | yes | JSP, private | 1,500, much of it Book of Mormon quotation |
| oc-1829-11-06-letter | Letter to JS | JSP, 3 pp. [link](https://www.josephsmithpapers.org/paper-summary/letter-from-oliver-cowdery-6-november-1829) | 6 Nov 1829; JSP D1 | scribal copy (JS, 1832) | yes | JSP, private | 650 |
| oc-1829-12-28-letter | Letter to JS | JSP, 2 pp. [link](https://www.josephsmithpapers.org/paper-summary/letter-from-oliver-cowdery-28-december-1829) | 28 Dec 1829; JSP D1 | scribal copy (JS, 1832) | yes | JSP, private | 350 |
| oc-1834-letters-to-phelps | Letters I-VIII to W. W. Phelps (RLDS reprint) | IA OCR [lettersofoliverc00cowd](https://archive.org/details/lettersofoliverc00cowd) | 1834-1835; reprint [18--] | printed | no | public domain | 24,000 |
| oc-1834-history-jsp | History, 1834-1836 (copies of the same letters) | JSP, 191 pp. [link](https://www.josephsmithpapers.org/paper-summary/history-1834-1836) | 1834-1836; JSP H1 2012 | scribal copy | no | JSP, private | witness only |
| oc-messenger-advocate | *Messenger and Advocate*, signed Cowdery items | IA OCR [LDSMessengerAndAdvocate18341837](https://archive.org/details/LDSMessengerAndAdvocate18341837) | 1834-1837 | edited | no | public domain | whole run about 450,000; Cowdery share unmeasured |

Also verified: the 1844 Liverpool reprint of the letters, IA
[lettersbyoliverc00oliv](https://archive.org/details/lettersbyoliverc00oliv) (Intellectual
Reserve rights claim; not needed), and the letters VI and VIII on
[Wikisource](https://en.wikisource.org/wiki/Author:Oliver_Cowdery).

How to fetch: `--id oc-1834-letters-to-phelps` (public); JSP items as above. The periodical
needs a later step that keeps only items signed by Cowdery.

**Do not use:**

- *Defence in a Rehearsal of My Grounds for Separating Myself from the Latter Day Saints*
  (dated 1839, first surfaced 1906; IA `cowdery1839`): widely judged a forgery.
- Unsigned *Messenger and Advocate* editorials: the editor changed (Cowdery, John Whitmer,
  Warren Cowdery), so unsigned pieces cannot be assigned.
- The Book of Mormon manuscripts in his hand: he was the scribe, not the composer of record,
  and the text is sealed.
- The quoted Book of Mormon passages inside the 1829 Articles: mask them, or the sample
  measures the Book of Mormon instead of Cowdery.

## Sidney Rigdon

No pre-1830 writing by Rigdon was found in any digitized source. He preached for the Baptists
and then the Campbell reform movement in the 1820s, but no sermon, letter or tract of his from
those years turned up. The Mahoning Association minutes and Alexander Campbell's periodicals
(*Christian Baptist*, 1823-1830; *Millennial Harbinger*, 1830-) are the places still to search.

| id | Text | Format / URL | Written; published | Provenance | Pre-1830 | Licence | Words (est.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sr-1838-oration | Fourth of July oration, Far West | IA OCR [orationdelivered01rigd](https://archive.org/details/orationdelivered01rigd) | 4 Jul 1838; 1838 | printed | no | public domain | 5,600 (measured OCR tokens) |
| sr-1840-appeal | *An Appeal to the American People* | IA OCR [appealtoamerican00rigd](https://archive.org/details/appealtoamerican00rigd) | 1839-1840; 1840 | edited (issued in his name for the church) | no | text PD; IRI claim on scan, private | 37,000 |
| sr-messenger-advocate-essays | Letters and essays, *Messenger and Advocate* | [Wikisource author page](https://en.wikisource.org/wiki/Author:Sidney_Rigdon) | 1836-1837 | printed | no | public domain | about 12,000 (rough guess) |

How to fetch: `--id sr-1838-oration` (fetched); `--id sr-1840-appeal` (goes to
`data/private/`); the Wikisource items are not yet fetched by the script.

**Do not use:**

- *Lectures on Faith*: authorship disputed between Rigdon, Smith and others; using it would
  build the answer into the sample.
- *A Collection of Sacred Hymns* (1845, IA `collectionofsacr00rigd`): compiled, not written.
- Autobiographical sketch in *Times and Seasons* (1843): third-person, likely written or
  edited by others.
- Spalding-Rigdon theory affidavits (Howe, *Mormonism Unvailed*, 1834): statements by others
  about him.

## Parley P. Pratt

Pratt joined in late 1830 and published nothing before 1835; there is no pre-1830 sample.

| id | Text | Format / URL | Written; published | Provenance | Pre-1830 | Licence | Words (est.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppp-1837-voice-of-warning | *A Voice of Warning*, 1st ed. | IA OCR [per_utah-and-the-mormons_pp-pratt_1837](https://archive.org/details/per_utah-and-the-mormons_pp-pratt_1837) | 1837 | printed | no | public domain | 50,000 |
| ppp-1838-mormonism-unveiled | *Mormonism Unveiled: Zion's Watchman Unmasked* | IA OCR [mormonismunveile00prat](https://archive.org/details/mormonismunveile00prat) | 1838 | printed | no | public domain | 18,000 |
| ppp-1840-late-persecution | *History of the Late Persecution* | IA OCR [historyoflateper00prat](https://archive.org/details/historyoflateper00prat) | 1839; this printing 1840 | printed (with documents by others) | no | text PD; IRI claim on scan, private | 30,000 |

How to fetch: `--id <id>`. Many later pamphlets (1840-1856) are also on IA under creator
"Pratt, Parley Parker" if more text is needed.

**Do not use:**

- *Autobiography of Parley P. Pratt* (1874, IA `autobiographyofp1874prat`): posthumous,
  assembled and edited by his son Parley P. Pratt Jr.
- *The Millennium* (1835, verse, IA `millenniumpoemto00prat`): poetry, not comparable prose.
- Later editions of *A Voice of Warning* (1839 onward): revised; use the 1837 first edition.
- *Journal of Discourses* sermons (1853-1857): stenographic reports edited for print.
- *Key to the Science of Theology* (1855): his, but 25 years later; use only if a late
  sample is wanted.

## W. W. Phelps

Phelps edited anti-Masonic newspapers before 1830, the *Lake Light* (Trumansburg, 1827-1828)
and the *Ontario Phoenix* (Canandaigua, 1828-1832). This is the biggest open gap in the
inventory: pre-1830 prose from a candidate who lived eleven miles from the Smiths, written
while the Book of Mormon was being dictated.

**Updated 2026-10-20 (BOM-41).** Both papers were checked everywhere a script or a browser
could reach:

- *Lake Light*, LCCN `sn84031024`, Trumansburg 1827-1829, publishers Phelps & Bloomer to
  18 Feb 1828, then Clark & Bloomer (see the attribution rule above). **Digitized and pulled**: the Ulysses Philomathic Library's Advantage Archives
  site holds the New York State Library microfilm run, 168 pages in 42 issues, 10 Oct 1827 to 19 Nov 1828 (about 16 issues are missing from the film)
  (`data/newspapers/lake_light/`, fetched by `ingest.advantage_archive`). This is the first
  digitized pre-1830 text from a candidate's own paper.
### Attribution rule for the *Lake Light* (BOM-13, written 2026-10-21)

Fixed **before any of this text enters Phelps's candidate sample**, because the sample is small
enough that a permissive rule would decide the result. Nothing from the *Lake Light* is scored
until a passage clears every test below.

**1. The paper changed hands, and the date ceiling is the first filter.** Read off the imprint
lines the OCR recovers:

| Issues | Imprint found | Status |
| --- | --- | --- |
| 1827-12-10 to 1828-02-18 | `PHELPS & BLOOMER` | Phelps era |
| 1828-03-19 onward | `CLARK & BLOOMER` | **not Phelps** |
| 1828-05-21, 1828-06-04 | `CLARK & BLOOMER ... is this day dissolved` | partnership wound up |

Phelps had left for the *Ontario Phoenix* by then; the issue of 3 Sep 1828 refers to the
"Ontario Phoenix, by W. W. Phelps" as another paper. **Only issues up to and including
18 February 1828 are eligible** — 15 of 42 issues, 196,448 OCR words of the 565,630. The gap
between 18 Feb and 19 Mar 1828 is indeterminate and is excluded, not split.

`W. W. PHELPS, & Co.` also appears on inside pages of several April 1828 issues, after the
masthead had changed. Those are standing advertisements or unreset job-printing notices, not
evidence of editorial control, and they do not extend the window.

**2. Two named publishers, so unsigned matter is not his.** The eligible run is *Phelps &
Bloomer*, not Phelps alone. Unsigned editorial matter could be either man's, and nothing in the
page tells them apart. Unsigned editorial matter is therefore **excluded**, which is the point
BOM-41 flagged.

**3. A country weekly is mostly reprint.** Credit-line language appears on 150 of 168 pages.
Reprinted items, congressional and official proceedings, legal notices, advertisements, market
tables and literary extracts are **excluded** regardless of date.

**4. What is admissible.** Only matter signed by Phelps or carried over his initials, inside the
date window, and not reprinted. Also admissible: a prospectus, salutatory or valedictory
signed by him alone.

**5. The expected result, recorded in advance.** Explicit `W. W. Phelps` signatures appear on
11 of 168 pages, and most are the masthead rather than a signature over an article. So this rule
will likely admit **little or nothing**, and the *Lake Light* may contribute nothing to Phelps's
sample. That is the honest outcome of a two-publisher, mostly-reprinted paper, and it is written
here before the extraction runs so that a disappointing yield cannot become a reason to loosen
the rule. If the yield is zero, Phelps keeps the "unreliable sample" flag of preregistration
section 3 and that is reported.

**6. The OCR is not yet good enough to apply this mechanically.** Identifying signatures and
credit lines requires segmenting the page into items, which this text layer does not support.
Extraction waits on BOM-14's cleaning; until then the window and the exclusions above stand as
the specification, not as a completed selection.

**Correction to this file's own record:** the entry below said "publishers Phelps & Bloomer
1827-1828". The imprint evidence above shows Phelps's involvement ends in early 1828, not at
year end.

- *Ontario Phoenix*, LCCN `sn84031006`, Canandaigua 1828-1832, publisher line **W. W. Phelps
  & R. M. Bloomer (1828-1829), W. W. Phelps (1829-1830)**. **Not digitized**: absent from
  NYS Historic Newspapers' title index, from Chronicling America (0 pages), from HathiTrust
  and the Internet Archive. The union list shows the only microfilm run starting 7 July
  1830, after Phelps had read the Book of Mormon, and about twenty scattered pre-1830 paper
  issues in four libraries. Out of scope under the digitized-only rule; the gap is reported.

So the "tens of thousands of words" hoped for from the Phoenix do not exist in any form.
What Phelps gets instead is the Lake Light: 42 four-page issues, of which only the
editorial matter is attributable, and the masthead names two publishers. Unsigned matter is
not automatically Phelps's, much of any weekly is reprinted from elsewhere, and the microfilm
OCR is poor. Attribution within the paper needs its own rule, and the text needs BOM-14's OCR
correction, before it enters his sample.

See `docs/new-york-newspapers.md`.

| id | Text | Format / URL | Written; published | Provenance | Pre-1830 | Licence | Words (est.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| wwp-evening-morning-star | *The Evening and the Morning Star*, Independence issues | IA OCR [EveningAndMorningStar18321834](https://archive.org/details/EveningAndMorningStar18321834) | Jun 1832-Jul 1833 | edited | no | public domain | whole run about 374,000; editorials unmeasured |
| wwp-messenger-advocate-letters | Letters 1-12 to Oliver Cowdery and "Thou Shalt Not Lie" | [Wikisource author page](https://en.wikisource.org/wiki/Author:William_Wines_Phelps) | 1834-1835 | printed | no | public domain | about 15,000 (rough guess) |

Also found but not in the manifest: Phelps's 1835-1836 Kirtland letters to his wife Sally,
edited by Bruce A. Van Orden in *BYU Studies* 33:3 (1993)
([ScholarsArchive issue](https://scholarsarchive.byu.edu/byusq/vol33/iss3)); the edition is
copyrighted, the originals are at the Church History Library.

How to fetch: `--id wwp-evening-morning-star` (2.2 MB); a later step must keep only
Phelps's editorials from the Independence issues.

**Do not use:**

- Hymns (preregistration section 3 excludes them): verse, and many are adaptations.
- Kirtland issues of the *Star* (Dec 1833-Sep 1834) and the 1835-1836 Kirtland reprint: edited
  by Oliver Cowdery, and the reprint altered the original texts.
- Revelations, letters and reprinted items inside the *Star*: other authors.
- *Times and Seasons* pieces he may have ghost-written for Joseph Smith (1842-1844): disputed
  attribution in both directions.

## Solomon Spalding

One work survives, the *Manuscript Story* (often called "Manuscript Found"), written around
1812 in Spalding's hand and published only after his death (1816). The holograph is at
Oberlin College Archives, RG 30/028 ([finding aid](https://oberlin.libraryhost.com/repositories/2/resources/455));
researchers must use a negative photostat and no digital images have been published.

| id | Text | Format / URL | Written; published | Provenance | Pre-1830 | Licence | Words (est.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ss-manuscript-story-1885 | *Manuscript Story*, RLDS edition | IA OCR [themanuscriptsto00spauuoft](https://archive.org/details/themanuscriptsto00spauuoft) | c. 1812; Lamoni 1885 | posthumous transcription from a verbatim copy | yes | public domain | 44,300 OCR tokens measured, about 40,000 without the publisher's letters |
| ss-manuscript-story-1886 | *Manuscript Story*, Deseret News edition | IA OCR [manuscriptfound.00spaurich](https://archive.org/details/manuscriptfound.00spaurich) | c. 1812; Salt Lake City 1886 | posthumous transcription | yes | public domain | witness only |
| ss-oberlin-original | The holograph | Oberlin RG 30/028 (not digitized) | c. 1812 | handwritten | yes | physical | arbiter for disputed readings |

Also verified: IA `manuscriptstoryo00spau` (a later RLDS printing), and Oberlin's own
[description page](https://www2.oberlin.edu/archive/oresources/smanuscript/index.html) (narrative only, no images).

How to fetch: `--id ss-manuscript-story-1885` (fetched); `--id ss-manuscript-story-1886`
for collation.

**Do not use:**

- The lost "Manuscript Found" as described by witnesses (affidavits in E. D. Howe,
  *Mormonism Unvailed*, 1834): recollections by others twenty years later, not Spalding's text.
- The publishers' introductions and correspondence bound into the 1885 and 1886 editions.

## Ethan Smith

Plenty of pre-1830 text. The main care point is that his books quote others at length (Adair,
Boudinot, Humboldt in *View of the Hebrews*); quotations must be stripped before style is
measured.

| id | Text | Format / URL | Written; published | Provenance | Pre-1830 | Licence | Words (est.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| es-1823-view-of-the-hebrews | *View of the Hebrews*, 1st ed. | IA OCR [viewofhebrewsexh00smitrich](https://archive.org/details/viewofhebrewsexh00smitrich) | 1823 | printed | yes | public domain | 55,000 |
| es-1825-view-of-the-hebrews | *View of the Hebrews*, 2nd ed. | IA OCR [viewofhebrewsort00smit](https://archive.org/details/viewofhebrewsort00smit) | 1825 | printed | yes | public domain | 100,000 (much added quotation) |
| es-1811-dissertation | *A Dissertation on the Prophecies Relative to Antichrist* | IA OCR [dissertationonpr01smit](https://archive.org/details/dissertationonpr01smit) | 1811 | printed | yes | public domain | 150,000 |
| es-1824-treatise | *A Treatise on the Character of Jesus Christ* | IA OCR [treatiseoncharac00smit](https://archive.org/details/treatiseoncharac00smit) | 1824 or earlier | printed | yes | public domain | 65,000 |
| es-1817-episcopacy | *Episcopacy Examined* | IA OCR [episcopacyexamin01smit](https://archive.org/details/episcopacyexamin01smit) | 1817 | printed | yes | public domain | 20,000 |
| es-1809-sermon-newburyport | Sermon to Dr Spring's Society, Newburyport | IA OCR [sermondeliveredt00smit](https://archive.org/details/sermondeliveredt00smit) | 1809 | printed | yes | public domain | 6,000 |
| es-1815-death-of-gods-chosen | *The Death of God's Chosen* (funeral sermon) | IA OCR [deathofgodschose00smit](https://archive.org/details/deathofgodschose00smit) | 1815 | printed | yes | public domain | 6,500 |

Also verified: 1823 Michigan copy IA `viewhebrewsexhi00smitgoog`, 1814 *Dissertation* IA
`dissertationonpr00smit`, *View of the Trinity* IA `viewoftrinitytre00smit`, *Key to the
Revelation* (1833) IA `keytorevelation00smit`, *Prophetic Catechism* (1839) IA
`propheticcatechi00smit`, and a Wikisource transcription of the 1825 *View of the Hebrews*
([link](https://en.wikisource.org/wiki/View_of_the_Hebrews), no source scan given).

How to fetch: `--id <id>`.

**Do not use:**

- *Memoirs of Mrs. Abigail Bailey* (1815, IA `memoirsofmrsabig00bail`): Bailey's memoir; Smith
  only edited it.
- *A Sermon Preached at the Instalment of the Rev. Ethan Smith* (1800, IA
  `bim_eighteenth-century_a-sermon-preached-at-th_smith-ethan_1800`): preached at his
  installation by another minister; catalogued under his name.
- Quoted matter in *View of the Hebrews* (Adair, Boudinot, Humboldt, Priest and others).
- The 1825 edition counted together with the 1823 edition: shared text would be counted twice.

## Gilbert J. Hunt

One known work, *The Late War* (1816), a school history of the War of 1812 written in
imitation-KJV style. It must be KJV-masked like the Book of Mormon, or its biblical phrasing
dominates any comparison.

| id | Text | Format / URL | Written; published | Provenance | Pre-1830 | Licence | Words (est.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gh-1816-late-war | *The Late War*, New York: Longworth | IA OCR [latewarbetween_00hunt](https://archive.org/details/latewarbetween_00hunt) | 1816 | printed | yes | public domain | 60,000 |
| gh-1819-late-war | *The Late War*, 1819 printing | IA OCR [latewarbetweenun00inhunt](https://archive.org/details/latewarbetweenun00inhunt) | 1816; 1819 | printed | yes | public domain | witness to fill gaps |

Also verified: a Wikisource transcription ([The Late War](https://en.wikisource.org/wiki/The_Late_War),
from the 1819 scan), a 1816 PDF at
[Book of Mormon Central](https://archive.bookofmormoncentral.org/sites/default/files/archive-files/pdf/hunt/2019-02-06/gilbert_j._hunt_the_late_war_1816.pdf),
IA `latewarbetweenun00hunt_0` (1819), and *The Historical Reader* (1819 school reissue, IA
`readercontain00hunt`, `historicalreader00huntgil`). The Online Books Page lists a HathiTrust
copy of the 1816 edition; its access status was not confirmed.

How to fetch: `--id gh-1816-late-war`, then `--id gh-1819-late-war` to fill the pages missing
from the 1816 scan.

**Do not use:**

- *The Historical Reader* (1817/1819) as a second sample: the same text reissued for schools;
  at most a collation witness.
- More than one printing at a time: each printing is the same text.

## Gaps and what was not verified

- **Pre-1830 samples are missing** for Rigdon, Pratt and Phelps, and nearly missing for
  Cowdery (about 2,500 words, much of it quotation) and for Joseph Smith in his own hand.
- **Phelps's *Ontario Phoenix*** (1828-1832): not digitized anywhere (checked 2026-10-20); the *Lake Light* (1827-1828) is digitized and pulled, see above.
- **Rigdon in Campbell's *Christian Baptist*** (1823-1830): not yet searched issue by issue.
- **HathiTrust**: no full-view record was confirmed for any candidate text; Internet Archive
  copies cover every printed item listed here.
- **Ethan Smith's *Treatise*** is listed on Wikisource as 1814; only 1824 printings were
  verified.
- **Word counts for Wikisource items and all JSP items** are rough estimates; real counts
  come when they are fetched.
- **Cowdery's letter to Hyrum Smith, 14 June 1829** (pre-1830) was not checked; worth
  searching for a surviving copy.
