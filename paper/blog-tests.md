# Rerunning the Book of Mormon arguments with everything in one place

*Draft, kept current as tests finish. Second write-up, separate from the authorship study. Tests
marked TBD have not been run.*

## Why do this

For almost two hundred years people have argued about the Book of Mormon by pointing at things in
it. This phrase is old English. That name is Hebrew. These place names are towns near Palmyra.
This word switches halfway through. Each argument is a count of something, and almost every one
stops at the count.

A count means little by itself. If a book has 29 place names that look like towns around the Great
Lakes, the question is how many it would have that look like towns around any other lake. If its
grammar matches the 1500s on five features, the question is how many other books printed in the
1820s do the same. Most of these arguments were made by one person with one book and a handful of
comparison texts, because that is what one person could do.

I spent the last few months building something different for the authorship study: about 60,000
English books printed before 1830, hand-typed texts back to 1473, period newspapers, the
manuscripts, Joseph Smith's own writing, a search index over 163 million passages, and language
models that have read nothing written after 1830. That study is finished. All of it is still
sitting here.

So this is the second project. Take the arguments people already make, from every side, and run
each one again with the comparison it never had.

I don't hold a position on where the book came from, and none of these tests can settle that.
What each one can say is narrower: is this feature of the book unusual, and unusual compared with
what?

## The setup: the same four steps for every test

Every test here goes through the same steps, so the results can be read side by side.

1. **State the claim as someone actually made it.** With the source, and with the numbers they
   published. Where I can, I reproduce their number first.
2. **Prove the method on cases where the answer is known.** Before the Book of Mormon is measured,
   the method has to get known cases right. If it cannot find a switch I planted, it has no
   business telling me about a switch in the Book of Mormon. If the check fails, the test stops.
3. **Measure the Book of Mormon and the comparison set the same way.** The comparison set is the
   point. Usually it is hundreds of ordinary books from the library, plus three special groups:
   - books written in Bible style in the 1810s and 1820s (*The Late War*, *The First Book of
     Napoleon* and about two dozen more),
   - real translations of ancient texts into English,
   - Joseph Smith's other dictated texts (the revelations, the Books of Moses and Abraham).
4. **Say what the result does not show.** Every result gets this line.

Three more habits. The rule for what counts as yes and as no is written on a one-page card before
the run. Tests about the book's setting score all three candidate worlds together (ancient
America, the Bible's world, the United States of the 1820s), never one alone. And every file that
came from outside is recorded with its address, so anyone can fetch the same thing and rerun it.

## The arguments, side by side

Five groups. "Before" is what the earlier work compared against. "Here" is what this project
compares against.

### 1. Is the language older than Joseph Smith?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-118 | About 64 word uses and phrases had died out of English before the 1740s | Skousen and Carmack 2018 | dictionary citations, one item at a time | every item searched for its meaning across the whole library, with the same search on Bible-style books | TBD; 48 of 64 items in hand |
| BOM-119 | The grammar is 1500s English: "did go" past tenses at 20% against under 2% in Bible-style books | Carmack 2015 to 2021 | five Bible-style books | every book in the library | **Done** |
| BOM-102 | It reads like a translation; it has Hebrew turns of phrase | Tvedtnes, Skousen and others | examples | real translations against Bible-style imitations | TBD |
| BOM-120 | "Therefore" and "wherefore" switch in the order the book was dictated | Metcalfe 1993 | the book alone | 264 long books by one author | **Done** |

### 2. Where did the words and ideas come from?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-126 | Phrases come from histories of the Revolution; Abinadi follows Bunyan | Donofrio; Davis 2012 | the claimed source alone | the claimed source ranked among every volume in the library | **Done** |
| BOM-122 | Changes to Isaiah follow Adam Clarke's commentary | Townsend 2025; Jackson's reply | Clarke alone | every commentary and annotated Bible held | TBD; 11 passages keyed |
| BOM-124 | New Testament wording appears centuries before Christ | many | single cases | the rate by section, against sermons and period translators | **Done** |
| BOM-123 | "Secret combinations" meant Freemasons in 1830 | Vogel 1993; replies | examples from each side | every use in print 1780 to 1835, by year | TBD |
| BOM-103 | The book answers the religious debates of 1820s New York | Campbell 1831 | a list | the print dates of the nearest passages, topic by topic | TBD |

