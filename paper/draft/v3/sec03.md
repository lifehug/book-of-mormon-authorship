## 3. Borrowing: the CES Letter's books, and everything else

The question with the plainest answer comes first: what did the Book of Mormon take from books
already in print? Borrowing can happen at four depths, and each has its own test: copied wording
(3.1), unusual phrases in common (3.2), the same ideas in different words (3.3), and the same story
in the same order (3.4). Section 3.5 then takes the three books named in the *CES Letter* one by
one, and 3.6 states what none of these tests can show.

All four tests read the text with its King James spans labelled, so that Bible quotation is counted
separately from everything else. All were run against the period library, not against a chosen
shelf, so that each result can be set beside what is ordinary for a book of its kind.

### 3.1 Copied wording

**Preparation.** The masked text was aligned against every eligible volume printed before it, with
its own copies left out. The aligner (passim) finds passages that match word for word or nearly so,
allowing for OCR errors (`docs/reuse-plan.md`; Amendment 10).

**Result.** 58 short passages in 47 earlier-catalogued volumes align with the Book of Mormon,
covering 0.52% of it. Seventeen of those volumes are later texts that quote the book under catalog
dates decades too early (section 2.2). Without them **0.16%** of the text remains shared with
earlier books, in 30 volumes, and all of it is short, loose religious stock phrasing (9 to 46
tokens). None of the 30 is a book proposed as a source. For scale, the same search finds that *The
Late War* (1816) shares 8.92% of its text with earlier books, mostly the War of 1812's own
documents, which it retells, and an 1821 volume of sermons 2.47%.

Beyond its King James passages, then, the Book of Mormon copies almost nothing word for word from
any earlier book in the library.

### 3.2 Rare shared phrases

**Preparation.** This is the test of Johnson and Johnson (2013), rebuilt on a full library. A
four-word phrase counts as rare if it occurs in at most 5 of the period's texts. A source's score
is the number of rare phrases it shares with the Book of Mormon per 10,000 of its own words, placed
against all 204,520 period volumes (`data/reuse/bom/rare.json`; Amendments 12-13). One correction
was needed before the test worked: rarity is counted by distinct text, not by volume, because nine
printings of *The Late War* in the library had made its own phrases look common (Amendment 8).

**Result.**

