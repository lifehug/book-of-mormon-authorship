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
| BOM-119 | The grammar is 1500s English: "did go" past tenses at 20% against under 2% in Bible-style books | Carmack 2015 to 2021 | five Bible-style books | every book in the library | TBD |
| BOM-102 | It reads like a translation; it has Hebrew turns of phrase | Tvedtnes, Skousen and others | examples | real translations against Bible-style imitations | TBD |
| BOM-120 | "Therefore" and "wherefore" switch in the order the book was dictated | Metcalfe 1993 | the book alone | 264 long books by one author | **Done** |

### 2. Where did the words and ideas come from?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-126 | Phrases come from histories of the Revolution; Abinadi follows Bunyan | Donofrio; Davis 2012 | the claimed source alone | the claimed source ranked among every volume in the library | **Done** |
| BOM-122 | Changes to Isaiah follow Adam Clarke's commentary | Townsend 2025; Jackson's reply | Clarke alone | every commentary and annotated Bible held | TBD; 11 passages keyed |
| BOM-124 | New Testament wording appears centuries before Christ | many | single cases | the rate by section, against sermons and period translators | TBD |
| BOM-123 | "Secret combinations" meant Freemasons in 1830 | Vogel 1993; replies | examples from each side | every use in print 1780 to 1835, by year | TBD |
| BOM-103 | The book answers the religious debates of 1820s New York | Campbell 1831 | a list | the print dates of the nearest passages, topic by topic | TBD |

### 3. How was it produced?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-106 | The text carries the marks of speech, not writing | Davis 2020 and others | description | trial transcripts and sermons taken in short-hand | TBD |
| BOM-127 | Manuscript errors are errors of hearing | Skousen 1998 | one editor's reading | manuscripts known to be copied and known to be dictated | TBD |
| BOM-125 | It is unlike other dictated or "received" books | Hales 2019; Dunn 2002 | length and schooling | the same measures on all of them | TBD |
| BOM-121 | Its speakers have more distinct voices than a novelist's characters | Fields and others, about 2021 | four novelists after 1830 | plays and letter novels before 1830, by one author | TBD |
| BOM-107 | It has deliberate chiasmus | Welch 1969; Edwards 2004 | the book and the Bible | the rate in every book | TBD |

### 4. Does the same hand show up elsewhere?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-104 | The Books of Moses and Abraham share the voice; Rigdon wrote the *Lectures on Faith* | Phipps 1977; Reynolds 2005 | small samples | the study's models and encoders | TBD |
| BOM-105, BOM-99 | Smith's revelations and his letters look like two different writers | Holmes 1992; the first study | Smith alone | other prophets who wrote in two voices (Southcott, Wroe, Brothers) | TBD |
| BOM-100, BOM-101 | A model can be taught to see the person and not the scripture voice | this project | | the known-answer set from BOM-99 | TBD |

### 5. Whose world is it?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-108 | The names are Hebrew, or Egyptian, or invented | Tvedtnes and others; Wilcox 2013, 2019 | 124 names against census names, Spalding, Tolkien | Hebrew inscriptions, Egyptian, Maya, Nahuatl, treaty signers, period print, four inventing authors | TBD |
| BOM-110 | Place names come from towns around the Great Lakes | Holley; replies | name by name | the same match rule on every other region | TBD |
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

## What I would want a reader to take from the whole set

TBD. This section gets written when enough tests are in to see a pattern, or to see that there
isn't one.

## How to check any of this

Every test has an issue on GitHub with its plan (BOM-99 to BOM-127), a command in the run guide
(`eval/README.md`), and a result file under `data/lab/`. Every outside source is listed with its
address in `data/lab/sources.json`. The texts under copyright are not published; the steps to
obtain them are in `docs/replication.md`.
