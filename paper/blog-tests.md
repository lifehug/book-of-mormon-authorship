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

### How each test is told

Most of these tests did not work the first time. I would rather show that than hide it, because
the failures say as much about the original arguments as the successes do. So every test below is
told in the order it happened:

1. **The claim**, as the person made it.
2. **Their way first**: their method, and whether I could reproduce their number or check their
   examples. Where I have not bought their book, it says so.
3. **What I tried**: the comparison they did not have.
4. **The check**: the known cases that had to come out right before the Book of Mormon was
   measured.
5. **When it failed: why, and what I changed.** Each wrong turn in order: what went wrong, what
   that told me, what I changed, and why the change still asks the same question. Where I changed
   something after seeing a result, I say so, because that kind of change counts for less.
6. **The result**, always next to what it is compared with.
7. **What it means, and what it doesn't.**
8. **What's left.**

## The arguments, side by side

Five groups. "Before" is what the earlier work compared against. "Here" is what this project
compares against.

### 1. Is the language older than Joseph Smith?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-118 | About 64 word uses and phrases had died out of English before the 1740s | Skousen and Carmack 2018 | dictionary citations, one item at a time | every item searched for its meaning across the whole library, with the same search on Bible-style books | Of 34 items I could test, 21 are still in use in 1740-1830, 2 turn up once, 11 not found; checked by two AI readings and my own, not by a person |
| BOM-119 | The grammar is 1500s English: "did go" past tenses at 20% against under 2% in Bible-style books | Carmack 2015 to 2021 | five Bible-style books | every book in the library | **Done** |
| BOM-102 | It reads like a translation; it has Hebrew turns of phrase | Tvedtnes, Skousen and others | examples | real translations against Bible-style imitations | **Hebraisms done; translation check failed** |
| BOM-120 | "Therefore" and "wherefore" switch in the order the book was dictated | Metcalfe 1993 | the book alone | 264 long books by one author | **Done** |

### 2. Where did the words and ideas come from?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-126 | Phrases come from histories of the Revolution; Abinadi follows Bunyan | Donofrio; Davis 2012 | the claimed source alone | the claimed source ranked among every volume in the library | **Done** |
| BOM-122 | Changes to Isaiah follow Adam Clarke's commentary | Townsend 2025; Jackson's reply | Clarke alone | every commentary and annotated Bible held | **Done** |
| BOM-124 | New Testament wording appears centuries before Christ | many | single cases | the rate by section, against sermons and period translators | **Done** |
| BOM-123 | "Secret combinations" meant Freemasons in 1830 | Vogel 1993; replies | examples from each side | every use in print 1780 to 1835, by year | **Done: Masonic in about 4 of 10 uses by 1827-1830, not almost all** |
| BOM-103 | The book answers the religious debates of 1820s New York | Campbell 1831 | a list | the print dates of the nearest passages, topic by topic | **Check failed twice; not scored** |

### 3. How was it produced?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-106 | The text carries the marks of speech, not writing | Davis 2020 and others | description | trial transcripts and sermons taken in short-hand | **Done** |
| BOM-127 | Manuscript errors are errors of hearing | Skousen 1998 | one editor's reading | manuscripts known to be copied and known to be dictated | **Done**, fragile |
| BOM-125 | It is unlike other dictated or "received" books | Hales 2019; Dunn 2002 | length and schooling | the same measures on all of them | **Done** |
| BOM-121 | Its speakers have more distinct voices than a novelist's characters | Fields and others, about 2021 | four novelists (Austen, Cooper, Dickens, Twain) | plays of 1660 to 1700, by one author | **Done** |
| BOM-107 | It has deliberate chiasmus | Welch 1969; Edwards 2004 | the book and the Bible | the rate in every book | **Done** |

### 4. Does the same hand show up elsewhere?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-104 | The Books of Moses and Abraham share the voice; Rigdon wrote the *Lectures on Faith* | Phipps 1977; Reynolds 2005 | small samples | the study's models and encoders | **Done, weak** |
| BOM-105, BOM-99 | Smith's revelations and his letters look like two different writers | Holmes 1992; the first study | Smith alone | other writers with two voices (Southcott, Wroe, Trapnel, Snowden, Elias Smith) | **Done** on three measures; the author models do not give a stable answer |
| BOM-100, BOM-101 | A model can be taught to see the person and not the scripture voice | this project | | the known-answer set from BOM-99 | BOM-100 **done: no gain**; BOM-101 **done: no gain at the size I could train** |

### 5. Whose world is it?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-108 | The names are Hebrew, or Egyptian, or invented | Tvedtnes and others; Wilcox 2013, 2019 | 124 names against census names, Spalding, Tolkien | Hebrew inscriptions, Egyptian, Maya, Nahuatl, treaty signers, period print, four inventing authors | **Done**, with a limit |
| BOM-110 | Place names come from towns around the Great Lakes | Holley; replies | name by name | the same match rule on every other region | **Done** |
| BOM-111 | Its animals, plants and metals do or do not fit ancient America | Coe 1973; Sorenson | lists | Bible, 1820s writing, native texts, Spanish chronicles | **Done** |
| BOM-109, BOM-112 | 131 details match the ancient Maya | Dale and Dale 2019; critics | one book, coded by the authors | three checklists, ten texts, coded blind | BOM-112 **arithmetic done; reader's check missed, controls not judged**; BOM-109 **both designs' checks failed; not scored** |
| BOM-113 | 174 of 226 claimed anachronisms are now confirmed | Roper 2025 | one coder, no control | place and period required; Spalding as control | **Counts done; reader's check passed; reading queued** |
| BOM-114 | The weights in Alma 11 match ancient systems | Welch 1999 | five systems searched | random systems as the baseline; number habits against Bible, modern and Mesoamerican texts | **Part done** |
| BOM-115 | Its warfare is ancient, or it is mound-builder forts | Vogel 1986 and others | examples | Bible, Josephus, American wars, conquest accounts | **Done** |
| BOM-116 | Its geography fits Mesoamerica, or the Great Lakes | Sorenson and others | argued from verses | every model against random regions; second design on real terrain | **Both designs' checks failed; not scored on fit; consistency part queued** |
| BOM-117 | Uto-Aztecan languages carry Hebrew and Egyptian words | Stubbs 2015 | his pairing alone | his sets checked against his own rules; word lists against unrelated and borrowing pairs | **Yaqui-Coptic: no layer of the claimed size; the rest cannot tell** |

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

Two cautions on that. Nine of the ten features, as I counted them, barely separate early books
from late ones in the first place, so "no book matches all ten" is a weaker statement than it
sounds. And the "did" rate I reproduced, 19.4 percent, matches the 20.2 in a published summary
of Carmack's work, but the abstract of his 2015 article says 27 percent. I have not worked out
which way of counting gives which, so call that one partly reproduced.

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

**Then the same six writers with the first study's own tools.** Common words are a blunt
instrument, and the first study's finding came from its style encoders. So I ran both encoders on
the same set.

| | Common words | First encoder | Second encoder |
| --- | --- | --- | --- |
| Joseph Smith's gap between voices | 0.92 | 0.58 | 0.64 |
| The other five writers | 0.86 to 1.22 | 0.37 to 0.75 | 0.31 to 0.82 |
| His rank of six (1 = largest gap) | 5th | 4th | 3rd |
| Other writers found across their two voices | 3 of 5 | 5 of 5 | 5 of 5 |

Same answer. His gap sits in the middle of the group under both encoders.

The encoders also do something the common words could not. Every gap is under 1.0, which means
each writer's two voices are closer to each other than two different writers are. And all five of
the other writers were found across their voices. So the encoders do keep hold of the person when
the voice changes. They find Joseph Smith across his too: most of his revelations are matched to
his letters, and most of his letters to his revelations.

One detail goes the other way. His revelations are slightly closer to John Wroe's prophecies than
to his own letters (0.75 against 0.73). Scripture voice still pulls scripture voice together.

*What it does not show.* Six writers is a small group, so "typical" is a weak word. Four are read
from uncorrected scans. An AI helper labelled which passages are which voice. Two of the six
(Southcott, Elias Smith) had text in the encoders' training; leaving them out does not change
where Joseph Smith falls.