### 3. How was it produced?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-106 | The text carries the marks of speech, not writing | Davis 2020 and others | description | trial transcripts and sermons taken in short-hand | TBD |
| BOM-127 | Manuscript errors are errors of hearing | Skousen 1998 | one editor's reading | manuscripts known to be copied and known to be dictated | **Done**, fragile |
| BOM-125 | It is unlike other dictated or "received" books | Hales 2019; Dunn 2002 | length and schooling | the same measures on all of them | TBD |
| BOM-121 | Its speakers have more distinct voices than a novelist's characters | Fields and others, about 2021 | four novelists after 1830 | plays and letter novels before 1830, by one author | TBD |
| BOM-107 | It has deliberate chiasmus | Welch 1969; Edwards 2004 | the book and the Bible | the rate in every book | TBD |

### 4. Does the same hand show up elsewhere?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-104 | The Books of Moses and Abraham share the voice; Rigdon wrote the *Lectures on Faith* | Phipps 1977; Reynolds 2005 | small samples | the study's models and encoders | TBD |
| BOM-105, BOM-99 | Smith's revelations and his letters look like two different writers | Holmes 1992; the first study | Smith alone | other writers with two voices (Southcott, Wroe, Trapnel, Snowden, Elias Smith) | **Done** with function words; models TBD |
| BOM-100, BOM-101 | A model can be taught to see the person and not the scripture voice | this project | | the known-answer set from BOM-99 | TBD |

### 5. Whose world is it?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-108 | The names are Hebrew, or Egyptian, or invented | Tvedtnes and others; Wilcox 2013, 2019 | 124 names against census names, Spalding, Tolkien | Hebrew inscriptions, Egyptian, Maya, Nahuatl, treaty signers, period print, four inventing authors | **Done**, with a limit |
| BOM-110 | Place names come from towns around the Great Lakes | Holley; replies | name by name | the same match rule on every other region | **Done** |
| BOM-111 | Its animals, plants and metals do or do not fit ancient America | Coe 1973; Sorenson | lists | Bible, 1820s writing, native texts, Spanish chronicles | TBD |
| BOM-109, BOM-112 | 131 details match the ancient Maya | Dale and Dale 2019; critics | one book, coded by the authors | three checklists, ten texts, coded blind | TBD |
| BOM-113 | 174 of 226 claimed anachronisms are now confirmed | Roper 2025 | one coder, no control | place and period required; Spalding as control | TBD |
| BOM-114 | The weights in Alma 11 match ancient systems | Welch 1999 | five systems searched | random systems as the baseline; number habits against Bible, modern and Mesoamerican texts | **Part done** |
| BOM-115 | Its warfare is ancient, or it is mound-builder forts | Vogel 1986 and others | examples | Bible, Josephus, American wars, conquest accounts | TBD |
| BOM-116 | Its geography fits Mesoamerica, or the Great Lakes | Sorenson and others | argued from verses | every model against random regions | TBD |
| BOM-117 | Uto-Aztecan languages carry Hebrew and Egyptian words | Stubbs 2015 | his pairing alone | his rules on unrelated languages | TBD |

## Results so far

### "Therefore" and "wherefore" (BOM-120)

Brent Metcalfe noticed in 1993 that the book says "therefore" in one long stretch and "wherefore"
in another, and that the stretches follow the order of dictation, not the order of the pages.
Mosiah was dictated first, after the first 116 pages were lost. 1 Nephi was dictated last.

Here are the counts, in dictation order:

