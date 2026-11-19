# Where the information for the new tests would come from

Research of 2026-11-18 for the seven tests written up as BOM-102 to BOM-108, and BOM-99. Two parts
for each test: what our own library already holds (counted from `data/catalog/catalog.parquet`,
works with text, newspapers left out), and what has to come from outside.

**How to read the status words.** *Opened*: the page or file was opened that day and holds what is
said. *Resolves*: the address answered but the content was not read. *Unverified*: from a search
summary or from memory; check before relying on it. Library counts are catalog records, not
distinct books; the library has many duplicate printings, so real numbers are lower. The outside
search was done by three AI research agents and has not been re-checked by a person.

Nothing was downloaded. Nothing here changes a result.

## Fetched, 2026-11-18 (owner: "get what you can get and the decision holds")

`python -m lab.sources fetch` fetched 78 of 79 sources, about 1.2 GB; `data/lab/sources.json`
records each with its address, terms, size and SHA-256. Open material is in
`data/corpus/lab/sources/`, copyrighted material in `data/private/lab/sources/`.

| Group | What arrived | For |
| --- | --- | --- |
| `speech/` | Old Bailey Corpus 2.0 (speech marked, three archives) and the full Old Bailey Online XML; eight hand-keyed short-hand texts from Evans TCP; Whitefield's *Eighteen Sermons* (111,000 words) | BOM-106 |
| `prophets/` | 18 volumes: Southcott (4; 820,000 words), Wroe (3; 430,000), Brothers, Job Scott's journal, Hicks's journal and letters, Shaker *Testimonies*, Blake's letters, Handsome Lake, Strang's three newspapers and one book, Nat Turner's *Confessions* | BOM-99, BOM-105 |
| `bible_style/` | seven scans (Dodsley, Ilive, Leacock, Snowden, *First Book of Napoleon*, O'Connor, *Book of Nullification*) and the wordtree transcriptions of 28 texts | BOM-102, 106, 107 |
| `dictated/` (private) | Old Testament Revision 1 (64 pages) and 2 (127), Visions of Moses (3), Book of Abraham manuscripts A, B, C (4, 6, 10) and the 1842 printing (11) | BOM-104 |
| `rigdon/` (private) | 1838 oration and 1840 *Appeal* from the Joseph Smith Papers; the "Millennium", "Gospel" and miscellaneous essays, 1833-38, as transcribed at sidneyrigdon.com | BOM-104 |
| `names/` | the Onomasticon's 377 entries; three Bible name datasets; Neo-Assyrian names; Morse's 1797 gazetteer (490,000 words) | BOM-108 |
| `debates/` | *Millennial Harbinger* 1831 and the 1832 *Delusions* pamphlet | BOM-103 |
| `chiasmus/` | the two published detectors' code | BOM-107 |
| `papers/` (private) | 16 papers: the translation-detection methods, Tvedtnes 1970 and 1991, *Echoes and Evidences*, Holmes 1992, the chiasmus detectors, the dating precedents | all |
| `translation_labels/` | `python -m lab.sources marc`: for each of our 62,163 HathiTrust records, the catalog fields that mark a translation | BOM-102 |

**Not fetched.** One paper refused the request (Kestemont 2015 preprint). Sites that refuse
programs, to be saved by hand in a browser: the Edwards chiasmus papers, Phipps's thesis, Reynolds
2005, Skousen 1994 and 1998, Carmack 2018 and 2021, Welch 1995, Wilcox 2019 (all on
scholarsarchive.byu.edu or digitalcommons.usu.edu). Left out on purpose: books under copyright
posted by users on the Internet Archive; Hansard (the Old Bailey corpus covers the need);
Hebrew names from inscriptions and the Egyptian name sites (no confirmed download). OCR text from
scans is uncorrected; the wordtree transcriptions are cleaner where both exist.

## Decisions for the owner (answered 2026-11-18: the 25 October decision holds)

1. **Joseph Smith Papers terms.** The site's terms allow viewing, downloading and printing for
   "personal, noncommercial use", forbid "any robot, spider, or other automatic device" without
   written permission, and do not mention research. Permission requests go through
   permissions.churchofjesuschrist.org (reply in about 45 days). BOM-104 needs new material from
   the site (Book of Moses and Book of Abraham manuscripts). The transcripts we already
   hold were fetched on the owner's decision of 2026-10-25 (a browser User-Agent, requests 2.5 to
   7.5 s apart; recorded in `docs/candidates.md` and `ingest/jsp.py`). Whether that decision
   covers this new material too, or to ask permission first, is the owner's call.