**And with the author models, which do not settle it.** The other half of the first study's
finding came from language models tuned on one author at a time. I tuned the smallest one on each
writer's ordinary voice and asked whether it recognises that writer's scripture voice.

| Training text per model | Joseph Smith's letters model finds his revelations | Other writers |
| --- | --- | --- |
| The study's small dose (about 2,000 tokens) | 0 of 51 | 7% to 89% |
| Four times that, without Wroe | 45 of 46 | 44% to 95% |

With a little text his letters model finds none of his revelations, the worst of the six. With
four times as much it finds nearly all of them, the best of the five. The small-dose run only just
passed its own check, and one writer's model (Snowden's) was soaking up more than half of
everybody's scripture passages. My reading is that the small-dose result is an artifact of too
little training text. That reading was made after seeing both runs, so the fair summary is:
cannot tell, leaning the same way as the encoders.

### Warfare (BOM-115)

About a fifth of the Book of Mormon is war. Is it the Bible's kind of war, the American kind its
first readers knew, the conquest of Mexico, or the earthwork forts that 1820s writers imagined
the mound builders defending?

I took the war passages of each text by one rule and counted a fixed list of war words: weapons,
armour, fortifications, how armies are organised.

| Tradition | How close the Book of Mormon's war vocabulary is (1.0 = identical) |
| --- | --- |
| Bible and Josephus | 0.66 |
| Mound-builder and Indian-war writing | 0.62 |
| Conquest of Mexico | 0.62 |
| American wars, 1775 to 1815 | 0.40 |

It is nearest the Bible and Josephus, but not by enough to separate the first three. What is
clear is the last row: it is not the American wars. There are no muskets, cannon, guns, bayonets
or tomahawks, and no months named.

The controls matter here. *The Late War* is written in Bible style about the War of 1812, and it
lands with the American wars. Spalding's novel lands with the mound-builder writing. Both sit
further from the Bible than the Book of Mormon does. So Bible diction does not by itself drag a
war story to the Bible.

Some words are its own. "Title of liberty", "arm-shield" and "thick clothing" appear in none of
the comparison traditions. "Cimeter", "heap of earth", "picket" and "decoy" are in it and not in
the Bible or Josephus. And the Bible has things it lacks: spear, dagger, helmet, trench, garrison,
ambush, tribute.

**The fortifications.** Alma describes cities fortified with a ditch, a bank of earth, timbers,
pickets and towers. Dan Vogel and others have pointed to 1820s descriptions of mound-builder forts
with picketed earth walls. I looked for those five things together. The Book of Mormon has all
five inside 507 words. The next tightest is Josiah Priest's book, at 1,419 words. In 300 ordinary
library books the tightest is 3,204. No comparison text packs them as close as the Book of Mormon
does, though Priest, writing about American antiquities, comes nearest.

**Army sizes.** The typical army figure in the Book of Mormon is 6,000, against 1,000 in the
Bible and Josephus, 500 in the American wars and 200 in the conquest of Mexico. That rests on
eleven figures.

*The check on the method.* Held-out texts landed with their own tradition 85% of the time. The
mound-builder group is weak: five texts, and their war passages are mostly Indian wars and travel,
not descriptions of earthworks. The native annals were too short to form a group at all.

*What it does not show.* Words in war passages, not how anyone fought. It cannot tell the top
three traditions apart.

### The inventory of things (BOM-111)

Every book set somewhere mentions the things of that place: its animals, crops, metals, tools,
buildings, clothes. I made a list of about 2,000 such things, from the Bible's world, from Mexico
and Central America, from New England, and counted them in each text.

| World | How close the Book of Mormon's inventory is (1.0 = identical) |
| --- | --- |
| Bible and Josephus | 0.50 |
| Ordinary English books of the period | 0.40 |
| American writing about Indians and antiquities | 0.28 |
| Mesoamerica (native texts and Spanish chronicles) | 0.17 |

The Bible's world, clearly, on every version of the test. Ten of the book's twelve large sections
land there and none lands in Mesoamerica.

The plainest number is this one. Count the words for things that existed only in the Americas
before Columbus: maize, cacao, turkey, jaguar, jade, obsidian, maguey, tobacco, squash.

| Texts | New World things per 10,000 words |
| --- | --- |
| Native Mesoamerican texts and Spanish chronicles | 5 to 49 |
| American writing about Indians | 0.5 to 9.5 |
| Bible and Josephus | 0 to 0.13 |
| Book of Mormon | 0 |

**What about a translator's word choices?** A translator might write "sword" for an obsidian-edged
club or "corn" for maize. I checked what the real translators of Bernal Díaz, Clavigero and the
native texts did. They mostly kept the native things visible: Old World stand-in words are 2 to
10% of their uses. Removing every such word from the Book of Mormon (sword, wine, brass and
seventeen others) changes the picture by one or two hundredths.

**What is missing.** Nineteen things appear in at least three quarters of the Mesoamerican texts
and nowhere in the Book of Mormon: maize, feathers, flowers, drums, flutes, deer, eagles, maguey
among them. But 83 things common in the Bible texts are missing too, so the book is not simply
the Bible's inventory either. And it has five words nobody can classify: cureloms, cumoms, neas,
sheum and ziff.

*The check on the method.* Held out one at a time, 154 of 173 comparison texts landed in their
own world. One check failed: a Mesoamerican profile built only from native texts does not
recognise the Spanish chronicles, so "Mesoamerica" here partly means "how Spaniards and their
translators wrote about it".

*What it does not show.* A word is not a thing: many of the book's most frequent items are
figures of speech (seed, flesh, church). The lists were written from memory. Only eight texts
stand for Mesoamerica. And this says nothing about archaeology. It compares vocabularies.

### Do the speakers have their own voices? (BOM-121)

The claim: Nephi, Alma, Mormon and the rest differ from one another, in the small common words
nobody chooses on purpose, more than a novelist's characters do. The published comparison was
four novelists: Austen, Cooper, Dickens and Twain. Their titles, word list and values are not
published, so I could not rerun it their way; what follows is the same claim tested my way.

I compared with what a writer of the time could have known: 354 plays printed between 1660 and
1700, where every speech carries its speaker's name. Each voice is 2,000 words of one speaker.
The spread of five voices is how far apart they sit on the 150 most common words.