| Book | wherefore | therefore |
| --- | --- | --- |
| Mosiah | 1 | 114 |
| Alma | 3 | 288 |
| Helaman | 0 | 63 |
| 3 Nephi | 1 | 77 |
| Mormon | 0 | 19 |
| Ether | 62 | 24 |
| Moroni | 38 | 0 |
| 1 Nephi | 98 | 14 |
| 2 Nephi | 128 | 8 |
| Jacob | 53 | 1 |
| Words of Mormon | 5 | 0 |

One break explains it. Before the break "wherefore" is 2% of the two words. After it, 88%. The
break falls partway through Ether.

Could it be the narrators? Mormon wrote the middle of the book and Nephi the start, so maybe each
had a favourite word. The counts say no. The flip happens inside Moroni's own writing. And Words
of Mormon, which Mormon wrote but which was dictated last, is all "wherefore".

Then the comparison. I ran the same measurement on 264 long books by single authors from the
library. None switches this sharply.

*The check on the method.* I joined pairs of library books that favour different words and asked
the method to find the join. It found it 93% of the time. My first version of this check failed,
because a few library books have a switch of their own inside them and the method found that
instead. I fixed the check before counting the Book of Mormon.

*What it does not show.* Who was choosing the words. A habit that changes in dictation order fits
one person dictating whose habit changed in the spring of 1829. It also fits any account in which
the English wording was produced in that order. And the order of dictation is taken from the
historical record, not tested here.

### Claimed sources, ranked (BOM-126)

Two claims. Thomas Donofrio says phrases in the war chapters come from histories of the American
Revolution, Mercy Otis Warren's and David Ramsay's above all. William Davis says the story of
Abinadi before King Noah follows the trial of Faithful in *The Pilgrim's Progress*. Each was made
by laying the two books side by side.

The first study already had a way to ask this fairly: score every volume in the library the same
way and see where the claimed book lands. It did that for *The Late War*. Here it is for these.

| Book | Shared rare phrases: rank of 204,520 volumes | Closeness in meaning: rank of 30,994 |
| --- | --- | --- |
| Warren's history | none shared | no near passage |
| Ramsay's *History of the American Revolution* | none shared | 24,650 |
| *The Pilgrim's Progress* | 1,073 | 511 |
| Foxe's *Book of Martyrs* | 4,756 | 44 |
| *Paradise Lost* | 6,034 | 816 |
| *The Late War*, for scale | 131 | 17,678 |
| *The First Book of Napoleon*, for scale | 63 | 4,706 |

Warren and Ramsay are in the crowd. For the war chapters, the nearest passages in the whole library
are almost all Josephus: his editions take every one of the top fifteen places.

Bunyan is more interesting. The book as a whole sits closer in meaning than most. But the trial of
Faithful, the scene the claim is about, is not among the hundred nearest passages to any part of
the Abinadi story. Foxe's martyrs are closer for every one of the 44 Abinadi passages, and
Josephus and printed sermons are closer still.

*The check on the method.* With *The Late War* as the target, its nine other printings came out
first to ninth of 204,527. The study's published ranks were reproduced exactly. And the Faithful
scene in one printing of Bunyan found the same scene in other printings 59 times out of 60. One
check had to be rebuilt first: my list of "known copies" of *The Late War* had other histories of
that war mixed in.

*What it does not show.* It does not rule out a few borrowed sentences or a borrowed plot outline;
the comparison of story order was not run. Donofrio's and Davis's own lists of parallels were not
in hand, so their examples were not scored one by one.

### Numbers, and the weights in Alma 11 (BOM-114)

Two questions. The Maya and the Aztecs counted in twenties. Does the Book of Mormon? And Alma 11
describes a system of weights (a senine, a seon twice that, a shum twice that, a limnah worth all
of them) that has been matched to ancient Near Eastern systems. Is the match better than a made-up
system would get?

**Twenties.** Take the round numbers between 20 and 400 in a text and ask what share are multiples
of twenty.