2. **Books under copyright posted on the Internet Archive by users** (Vogel's *Religious Seekers*,
   Metcalfe's *New Approaches*). Fine to read for a topic list; not to be added to the corpus.
3. **Non-commercial licences.** Old Bailey data is CC BY-NC (and BY-NC-SA for the speech-tagged
   corpus). Usable for the study; record it in SOURCES.md and do not republish the text.

## BOM-102: does it read like a translation?

**Held.** About 6,050 records whose title says "translated from", "from the German of" and the
like: French 2,886, Latin 862, German 767, Greek 555, Italian 347, Spanish 283, Dutch 221, Persian
102, Hebrew 79, Arabic 76. Bible-style books written in English by known authors, 19 distinct
titles: Snowden's *American Revolution* (1793-1823 printings), Hunt's *Late War*, *The First Book
of Napoleon* (1809), several "Chronicles" political parodies. EEBO-TCP for the King James Bible.

**Better labels than title phrases.** Library catalog records mark translations: MARC field 041
(first indicator 1 = "is or includes a translation"; subfield h = language of the original;
subfield k = intermediate language), 240 subfield l, and 765 ("Translation of"). Field definitions
at https://www.loc.gov/marc/bibliographic/bd041.html (opened). HathiTrust returns full records at
`https://catalog.hathitrust.org/api/volumes/full/recordnumber/<id>.json` (opened). Old records are
uneven (a 1760 Horace has subfield h but a blank indicator), so combine 041 h, 240 l and title
phrases, then hand-check a sample. No ready-made labelled set of 18th-19th century English
translations was found.

**Methods to follow.**

| Paper | Where | What it gives | Status |
| --- | --- | --- | --- |
| Koppel and Ordan 2011 | https://aclanthology.org/P11-1132/ | 300 function words; also identifies the source language | opened |
| Rabinovich and Wintner 2015 | https://aclanthology.org/Q15-1030/ | unsupervised separation of translated from original | opened |
| Rabinovich, Ordan and Wintner 2017 | https://aclanthology.org/P17-1049/ | the source language's signal survives translation | opened |
| Pylypenko and others 2021 | https://aclanthology.org/2021.emnlp-main.676/ | hand-made features against a neural model; the neural model wins by 20 points | opened |
| Amponsah-Kaakyire and others 2022 | https://arxiv.org/abs/2210.13391 | part of the neural model's edge is topic, not translation | resolves |
| Baroni and Bernardini 2006 | DOI 10.1093/llc/fqi039 | the founding paper | paywalled, unverified |
| Volansky, Ordan and Wintner 2015 | DOI 10.1093/llc/fqt031 | the standard feature sets | paywalled, unverified |

No paper released code. Modern test data with known direction:
https://shuly.cs.haifa.ac.il/research/projects/translationese (opened).

**The lists of claimed Hebraisms** (what to count):

| Source | Where | Constructions | Status |
| --- | --- | --- | --- |
| Tvedtnes 1970, *BYU Studies* | archive.bookofmormoncentral.org (PDF) | "it came to pass", construct state, adverbs, idioms | opened |
| Tvedtnes 1991 | archive.bookofmormoncentral.org (PDF) | construct state ("plates of brass"), cognates, compound prepositions ("by the hand of"), repeated *and*, "after that", "because that" | opened |
| Parry 2002, in *Echoes and Evidences* | archive.bookofmormoncentral.org (PDF) | simile curses, prophetic perfect, cognate accusative, plural amplification, repeated possessive | opened |
| Skousen 1994 | https://scholarsarchive.byu.edu/jbms/vol3/iss1/3 | the if-and conditional (14 originally), surplus "and it came to pass", nested embedding | opened |
| Carmack 2018 | https://scholarsarchive.byu.edu/interpreter/vol28/iss1/14 | argues Early Modern English, not Hebrew: periphrastic *did*, "the more part", "had spake" | opened |

Critical responses (Ashment 1993) are in print only.

**The Bible-style control set.** The fullest list is the appendix of Carmack 2021
(https://scholarsarchive.byu.edu/interpreter/vol49/iss1/5, opened): 25 texts, about 585,000 words.
Transcriptions of 28 such texts are at https://github.com/wordtreefoundation/books (opened; no
licence stated). The larger ones: Dodsley's *Chronicle of the Kings of England* (1740), Ilive's
*Book of Jasher* (1751), Leacock's *American Chronicles of the Times* (1774-75), Snowden (1793),
*First Book of Napoleon* (1809), Elias Smith's *History of Anti-Christ* (1811), Hunt (1816),
O'Connor's *Chronicles of Eri* (1822). Shalev's own list (2010 article, *American Zion*) is
paywalled.

**Gap.** A labelled translation set has to be built from catalog records and hand-checked.

## BOM-103: do its debates date to the 1820s?

**Held: everything needed for the first pass.** The meaning index, publication years, and reprints
of older writers as the "written long before" control (Bunyan alone is 198 records).

**The 1831 claim, wording checked against the scan.** Alexander Campbell, "Delusions", *Millennial
Harbinger* 2:2, 7 February 1831: "every error and almost every truth discussed in New York for the
last ten years. He decides all the great controversies;—infant baptism, ordination, the trinity,
regeneration, repentance, justification, the fall of man, the atonement, transubstantiation,
fasting, penance, church government, religious experience, the call to the ministry, the general
resurrection, eternal punishment, who may baptize, and even the question of free masonary,
republican government, and the rights of man." Scan:
https://archive.org/details/millennialharbinger1831 (opened); 1832 pamphlet:
https://archive.org/details/delusionsanalysi00camp (opened). **Campbell's twenty topics are a
ready-made topic list, fixed in 1831.**

**Other topic lists** (to be read, not ingested): Vogel, *Religious Seekers* (1988) and
"Anti-Universalist Rhetoric in the Book of Mormon" (1993); Bushman, "The Book of Mormon and the
American Revolution" (https://byustudies.byu.edu/article/the-book-of-mormon-and-the-american-revolution,
title confirmed); Thomas, *Digging in Cumorah* (print only). No verse lists were extracted.