| Five voices taken from | Spread |
| --- | --- |
| One play (one author's characters) | 0.72 |
| The leads of five plays by one author | 0.79 |
| The leads of five plays by five authors | 0.84 |
| **The Book of Mormon's five largest speakers** | **1.07** |

So the book's speakers are further apart than the characters of any one playwright, and further
apart than five different playwrights. Taken alone that would look like the claim confirmed.

It is not that simple, and the next table is why.

| What | Spread |
| --- | --- |
| Random 2,000-word stretches of the Book of Mormon, speakers ignored | 0.99 |
| Random stretches of one play, speakers ignored | 0.67 |
| Four Bible-style books of 1810 to 1829, by four different people | 0.97 |
| One writer in two kinds of writing (six writers, Joseph Smith among them) | 0.94 to 1.16 |

Any five stretches of the book are almost as far apart as its five speakers. Knowing who is
speaking adds 8 percent. The book is simply a varied book: sermon, war story, letter, prophecy,
quoted scripture. And a spread of about 1.0 is what one person produces by changing the kind of
writing, as Joseph Smith's own letters against his revelations show (0.97).

What I take from it: the speakers do differ more than a playwright's characters, and most of
that difference is the book changing subject and kind, not the speaker changing. This test
cannot tell several hands from one hand writing in several kinds.

Limits. The check that the measure can tell different authors from one author's characters
missed at my first setting (1,000 words a voice) and passed, narrowly, only after I doubled the
length. Plays are verse and dialogue, not prose narrative. Who speaks each verse of the Book of
Mormon was labelled by an AI model. The published study's own numbers are not available in
full, so this tests the claim, it does not reproduce the paper.

### Do its debates date to the 1820s? (BOM-103)

Alexander Campbell said in 1831 that the book settles "every error and almost every truth
discussed in New York for the last ten years": infant baptism, the trinity, the fall, free
masonry, who may preach for pay. If that is right, the passages nearest in meaning to the book's
debate passages should have been printed in the 1820s more than elsewhere.

The plan: take the passages on 17 such topics, find the 100 nearest passages among 13 million
from religious books printed 1640 to 1829, and see which decade they pile up in.

First the same thing on books whose date I know. It did not work.

| Books printed in | Dated to within a decade of the truth |
| --- | --- |
| 1650s | 7 of 20 |
| 1740s | 12 of 20 |
| 1780s | 10 of 20 |
| 1820s | 5 of 20 |
| 1780 to 1799, clean hand-typed text | 0 of 20 |

I had said 12 of 20 in every group. Only one group got there, so I did not run the Book of
Mormon at all.

Why it failed is worth a line. The library is lopsided: 3.9 million religious passages from the
1820s and only 22,000 to 49,000 from each decade of the middle 1700s. I divided by each decade's
size to be fair, and that made the thin decades win on a handful of neighbours. Nearly
everything in modern spelling got dated to the 1750s. The clean copy of the 1830 text would
have landed there too, whatever it says.

So I tried once more, and said beforehand it would be the last try: search 1780 to 1829 only,
and give every decade the same number of passages.

| Books printed in | Dated to their own or the next-door decade | Chance |
| --- | --- | --- |
| 1780s | 8 of 20 | 8 |
| 1790s | 11 of 20 | 12 |
| 1800s | 10 of 20 | 12 |
| 1810s | 20 of 20 | 12 |
| 1820s | 18 of 20 | 8 |
| 1780 to 1809, clean hand-typed text | 3 of 20 | 10 |
| Written before 1760, reprinted 1780 to 1829 | 15 of 20 land in the 1810s | |

Now everything lands late instead of in the 1750s. The 1810s and 1820s books "pass" only because
all books land there, including ones written a century earlier. Had I run the Book of Mormon it
would have come out 1810s or 1820s, and so would a reprint of a sermon from 1700. Finding the
nearest passages by meaning does not tell you when something was printed. I did not run the Book
of Mormon.

One small thing did work, because it is only counting. Five of the book's doctrinal phrases, by
decade, in 31,901 religious books:

| Phrase (times in the Book of Mormon) | First seen | In the 1820s |
| --- | --- | --- |
| infinite atonement (3) | 1730s | about as common as in any decade since |
| plan of salvation (3) | 1740s | steady since the 1750s |
| probationary state (3) | 1740s | steady since 1800 |
| demands of justice (4) | 1640s | commonest in the 1720s and 1740s |
| fall of man (5) | throughout | |

None of the five is new in the 1820s. They were all in print before Joseph Smith's grandparents
were born. That neither supports nor undoes Campbell: he said the book took sides in the
arguments of his day, not that it coined their words.

So Campbell's claim is untested here. It needs a different tool, and any new one has to show
first that an old reprint does not come out looking new.

**A third design, after going back to the claim.** Alexander Campbell wrote in 1831 that the
book decides "every error and almost every truth discussed in New York for the last ten
years" and named twenty. He compared them with nothing. So first his list, his way: is each
topic in the book, and was it any less discussed in other times?

Thirteen of his twenty are in the 1830 text by my search rules. Seven are not there at any
real rate: infant baptism, the trinity, regeneration, justification, transubstantiation,
penance and the call to the ministry all come in under 3 mentions per 100,000 words. Then the
comparison he did not make. Of his twenty topics, English religious print of the 1640s
discusses 13, the 1740s to 60s 15, the late 1700s 11, and American print of 1815 to 1829, 13.
The 1640s cover his list as fully as the 1820s do. One topic is different: oath-bound secret
societies, which he called freemasonry, are in the book and in none of the earlier bodies.
That fits the "secret combinations" test, where the newspapers jump in 1828.

So the list, as a list, is not a fingerprint of the 1820s. Most of it is what Protestants
argued about for two hundred years.

Then my own test: take the topics from surveys of sects written in each period, not from the
book, and ask whether a text's mix of topics places it in its era. It does not. Known texts
landed in their own era 20 to 50 percent of the time, and I had set 55. The old reprints no
longer land late, which was the fault of the second design, but they scatter. Joseph Smith's
own revelations of 1828 to 1835 were pulled early by their King James wording, one block of
four landing where it should. Three designs now, three misses, and I did not score the book.

I think that is itself the finding, and it is about the claim more than about my tools. If
texts whose dates I know cannot be placed by which doctrines they discuss, then "it discusses
the questions of the 1820s" cannot carry the weight Campbell put on it, and neither can "these
are timeless questions" be shown this way. What is left that could be tested is narrower:
which side the book takes on each question, and the one topic that really is new.

### Chiasmus, with something to compare it to (BOM-107)

A chiasm says things and then says them again in reverse order: A, B, C, then C, B, A. Welch
found them in the Book of Mormon in 1969 and they have been offered ever since as a mark of
ancient Hebrew writing. What nobody had was the rate in everything else.

I wrote one fixed rule: reduce the text to its content words, and count every place where three
or more words repeat in mirror order around a centre. Then I ran it on the Book of Mormon, the
King James Bible, 360 library books, 120 translations, 25 Bible-style books and Joseph Smith's
other dictations.

| Text | Chiasms per 10,000 words (three levels or more, 40 words each side) |
| --- | --- |
| Book of Mormon | 34.7 |
| King James Bible | 36.4 |
| Library books | 34.7 |
| Translations | 36.6 |
| Bible-style books | 37.4 |
| Joseph Smith's other dictations | 37.4 |

The Book of Mormon sits in the middle of the library, at the 48th percentile. Then the control
that matters: count the same repeated words in the same places but in plain repeated order (A,
B, C, A, B, C). If mirror order were being used on purpose, it should beat plain order. In the
Book of Mormon mirror order comes out at 0.88 of plain order, in the King James Bible 0.94, in
the library 0.95. Nothing is above 1.

Alma 36 is the famous one. By this rule its deepest mirror run is 5 levels in a tight window,
and only 3 library passages in 1,000 of the same length do that. But the same chapter read in
plain order reaches 6. It is a very repetitive chapter, in both directions.

What I take from it: counted by repeated words, the Book of Mormon has no more chiasmus than an
ordinary book of its time, and neither does the Bible. That second half is the limit. A rule
that cannot tell the Bible from ordinary prose is counting word repetition, not the idea-level
patterns Welch meant. So this says the word-level counts do not set the book apart. It does not
say the hand-identified chiasms are not there.

The rule found 4 of 5 well-known Bible chiasms and 300 of 300 planted ones. I changed two things
after the first check failed and before the Book of Mormon was counted: a fix to how words are
reduced, and the plain-order control in place of shuffling sentences.

### Other books that were dictated or "received" (BOM-125)

The claim, made most fully by Brian Hales: the Book of Mormon is too long and too complex to
have been dictated in a few months by a farmhand with little schooling. The usual comparison is
to what an ordinary writer can do. A fairer one is to other long books that were dictated, or
that their makers said were given to them.

I collected 23: Milton's *Paradise Lost* (dictated blind), five works of Swedenborg, Andrew
Jackson Davis's *Principles of Nature* (dictated in trance by a man of 19 with a few months of
school), *Oahspe*, the Koran in Sale's English, Mary Baker Eddy, the Patience Worth novels (a
St. Louis housewife at a ouija board), three late novels Henry James dictated, and the English
prophets Southcott, Brothers and Wroe. Then I measured every one the same way, 20,000 words at
a time.

| Measure | Book of Mormon | The 23, middle | The 23, lowest to highest |
| --- | --- | --- | --- |
| Different words in 20,000 | 1,679 | 2,625 | 1,672 to 4,226 |
| Words per sentence | 39.9 | 24.4 | 11.3 to 44.8 |
| School grade needed to read it | 15.8 | 10.3 | 4.1 to 18.3 |
| Names in 20,000 words | 75 | 106 | 30 to 442 |
| Share of words in King James phrases | 24% | 2% | 0.4% to 26% |
| Share that repeats its own earlier phrases | 7.0% | 0.9% | 0 to 4.5% |

On eight of ten measures the Book of Mormon is inside the range of the other received books. On
two it is outside, and both point the same way: it has the narrowest vocabulary of all 24 but
one, and it repeats its own six-word phrases more than any of them. A typical book of the
period uses 3,753 different words in 20,000. The Book of Mormon uses 1,679. Its long sentences
are mostly the 1830 printer's punctuation.