| Text | Share that are multiples of twenty |
| --- | --- |
| Native Mesoamerican texts in English (two of Brinton's translations) | 91% (32 of 35) |
| Clavigero's *History of Mexico* (1787) | 66% (346 of 527) |
| Modern English books | 60% (468 of 780) |
| King James Bible and Josephus | 53% (643 of 1,218) |
| Book of Mormon | 40% (19 of 47) |

The habit survives translation: the native texts show it plainly, and Clavigero, a European
writing about Mexico, shows some. The Book of Mormon shows none. It is below both the Bible and
ordinary English books.

These are small counts: 35 numbers on the Mesoamerican side and 47 in the Book of Mormon.

**The wider number profile did not get an answer.** I also tried to place the book by its whole
number profile (favourite numbers, how years are counted). The method had to sort held-out texts
into their own tradition first, and it did not do that well enough: 71% against a bar of 75%, and
only 3 of 7 Mesoamerican pieces. *The Late War* landed with the Bible seven times out of eight,
which says the profile was reading Bible style, not counting. So the Book of Mormon was not scored
on it.

**Alma 11.** The system's values are 1/8, 1/4, 1/2, 1, 1 1/2, 2, 4 and 7. Against a list of real
systems the best fit is 6 of the 8 values, a tie between English dry and liquid measure and Roman
coins. Hebrew weights fit 2 of 8. Whether 6 of 8 is impressive depends entirely on what "random"
means. If random systems are built from the kinds of steps real systems use (halves and
doublings), 10% of them fit some real system that well. If they are built from arbitrary small
ratios, none of 20,000 does. The fit is the run of doublings, and doubling is what most systems
of measure do.

This part is a pilot. The list of real systems was written from memory and has not been sourced.

*What it does not show.* The twenties result is about counting habit only. The Alma 11 result
says the ratios do not pick out one ancient system; it does not test the names of the units.

### The names (BOM-108)

The book has 163 names that are not in the Bible: Nephi, Moroni, Zarahemla, Coriantumr. People
have called them Hebrew, Egyptian, and made up. I gathered lists to compare them with: 4,673 King
James names, 752 Hebrew names from inscriptions, 8,451 Egyptian names, 2,774 names of Native
American treaty signers, Maya rulers, Aztec names, classical names as printed in English, the
1790 census, and the names four authors invented (Spalding, Swift, Spenser, Macpherson's Ossian).
Then a simple model of letter patterns for each list, and the question: which list does each Book
of Mormon name look most like?

**The limit comes first, because it decides what the test can say.** I took King James names and
wrote them the way scholars transcribe Hebrew. Only 8% of them were still recognised as King
James names. 47% went to the Hebrew-inscription list. So a model like this mostly sorts names by
how they are spelled, not by what language they come from. Comparing "Nephi" in 1830 English
spelling with a Hebrew name in scholarly transcription is not a fair comparison, and I draw no
conclusion from it.

What can be compared fairly is lists that are all in English spelling:

| Names | Closest to King James | Closest to classical | Closest to the 1790 census |
| --- | --- | --- | --- |
| Book of Mormon, non-biblical | 55% | 20% | 11% |
| Spalding, Swift and Ossian together | 19% | 23% | 33% |
| Book of Mormon names with letters shuffled | 38% | 16% | 14% |

The Book of Mormon's names look like King James names far more than three other authors' invented
names do. Jaredite, Nephite and place names all come out the same, about 52 to 56%.

A second count: how many names are one changed letter or one splice away from a King James name
(Nephi, Lehi and Laban are that close)? Book of Mormon 58%. Spalding 35%, Ossian 33%, Spenser 14%,
Swift none. For comparison, real King James names held out of the list score 82%.

*The check on the method.* Held-out names were sorted into their own list 65 to 68% of the time,
against 9 to 20% by chance. One comparison needed its lists cleaned twice before it passed.

*What it does not show.* Where the names come from. Names that look like King James names fit
someone steeped in the King James Bible making up names, and fit Hebrew names put into King James
spelling equally well. This is a test of letters, not of sounds, and the Assyrian list turned out
to be an empty download.

### The Great Lakes place names (BOM-110)

Vernal Holley drew a map in the 1980s pairing Book of Mormon place names with towns around the
Great Lakes: Angola, Alma, Oneida and Onidah, Lehigh and Lehi, about 29 pairs. The argument since
has gone name by name. Did that town exist in 1829? Is that spelling close enough?

The question that was missing is simple. Take the book's 57 place names that are not in the
Bible. Count how many match a place name within 500 km of Palmyra under one fixed rule. Then do
the same around a few hundred other points in the English-speaking world, each with as many place
names to choose from.

| Rule | Matches near Palmyra | Typical far-away region | Where Palmyra ranks |
| --- | --- | --- | --- |
| Strict, within 500 km | 6 of 57 | 9 of 57 | 27th percentile of 232 regions |
| Strict, within 150 km | 2 of 57 | 2 of 57 | 63rd percentile of 374 |
| Loose, within 500 km | 50 of 57 | 49 of 57 | 77th percentile |

Palmyra is an ordinary region. Under the strict rule it does a little worse than most. Under the
loose rule nearly every name matches something nearly everywhere, which is the point: with a loose
enough rule and a big enough map, any list of short names finds partners.

Then the period sources. In the New York gazetteers of 1813 and 1824 and three national ones,
none of the 57 names has a close match among New York entries.

And Holley's own pairs. Nine of the 29 pass the strict rule. Seven of those are Bible names that
are identical in both lists (Jerusalem, Jordan). The other two are Angola and Alma, both towns
named after 1830.

*The check on the method.* A set of New York names with one letter changed was found in 20 of 20
tries. The first version of the spelling check failed, with only twelve test pairs; I rebuilt it
on 4,365 variant spellings printed in an 1823 gazetteer. No single threshold was both sensitive
and strict, so I report two.

*What it does not show.* It cannot rule out one or two real borrowings; Oneida and Onidah is a
single pair and no count can speak to it. It uses today's place names for the regional comparison
and period gazetteers only for New York. Holley's list came from one web page summarising it.

### New Testament wording before Christ (BOM-124)

Critics point out that Nephi and Alma, centuries before Christ, use phrases from Paul and John.
Believers answer that a translator reaches for familiar wording. Both sides argue it case by case.
Nobody had measured how much there is, or compared it with what a translator of the period
actually did.

The measure: phrases of four or five words that are in the King James New Testament and not in
the Old Testament, counted per 10,000 words. Chapters that quote Isaiah or the Sermon on the Mount
at length are set aside.

| Text | New Testament-only phrases per 10,000 words |
| --- | --- |
| Ordinary non-religious books, 1800 to 1830 | 14 |
| Bible-style books (*The Late War* and a dozen more), typical | 54 |
| Sale's Koran (1734 translation) | 57 |
| Sermons, 1800 to 1830, typical | 64 |
| Josephus on Old Testament times (Whiston's translation) | 74 |
| **Book of Mormon before Christ** (1 Nephi to Helaman, and Ether) | **195** |
| Book of Moses, the text added to Genesis | 220 |
| Book of Mormon from 4 Nephi on | 234 |
| Joseph Smith's revelations | 261 |
| 3 Nephi | 281 |

The pre-Christian parts of the book carry about three times the New Testament wording of the two
period translators, and of the Bible-style books. Among 300 sermons they sit at the 93rd
percentile: high, though some preachers went higher. The closest match in the table is Joseph
Smith's own addition to Genesis.

Is there a jump when Christ arrives? The rate rises by about a third at 3 Nephi (somewhere
between 4% and 65%). That is under the bar I set for calling it a step, so: cannot tell.

No one New Testament book dominates. The Gospels, Paul and Hebrews each supply about their share.

*The check on the method.* Every New Testament book, scored against phrase lists built without
it, outranked every Old Testament book. Sermons outranked non-religious books 88% of the time.

*What it does not show.* Shared wording cannot tell a translator using familiar phrases from an
author composing with them. What the comparison adds is scale: Whiston and Sale, translating
ancient non-Christian texts into the same Bible-soaked English, used a third as much. It counts
exact phrases only, not paraphrase.

### The grammar of the 1500s (BOM-119)

Stanford Carmack's strongest number is about a small word. The Book of Mormon says "they did go"
and "he did preach" where ordinary English says "they went" and "he preached", and it does so in
about a fifth of its past tenses. That habit peaked in English around 1550 to 1600 and had mostly
died by 1700. The King James Bible does it under 2% of the time. So, the argument goes, this is
not Bible imitation; nobody imitating the Bible would produce it. His comparison was five
Bible-style books.

First I reproduced his numbers. Book of Mormon: 19.4% (he reports 20.2%). King James Bible: 1.6%
(he reports 1.7%). Joseph Smith's 1832 history: none in 98 past tenses (he reports none in 88).

Then every book in the library, 207,471 of them.

| Printed | Books at or above the Book of Mormon's rate | Books counted |
| --- | --- | --- |
| 1500 to 1549 | 9 | 576 |
| 1550 to 1599 | 72 | 2,636 |
| 1600 to 1649 | 75 | 7,767 |
| 1650 to 1699 | 58 | 16,008 |
| 1700 to 1749 | 0 | 1,883 |
| 1750 to 1799 | 14 | 45,013 |
| 1800 to 1830 | 15 | 132,826 |

Carmack is right about the shape. This is a 1500s and 1600s habit, and after 1700 it nearly
vanishes: 29 books out of about 180,000.

What are the 29? Fourteen are reprints of books written before 1700. Nine are the articles of
impeachment against Warren Hastings and Burke's works that contain them, where "did" is the
language of an indictment ("the said Warren Hastings did receive"). Two are copies of a hymn book,
one more hymn book, a book of ballads written "in imitation of the antient", a comic poem and a
short play.

And one more, which matters most. *Chronicles of Eri* (1822) is a book in Bible style presented as
a translation of ancient Irish records. Its second volume says "did" in 19.3% of its past tenses,
level with the Book of Mormon. Carmack himself had allowed that it might. So one author writing
mock-ancient scripture in the 1820s did produce this rate.

But the "did" rate is one feature of ten. *Chronicles of Eri* has none of the others. No book
printed between 1780 and 1830 matches the Book of Mormon on all ten together; the most any single
book matches at once is three.

Three more comparisons:

- **Bible-style books:** none of the 20 in the library reaches the rate.
- **Real translations:** none of the 341 marked as translations reaches it.
- **Joseph Smith's other dictated texts:** the revelations, the Book of Moses, the Abraham
  manuscripts, his letters and his 1832 history all sit between 0% and 1.6%.

That last one is the surprise. Whatever produced the "did" in the Book of Mormon, it is absent
from everything else he dictated, including scripture dictated a year later.

*The check on the method.* The rate separates books of 1540 to 1620 from books of 1760 to 1830
correctly 89% of the time. I read 60 of the extracted "did" phrases; 59 were right. One bug was
found and fixed after a first count of the Book of Mormon came out low (the verb list had dropped
"go" and "bring"); the checks were rerun after the fix.

*What it does not show.* Who composed the text or how. The past-tense count is an approximation.
Which books are reprints was judged from titles and authors' dates, not by reading them. The
library is thin for 1700 to 1780.

### Heard or copied? The manuscript's corrections (BOM-127)

Royal Skousen argues that the mistakes in the original manuscript are mistakes of the ear. A
scribe taking dictation writes "their" for "there". A scribe copying from a page skips a line. If
the corrections are ear mistakes, the text was dictated. His case rests on his own reading of the
manuscript, with nothing to compare it to.

There is something to compare it to. The printer's manuscript is a copy of the original, made by
the same scribe, so its mistakes are copying mistakes. I sorted every one-word correction in each
by rule.

| Manuscript | Sound-alike corrections | One-word corrections |
| --- | --- | --- |
| Original manuscript (dictated, by the claim) | 28 (3.9%) | 720 |
| Printer's manuscript (a copy) | 5 (0.6%) | 854 |
| Oliver Cowdery in the original | 28 | 615 |
| Oliver Cowdery in the printer's manuscript | 5 | 759 |

On its face that is Skousen's result: the same scribe makes six times as many ear mistakes in the
original as in the copy.

Now the weakness. Twenty-three of the 28 are one pair of words, "there" and "their", all in
Cowdery's hand. Take that pair out and the original has 5 in 720, the copies 6 in 1,114. No
difference.

So the finding is real and narrow. It is one confusion, made over and over by one scribe, in the
manuscript he is said to have taken by ear, and hardly at all when he copied it.

Two more things cut against a simple reading. The first draft of the Book of Moses was certainly
dictated, and it shows almost no ear mistakes (1 in 168). And the original manuscript has
eye-skips too, 14 of them.

Names: 69 of 86 names are spelled the first time the way they were printed. Of the 17 that are
not, 10 differ only in a vowel.

*The check on the method.* The sound rule joined 45 of 49 known sound-alike pairs and none of 40
others. Planted mistakes of each kind were recovered 97 to 100% of the time.

*What it does not show.* Who composed the text; this is only about how words reached the page.
It reads the published transcripts, not the manuscript pages, so letters written over other
letters are missed.

### Prophets in two voices (BOM-105, BOM-99)

The first study's central finding was awkward. Joseph Smith's revelations look like the Book of
Mormon. His letters do not look like either. David Holmes found the same split in 1992 and called
it a "prophetic voice". The obvious question is whether that split is something about Joseph
Smith, or something that happens to anyone who writes as a prophet on Monday and writes to a
friend on Tuesday.

So I looked for other people who did both, with enough of each to measure. Six made the cut:

| Writer | Scripture voice | Ordinary voice |
| --- | --- | --- |
| Joseph Smith | revelations, 65,000 words | letters and journal, 30,000 |
| John Wroe (English prophet, 1820s) | 255,000 | 6,000 |
| Joanna Southcott (English prophet, 1790s on) | 53,000 | 24,000 |
| Anna Trapnel (English prophet, 1650s) | 31,000 | 31,000 |
| Richard Snowden (wrote a Bible-style history) | 56,000 | 142,000 |
| Elias Smith (wrote a Bible-style tract) | 16,000 | 108,000 |

For each I measured how far apart the two voices are, using the small common words (the, of, and,
that) that writers use without thinking. The yardstick is the distance between two different
people writing in the same voice. A gap of 1.0 means: this writer's two voices are as far apart
as two strangers.

Joseph Smith's gap is 0.92. The other five run from 0.86 to 1.22. His is the second smallest.

So on this measure the split is ordinary. Everyone who changes voice looks like a different
person. Joseph Smith does it no more than Joanna Southcott or a man writing a mock-biblical
history of the Revolution.

Can you still find the person across the gap? Sometimes. For three of the other five writers,
most of their scripture-voice passages were matched to their own ordinary writing. That number
moves when Bible phrases or archaic words are taken out, so I would not lean on it.

*The check on the method.* Within one voice, passages went to their own writer 92 to 93% of the
time. A seventh writer, Edward Burrough, was dropped before any cross-voice number was computed:
none of his passages matched him, and his "ordinary" sample turned out to include a report he may
not have written alone.

*What it does not show.* This uses common words only. The first study's finding came from language
models and a style encoder, and those have not been run on this set yet. Four of the six writers
are read from uncorrected scans. Six is a small group. I labelled the voices myself.

## What I would want a reader to take from the whole set

TBD. This section gets written when enough tests are in to see a pattern, or to see that there
isn't one.

## How to check any of this

Every test has an issue on GitHub with its plan (BOM-99 to BOM-127), a command in the run guide
(`eval/README.md`), and a result file under `data/lab/`. Every outside source is listed with its
address in `data/lab/sources.json`. The texts under copyright are not published; the steps to
obtain them are in `docs/replication.md`.