| Source | Rare shared phrases | Per 10,000 words | Rank of 204,520 | p (95% interval) | Passes the registered rule |
| --- | --- | --- | --- | --- | --- |
| *The First Book of Napoleon* (1809) | 12 | 5.45 | 63 | 0.0003 (0.0002-0.0031) | yes |
| *The Late War* (1816) | 22 | 3.86 | 131 | 0.0006 (0.0004-0.0017) | yes |
| *View of the Hebrews* (the 1823 edition's text) | 2 | 0.37 | 9,496 | 0.046 (0.017-1.0) | no |
| Spalding, *Manuscript Story* | 1 | 0.24 | - | 0.068 | no |

*The Late War* and *Napoleon* pass, as Johnson and Johnson reported. But both are imitations of
scripture, books written on purpose in King James style, and within that group they are not
unusual. Set beside the curated imitation-scripture works (a post hoc comparison), an 1829 reprint
of Jacob Ilive's *Book of Jasher* shares more than either (31 phrases, 7.99 per 10,000 words). That
reprint was printed in Bristol, and its circulation in America is not established; nobody proposes
it as a source. The shared phrases are battle and chronicle formulas. In all, 2,044 volumes pass
the same rule, most of them short pieces sharing a single phrase.

The reading is that the signal is real and belongs to a genre. A book written in imitation of the
King James Bible shares rare King James-like phrasing with another such book, whether or not either
author saw the other.

### 3.3 Paraphrase

**Preparation.** To find the same ideas in different words, the eligible library (278,796 volumes)
was cut into 128-word passages, 163 million of them, and each was turned into a vector by an
embedding model (a model that places passages with similar meaning near each other), chosen
beforehand on a known-answer paraphrase test (Amendment 14). Each Book of Mormon passage was
searched against all of them. A named source is then scored two ways: by its rank within its
subject group, and against a null of 500 volumes matched to it in genre and length. The registered
bar is the top 1% of that null. The genre label for each source's null was chosen after the
sources' ranks had been seen (Amendment 21, post hoc).

**Result** (`data/semantic/named.json`, `data/semantic/named_null.json`).

| Source | Rank in its subject group | Score (95% interval) | Null median | Null 99th percentile | Percentile in null | Stands out |
| --- | --- | --- | --- | --- | --- | --- |
| *View of the Hebrews* (1825) | 1 of 49 | 29.6 (28.0-31.3) | 14.6 | 45.0 | 84.6 | no |
| *View of the Hebrews* (1823) | 2 of 49 | 29.5 (27.9-31.1) | 9.2 | 38.4 | 94.0 | no |
| *The First Book of Napoleon* | 3 of 18 | 7.9 (6.9-9.0) | 0.1 | 8.8 | 98.4 | no |
| *The Late War* | 6 of 18 | 1.9 (1.4-2.4) | 0.4 | 14.6 | 79.8 | no |
| Spalding, *Manuscript Story* | 12 of 49 | 5.5 | - | - | - | no (by rank) |

*View of the Hebrews* comes first of the 49 books on the origin of the American Indians. That is a
real result: on its subject it is the closest book in the library. But the Book of Mormon is a
religious book, and 77 of 500 equally religious volumes of similar length score higher than *View
of the Hebrews* does. It sits at the 85th percentile, short of the top-1% bar. The two rankings
answer different questions, and both are reported: closest on its subject, not unusual for a
religious book.

**The whole library.** In the search over every volume, editions of Josephus take 14 of the top 20
places, and the registered rule flags 622 sources (`data/semantic/corpus_bom.json`). A count that
large mostly measures biblical register: many period books retell or expound scripture.

**Proposed parallels (exploratory, not registered).** Of the 500 parallels proposed in Rick
Grunder's *Mormon Parallels*, 139 match firmly to works in the catalog. Their sources score
slightly closer than other volumes (median percentile 91.0 against 87.4, p 0.087), as would be
expected from how they were chosen, and two firmly matched entries stand out, Josephus and the Owen-Campbell *Debate on the
Evidences of Christianity* (4 of 99 volumes; `data/semantic/grunder_ranks.json`).

**Reading the surfaced pairs.** Every pair of passages the searches brought up, 1,069 in all, was
then read and labelled as King James wording, period stock phrasing, or specific to the two texts.
The first reading was by one AI model; a second AI model, not shown the first label, reread every
pair called specific and a seeded tenth of the rest. Both readings are simulated review, not human
judgment. The first pass labelled 382 pairs King James wording, 685 stock phrasing and 2 specific;
the second pass called both of those common. **No pair is specific under both readings**
(agreement on the 104 pairs read twice 0.74, Cohen's kappa 0.51; `data/semantic/triage.json`).

### 3.4 Story order

**Preparation.** Two books can tell the same story with no sentence in common. Each 2,000-word
block of the Book of Mormon, and of each source, was reduced by a hosted AI model to at most 12
events with the characters named by role ("a commander writes to the governor"), giving 1,421
events for the Book of Mormon. The reduction was checked on 20 King James chapters read twice
(median agreement 0.92; the check covers biblical narrative, not period prose, and no
chance-corrected figure was computed). Two event sequences are then aligned, and each alignment is
tested against 1,000 shuffles of the source's order (Amendment 15; `data/semantic/skeleton/`).

**Checked first on a known retelling.** Josephus's *Antiquities* retells Genesis to Judges. The
test finds 108 events in the same order as the Bible (p 0.001). The registered control had three texts: the test also finds the *Testaments of the
Twelve Patriarchs* (8 events, p 0.003) and does not find Ilive's *Book of Jasher* (4 events,
p 0.75; `data/semantic/skeleton/controls.json`). It can find a retold story when the retelling
is close; it missed one of three.

**Result.** No book shares the Book of Mormon's plot. Among the 20 leading sources of the
paraphrase search the longest shared run is 9 of its 1,421 events (an edition of Josephus, p 0.24).
The named sources share 2 to 4 events each, none in an order that differs from chance: *View of the
Hebrews* 1823, 3 events (p 0.97) and 1825, 2 (p 1.0); Spalding, 4 (p 0.67); *The Late War*, 2 (p
1.0); *Napoleon*, 3 (p 1.0).

One book of the 49 in the Indian-origins group does reach the registered level: Benjamin Church's
*History of Philip's War* (p 0.008). The shared run is six events from one stretch of each book,
the common shape of military correspondence: a commander writes angrily to a governor, the governor
replies, troops march. With 49 books tested, one p-value that small arises by chance about 1 time in 3. It is reported as it came out and read as chance.

### 3.5 The Letter's three books, one by one

The *Letter to a CES Director* (Jeremy Runnells, 2013) is the most widely read critical
compilation. Its Book of Mormon section names three books as sources or parallels: *View of the
Hebrews*, *The Late War* and *The First Book of Napoleon* (`docs/ces-letter-books.md`, checked
against the Letter's text). Each claim was registered with its decision rule (`data/claims/register.yaml`): claims c01-c12
on 2026-10-18, before any result; c13-c17, which include Spalding and *The First Book of
Napoleon*, on 2026-11-06, before the blind run and after the borrowing results existed. Access scores run from 3 (documented within Joseph Smith's reach
before mid-1829) to 0 (no evidence of circulation in the region); availability is not use
(`data/access/access_table.csv`).

**3.5.1 *View of the Hebrews*** (Ethan Smith, 1823; second edition 1825). *The claim:* B. H.
Roberts' parallels, shown chart by chart: a Hebrew origin for the American Indians, buried records,
the scattering and gathering of Israel.

| Test | Result |
| --- | --- |
| Copied wording (3.1) | none |
| Rare phrases (3.2) | 2 shared, rank 9,496 of 204,520, p 0.046: does not pass |
| Paraphrase (3.3) | first of 49 on its subject; 85th percentile against 500 matched religious volumes (94th for the 1823 edition): does not stand out |
| Surfaced pairs | none specific |
| Story order (3.4) | 1823: 3 events, p 0.97; 1825: 2 events, p 1.0 |
| Ethan Smith as author | the one candidate the models recognise across his books, and not the closest to the text (section 7.4) |
| Access | 2 for both editions: the first reviewed in Utica in 1825, the second advertised there in 1826; no Palmyra notice found |
| Verdict (claim c02) | **contradicted**: the shared themes are real and are common to the period's writing on Indian origins; no wording, passage or plot is shared beyond that genre |

**3.5.2 *The Late War between the United States and Great Britain*** (Gilbert J. Hunt, 1816; the
Letter gives 1819, the year of a reissue for schools). *The claim:* shared phrasing.

| Test | Result |
| --- | --- |
| Copied wording | none |
| Rare phrases | 22 shared, rank 131 of 204,520, p 0.0006: **passes**; an imitation-scripture reprint shares more, and the phrases are battle and chronicle formulas |
| Paraphrase | 6th of 18 in its group, 80th percentile: does not stand out |
| Surfaced pairs | none specific |
| Story order | 2 events, p 1.0 |
| Hunt as author | section 7.5; at equal training dose a slice of *The Late War* is ahead of Joseph Smith's revelations on 63% of chunks at 590M and not at the smaller sizes (section 6.2), an effect of shared register |
| Access | 1: Palmyra advertisements of 1827-30 for a "Historical Reader" do not name an author |
| Verdict (claim c01) | **mixed**: the rare-phrase signal is real, as Johnson and Johnson found, and it is shared with other imitation scripture; no passage or plot is shared |

**3.5.3 *The First Book of Napoleon*** (1809). *The claim:* shared phrasing.

| Test | Result |
| --- | --- |
| Copied wording | none |
| Rare phrases | 12 shared, rank 63 of 204,520, p 0.0003: **passes** |
| Paraphrase | 3rd of 18 in its group, percentile 98.4, just under the bar: does not stand out |
| Surfaced pairs | none specific |
| Story order | 3 events, p 1.0 |
| Access | 0: a London imprint; no American printing or advertisement found |
| Verdict (claim c14) | **mixed**: dense rare phrasing of the same chronicle kind, and nothing else |

**3.5.4 Beside the Letter: Spalding's *Manuscript Story*.** The Letter does not name it; other
critics do, from 1834 on, so it gets the same treatment, labelled as not from the Letter. Only the
surviving manuscript can be tested.

| Test | Result |
| --- | --- |
| Rare phrases | 1 shared, p 0.068: does not pass |
| Paraphrase | 12th of 49: does not stand out |
| Surfaced pairs | one pair called specific on the first reading (elephant-like "Mammoons"), called common on the second |
| Story order | 4 events, p 0.67 |
| Spalding as author | section 7.3 |
| Access | 0: unpublished until 1885 |
| Verdict (claim c13) | **contradicted** as a source |

**What the Letter argues that this study does not test.**

- *The King James arguments:* that the text follows the errors of the 1769 edition, carries the
  translators' italic words, and reproduces Isaiah and the Sermon on the Mount. This study sets
  every King James span aside and does not ask which printing the text follows. One measurement of
  the italic words was made, but its own validity check failed, so by its registered rule it is not
  offered as a test (`docs/italics-plan.md`).
- *The place-name and reading-environment arguments:* Captain Kidd stories, an 1808 map of Africa,
  Vernal Holley's table of place names. Names and biography are outside these methods.

**Summary.** Of the three books the Letter names, two share an unusual density of rare phrases with
the text, and so does much of the imitation-scripture genre they belong to. None shares a copied
passage, a sequence of events, or a passage that two readings judged specific.

### 3.6 Limit

A test is informative about a question only if it gives different answers when the truth differs.
So each borrowing test was first run on texts where the truth is known: nine genuine period
translations of ancient texts, and three period compositions presented as ancient (Amendment 9).

| Test | Does it separate genuine translations from period books written to sound ancient? |
| --- | --- |
| Copied wording | no (p 0.96) |
| Rare phrases | no (p 0.93) |
| Paraphrase | no (p 0.50) |

None of them does. A genuine translation made in the 1820s and a book written in the 1820s to sound
ancient look alike to these searches, because both are period English and both lean on the King
James Bible. "No borrowing found" therefore describes the text: which period books share its
wording, its ideas or its plot, and how unusual that sharing is. It says nothing about the text's
origin, in either direction.

A second limit is practical. In poorly scanned volumes more than half of any real shared phrasing
is lost to OCR error (section 2.2), so the wording searches can miss borrowing from a badly scanned
book.