So by these measures it is not more complex than other dictated and received books. It is a
long book made from few words, much repeated, with a quarter of it in the Bible's phrasing.

That does not answer Hales. His case rests on things this cannot count: the plot holding
together across 265,000 words, the flashbacks, the calendar, the speed. Counting words says
nothing about whether a story is consistent. And I could not get his own table of sixteen
texts, so this is his question with my list. Not included, because they are under copyright:
*A Course in Miracles* and the Seth books. *Oahspe* is the first volume only.

### The geography (BOM-116)

People have fitted the book's lands to southern Mexico, to western New York, to the Mississippi
valley and to the whole hemisphere. Each map looks reasonable to the person who drew it. What I
wanted to know is whether any real region fits the book's own directions better than a random
patch of the earth does.

One fixed rule pulls out every sentence that places one named place against another: north of,
east of, by the sea, near, so many days' journey. Then, for a region, a program looks for the
best real sites for each place, and I compare the region's score with 400 random regions.

First the texts where I know the answer. Step one worked. Put the Bible's places at their true
coordinates and 71 percent of its statements hold, against 29 percent when the same places are
scattered at random. So the sentences do carry real geography.

Step two did not work.

| Text | Its real region | Random regions that fit as well or better |
| --- | --- | --- |
| The Bible's narrative | Palestine | 149 of 398 |
| Josephus, *Antiquities* | Palestine | 119 |
| Josephus, *War* | Palestine | 296 |
| Clavigero's history of Mexico | Mexico | 50 |
| Ramsay's American Revolution | Philadelphia | 327 |

If the method cannot find Palestine from the Bible, it cannot find anything from the Book of
Mormon. Given a few hundred towns to choose from, the program can make almost any set of
directions fit almost anywhere. Which is, I think, the real finding: it is easy to fit a map,
and a good-looking fit to one region is not evidence until someone shows how badly the same
text fits everywhere else. I did not score the Book of Mormon against any region.

What I can say about the book's own statements: the rule found 33 of them about 23 places (14
directions, 12 by the sea, 6 near, 1 narrow neck), and none contradicts another. They can all be
true at once on a flat map. But they are few, and the rule misses the long description in Alma
22 because it runs across sentences.

A fair test needs each model's own published placements (Sorenson's map, the Heartland maps),
scored against random placements of the same places, the way the Bible check worked.

**A second design, with real terrain.** The first try used 33 short statements. This time a model
read every passage with a place in it (simulated reading) and turned each into a typed statement:
north of, up from, by the sea, a river running from here to there, so many days' travel. Then a
program laid the places out on real coastlines, rivers and elevation (Natural Earth and NOAA's
ETOPO, both public), on circles of land the size the text covers. The question was how many
circles on Earth could hold the whole map at once. If almost none can, a fit means something.

Before the Book of Mormon, five texts whose real setting is known had to pass: the Bible's
narrative books, Josephus, Xenophon's march, Lewis and Clark, and *The Late War*. None did.

The Bible's places spread across about 1,200 km. At that size its stated geography fits 58
percent of the circles of land on Earth, Palestine among them. Josephus fits 96 percent, *The
Late War* 93. Lewis and Clark, with 338 statements, fits none at all, not even the Missouri and
the Columbia. The more a text says, the more chances for one misread statement to rule out every
place; the less it says, the more places it fits. So the count measured how much each text says,
not where it is set. And when the model read the same passages twice in different formats, the
two readings agreed barely more than chance would give (kappa 0.26).

I also tried John Clark's 1989 method on the Bible: build the internal map first, then compare.
Of three plain features of Palestine (sea to the west, Jordan south into the Salt Sea, hill
country up from Jericho), it rebuilt one.

So the Book of Mormon was not scored on fit. What I take from it: "the geography fits region X"
needs two things nobody has shown, for any region, on any side. One is a reading of the book's
statements that two readers agree on. The other is a scale at which even the Bible picks out
Palestine from the rest of the world. The other half of this test asks whether real maps
contradict themselves less than invented ones (*Gulliver*, *Treasure Island*, Oz). It has its own
check, and its reading is queued.

A side result from the radiocarbon data: within 300 km of the Isthmus of Tehuantepec, the open
databases hold 5 dates from 1000 BC to AD 1000; Panama 0; the Great Lakes 398. So dated occupation
cannot be compared fairly between the proposed settings with open data.

### "Secret combinations" (BOM-123)

The Book of Mormon calls the Gadianton robbers a "secret combination". In September 1826 William
Morgan vanished in western New York after threatening to print the Masons' secrets, and the
anti-Masonic movement began. Dan Vogel and others say that in those years the phrase meant
Freemasonry. Daniel Peterson and others say it was an ordinary phrase for any conspiracy.

I counted every use in 209,467 books printed 1700 to 1830 and 114,633 newspaper pages from 1800
to 1830. There are 926.

| Years | Uses in books, per million words | Uses in newspapers, per million words |
| --- | --- | --- |
| 1780 to 1799 | 0.068 | none held |
| 1800 to 1819 | 0.036 | 0.050 |
| 1820 to 1825 | 0.084 | 0.039 |
| 1827 | 0.069 | (2 uses) |
| 1828 | 0.105 | 0.59 |
| 1829 | 0.060 | 0.54 |
| 1830 | 0.082 | 0.15 |

For scale, over the same years the word "anti-masonic" goes from 0.001 per million words to
3.5, more than three thousand times.

Two things are plain from the counts. The phrase was not new: it is in print through the whole
century before, and in books its rate does not move when the Morgan affair breaks. And in
newspapers it does jump, about tenfold, in 1828 and 1829.

What the counts cannot say is what each use is about, and that is the whole dispute. I wrote a
rule: call a use Masonic if a word like "mason" or "lodge" stands within 30 words. Then I
checked the rule on books whose titles settle the subject. In books about Freemasonry it found
only 16 of 37 uses. Anti-Masonic writers used "secret combination" as a name for Masonry
without saying "Mason" anywhere near it. So the rule undercounts exactly the uses that matter,
and I did not use it, and I did not go on to the Book of Mormon's own uses.

The next step is to have each of 826 uses read in its paragraph and labelled (by an AI model,
which I will say is simulated judging), after the same check on the titled books. It is in the
queue.

Limits. The newspapers held are mostly from Rhode Island, Virginia and Washington, none from New
York. The catalogue does not say where a book was printed. Reprints count once a copy.

**The reading, done.** The model (sonnet; simulated judging) first read the uses in books whose
titles settle the subject. It called 21 of 26 passages in Masonic-titled books Freemasonry,
above the bar of 75 percent, and none of the passages in trade or politics books. So it passed,
and I let it read the 826-use sample.

Vogel's claim, as I wrote the bar down beforehand: at least 9 in 10 uses Masonic in 1827 to 1830
would be a yes, half or fewer a no. The answer is a no. Pooled, the Masonic share was 0 in 1800 to
1825, then 14 percent in 1826, 19 in 1827, 33 in 1828, 50 in 1829 and 45 in 1830: 38 percent
across the four years, on 157 uses. Before 1826 the phrase was almost always political, a faction
or a plot against a government.

Newspapers look different: 0 of 18 uses Masonic before Morgan disappeared in September 1826, 28
of 34 after. That would be Vogel's pattern. But when I looked at where they came from, 23 of the
28 are from one paper, the *Pawtucket Herald and Independent Inquirer*, started in September 1828,
with anti-Masonry on 202 of the 279 pages we hold. So the newspaper jump I reported above is mostly
one anti-Masonic weekly. We hold no New York paper from those years, and that is where the
question really sits: the Palmyra papers are the ones to find.

The Book of Mormon's own 20 uses read as robber bands (15), some other secret society (3) or
political plots (2), none as Freemasonry. That is what the text says on its face. It cannot tell
whether whoever wrote it had Masons in mind by analogy, which is the actual argument.

### Joseph Smith's other dictated texts, and the Lectures on Faith (BOM-104)

Two questions. Do the Book of Moses, the Book of Abraham and the later revelations sit near the
Book of Mormon, near Joseph Smith's ordinary writing, or near somebody else? And who wrote the
1835 Lectures on Faith, which earlier studies give mostly to Sidney Rigdon?