**Method precedents.** https://aclanthology.org/P16-1141/ (meaning change over time),
https://aclanthology.org/E14-4004/ and https://aclanthology.org/S15-2147/ (dating texts); all opened.

**Gap.** None for the first pass. Reaching before 1780 needs EEBO-TCP embedded (held, not indexed).

## BOM-104: Joseph Smith's other dictated texts, and the Lectures on Faith

**Held.** The *Lectures on Faith*: all seven, in our 1835 Doctrine and Covenants transcript
(`data/private/replication/`; printed pages 5-74). Revelation Book 1 whole. Rigdon's 1838 oration
and 1840 *Appeal*. Campbell's *Christian Baptist* (1823 on).

**To fetch** (see the decision on Joseph Smith Papers terms above; all opened):

| Text | Address on josephsmithpapers.org | Scribes |
| --- | --- | --- |
| Old Testament Revision 1 (Book of Moses, earliest; June 1830 to March 1831; 60 pages) | /paper-summary/old-testament-revision-1/1 | Cowdery (first nine pages), John Whitmer, Emma Smith (two pages), Rigdon (most of the rest) |
| Old Testament Revision 2 (119 pages) | /paper-summary/old-testament-revision-2/1 | Whitmer's copy of the first, then Williams and Rigdon |
| Visions of Moses, June 1830 | /paper-summary/visions-of-moses-june-1830-moses-1/1 | Cowdery |
| Book of Abraham manuscripts A, B, C (1835) | /paper-summary/book-of-abraham-manuscript-circa-july-circa-november-1835-a-abraham-14-26/1 and siblings | Williams; Parrish; Phelps and Parrish |
| Book of Abraham, 1842 printing | /paper-summary/book-of-abraham-and-facsimiles-1-march-16-may-1842/1 | |
| Who copied each revelation | /bc-jsp/content/jsp/images/content/pdf/TOC/MRBTOC.pdf | Revelation Book 1: Whitmer about 100 items, Cowdery 5. These are copyists of the register, not always the scribe at dictation |