Both need the same thing first: a measure that can tell Smith, Rigdon, Cowdery, Phelps and
Parley Pratt apart on writing I know is theirs. I held back ten 1,000-word pieces from each and
asked every measure whose they were. Guessing gets 2 in 10.

| Measure | Smith | Rigdon | Cowdery | Phelps | Pratt |
| --- | --- | --- | --- | --- | --- |
| Common words | 5 | 1 | 6 | 6 | 7 |
| Common words, second way | 9 | 2 | 7 | 6 | 6 |
| Style encoder one | 6 | 3 | 8 | 0 | 8 |
| Style encoder two | 7 | 6 | 6 | 1 | 8 |
| Author models, light tuning | 6 | 1 | 7 | 1 | 2 |
| Author models, heavier tuning | 10 | 4 | 8 | 1 | 6 |

I had said 8 in 10 on average and no one below 5. Nothing reached it. Rigdon, the man the
published studies name, is the one hardest to recognise, and Phelps is nearly invisible. So I
scored neither the dictated texts nor the Lectures, and this can neither confirm nor contradict
the Rigdon attribution.

The likely reason is the samples. Rigdon's signed writing here comes to 20,000 words. Four of
the five men were printed in the same two church papers, perhaps through the same editor's
pen. Smith's known writing is letters and a history, not doctrine.

One thing I got wrong in the procedure: the author-model program scored every text in one
pass, so numbers for the Book of Mormon and the Lectures were computed and saved before the
check had been read. I did not look at them, and the program now refuses to read them when the
check fails. It should have been two passes.

I tried once more with more text: 18 more of Smith's letters, and two long series from the 1833
to 1835 church paper that the editor of Rigdon's collected writings gives to Rigdon (they are
unsigned). Phelps had too little and was dropped. This time one measure of six just passed,
common words, at exactly 8 in 10. Move one piece and it fails. So read the rest as a lean.

| Lecture | Closest | Next | Earlier studies say Rigdon |
| --- | --- | --- | --- |
| 1 | Rigdon | Pratt | agrees |
| 2 | Smith | Pratt | differs |
| 3 | Rigdon | Pratt | agrees |
| 4 | Rigdon | Pratt | agrees |
| 5 | Pratt | Smith | differs |
| 6 | Rigdon | Pratt | agrees |
| 7 | Rigdon | Pratt | agrees |

Five of seven go to Rigdon, as the earlier studies said. Every margin is thin, and the runner-up
is nearly always Parley Pratt, who was not at the school where the Lectures were given. Pratt is
in the test as a decoy. A decoy that keeps coming second is the measure recognising a kind of
writing, the doctrinal essay of the 1830s, more than a man. And the Rigdon text I added is that
same kind, from those same years.

For the dictated texts, the same measure puts the revelations of 1828 to 1834 with Smith's own
letters (47 of 52 pieces), the Book of Moses nearest the Book of Mormon, and the Book of Abraham
nearest Pratt. None of it is firm enough to call, and Rigdon is never the closest to any of
them. I see no drift away from the Book of Mormon over the years.

So: a lean toward Rigdon for most of the Lectures, on one measure that barely qualified.

### Does it read like a translation? (BOM-102)

Two versions of one claim. The broad one: translated books carry marks of translation, and the
Book of Mormon has them. The narrow one: it has particular Hebrew turns of phrase, "plates of
brass" for "brass plates", "dreamed a dream", "and it came to pass".

The hard part of both is the same. Plenty of Americans before 1830 wrote whole books in Bible
style on purpose: *The Late War*, the *Chronicles of Eri*, *The First Book of Napoleon*. None
had a Hebrew original. A test that cannot tell those from real translations only detects Bible
style.

**The broad version failed its check.** I trained a classifier on 695 books the library
catalogue marks as translations and 1,387 written in English. On books it had not seen it was
right 88 percent of the time. But it had to do two more things at once: call the King James
Bible, Sale's Koran and Whiston's Josephus translations, and not call the imitations
translations. No version did both. One scored *The Late War*, a history of the War of 1812, as
more of a translation than the Bible. So I did not score the Book of Mormon.

**The narrow version ran.** Ten rules, one per construction. Seven passed their check (at least
twice as common in the King James Old Testament as in ordinary prose). Per 10,000 words:

| Construction | Book of Mormon | King James Old Testament | Highest Bible-style imitation | Other translations from Hebrew | Ordinary prose |
| --- | --- | --- | --- | --- | --- |
| "it came to pass" | 59.3 | 8.7 | 38.8 | 0.6 | 0.1 |
| "of" + material ("rod of iron") | 2.8 | 5.7 | 4.7 | 1.3 | 1.0 |
| "dreamed a dream" kind | 0.36 | 0.54 | 1.36 | 0.07 | 0.05 |
| "by the hand of", "from before" | 4.5 | 3.6 | 4.2 | 0.5 | 0.1 |
| "and ... and ... and" | 13.3 | 18.2 | 47.1 | 1.6 | 2.4 |
| "his ... and his ... and his" | 11.9 | 9.1 | 19.1 | 1.7 | 1.2 |
| "because that" | 1.2 | 0.25 | 0.64 | 0.02 | 0.06 |

On four of the seven, some English imitator with no Hebrew in front of him uses the
construction as much as the Book of Mormon does, or more. On the other three ("it came to
pass", the compound prepositions, "because that") none quite does.

Look at the fifth column, though. Translations from Hebrew other than the King James Bible
barely have any of these, less than a tenth of the Bible's rate. So they are not marks of
Hebrew coming through into English. They are marks of the King James Bible's English. And the
Book of Mormon overshoots the Bible on three of them: "it came to pass" at seven times the Old
Testament's rate. Joseph Smith's Book of Moses does the same (27.8), and has "because that"
at a higher rate than the Book of Mormon.

What I take from it: these constructions show closeness to King James English, which nobody
disputes. They do not separate a translation from Hebrew from an English writer steeped in the
Bible, because such writers produce most of them freely and other Hebrew translations do not
produce them at all.

Limits. The rules were checked on planted examples, not on a hand-read sample of what they
caught. The imitations add up to only 445,000 words. The "if ... and" construction, the one
Skousen stresses most, could not be tested: the King James Bible does not have it, so my check
had nothing to stand on.

**A second design, after going back to the claim.** The first design had not reproduced
anybody's work first, so this one starts there. I keyed every verse that Tvedtnes (1970, 1991),
Parry (2002), Peterson and Skousen cite for a Hebraism, 170 items, and checked each in the
1830 text.

| Source | Found as cited | Reads differently in 1830 | Not found |
| --- | --- | --- | --- |
| Tvedtnes 1991 | 80 | 11 | 2 |
| Tvedtnes 1970 | 6 | 0 | 0 |
| Parry 2002 | 47 | 5 | 3 |
| Skousen 1994 and the if-and lists | 12 | 0 | 0 |

So their examples are there, nearly all of them. "Land of promise" is 22 times, as claimed;
"promised land" is 20, not the 10 claimed. The eleven "if ... and" sentences are in the 1830
text and the printer's manuscript. A fourteenth case needs Skousen's volume, which I have not
bought, so that one is not replicated.

Finding the examples is the easy half. The claim is that an English author would not have
produced them. The seven features I counted the first time turned out to be King James
English, which any imitator copies. So the new test looks only at Hebrew constructions the
King James translators *removed*: an imitator of the King James could not have picked those
up from it. I built the list from the Hebrew text itself. The doubled verb is the clear case
("dying thou shalt die"): the King James keeps it in about 1 percent of places.

The known-answer check had four parts and two missed.

Very literal translations from Hebrew were supposed to show these constructions at three
times the King James rate. Two of three features did (Ainsworth's 1627 translation has the
doubled verb 35 times as often). The third did not, and it is the one that matters most to
the claim: the "if ... and" sentence. Ainsworth and Young, the two most literal English
translations I have, use it no more than the King James does. English translators of Hebrew,
even stubborn ones, just did not write it. My rule also finds only 4 of the 11 cited cases in
the Book of Mormon, so the rule is weak too.

And books that only pretend to be translations were supposed to score like the King James.
*The Late War* did, the hard case from the first design. But Macpherson's *Ossian* scored 3.8
times the King James level and the fake *Book of Jasher* of 1751 scored 3.0. Neither came
from Hebrew. One came from an imagined Gaelic and one from nothing.

So I did not score the Book of Mormon. What the miss says, as far as raw counts go: English
writers reaching for an ancient sound produce some of these constructions on their own, which
is a point against using them as marks of Hebrew; and the star example, if-and, is so rare
even in literal translation that there is nothing to compare the book's eleven cases to. That
cuts both ways. It means I cannot show an imitator would write it, and I cannot show a
translator would. The counts above are from rules nobody has checked by hand yet; 514
questions for the judge are prepared to do that.

### Spoken or written? (BOM-106)

Everyone who was there said the book was spoken aloud to scribes. William Davis argued in 2020
that it shows the habits of a practised oral performer. Does the text itself read like speech?

I needed speech to compare with, from the time. The best there is: a million answers given by
witnesses at the Old Bailey in London, taken down in shorthand as they spoke; trials reported
the same way; and sermons taken down by shorthand writers in the pews. On the other side,
printed sermons and ordinary written prose. I counted 25 marks of speech in 1,000-word pieces
(short words, few new words, repeated phrases, "did", "that", restarts like "I say" and "or
rather") and trained a simple score on them. Zero is the middle of the written texts and one
is the middle of the spoken ones.

It can tell them apart. Speech from writing overall, 96 times in 100. The hard case, a sermon
taken down from the pulpit against a sermon written for print, 76 in 100, which just clears the
75 I had set.

| Text | Score |
| --- | --- |
| Old Bailey testimony | 1.09 |
| **Book of Mormon, 1830** | **0.88** |
| Book of Mormon, original manuscript | 0.72 |
| Joseph Smith's Book of Moses | 0.65 |
| Joseph Smith's revelations | 0.57 |
| Trials taken in shorthand | 0.50 |
| King James Bible | 0.46 |
| Joseph Smith's letters in his own hand | 0.33 |
| Sermons taken in shorthand | 0.32 |
| Late Henry James (dictated) | 0.26 to 0.33 |
| Bible-style imitations | 0.17 |
| Translations | 0.10 to 0.27 |
| Printed sermons | 0.04 |
| Scott's dictated novel | 0.02 |
| Milton, *Paradise Lost* (dictated) | -0.43 |

By the rule I set, the Book of Mormon reads like speech. It scores higher than anything except
courtroom testimony, well above the Bible, and far above the imitations of the Bible. Every
narrator does (0.81 to 1.07), and narration scores as high as the sermons in it.

Now the cautions, which are real.

What lifts the score is mostly repetition: few new words, the same four-word phrases coming
round again, "that", "did". Those are marks of speech. They are also marks of this particular
book, as the test on dictated books showed (it has the narrowest vocabulary of 24). The plain
marks of someone talking, the restarts and "I say", are rare in it. So "like speech" here means
"repetitive and formulaic the way speech is", not "full of slips".

And dictating does not by itself make a text score as speech. Milton dictated *Paradise Lost*
and it scores as the most written thing on the list. Henry James and Scott dictated novels that
score as writing. A composed work stays composed when spoken to a secretary. So the score does
not measure whether a text was dictated. It measures whether it was put together the way people
talk, in the moment, leaning on formulas. On that, the Book of Mormon sits with the talkers.

The Bible-style imitations matter here: they copy the Bible's "and"s and its cadence and score
0.17. Bible style alone does not get a text to 0.88. Taking the "and" marks out changes
nothing (0.95).

One fix after the first run: the scribes wrote "&" for "and" and my reader was dropping it.

### The Isaiah chapters and Adam Clarke (BOM-122)

About a third of Isaiah is quoted in the Book of Mormon, mostly word for word from the King
James Bible, but not entirely. Colby Townsend argued in 2025 that some of the changes follow
Adam Clarke's commentary, the big Methodist Bible commentary that was coming out in the 1820s.
Kent Jackson replied that they do not. Both argued from a handful of verses.

I lined up every quoted verse against the King James text. There are 552 changes in 263 of the
420 verses. One thing shows at once, and it is not new but it is stark: 30 percent of the King
James words the book changes or drops are words the King James printers put in italics (words
the translators supplied). Of the words it keeps, 2 percent are italic.

Then I searched all 252,431 books in the library printed before 1830 for each changed reading,
in its verse. To know what a match is worth, I also made up 1,080 changes the Book of Mormon
does not make, and searched for those too. A book that reworded Isaiah freely will "match" by
accident, and the made-up changes measure how much.

First, on a case with a known answer. Bishop Lowth published his own translation of Isaiah in
1778. Given Lowth's changes, the search ranked the other printings of Lowth first, second,
third and fourth among a quarter of a million books. So it can find a real source.

| | Book of Mormon's real changes (523) | Made-up changes (1,080) |
| --- | --- | --- |
| Found in Clarke's commentary | 2 | 4 |
| Found in any printing of Lowth | 13 | 4 |
| Found in some book somewhere | 36% | 17% |
| Found nowhere | 333 | |

Clarke matches 2 of the real changes and 4 of the made-up ones. That is chance. By matches he
ranks about 3,300th among the books in the library. The two he matches are small and common
("briers" spelled "briars" is in 45 books). At the verses Townsend names, Clarke's volume has
none of the Book of Mormon's wording.

So by wording, Clarke is not a source of the Isaiah changes, and neither is any other single
book: the best any one book does is 16 of 523. About two thirds of the changes are in no book
I hold. The ones that are found are mostly either common ways of misquoting a famous verse or
readings in older annotated family Bibles.

One real limit. This finds shared wording. Two of Townsend's examples are a different kind of
claim: that Clarke's note argues for a reading in his own words and the Book of Mormon then has
that reading. A word search cannot see that. There are questions prepared to have each of
Clarke's notes at those verses read for it; that step has not been run.

This passed its check on the second design. The first had a bar I had set badly, and the
second card says what changed and why.

### Can the scripture voice be subtracted out? (BOM-100)

The two-voices test showed the weak spot in the first study's main tool. An author model learns
a person from their ordinary writing and is then asked about a text in scripture voice. The
voice is so strong that it can swamp the person. The idea here: measure each text against a
model of the scripture voice in general (learned from Bible-style books by other people), and
not against a plain model, so that what is left over is the person.

It does not help.

| Tuning | Study's rule, right writer picked across voices | With the voice subtracted |
| --- | --- | --- |
| Light | 28.5% | 28.0% |
| Heavier | 70.5% | 70.3% |

(Chance is 17 to 20 percent.)

Part of this is arithmetic I should have seen sooner. If you ask "which of six author models
fits this passage best", subtracting the same reference from all six cannot change the winner.
The reference only matters where scores are compared from one passage to another, and there it
made no difference either.

Two things stand. The tool does carry a person across voices better than chance, 70 percent at
the heavier tuning. And how much you tune still matters far more than anything else, 28 against
70 percent, which is the instability the two-voices test found. That, not the reference, is
what needs fixing. It also still accepts a writer who is not on the list at all, most of the
time, which is the first study's "none of these" problem again.

Smallest model size only, one seed. The Book of Mormon was not touched.

### Can a model be trained to ignore the voice? (BOM-101)

The other idea. The style encoder is the tool that turns a passage into a fingerprint of its
writer. Train it on pairs where the same person writes in two registers, a sermon and a
letter, a history and a poem, so that it learns to keep the person and drop the register.

The library gave 45,364 such pairs from about 4,500 authors, after removing pairs where one
book contains the other (collected works were the main culprit, 8.7 percent of pairs). I
trained on the Mac for eleven hours, starting from the second encoder.

| Measure | First encoder | Second | New |
| --- | --- | --- | --- |
| Six writers, found across their two voices | 0.700 | 0.749 | 0.735 |
| Held-out authors, across registers | 0.801 | 0.809 | 0.796 |
| "None of these", all books | 0.954 | 0.955 | 0.954 |

No gain. I had set three conditions for "better" and it met none, so I did not point it at
the Book of Mormon. The training made the encoder slightly worse on its own validation set
from the first snapshot on, and the best snapshot was the least trained one.

Two things leaned the other way, and I looked at both after the rule had failed, so they are
leads and nothing more. On the four writers no encoder had seen in training, the new one does
a little better, 0.71 against 0.66, mostly because Joseph Smith's revelations now find his
letters (0.93 against 0.69). And it accepts fewer false pairs across genres, 43 percent
against 67. Against that, Joanna Southcott got worse.

The honest limit is size. Eleven hours on the Mac is about 2 percent of the training the
second encoder had. A full-size run needs a rented GPU for about five hours, roughly 15 to 20
dollars. I have not done that. Also, "religious" here means sermons: the library has almost
no writers with a scripture-voice book and an ordinary one, which is the exact case in point.

### The 131 correspondences (BOM-112)

In 2019 Bruce and Brian Dale took Michael Coe's textbook on the Maya, found 131 statements in it
that they judged the Book of Mormon gets right and 18 it gets wrong, gave each a weight (2, 10
or 50 to one, by how specific), multiplied them all together, and reported odds against the
book being fiction of a number with 111 zeros.

I keyed all 149 from their appendices and redid the sum. It comes out as they printed it, once
two slips of theirs are allowed for (one tally in the summary is a single item off from their
own list, and one rounding). So the arithmetic is honest. The question is what it rests on.

It rests on two things: that the weights are right, and that 131 items are 131 separate pieces
of evidence. Here is what happens to the headline when each is relaxed. The first column is the
odds that the book is fiction: a tiny number favours an ancient origin, a number above 1
favours fiction.

| Change | Odds of fiction |
| --- | --- |
| As they published | 1 in 10^111 |
| Every weight capped at 2 to one, for and against | 1 in 10^25 |
| Hits capped at 2 to one, misses left at their 50 | about even |
| Drop the items that are also true of the Bible's world (39 of 131 left) | 1 in 10^11 |
| Drop the items true of most farming kingdoms anywhere (75 left) | 1 in 10^59 |
| Drop both, and the unclear ones (8 left) | 10^29 the other way |
| Count each of their six categories once | 400,000 the other way |

The answer swings across 140 orders of magnitude, in both directions, depending on choices no
one can settle by arithmetic. If the items are independent and the weights fair, the result is
overwhelming. If "had kings", "kings were hereditary" and "some kings were wicked" are one
observation and not three, it is not. The whole result turns on about ten truly independent
items: with fewer than that, the odds cross even.

Which items are "also true of the Bible's world" is my coding, from memory, with no second
reader: I marked 92 of the 131 yes. That is the weakest part of this and I would not lean on
the exact rows. The swing is the finding.

The real test is still to come. Apply the same 131 items, by the same loose standard, to books
we know were written in the 1800s: *View of the Hebrews*, Spalding's manuscript, *The Late
War*. If those "match the Maya" 60 or 80 times as well, the checklist measures how easy it is
to match, not who wrote the book. 947 questions are prepared for that, starting with the Book
of Mormon itself to see whether the reader reproduces the Dales' own judgments.

**That first step missed.** The reader saw, for each of the Dales' 131 positive items, the
passages my keyword search pulled from the Book of Mormon, and was asked whether they plainly
state the feature. It said yes for 70, 53 percent; the bar was 75. For the 18 negative items
(things Coe says the Maya lacked and the book has) it said yes for 17. Every item had some
passages, so the search never came up empty, but it may have pulled the wrong ones. Or the Dales
counted things the book only hints at. I cannot tell those apart without reading the 61 by hand
against the whole book, so the control books were not judged.

### The anachronism tally (BOM-113)

Matthew Roper's 2025 study lists every thing critics have called out of place in the Book of
Mormon since 1830: horses, steel, wheat, silk, chariots, and 220 more. He reports that 174 of
226 have since been confirmed, 31 partly, and 21 not, and that the trend has run the book's way.

I keyed his list from the nine published chapters. The first thing to say is small but should
be said: I count 227 items in his headings, not 226, with 175 confirmed, and his own charts do
not agree with each other (the chart for 2024 has 213 labels; three items sit in both the
confirmed and unconfirmed columns for 1965). I changed nothing to make it fit. It does not
alter the picture.

My guess going in was that "confirmed" would mostly mean "is in the Bible". A sword is easy to
confirm. That guess was wrong.

| | Confirmed by his count | Not confirmed |
| --- | --- | --- |
| Item is named in the King James Bible | 86 | 21 |
| Item is not | 26 | 11 |

Bible things are confirmed 80 percent of the time and the rest 70. That difference is what
chance gives. Being biblical does not explain his confirmations.

What his own headings do show is where the confirmations are thin. For 40 items the heading
says what kind of evidence he means. Those he ties to the New World are confirmed less often
than the rest: 2 of 6 that he places "in Book of Mormon times" and 20 of 34 where he gives no
period, against about four in five overall. Eight more are confirmed by reading the word as
something else (the "horse" that may be a tapir or deer). For the other 168 the kind is not in
the heading, and those go to a reader.

The control the tally has never had: how would a book known to be from the 1800s do? I could
count 144 of his items as words.

| Book | Share of his items that appear in it |
| --- | --- |
| *View of the Hebrews* (1825) | 58% |
| Mathews, *Behemoth* (1839, mound builders) | 58% |
| *The Late War* (Bible style, War of 1812) | 48% |
| *Chronicles of Eri* (1822) | 44% |
| *Book of Jasher* (1751) | 42% |
| Spalding's manuscript | 38% |

So a nineteenth-century book set in antiquity uses 40 to 60 percent of the same things, and so
does a Bible-style book about 1812. That is only words in a text. Whether those books' horses
and steel would count as "confirmed" by the standard Roper applies is a judgment about
evidence, and that is the step still to run: 448 questions, starting with twelve whose answers
are not in doubt.

What I take from it so far: his list is real and mostly holds as a list, my easy explanation
for it failed, and the comparison that would say what a 77 percent confirmation rate means has
not been made by anyone yet.

**The reader's check passed.** Before it reads Roper's items, the model had to code 12 things
whose answer is not in dispute: maize, cacao, turkey and jaguar in ancient Mesoamerica; llama and
potato in the Americas but elsewhere; wheat, war chariots and silk in the Old World only;
gunpowder, the telescope and movable type nowhere before AD 421. It got all 12. Roper's 227 items
and the things in the five control books are next in the queue.

### Where the three worlds disagree (BOM-109)

This was meant to pull the setting tests together. Take only the features on which three
worlds differ: the Bible's Near East, ancient Mexico as its own texts and the Spanish
chroniclers describe it, and ancient America as an American of the 1820s pictured it. Horses or
no horses. Counting in tens or twenties. Coins or none. Then see which world each text sides
with.

I ended up with 31 features that can be counted from words and on which the worlds really
disagree. Then eight texts whose world I know.

| Text | Sides with | Agreements (Near East / Mexico / 1820s) |
| --- | --- | --- |
| 1 and 2 Kings | Near East | 29 / 11 / 9 |
| Josephus, *Antiquities* | Near East | 24 / 8 / 10 |
| Josephus, *War* | Near East | 25 / 11 / 12 |
| Annals of the Cakchiquels | Mexico | 14 / 23 / 11 |
| Bernal Díaz, the conquest of Mexico | **1820s** | 12 / 15 / 24 |
| Spalding's manuscript | 1820s | 10 / 12 / 22 |
| *View of the Hebrews* | 1820s | 11 / 9 / 21 |
| Mathews, *Behemoth* | 1820s | 15 / 11 / 18 |

Seven of eight. I had said eight, so I did not count the Book of Mormon.

The miss is instructive. Bernal Díaz was a Spanish soldier writing about Mexico, and his book
is full of his own side's things: guns, coins, horses. On a word count he looks like a modern
European, which he was. A Mesoamerican text and a text about Mesoamerica are not the same
thing, and the same trouble showed in the inventory test.

There is a setting under which all eight pass (only read "absent" from texts over 50,000
words), but then Díaz passes by a single feature, and I found it after seeing the result. An
instrument that flips on one setting is not ready to be pointed at the question. So no answer
here either. Twelve more features need reading and are prepared as questions (succession,
markets, sacrifice, burial, money and others); for those the 1820s values are from my memory,
which is its own weakness.

**A second design: whose is it?** The first design counted a horse for whoever's book it was in.
But in Bernal Díaz most horses are the Spaniards'. So this time a model reads each mention and
says whose it is (the book's own people, outsiders, the author's own world, a figure of speech,
a prophecy) and what the passage says (they have it, lack it, it was brought). Before any real
reading, the model had to pass a check on 150 made-up passages with known answers, and two
readings of 100 real mentions had to agree.

It missed, in two ways. On "whose", the made-up passages were perfect: 150 of 150. On "what" it
got 109 of 150, under the bar of 85 percent. When I looked, every miss was a passage where my
answer key was arguable: "strangers would bring horses into the land" I had keyed as saying
nothing; the model said "brought from outside", which is fair. Where the thing belongs to the
book's own people, which is the only place the score uses it, it was 60 of 60. That is my key's
fault, not the reader's, but I found it after the result.

The other miss is real. Two readings of the same 98 real mentions agreed on whose it is only 76
percent of the time (bar 80). Most of the disagreement is between "the people the book is about"
and "the author's own world", and much of it comes from *View of the Hebrews*, an essay where
the author talks about the Indians in his own voice. That line is hard to draw, and it is the line
the test turns on.

So the Book of Mormon was not scored, and I did not spend the 45 hours of reading behind it.

### Words that were supposed to be dead (BOM-118)

Skousen and Carmack list word uses and phrases in the Book of Mormon that, by the dictionary's
citations, had dropped out of English before the 1740s. "Arrive to" a place. "It was desirous"
for it was desirable. "Depressed" for weakened in body. If that holds, the vocabulary was out
of a man's reach in 1829. The dictionary works from the citations its readers happened to
collect. I have a quarter of a million books, so I searched for each item.

I had 48 of their 64 items in hand. Six I could not turn into a search, four of them because
the claimed word is Skousen's reconstruction and not what the 1830 edition prints. For the
other 42 I cut the search down to the construction of the cited verse and scanned all 207,082
works printed 1740 to 1830. Then a model read up to 60 hits per item per decade and said
whether each carried the claimed old sense or the ordinary one. That is simulated judging by an
AI model, 8,444 passages of it.

The known-answer check was per item: the model had to read the Book of Mormon's own verse in
the claimed sense and two ordinary uses as ordinary. 34 items passed. Eight did not and are
out.

The model said "claimed sense" 2,509 times. I had planned for a person to check every one of
those. Nobody has. Instead a second, stronger model read each and sorted it: the writer's own
words, a quotation or reprint of something older, or not the sense after all. Then I (the AI
assistant, not Dave) read about 130 of the deciding passages myself, every one for the items
resting on a handful of books and a sample of four from each larger item.

That last step mattered. Three finds for "to that" meaning until were all the old long s:
the scanner read "so that" as "to that". Seven finds for "molten" as a verb were one speech by
the Irish lawyer Curran in seven editions, and it is the ordinary participle anyway. Every
find for "give" meaning describe was somebody who "gave the land the name of" something.
Three of five "into a effect" were smudged "into effect". My reading changed 71 verdicts, and
I now count a passage once however many editions reprint it.

| Outcome | Items | Which |
| --- | --- | --- |
| Still in use 1740-1830, in the writer's own words, two or more separate passages | 21 | arrive to (316 passages), flatter into (120), on the Nth month (73), strong hold (55), do away (52), in the favor of (34), devour (24), extinct (23), be aware (18), hail (18), depressed (17), course (11), belief on (10), in the Nth day (10), desirous (7), for the cause of (5), begin to (3), call (3), hurl away (3), belove (2), into an effect (2) |
| Found once | 2 | counsel (1813), cross (1789) |
| Not found | 11 | molten as a verb, consigned, give, rebellion, rent, views, welfare, whereby, somewhat contentions, to that, where unto |
| Could not test | 14 | 6 with no workable search, 8 where the model missed the item's check |

Some of the 21 are everywhere. People "arrived to" an age or a height all through the period.
A senator in 1827 said "it was desirous they should be performed". Basil Hall in 1829 saw
houses in Rochester, New York, built on wheels "for the avowed purpose of being hurled away
when the land should be sold". All but one of the 21 are found as late as the 1820s.

So of the 34 items I could test, about three in five had not died. The dictionary's last
citation is not the last use. That is the plain result, and it does not surprise anyone who
has used a big library against a citation dictionary.

What it does not show. Eleven items were not found, and that is real, though "not found"
means not found by one construction with a cap of 60 passages per decade. The 14 I could not
test are simply open, and there are 16 more items I do not have. Five of the 21 rest on two or
three passages (belove, into an effect, begin to, call, hurl away), and for some the sense is
a judgment call: is "the call of its stomach" a need or a demand? No person has checked any
of it. The second model was wrong on about a third of the passages I read in the thin items
and on 8 of the 60 I sampled in the larger ones, so the passage counts in the table are too
high by some margin, though not by enough to move a large item. The list of all 2,509 is kept
for anyone who wants to read them.

### Hebrew and Egyptian in the Uto-Aztecan languages (BOM-117)

Brian Stubbs, a linguist, spent decades on the Uto-Aztecan family (Hopi, Yaqui, Nahuatl and
about thirty more). In 2015 he published about 1,500 sets pairing their words with Hebrew,
Aramaic and Egyptian words, under a table of sound rules: this Hebrew sound becomes that
Uto-Aztecan sound. He reads it as a large layer of borrowed words. People cite it beside the
Book of Mormon. Nobody, as far as I could find, has asked the question every linguist asks first:
how many matches like these would turn up between languages that never met?

The book is posted free for private reading, so I could check it his way first. I drew 150 of
his sets at random and had a program read them against his own table. 71 were laid out clearly
enough for a program to read. Of those, 41 follow his table at every consonant, and 62 at the
first one. Then the harder question: for the same Uto-Aztecan word, how many *other* Hebrew or
Coptic dictionary words would pass the same rules? On sound alone, a median of 44. Once the
meaning has to be at least as close as his, a median of 1. For 34 of the 71 there was no other
candidate as good. So his meanings do real work; the sound rules alone are loose. This is all by
rule. Nobody has read the 150 sets by hand.

Then the test linguists use (Kessler's): turn each word into its broad consonant class, count
how often the classes line up across shared meanings, then shuffle the meanings 10,000 times and
see if the real lists line up better than the shuffled ones. Before trusting it on Stubbs, it had
to pass on pairs where the answer is known: Hebrew and Arabic (related), six pairs that borrowed
heavily (Finnish and Swedish, English and French, Yaqui and Spanish...), and eight pairs that
never met (Yaqui against Finnish, Japanese, Korean...).

It mostly failed. Open word lists for the ancient languages are short: 26 to 38 meanings for
Aramaic, Late Egyptian and Stubbs's reconstructed Proto-Uto-Aztecan. At that length the test
could not even find Hebrew and Arabic, which share a parent. So for ten of the twelve
comparisons, the answer is "cannot tell". It passed at one size, the long lists (663 meanings),
and only just: at 629 meanings, 34 fewer, it missed because one borrowing pair came out the wrong
way. That near miss is why Yaqui against Hebrew, at 629, is also "cannot tell".

The one comparison that could be scored was Yaqui against Coptic, the last stage of Egyptian.
Nothing. The real lists lined up no better than shuffled ones (p = 0.49), and the meanings where
loans usually fall (body-part words seldom, trade words often) showed no lean at all. His index
gives a Semitic or Egyptian source for 340 of those 663 meanings. When I planted fake loans in
unrelated pairs, the test found a quarter of that, 85, every single time.

Two limits on that "nothing". The 340 counts meanings with a Near Eastern source anywhere in the
family, not words Yaqui itself carries from Egyptian; if Yaqui has fewer than about 85, this
test does not speak to it. And my fake loans follow a perfectly regular rule, which real loans
do not. Coptic is also only a stand-in for the Egyptian of 600 BC. Stubbs's 2011 book and his
*Changes in Languages* I have not bought, so they are not replicated.

## What I would want a reader to take from the whole set

TBD. This section gets written when enough tests are in to see a pattern, or to see that there
isn't one.

## How to check any of this

Every test has an issue on GitHub with its plan (BOM-99 to BOM-127), a command in the run guide
(`eval/README.md`), and a result file under `data/lab/`. Every outside source is listed with its
address in `data/lab/sources.json`. The texts under copyright are not published; the steps to
obtain them are in `docs/replication.md`.