**Rigdon's prose** (index at http://sidneyrigdon.com/RigWrit1.htm, opened; word counts are whole
pages with the editor's notes, so upper bounds): "Millennium" series 1833-35 (33,000), "The Gospel"
series (21,000), miscellaneous articles and letters 1834-38 (35,000), "Faith of the Church of
Christ" (mostly his, per the index). Page scans of the *Messenger and Advocate*:
`latterdaysaintsm01unse` on the Internet Archive (we also hold the run: `oc-messenger-advocate`,
570,842 words, of which only Cowdery's signed items were used). Cautions: the 1838 oration may have
had help from Joseph or Hyrum Smith; the *Appeal* is unsigned. **No signed Rigdon text from before
1830 was found.**

**Earlier studies of the Lectures** (to compare against):

| Study | Where | Conclusion | Status |
| --- | --- | --- | --- |
| Phipps 1977, BYU thesis | https://scholarsarchive.byu.edu/etd/5045 | Rigdon for Lectures 1 and 7, fairly for 2, 3, 4, 6; Smith for 5 | record opened; PDF needs a browser |
| Larsen and Rencher 1982 | summary at rsc.byu.edu | largely supports Phipps | summary only |
| Reynolds 2005, *Journal of Mormon History* 31:3 | https://scholarsarchive.byu.edu/facpub/1480 | Rigdon wrote all seven | abstract only |

The summaries disagree on which lecture goes to Smith (2 or 5); read the originals. No newer
stylometric study was found.

## BOM-105 and BOM-99: prophets in two voices

**Prior work that bears directly on our headline finding.** Holmes 1992 (*Journal of the Royal
Statistical Society A* 155:1; copy at
https://www.physics.smu.edu/pseudo/ScienceReligion/MormonStylometric.pdf, opened and read): by
vocabulary richness, Joseph Smith's personal writings cluster apart, while the revelations, the
Book of Abraham and the Book of Mormon cluster together, which he calls a "prophetic voice". Our
paper cites Holmes (sections 2, 4, 10); check that it says our result agrees with his on this
point. Also: Kestemont and others 2015 on Hildegard of Bingen (DOI 10.1093/llc/fqt063): visions
written down under her secretary read as the secretary. No such comparison was found for Ellen
White, Swedenborg or Southcott, so this test would be new for them.

**Held.** Joanna Southcott, 25 distinct titles, both prophecies and letter collections (1804
*Letters and communications*; 1813 *Copies of letters sent to the clergy of Exeter*). John Wroe:
one 1829 book, *Life and journal; with divine communications*, both voices in one volume. Richard
Brothers 22 records, Swedenborg in translation 122, Job Scott 27, Elias Hicks 16 (sermons, an
epistle), Shaker titles 109, Jemima Wilkinson 1 or 2. Not held: William Blake's prophetic books.

**Outside** (Internet Archive item names; found by search, content not read unless said):

| Writer | Revelation | Ordinary writing | Note |
| --- | --- | --- | --- |
| Southcott | `strangeeffectsof00sout`, `mrssouthcottswor01soutiala` and 35 more | letters printed inside the pamphlets | dictated to scribes |
| Wroe | `privatecommunica01wroe` (1845) | `abridgementofjoh01wroe` (1837) | |
| Brothers | `ARevealedKnowledgeOfThePropheciesAndTimes` (1794) | later letters, unverified | |
| Hicks | sermons (held) | journal `journalofliferel00hick`, letters `lettersofeliashi00hick` | |
| Blake | https://www.blakearchive.org/ | letters, same site | |
| Nat Turner | https://docsouth.unc.edu/neh/turner/turner.html (opened) | none | taken down by Gray |
| Strang (after 1830) | Book of the Law: no open text found | `VoreeHerald1846`, `GospelHerald18471850` | |
| Ellen White (after 1830) | https://egwwritings.org/ | letters, same site | estate claims copyright in unpublished items |
| Mary Baker Eddy (after 1830) | 1875 first edition not found | https://mbepapers.org/ | |

Swedenborg is a translator's voice; Ann Lee wrote nothing herself; Handsome Lake's Code is a
translation. Further names not checked: William Miller, Robert Matthews, Jacob Cochran, Thomas
Lake Harris, Andrew Jackson Davis.

**Gap.** Wilkinson and Strang's revelation text have no open copy. The usable pre-1830 group with
both voices and enough words may be small (Southcott, Wroe, Brothers, Hicks, Scott); count words
before designing around it.

## BOM-106: spoken or written?

**Held.** 191 distinct titles saying "taken in short-hand" or "from his own mouth" (mostly trials);
66 dictated narratives (some are novels using the phrase as a device: hand-check); 947 trial
records, 746 debate records, 975 printed-speech records. The original and printer's manuscript
transcripts.

**Outside: speech taken down as spoken.**

| Collection | Where | Size | Terms | Status |
| --- | --- | --- | --- | --- |
| Old Bailey Proceedings, 1674-1913 | https://orda.shef.ac.uk/articles/dataset/Old_Bailey_Online_XML_Data/4775434 | 2,163 proceedings, one 315 MB file | CC BY-NC 4.0 | opened |
| Old Bailey Corpus 2.0, speech and speaker marked | https://fedora.clarin-d.uni-saarland.de/oldbailey/downloads.html | 24.4 million spoken words, 1720-1913 | CC BY-NC-SA 4.0 | opened |
| Hansard from 1803 | https://www.hansard-archive.parliament.uk/ ; cleaned at https://github.com/Democracy-Lab/hansardr | whole run | parliamentary copyright; licence page not read | opened |
| Corpus of English Dialogues 1560-1760 | Oxford Text Archive item 2507 | 1.18 million words | non-commercial research | unverified |
| Evans TCP short-hand titles | https://github.com/textcreationpartnership | 23 titles, hand-keyed: Whitefield's sermons taken by Gurney, the Boston Massacre trial | free | opened (catalogue) |

The Old Bailey corpus is the strongest single source: hand-corrected, speech separated from
narrative, and it spans our period. No machine-readable Annals of Congress was found.

**Features to measure.** Biber 1988, *Variation across Speech and Writing* (67 features; a tagger
at https://github.com/andreanini/multidimensionalanalysistagger, opened). Culpeper and Kytö 2010,
*Early Modern English Dialogues* (print). Most of Biber's "spoken" features (contractions,
second-person pronouns) will be rare in scripture-style text; clause chaining and repetition are
the ones likely to carry over.

**Claims already made about the Book of Mormon that this could test.** Davis 2020, *Visions in a
Seer Stone*: "laying down heads", that is, summary outlines stated first and then expanded, as
preachers of the time were trained to do (read only through Hales's review,
https://scholarsarchive.byu.edu/interpreter/vol39/iss1/10/, opened). Skousen 1998
(https://scholarsarchive.byu.edu/jbms/vol7/iss1/4, opened): mishearing errors, about 20 words
dictated at a time, names spelled out.

## BOM-107: chiasmus with a real baseline

**Held.** The library, the King James Bible, the Bible-style books.

**The statistic to reproduce.** Edwards and Edwards 2004
(https://byustudies.byu.edu/article/does-chiasmus-appear-in-the-book-of-mormon-by-chance, opened;
PDF at https://digitalcommons.usu.edu/physics_facpub/574): for a chiasm of n elements each
appearing twice, the chance of that order is L = 1/(2n-1)!!; over N opportunities in a work,
P = 1 - (1-L)^N. Their published values give us numbers to match first: Alma 36, n = 8, P =
0.00018; Leviticus 24:13-23, n = 7, P = 0.0025; Doctrine and Covenants 88:34-39, P = 0.52. Their
program is no longer on the page the paper names; ask BYU Studies or the authors, or rewrite it
from the paper. Their 2010 paper on admissibility:
https://scholarsarchive.byu.edu/byusq/vol49/iss4/8/ (abstract only read).

**Test items.** No list exists as data. Hand-key from Edwards's Table 1, Welch 1969
(https://byustudies.byu.edu/article/chiasmus-in-the-book-of-mormon, opened), Welch's 1995 criteria
(https://scholarsarchive.byu.edu/jbms/vol4/iss2/1/, opened), Parry's *Poetic Parallelisms*
(https://scholarsarchive.byu.edu/mi/61/), and the BYU Chiasmus Index
(https://byustudies.byu.edu/chiasmus/index, opened; no download).

**Automatic detectors.** Dubremetz and Nivre 2015-2018 (https://aclanthology.org/W15-0703/, code
https://github.com/mardub1635/chiasmusDetector, GPL-3); Schneider and others 2021
(https://aclanthology.org/2021.latechclfl-1.11/, code https://github.com/cvjena/chiasmus-detector).
All opened. **They find short word-level reversals ("ask not what your country..."), not the long
many-verse structures claimed for Alma 36.** So the library baseline can be run two ways: short
reversals with an existing detector, and long structures with our own counter built on Edwards's
statistic.

**Critics** (Wunderli 2005 and the exchange that followed, in *Dialogue*): addresses found, site
would not open; unverified.

## BOM-108: the names

**The list.** The BYU Book of Mormon Onomasticon (https://onoma.lib.byu.edu/, opened): 337 proper
names, 188 unique to the Book of Mormon and 149 shared with the Bible; grouped as Lehite (104
personal, 67 place), Jaredite (46, 18), and smaller groups. Its listing can be read by program
(one call returned 377 entries). No licence is stated; our own extraction from the 1830 text
should be the primary list, checked against theirs.

**Bible names as data.** https://github.com/robertrouse/theographic-bible-metadata (3,067 people,
1,298 places; CC BY-SA 4.0), https://github.com/BradyStephenson/bible-data (CC BY 4.0; includes
Hitchcock's name dictionary), https://github.com/openbibleinfo/Bible-Geocoding-Data (CC BY 4.0).
All opened. None covers the Apocrypha: take those names from our own King James text.

**Ancient names.**

| Source | Where | Download | Status |
| --- | --- | --- | --- |
| Neo-Assyrian names (ORACC) | https://oracc.museum.upenn.edu/pnao/ | yes, one small file; CC BY-SA 3.0 | opened |
| Trismegistos (Egypt, Greek and Egyptian names) | https://www.trismegistos.org/dataservices/ | record by record; no full list; CC BY-SA 4.0 | opened |
| Greek personal names (LGPN) | https://www.lgpn.ox.ac.uk/ | search only | opened |
| Hebrew names from inscriptions (Golub, about 950) | https://www.onomasticon.net/ | not confirmed | unverified |
| Egyptian Middle Kingdom names | https://pnm.uni-mainz.de/ | not confirmed | unverified |

Ranke's Egyptian name book exists as scans only. Nothing open was found for Ugaritic.

**Comparison sets from our side.** Morse's *American Gazetteer* 1797
(https://archive.org/details/americangazettee00mors, public domain) and the 277 gazetteer records
we hold; Spalding's invented names from his manuscript (held). **No dataset of invented names in
fiction before 1830 exists**; it would be built from our fiction (30,479 records) by rule.

**The earlier study to answer.** Wilcox and others 2019
(https://scholarsarchive.byu.edu/interpreter/vol33/iss1/6, opened): sound-pattern probabilities;
found the names pattern with authentic names more than with Spalding's or Tolkien's; the authors
call it exploratory, release no data, and no published critique was found. Their comparison sets
were small; ours would add King James names as a reference, which theirs lacked as a separate
tradition.

**Gap.** Hebrew names from inscriptions are the most relevant ancient set and the least confirmed.

## Which tests are ready, by what they still need

| Test | Needs from outside | Readiness |
| --- | --- | --- |
| BOM-103 debates | nothing | ready |
| BOM-107 chiasmus | nothing; hand-key test items; rewrite Edwards's program | ready |
| BOM-106 spoken or written | Old Bailey corpus (one download) | nearly ready |
| BOM-102 translation | catalog records for labels; the Bible-style transcriptions | needs a labelled set built |
| BOM-105 / BOM-99 two voices | a few Internet Archive volumes | ready for a small group; group size is the risk |
| BOM-108 names | name lists; Hebrew inscriptions unconfirmed | partly ready |
| BOM-104 dictated texts | Joseph Smith Papers material (owner's decision on terms); Rigdon's essays | Lectures on Faith ready now; the rest waits |
