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
| BOM-102 | It reads like a translation; it has Hebrew turns of phrase | Tvedtnes, Skousen and others | examples | real translations against Bible-style imitations | **Hebraisms done; translation check failed (rules' hits read by a model: still fails on if-and)** |
| BOM-120 | "Therefore" and "wherefore" switch in the order the book was dictated | Metcalfe 1993 | the book alone | 264 long books by one author | **Done** |

### 2. Where did the words and ideas come from?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-126 | Phrases come from histories of the Revolution; Abinadi follows Bunyan | Donofrio; Davis 2012 | the claimed source alone | the claimed source ranked among every volume in the library | **Done** |
| BOM-122 | Changes to Isaiah follow Adam Clarke's commentary | Townsend 2025; Jackson's reply | Clarke alone | every commentary and annotated Bible held, by wording and by reading the notes | **Clarke does not stand out; one real example (Isaiah 9:3); Clarke's scan read at under half the changes, to fix** |
| BOM-124 | New Testament wording appears centuries before Christ | many | single cases | the rate by section, against sermons and period translators | **Done** |
| BOM-123 | "Secret combinations" meant Freemasons in 1830 | Vogel 1989; replies | examples from each side | every use in print 1780 to 1835, by year | **Done: Masonic in about 4 of 10 uses by 1827-1830, not almost all** |
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
| BOM-104 | The Books of Moses and Abraham share the voice; Rigdon wrote the *Lectures on Faith* | Phipps 1977; Larsen, Rencher and Layton 1980; Reynolds 2005 | Phipps's samples (all three); rerun: Phipps and Reynolds come back, Larsen does not | the study's models and encoders | **Done, weak** |
| BOM-105, BOM-99 | Smith's revelations and his letters look like two different writers | Holmes 1992; the first study | Smith alone | other writers with two voices (Southcott, Wroe, Trapnel, Snowden, Elias Smith) | **Done** on three measures; the author models do not give a stable answer |
| BOM-100, BOM-101 | A model can be taught to see the person and not the scripture voice | this project | | the known-answer set from BOM-99 | BOM-100 **done: no gain**; BOM-101 **done: no gain at the size I could train** |

### 5. Whose world is it?

| Test | The claim | Who | Before | Here | Status |
| --- | --- | --- | --- | --- | --- |
| BOM-108 | The names are Hebrew, or Egyptian, or invented | Tvedtnes and others; Wilcox 2013, 2019 | 124 names against census names, Spalding, Tolkien | Hebrew inscriptions, Egyptian, Maya, Nahuatl, treaty signers, period print, four inventing authors | **Done**, with a limit |
| BOM-110 | Place names come from towns around the Great Lakes | Holley; replies | name by name | the same match rule on every other region | **Done** |
| BOM-111 | Its animals, plants and metals do or do not fit ancient America | Coe 1973; Sorenson | lists | Bible, 1820s writing, native texts, Spanish chronicles | **Done** |
| BOM-109, BOM-112 | 131 details match the ancient Maya | Dale and Dale 2019; critics | one book, coded by the authors | three checklists, ten texts, coded blind | BOM-112 **done on the third design: the book has 107 of 131, more than any control; the King James histories have 88**; BOM-109 **third design's check passed (whose 130/130; two readers kappa 0.77); long reading queued** |
| BOM-113 | 174 of 226 claimed anachronisms are now confirmed | Roper 2025 | one coder, no control | place and period required; Spalding as control | **Done: holds only loosely (31% strict, 85% loose); the controls match it loosely** |
| BOM-114 | The weights in Alma 11 match ancient systems | Welch 1999 | five systems searched | random systems as the baseline; number habits against Bible, modern and Mesoamerican texts | **Part done** |
| BOM-115 | Its warfare is ancient, or it is mound-builder forts | Vogel 1986 and others | examples | Bible, Josephus, American wars, conquest accounts | **Done** |
| BOM-116 | Its geography fits Mesoamerica, or the Great Lakes | Sorenson and others | argued from verses | every model against random regions; second design on real terrain | **Both designs' checks failed; not scored on fit; consistency cannot be compared (invented stories state too little geography)** |
| BOM-117 | Uto-Aztecan languages carry Hebrew and Egyptian words | Stubbs 2015 | his pairing alone | his sets checked against his own rules and his 2011 vocabulary; his rules on 8 languages that never met; word lists against unrelated and borrowing pairs | **Yaqui-Coptic: no layer of the claimed size; his rules find Hebrew no more than unrelated languages (a Modern Hebrew lead did not survive its rerun)** |

## Results so far

### "Therefore" and "wherefore" (BOM-120)

**The claim.** Brent Metcalfe noticed in 1993 that the book says "therefore" in one long stretch
and "wherefore" in another, and that the stretches follow the order of dictation, not the order
of the pages. Mosiah was dictated first, after the first 116 pages were lost. 1 Nephi was dictated
last. Metcalfe read it as a sign of one writer whose habit changed. Later, Eccel (2018) reported a
sharp break rather than a slow drift, and Wunderli (2013) used the same switch as evidence for
Joseph Smith. It is an argument for a nineteenth-century
author, but it rests on a fact anyone can count.

**Their way first.** I now have Metcalfe's chapter, "The Priority of Mosiah", in *New Approaches
to the Book of Mormon* (1993), pages 395 to 444. His method is simple. He counted the two words
book by book. Then he printed the counts twice: once in page order, once starting from Mosiah
(Tables 1 and 2, page 410). In page order the "wherefore" books sit at both ends with a
"therefore" stretch in the middle. Starting from Mosiah, it becomes one change, from "therefore"
to "wherefore". He set those counts beside Joseph Smith's revelations from the same months, which
also go from all "therefore" to all "wherefore". Then he refined the counts (Table 3, page 413).
He took out the uses copied from the King James Bible, 42 of them, each listed by verse, and put
back eight that the manuscripts had and later printings dropped. He also split Ether into thirds
(page 412) and counted eleven passages he takes as Mormon's own (page 415). No blocks, no
statistics, no other books. His conclusion: dictation began at Mosiah, Ether was the turning
point in late May 1829, and the habit was Smith's.

Do his numbers come back? Yes, and more closely than I expected. One thing surprised me. His
book table matches the 1920 edition exactly, every book. So he counted a modern text, not the
1830, even though the totals he cites on page 409 (668 and 420) are for the 1830. In the 1830
text every book is within 2 of his, and the gaps are differences between editions. Later
printings dropped or swapped a word in 14 chapters.

| Book (dictation order) | his "therefore", "wherefore" | 1920 text | 1830 text |
| --- | --- | --- | --- |
| Mosiah | 123, 1 | 123, 1 | 123, 1 |
| Alma | 286, 3 | 286, 3 | 288, 3 |
| Helaman | 63, 0 | 63, 0 | 63, 0 |
| 3 Nephi | 98, 3 | 98, 3 | 98, 3 |
| 4 Nephi | 5, 0 | 5, 0 | 5, 0 |
| Mormon | 22, 0 | 22, 0 | 22, 0 |
| Ether | 24, 63 | 24, 63 | 24, 62 |
| Title Page | 0, 2 | (1830) | 0, 2 |
| Moroni | 0, 38 | 0, 38 | 0, 38 |
| 1 Nephi | 13, 98 | 13, 98 | 14, 100 |
| 2 Nephi | 28, 138 | 28, 138 | 29, 139 |
| Jacob | 1, 52 | 1, 52 | 1, 53 |
| Enos, Jarom, Omni | 0, 15 | 0, 15 | 0, 15 |
| Words of Mormon | 0, 4 | 0, 4 | 0, 5 |

His refined table comes back too. Following his own steps on the 1920 text, every cell matches
but one. He has 289 for Alma, but his own starting count plus his own two additions makes 288.
Of his 42 Bible verses, 41 hold the word where he says. The other is a misprint ("14:14" for
2 Nephi 15:14, which does hold it). Ether by thirds matches exactly in the 1920 text and is one "wherefore"
short in the last third of the 1830. His list of Mormon's
passages, ten of eleven exactly and the last off by one.

Two corrections came out of this, both mine. First, the table I printed here before was the
count *without* the long Bible chapters, labelled as if it were the whole count. That is why it
had 2 Nephi at 8 "therefore" when the book has 29. Second, my count for Mormon was 3 short,
19 against his 22. The cause was in the project's own 1830 table. One long passage of 3,152
words, where Moroni takes over his father's record, is labelled as a chapter heading. Any count
of "body text only" leaves it out. Counting all the book's text fixes it. I reran my break-finder
that way too. The break stays in the same place inside Ether, the before and after shares move
by about a point, and no library book matches it. My first attempt at his refined table also had
a mistake, and I found it only from the result. I added his eight restored words to the 1830
count, but seven of those eight are already in the 1830 text. They are the words later printings
dropped, so that counted them twice. I redid it his way, on the text he actually used.

I did not redo his revelation column. Our copy of Revelation Book 1 is stored page by page,
not revelation by revelation, so I can't yet date each count.

One more thing I had wrong. I wrote that Metcalfe "stopped at the counts" and left the narrator
question open. He didn't. His Figures 2 to 4 take the passages written in Mormon's own voice
and show they switch in dictation order too. That answers the narrator explanation in its own
way. What he did not have is a formal comparison of the two explanations, or any other book to
compare against.

**What I tried.** Before I had his chapter, I thought Metcalfe stopped at the counts. He didn't
quite, as above, but two questions were still open. Could the narrators explain it as well as
dictation order does, in a formal comparison? And how often does any long book by one
author switch a habit this sharply? So I cut the text into blocks, found the single break that
best splits it into a "before" rate and an "after" rate, and compared three explanations: one
break in dictation order, one break in printed order, and one rate per narrator (Mormon, Moroni,
the small-plates writers). Then I ran the same break-finder on long single-author books from the
library, which is the comparison nobody had.

**The check.** Before trusting the break-finder, I gave it a case with a known answer. I took
pairs of library books that favour different words, joined them end to end, and asked it to find
the join. The bar was 90 percent.

**When it failed.** The first version of that check found the join in 147 of 200 pairs, 73.5
percent. Under the bar. Looking at the misses told me why. Only 6 of 281 library books use
"wherefore" for 40 percent or more of the two words, so the 200 pairs kept reusing the same few
books, and three of those have a switch of their own inside them. The method was finding a real
switch, just not the one I had planted. That is exactly what the library comparison is supposed
to measure, so it is not a failure to find breaks. I changed the check: each book's blocks are
shuffled before the join, so the join is the only break in the pair. I made that change after
seeing the first check fail, but before anything about the Book of Mormon had been counted. The
revised check found the join in 186 of 200 pairs, 93 percent, and passed.

**The result.** One break explains the book. Before it, "wherefore" is 2 percent of the two words.
After it, 88 percent. The break falls partway through Ether. Taking out the long Bible-quoting
chapters makes it sharper still (0.9 percent before, 89.9 after).

Dictation order beats the narrators. On the score I set beforehand (a difference of 10 or more
decides it), the dictation-order break scores 485, one rate per narrator 529, and one break in
printed order 902. Lower is better. The plainest evidence is inside single narrators. Ether's
first 1830 chapter has 7 "wherefore" and 13 "therefore"; its later chapters 55 and 11. Words of
Mormon, which Mormon wrote but which was dictated last, has 5 and 0.

Then the comparison. I sampled 600 long single-author books and kept the 264 that use the two
words at least 100 times. None of the 264 switches as sharply and as strongly as the Book of
Mormon. Five switch as sharply, but on very few uses. The nearest is a collection of Thomas
Paine's political pieces, and its switch is weaker on both counts.

**What it means, and what it doesn't.** The habit really does change in dictation order, and a
change that clean is unusual for a long book. That part of Metcalfe's argument holds. What it
cannot tell you is who was choosing the words. A habit that changes in dictation order fits one
person dictating whose habit changed in the spring of 1829. It fits just as well any account in
which the English wording was produced in that order, whoever or whatever produced it. And the
dictation order itself comes from the historical record; it is taken as given here, not tested.
The library comparison is printed books by one author, not other dictated texts.

**What's left.** His revelation column, which needs a table of the 1828-1830 revelations by
date. The whoso/whosoever pair (his page 408, from Foster 1983). Eccel's figures in *Mormon
Genesis*, which I still haven't bought. And the mislabelled 3,152-word passage in the project's
1830 table, which is the study's to fix, not the lab's.

### Claimed sources, ranked (BOM-126)

**The claim.** Two claims, both for a nineteenth-century source. Thomas Donofrio says phrases in
the war chapters come from histories of the American Revolution, Mercy Otis Warren's and David
Ramsay's above all, with shared phrases like "the cause of liberty". William Davis, in 2012, says
the story of Abinadi before King Noah follows the trial of Faithful in *The Pilgrim's Progress*
point by point: arrested, tried before an assembly, accused of slandering the rulers, speaks
boldly, condemned, burned, and a witness converted. Each was made by laying two books side by side.
Replies say parallels like these turn up between any two long books.

**Their way first.** I could not rerun either one their way. Donofrio's own pages were not in hand
when I ran this. Davis's list of parallels (14 elements, as the census later found) was not in
hand either. So neither author's examples were scored one by one. That is not replicated yet.

**What I tried.** The first study already had a fair way to ask this, and used it on *The Late
War*: score every volume in the library the same way and see where the claimed book lands. A
claimed source in the top handful of 200,000 volumes is a lead. One in the crowd says the
parallels are what any book of its kind would give. So I looked up each claimed book on the
study's two borrowing measures (rare shared phrases, and closeness in meaning), and then went down
to the passages: for the Abinadi story and the war chapters, which works in the whole library hold
the nearest passages? I added *Paradise Lost*, the Westminster Confession and Foxe's *Book of
Martyrs* to the table, and *The Late War* and *The First Book of Napoleon* for scale.

**The check.** Three parts, all before I looked anything up about the Book of Mormon. First, a
known borrower: with *The Late War* as the target, its other printings should come out at the top.
Second, the study's own published ranks had to be reproduced exactly. Third, the passage search
had to find the trial of Faithful in one printing of Bunyan when given the same scene from
another printing.

**When it failed.** The first part failed. Of 104 "other printings" of *The Late War*, 9 came out
at ranks 1 to 9 and the rest were scattered as far down as 201,922. The ranking was fine. My list
was wrong. I had borrowed the study's list of volumes to keep out of the phrase counts, and that
list holds every history of the War of 1812, not just Hunt's book: Brackenridge, Thomson, a poem
called *The Fredoniad*. The nine that really are Hunt's book are exactly the nine at the top. I
fixed the list to "author Hunt, 'late war' in the title", kept the bar the same, and recorded that
I changed it after seeing the first try fail. The best-placed other history of that war came out
66th, which is itself useful: a book on the same subject does not rank like a reprint.

After that, all three parts passed. Hunt's nine printings ranked 1 to 9 of 204,527. The study's
published ranks came back exactly (131 for *The Late War*, 63 for *Napoleon*, all 139 of the
Grunder entries). And Faithful's trial found itself in another printing in 59 of 60 pairs.

**The result.**

| Book | Shared rare phrases: rank of 204,520 volumes | Closeness in meaning: rank of 30,994 |
| --- | --- | --- |
| Warren's history | none shared | no near passage |
| Ramsay's *History of the American Revolution* | none shared | 24,650 |
| *The Pilgrim's Progress* | 1,073 | 511 |
| Foxe's *Book of Martyrs* | 4,756 | 44 |
| *Paradise Lost* | 6,034 | 816 |
| *The Late War*, for scale | 131 | 17,678 |
| *The First Book of Napoleon*, for scale | 63 | 4,706 |

Warren and Ramsay are in the crowd on every measure. Warren has no passage among the nearest
hundred to anything in the war chapters. For the war chapters, the works with the most nearest
passages are editions of Josephus: they take all fifteen of the top fifteen places.

Bunyan is more interesting, and not in the way the claim says. The book as a whole sits closer in
meaning than most, and its passages turn up near the war chapters about twelve times as often as
its size would predict. But the trial of Faithful, the scene the claim is about, is not among the
hundred nearest passages to any part of the Abinadi story. For every one of the 44 Abinadi
passages, Foxe's martyrs have a closer passage, and Josephus and printed sermons are closer still.
One caution on Bunyan's good meaning rank: the flag compares him with fiction of the same length,
not with religious books, so it is weaker than it looks.

**What it means, and what it doesn't.** The histories of the Revolution are not special neighbours
of the war chapters; Josephus is. Bunyan's trial scene is not the nearest thing in print to
Abinadi; martyr stories in general, Foxe above all, are nearer. That cuts against both claims as
made. It does not rule out a few borrowed sentences, which whole-book ranks would not see, or a
borrowed plot outline, which this search is not built to see.

**What's left.** Davis's 14 elements scored in the Abinadi story, in Faithful's trial and in Foxe's
martyrs, and the study's story-order comparison run on them (it needs paid model time, so it waits
on my yes). Donofrio's original pages found and his phrases scored by rarity.

### Numbers, and the weights in Alma 11 (BOM-114)

**The claim.** Two questions sit together here. The first has no published claimant that I found:
nobody seems to have counted the book's numbers. But if the book is set in ancient Mesoamerica, as
many defenders argue, it is fair to ask whether it counts the way the Maya and the Aztecs did, in
twenties. The second is John Welch's, from 1999. Alma 11 describes a system of weights (a senine,
a seon twice that, a shum twice that, a limnah worth all of them), and Welch matched its features
with five ancient Near Eastern systems, nine parallels in all. Nobody had asked how often a
made-up system would match one of them as well.

**Their way first.** For the twenties there is nothing to reproduce. For Welch, I have not read the
article itself; his nine parallels came to me from a summary page, and I did not redo his
five-system search. So his result is not replicated yet.

**What I tried.** For the twenties: take the round numbers between 20 and 400 in a text and ask what
share are multiples of twenty. Then compare the Book of Mormon with native Mesoamerican texts in
English, the Bible and Josephus, and modern books. I also tried something more ambitious: place the
book by its whole number profile (favourite numbers like 7, 12, 40 or 13, 20, 52, how years are
counted, how numbers are written). For Alma 11: write its values as ratios (1/8, 1/4, 1/2, 1,
1 1/2, 2, 4 and 7), score the fit against a list of real systems under one rule, and then do the
same for 20,000 random systems to see how often chance does as well.

**The check.** Two checks, one for each idea. For the twenties: the native texts had to come out
clearly above the Bible and the modern books, or the measure cannot see base twenty through an
English translation at all. For the whole profile: hold each known text out in turn and see whether
the method puts it back in its own tradition, 75 percent of the time overall and at least half in
each tradition.

**When it failed.** The twenties check passed. The profile check did not: 71 percent against a bar
of 75, and only 3 of 7 Mesoamerican pieces went home. The Mesoamerican side was too small, 694
numbers in four texts, and one of them (a 1908 summary of the Popol Vuh) sorted with modern writing.
The decoy told me something worse. *The Late War*, a modern book written in Bible style, landed with
the Bible in 7 of 8 parts. So the profile was reading Bible style, not counting. I did not redesign
the check after it failed, and I did not score the Book of Mormon on the profile.

There was one fix before the count: the loader read almost nothing from one native text, because
only its first hymn was headed "Translation". I fixed that on the native text alone; it did not
change either check's outcome.

**The result.** The twenties:

| Text | Share that are multiples of twenty |
| --- | --- |
| Native Mesoamerican texts in English (two of Brinton's translations) | 91% (32 of 35) |
| Clavigero's *History of Mexico* (1787) | 66% (346 of 527) |
| Modern English books | 60% (468 of 780) |
| King James Bible and Josephus | 53% (643 of 1,218) |
| Book of Mormon | 40% (19 of 47) |

The habit survives translation: the native texts show it plainly, and Clavigero, a European writing
about Mexico, carries some of it. The Book of Mormon shows none. It sits below both the Bible and
ordinary English books. These are small counts, 35 numbers on one side and 47 on the other, and
much of the native figure is one turn of phrase ("four score years" for four of their twenty-year
periods).

Alma 11. Against my list of real systems the best fit is 6 of the 8 values, a tie between English
dry and liquid measure and Roman coins. Hebrew weights fit 2 of 8. The best Mesoamerican fit is far
lower. Whether 6 of 8 is impressive depends entirely on what "random" means. I had fixed one rule
to decide: random systems built from the kinds of steps real systems use. Under that rule, 10
percent of random systems fit some real system that well, against a bar of 5 percent, so by my own
rule it is no closer than a made-up system. Under a second rule, random steps of any small ratio,
none of 20,000 does. The two disagree because the whole fit is the run of doublings, from 1/8 up to
4, and doubling is what most systems of measure do. The 1 1/2 and the 7 match almost nothing.

This part is a pilot. My list of real systems was written from memory and has not been sourced.

**What it means, and what it doesn't.** The book's round numbers do not lean to twenties. That is a
fact about its counting habit in English, on small counts. It does not show that a book from a
base-twenty world could not come out base-ten in translation. On Alma 11, the ratios do not pick out
one ancient system: English measures fit as well as anything Near Eastern. That says the match is
mostly doubling. It does not test Welch's other points, like the names of the units.

**What's left.** A sourced list of weight and coin systems, each with a citation, and the Alma 11
part run again on it. More native Mesoamerican text (Christenson's Popol Vuh, the Chilam Balam), so
the profile check has a chance of passing.

### The names (BOM-108)

**The claim.** The book has 163 names that are not in the Bible: Nephi, Moroni, Zarahemla,
Coriantumr. People on one side call them Hebrew or Egyptian, name by name. Hugh Nibley paired
Paanchi and Korihor with Egyptian names. Tvedtnes, Gee and Roper in 2000 found 16 of the names in
ancient Hebrew inscriptions. Black and Wilcox in 2011 said the names break the habits fiction
writers follow. And Wilcox and colleagues, in 2013 and 2019, compared the sounds of 124 names with
100 census names, Spalding's invented names and Tolkien's, and found the book's names patterned like
real names, not one author's inventions. On the other side, people say they are made up.

**Their way first.** Wilcox's study cannot be rerun. It needs a hand transcription of every name
into sounds and a particular online calculator, and the authors released no data. So I built a
rough stand-in with letters instead of sounds, and labelled it a stand-in. It points the same way
they did: the book's names sit closer to 1790 census names than to Spalding's. For Tvedtnes, Gee
and Roper, I reduced names to a rough skeleton of consonants. All 7 of their 16 names that I could
test match a Hebrew inscription name that way. But the same rule matches 26 percent of all the
book's names, 27 percent of King James names, and 20 percent of the book's names with their
letters shuffled. So their matches come back, and so do matches for almost anything.

**What I tried.** I gathered lists to compare with: 4,673 King James names, 752 Hebrew names from
inscriptions, 8,451 Egyptian names, 2,774 Native American treaty signers, Maya rulers, Aztec names,
classical names as printed in English, the 1790 census, and names four authors invented (Spalding,
Swift, Spenser, Macpherson's *Ossian*). For each list, a simple model of letter patterns. Then the
question: which list does each Book of Mormon name look most like? The invented names, scored the
same way, are the comparison the earlier work did not have at this size.

**The check.** Two. Names held out of each list had to be sorted back into their own list well
above chance. And a spelling check, which turned out to matter more. I took King James names and
wrote them the way scholars transcribe Hebrew. If the method sorts by language, they should still
go to the King James list.

**When it failed.** The held-out check missed twice on the English-spelled lists before it passed.
The first time (49 percent against a bar of 50), census given names kept going to King James and to
census surnames. That is fair enough: a given name in 1790 is very often a Bible name, and a surname
is often a given name. I merged the two census lists. The second time (58 percent against 60), the
lists had been cut to 120 names each, only to keep two tiny lists in that are not in this design;
I let the English lists use 600. The third run passed at 68 percent. Both changes were made after
seeing a result on known cases, and before any Book of Mormon name was scored.

The spelling check gave the same answer every time, and it decides what this test can say. Only 8
percent of the King James names in scholarly dress were still recognised as King James names. 47
percent went to the Hebrew-inscription list. So a model like this mostly sorts names by how they are
spelled, not by what language they come from. Comparing "Nephi" in 1830 English spelling with a
Hebrew name in scholarly transcription is not a fair comparison, and I draw no conclusion from it
about Hebrew, Egyptian, Maya or Aztec. Stripping names down to consonants did not rescue it either.

**The result.** What can be compared fairly is lists that are all in English spelling:

| Names | Closest to King James | Closest to classical | Closest to the 1790 census |
| --- | --- | --- | --- |
| Book of Mormon, non-biblical | 55% | 20% | 11% |
| Spalding, Swift and Ossian together | 19% | 23% | 33% |
| Book of Mormon names with letters shuffled | 38% | 16% | 14% |

The book's names look like King James names far more than three other authors' invented names do.
The shuffled row matters: the letters alone, in any order, already send 38 percent to King James;
their order adds the rest. Jaredite, Nephite and place names all come out the same, 52 to 56
percent.

A second count: how many names are one changed letter or one splice away from a King James name?
Nephi, Lehi and Laban are that close. Book of Mormon 58 percent. Spalding 35, Ossian 33, Spenser
14, Swift none. For scale, real King James names held out of the list score 82.

**What it means, and what it doesn't.** It cuts against the idea that the names are unlike anything
a fiction writer would choose: they follow one clear habit, closeness to King James names, more
than other inventors' names do. But that habit fits two stories equally well. Someone steeped in
the King James Bible making up names would give this. So would Hebrew names put into King James
spelling. The test cannot tell those apart, because King James spelling is both. It is a test of
letters, not sounds. And the Assyrian list I thought I had turned out to be an empty download.

**What's left.** Put every list into one spelling, or into sounds, so the ancient lists can be
compared fairly. The made-up names in the Bible-style books I hold are a better invention baseline
than Swift's.

### The Great Lakes place names (BOM-110)

**The claim.** Vernal Holley drew a map in the 1980s pairing Book of Mormon place names with towns
around the Great Lakes: Angola, Alma, Oneida and Onidah, Lehigh and Lehi, about 29 pairs. The point
was that the names came from Joseph Smith's surroundings. The argument since has gone name by name.
Did that town exist in 1829? Is that spelling close enough? One review judged 17 of the 29 invalid,
mostly because the place was named after 1829. Nobody, on either side, had counted how many such
pairs chance gives.

**Their way first.** I did not have Holley's own booklet. His 29 pairs came to me from one web
summary, read through an AI summary and not checked by a person. I scored them anyway under one
fixed rule. Nine pass. Seven of the nine are Bible names spelled the same in both lists (Jerusalem,
Jordan, Boaz, Midian). The other two are Angola and Alma, both towns named after 1830 by the dates
on the reply page. Under a loose rule 24 pass; five fail even then, among them Tecumseh and Teancum,
and Monroe and Moroni.

**What I tried.** The missing question is simple. Take the book's 57 place names that are not in
the Bible. Count how many match a place name within 500 km of Palmyra under one rule. Then do the
same around a few hundred other points in the English-speaking world, each with as many place names
to choose from. If Palmyra stands out, that means something. If it is ordinary, the map is what any
region gives. I added control name sets too (Spalding's, Swift's, invented King James-like names)
and the New York gazetteers printed before 1830.

**The check.** Two parts. The matching rule had to find real variant spellings of the same place
while almost never matching two different places. And a planted case: New York names, each with one
letter changed, had to make the Palmyra region stand out.

**When it failed.** The planted case passed every time, 20 of 20. The spelling check failed in its
first form. I had tested it on twelve pairs of Bible place names spelled two ways, and several of
those were not spellings at all but different names (Hiddekel and Tigris). It found 4 of the 12.
A much better test set was already on disk: Worcester's 1823 gazetteer prints its own variant
spellings ("Delfino, or Delvino"), 4,365 of them. On those, the rule had a real problem. No single
setting does both jobs. Strict enough to keep random matches under 1 in 10,000, it finds 21 percent
of real variants. Loose enough to find 60 percent, it matches random pairs about 2 times in 1,000.
That is a result in itself. So I report two settings, strict and loose, both fixed before the book
was scored, and kept the strict one as the verdict, as first written. I changed this after seeing
the first check, and the card says so.

**The result.**

| Rule | Matches near Palmyra | Typical far-away region | Where Palmyra ranks |
| --- | --- | --- | --- |
| Strict, within 500 km | 6 of 57 | 9 of 57 | 27th percentile of 232 regions |
| Strict, within 150 km | 2 of 57 | 2 of 57 | 63rd percentile of 374 |
| Loose, within 500 km | 50 of 57 | 49 of 57 | 77th percentile |

Palmyra is an ordinary region. Under the strict rule it does a little worse than most: 178 regions
do as well or better. The six local matches are Alma, Ani, Gid, Josh, Corihor (against "Corridor")
and Mormon. Under the loose rule nearly every name matches something nearly everywhere, which is the
point: with a loose enough rule and a big enough map, any list of short names finds partners. The
controls agree. Swift's invented names put Palmyra at the 1st percentile, Spalding's at the 22nd;
real King James place names put it at the 86th, because the north-east is full of Bible-named towns.

Then the period sources. In the New York gazetteers of 1813 and 1824 and three national ones, none of
the 57 names has a close match among New York entries under the strict rule. Under the loose rule
New York leads the other states in two of three gazetteers, but control name sets put New York
first about as often.

**What it means, and what it doesn't.** As a whole, the map is what chance gives; the Great Lakes
are not special for these names. That does not hold for every pair. One or two real borrowings would
be invisible in a count like this, and Oneida and Onidah is a single pair that no count can speak
to. The regional comparison uses today's place names, with period gazetteers only for New York. And
the matching is spelling reduced to sound, by one rule.

**What's left.** Holley's own list, checked by a person against his map. Period gazetteers for the
comparison regions, not only New York.

### New Testament wording before Christ (BOM-124)

**The claim.** Critics point out that Nephi and Alma, centuries before Christ, use phrases from Paul
and John. Defenders answer that a translator reaches for familiar wording. Both sides argue it case
by case. Nicholas Frederick in 2015 and others have proposed careful ways to grade single cases:
quotation, allusion, echo. Nobody had measured how much there is, or compared it with what a real
translator of the period did.

**Their way first.** There is no published number to reproduce. The claims are single cases, and the
grading schemes are methods, not counts. I did not apply Frederick's grades here, so his part is not
replicated yet.

**What I tried.** Count phrases of four or five words that are in the King James New Testament and
not in the Old Testament or the Apocrypha, per 10,000 words. Chapters that quote Isaiah or the
Sermon on the Mount at length are set aside. Then put the book's pre-Christian parts (1 Nephi to
Helaman, and Ether) beside four kinds of comparison: period sermons, Bible-style books on other
subjects, real translators of ancient non-Christian texts into Bible-soaked English (Whiston's
Josephus, Sale's Koran), and Joseph Smith's other dictated texts. And ask whether there is a jump
when Christ arrives in 3 Nephi.

**The check.** Two known answers. Each New Testament book, scored against phrase lists built without
it, had to outscore the Old Testament books. And sermons had to outscore non-religious books.

**When it failed.** It didn't, this time. Every New Testament book outranked every Old Testament
book, and sermons beat non-religious books 88 percent of the time against a bar of 80. Nothing was
changed after any result. There was one surprise in the check worth saying. I expected an Old
Testament book held out of the lists to score near zero. It scored 66, because the measure also
picks up ordinary biblical phrases that happen to be in the New Testament. So the numbers below are
only good for comparing texts with each other. They are not counts of "New Testament quotations".

**The result.**

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
period translators, and of the Bible-style books. Among 300 sermons they sit at the 93rd percentile:
high, though some preachers went higher, and under the 95th that I had set for "above sermons". The
closest match in the table is Joseph Smith's own addition to Genesis.

Is there a jump when Christ arrives? The rate rises by about a third at 3 Nephi, somewhere between 4
and 65 percent. I had set 50 percent as the bar for calling it a step, so: cannot tell. A modest
rise, not a clean step.

No one New Testament book dominates. The Gospels and Acts, Paul, Hebrews and Revelation each supply
about their share of the New Testament's words.

**What it means, and what it doesn't.** For critics: the amount is real and large, far more than two
real translators of ancient texts used, in the same kind of English. For defenders: shared wording
cannot tell a translator using familiar phrases from an author composing with them, and the rate is
inside the range of a busy preacher. What the comparison adds is scale, and one neighbour: the text
nearest the book here is Joseph Smith's own addition to Genesis. It counts exact phrases only, not
paraphrase.

**What's left.** A paraphrase count with the meaning index. A sample of the 4,043 pre-Christian hits
graded by Frederick's criteria, to separate quotation from echo. A checked list of quotation
chapters; the one used is approximate.

### The grammar of the 1500s (BOM-119)

**The claim.** Stanford Carmack's strongest number is about a small word. The Book of Mormon says
"they did go" and "he did preach" where ordinary English says "they went" and "he preached", and it
does so in about a fifth of its past tenses. That habit peaked in English around 1550 to 1600 and
had mostly died by 1700. The King James Bible does it under 2 percent of the time. So, the argument
goes, this is not Bible imitation; nobody imitating the Bible would produce it. His comparison was
five Bible-style books, plus a 700-million-word database of early printed English. In later papers
he added about nine more features of the same kind.

**Their way first.** I reproduced his numbers before anything else. Book of Mormon: 19.4 percent (he
reports 20.2). King James Bible: 1.6 percent (he reports 1.7). Joseph Smith's 1832 history: none in
98 past tenses (he reports none in 88). Those were the figures I had set out to match, within a
stated margin, and they match.

There is a catch I have to own. The 20.2 percent is from his later book with Royal Skousen, as quoted
in a summary. His own 2015 article says 27.2 percent, from a smaller count of past tenses. If I leave
"came to pass" out of my past-tense count I get 23.3, closer but not 27. I have not worked out which
way of counting gives which, so call that one partly reproduced.

**What I tried.** Then every book in the library, 207,471 of them printed from 1500 to 1830, counted
the same way. The question: does any book printed after 1700, that is not a reprint of an older one,
reach the Book of Mormon's rate? And on Carmack's other features, does any book of 1780 to 1830
match on all of them together?

**The check.** Three parts. Reproduce the published rates, as above. Show that the "did" rate
separates books of 1540 to 1620 from books of 1760 to 1830 (bar 80 percent). And read 60 of the
extracted "did" phrases to see whether the program finds the right thing (bar 90 percent).

**When it failed.** The first version passed every check. The Book of Mormon came out at 17.8
percent, inside my margin. But the raw count, 1,408 uses, was well short of Carmack's "over 1,700",
so I looked at what was missing, and "did go" was not being counted at all. Two bugs in the verb
list: it dropped two-letter words (losing "go") and every word ending in -ing (losing "bring" and
"sing"). I fixed both. At the same time I loosened one setting that decides what counts as a verb,
which let in words like "march" and "minister". That one was a judgment, not a bug, and I made it
after seeing the Book of Mormon count, so it counts for less. Then I reran all three checks. The rate
separates early from late books 89 percent of the time. I read 60 fresh "did" phrases and 59 were
right.

**The result.**

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
vanishes: 29 books out of about 180,000. Even in its peak years the Book of Mormon is in the top 3
percent.

What are the 29? Fourteen are reprints of books written before 1700: psalters, a prayer book, old
sermons. Nine are the articles of impeachment against Warren Hastings and Burke's works that contain
them, where "did" is the language of an indictment ("the said Warren Hastings did receive"). The
rest are hymn books, a book of ballads written "in imitation of the antient", a book by William Combe
of 1824 and a short comedy.

And one more book, which matters most. *Chronicles of Eri* (1822) is written in Bible style and
presented as a translation of ancient Irish records. Its second volume says "did" in 19.3 percent of
its past tenses, level with the Book of Mormon. A summary of Carmack's work had already granted that
it probably might. So one author writing mock-ancient scripture in the 1820s did produce this rate.
Another, *The Chronicles of Andrew* (1815), reaches 13.4 percent on a short text.

But the "did" rate is one feature of ten, and *Chronicles of Eri* has none of the others. No book
printed between 1780 and 1830 matches the Book of Mormon on all ten together; the most any single
book manages is three. That sounds stronger than it is. In my check, nine of the ten features barely
told early books from late ones in the first place. Only the "did" rate really dates a book.

Three more comparisons:

- **Bible-style books:** none of the 20 in the library list reaches the rate.
- **Real translations:** none of the 341 marked as translations reaches it.
- **Joseph Smith's other texts:** the revelations, the Book of Moses, the Abraham manuscripts, his
  letters and his 1832 history all sit between 0 and 1.6 percent.

That last one is the surprise. Whatever produced the "did" in the Book of Mormon, it is absent from
everything else he dictated, including scripture dictated a year later.

**What it means, and what it doesn't.** For defenders, the core holds: this is an old habit, rare
after 1700, absent from Bible imitations as a group and from Joseph Smith's own other writing. For
critics, the strongest form of the claim does not: an 1820s author of mock-ancient scripture reached
the same rate, so it could be done. It says nothing about who composed the text or how. The
past-tense count is an approximation, my count is about 5 percent short of Carmack's hand count, and
which books are reprints was judged from titles and authors' dates, not by reading them. The library
is thin for 1700 to 1780.

**What's left.** Read the 15 later books that reach the rate, and *Chronicles of Eri*, to say what
their "did" is. Compare Carmack's other features with his own published numbers, feature by feature.

### Heard or copied? The manuscript's corrections (BOM-127)

**The claim.** Royal Skousen, the editor of the critical text, argued in 1998 ("How Joseph Smith
Translated the Book of Mormon", *Journal of Book of Mormon Studies* 7/1) that the mistakes in the
original manuscript are mistakes of the ear. A scribe taking dictation writes "their" for "there".
A scribe copying from a page skips a line. If the corrections are ear mistakes, the text was
dictated. His case is his own reading of the manuscript, one editor classifying one manuscript,
with nothing to compare it to.

**Their way first.** I can't rerun Skousen's reading event by event. It is an expert's judgement,
not a rule, and his full typology is in his 2001 facsimile volumes, which I haven't bought. So his
way is not replicated until that book is bought. The first study did a rough version (BOM-34): a
fixed list of sound-alike word pairs, counted in the original manuscript and in the printer's
manuscript. It found 36 in the original against 8 in the copy, which agreed with him.

**What I tried.** Two things the earlier count lacked. First, a written rule that sorts every
correction into a kind: spelling, sound-alike, a slip of the eye (letters of similar shape, a
doubled run, a line skipped between two copies of the same word), a word jumped ahead to or
repeated from just before, grammar, other. Second, known cases from outside the Book of Mormon.
The printer's manuscript is a copy of the original, made mostly by the same scribe, Oliver Cowdery,
so its mistakes are copying mistakes. And the first draft of Joseph Smith's Bible revision (the
Book of Moses and early Genesis) was dictated, while a second draft of the same chapters, in John
Whitmer's hand, is a copy of it. That pair should be the cleanest test there is.

**The check.** Four parts had to pass before the original was scored.

- The sound rule had to join known sound-alike pairs and not join others. It joined 45 of 49 and
  none of 40.
- The printer's manuscript, a copy, had to come out at no more than 10% sound-alike. It came out
  at 0.6% (5 of 854).
- Mistakes I planted in clean King James text had to be recovered. Each kind was found 97 to 100%
  of the time. For the eye-slip kinds that is close to circular, since the rule was written to
  find exactly what I planted.
- The dictated draft had to show at least twice the copied draft's share of sound-alikes.

The last one didn't work. The dictated draft has 1 sound-alike in 168 one-word corrections, the
copy 2 in 236. That is too few to test anything. The card said in that case the run goes ahead but
is flagged. So the one known dictated manuscript I hold doesn't show the signature at all. That
matters for everything below.

**The result.**

| Manuscript | Sound-alike corrections | One-word corrections |
| --- | --- | --- |
| Original manuscript (dictated, by the claim) | 28 (3.9%) | 720 |
| Printer's manuscript (a copy) | 5 (0.6%) | 854 |
| All copied text pooled (printer's, the copied Bible draft, a letterbook of copies) | 7 (0.6%) | 1,114 |
| Oliver Cowdery in the original | 28 | 615 |
| Oliver Cowdery in the printer's manuscript | 5 | 759 |

By the rule on the card, that is "heard-like". The same scribe makes six times as many ear
mistakes in the original as in his own copy, and that difference would turn up by chance about
twice in a million tries.

**Then I looked at what the 28 actually are.** I did this after seeing the first result, so it
counts for less. Twenty-three of the 28 are one pair of words, "there" and "their", all in
Cowdery's hand: 21 "there" for "their" and 2 the other way. Take that pair out and the original
has 5 in 720, the copies 6 in 1,114. No difference. Within Cowdery alone it is 5 of 615 against 4
of 759.

Two more things cut against a simple reading. The dictated Bible draft shows almost no ear
mistakes (1 in 168). And the original has eye-type corrections too: 14 of its 720 (1.9%), against
7 of 854 in the printer's manuscript and about the same share in the copy pool. Testing the rules
in a different order (jumped-ahead words before sounds) changed no count.

The names gave a small, separate picture. Of 86 printed names found on the surviving pages, 69 are
spelled the first time the way they were printed. Of the 17 that aren't, 10 differ only in a vowel.
Names start a little less settled and then settle, but the copy shows 13 such first variants too,
so the counts are small.

**What it means, and what it doesn't.** For the dictation side: there is a real signal, and it
sits exactly where the claim says it should. One scribe makes one confusion over and over in the
manuscript he is said to have taken by ear, and hardly at all when he copied it. Against a strong
reading: it is one pair of words. Outside that pair the original looks like a copy, and the one
manuscript known to be dictated doesn't show the pattern either. And a "there" for "their" shows a
word was held as a sound at that moment. That could come from a speaker, or from a scribe reading
a page aloud to himself. None of this says who composed the text. It is about how words reached
the page. It reads the published transcripts, not the page photographs, so letters written over
other letters are missed.

**What's left.** A dictated text with a scribe who wasn't copying a known page (the Doctrine and
Covenants manuscripts in Cowdery's or Whitmer's hand), to give "dictated" a real reference.
Skousen's facsimile volumes, to check the automatic sorting against his, event by event.

### Prophets in two voices (BOM-105, BOM-99)

**The claim.** In 1992 David Holmes measured vocabulary richness and found that Joseph Smith's
personal writing sits apart, while his revelations, the Book of Abraham and the Book of Mormon sit
together. He called it a "prophetic voice". The first study found the same split with far heavier
tools: the revelations look like the Book of Mormon, the letters don't look like either.

**Their way first.** The first study reproduced Holmes (BOM-22) with all five of his measures on
10,000-word samples, and got all three of his findings back: Joseph Smith's own writing stands
alone, the prophets don't separate from each other, and the revelations sit with the prophets. So
the split is solid. The question is what it means. Is it something about Joseph Smith, or
something that happens to anyone who writes as a prophet on Monday and to a friend on Tuesday?
Nobody had checked, because nobody had put other two-voice writers beside him.

**What I tried.** Find other people who did both, with enough of each to measure. I read volumes
to choose them before measuring anything. Seven made the first cut:

| Writer | Scripture voice | Ordinary voice |
| --- | --- | --- |
| Joseph Smith | revelations, 65,000 words | letters, journal and histories, 30,000 |
| John Wroe (English prophet, 1820s) | 255,000 | 6,000 |
| Joanna Southcott (English prophet, 1790s on) | 53,000 | 24,000 |
| Anna Trapnel (English prophet, 1650s) | 31,000 | 31,000 |
| Edward Burrough (Quaker, 1650s) | dropped, see below | |
| Richard Snowden (wrote a Bible-style history) | 56,000 | 142,000 |
| Elias Smith (wrote a Bible-style tract) | 16,000 | 108,000 |

For each I measured how far apart the two voices are, using the 150 small common words (the, of,
and, that) that writers use without thinking. The yardstick is the distance between two different
people writing in the same voice. A gap of 1.0 means this writer's two voices are as far apart as
two strangers. Before any measuring, an AI helper (not a person) read five sample passages per
writer and voice to see the labels were right. One fix came out of that: Snowden's book had a
poem printed with it, so verse was dropped from his scripture-style text.

**The check.** Within one voice, the measure had to send passages back to their own writer at
least 80% of the time. Chance was about one in seven.

**When it failed.** It missed. In the ordinary voice it came out at 0.79. All of the shortfall was
Edward Burrough: none of his 11 ordinary-voice passages went to him. Looking at why, his
"ordinary" sample was two unlike documents, a short spiritual autobiography and a long report on
the sufferings of London Quakers written as "we", which he may not have written alone. If the
method can't recognise him inside one voice, it can't say anything about him across two. I dropped
him. I did that after seeing the check fail, but before any cross-voice number or any Joseph Smith
number existed. The check then passed: 0.93 and 0.92. It left exactly five writers beside him, the
minimum the card allowed.

**The result, common words.** Joseph Smith's gap is 0.92. The other five run from 0.86 to 1.22.
His is the second smallest. The same holds with King James phrases taken out (0.94) and with the
thee-and-thou words taken out (0.91). On this measure the split is ordinary. Everyone who changes
voice looks like a different person.

Can you still find the person across the gap? It wobbles. Three of the other five are found
across it, two of five with King James phrases dropped, four of five without archaic words. And
Joseph Smith's own perfect score is partly fake: his letters are the most scripture-like ordinary
writing in the set, so they pulled in 36% of everybody's scripture passages.

**Then the first study's own tools.** Common words are a blunt instrument, and the first study's
finding came from its two style encoders. So I ran both on the same six writers, with the same
check and the same rule. Both passed the check easily (0.93 to 0.99).

| | Common words | First encoder | Second encoder |
| --- | --- | --- | --- |
| Joseph Smith's gap between voices | 0.92 | 0.58 | 0.64 |
| The other five writers | 0.86 to 1.22 | 0.37 to 0.75 | 0.31 to 0.82 |
| His rank of six (1 = largest gap) | 5th | 4th | 3rd |
| Other writers found across their two voices | 3 of 5 | 5 of 5 | 5 of 5 |
| His letters' pull on others' scripture passages | 36% | 8% | 7% |

Same answer: his gap sits in the middle of the group. The encoders also do something common words
couldn't. Every gap is under 1.0, so each writer's two voices are closer to each other than two
different writers are, and all five others are found across their voices. The encoders keep hold
of the person when the voice changes. They find Joseph Smith across his too: 51 of 64 revelation
passages go to his letters under the first encoder, 17 of 29 letter passages to his revelations.

One detail goes the other way. Pair by pair, his revelations are a shade closer to John Wroe's
prophecies than to his own letters (0.75 against 0.73). Scripture voice still pulls scripture
voice together. And two writers (Southcott, Elias Smith) had text in the encoders' training, which
pulls their two voices together. Leaving them out doesn't change where Joseph Smith falls.

**Then the author models, which do not settle it.** The other half of the first study's finding
came from language models tuned on one author at a time. With the owner's yes for an overnight Mac
run, I tuned the smallest one (125M) on each writer's ordinary voice and asked whether it
recognises the scripture voice, with King James phrases masked as the study did.

| Training text per model | Joseph Smith's letters model finds his revelations | Other writers |
| --- | --- | --- |
| The study's small dose (about 2,000 tokens) | 0 of 51 | 7% to 89% |
| Four times that, without Wroe | 45 of 46 | 44% to 95% |

The small-dose run only just passed its check (0.803 against 0.80). A version without the King
James masking failed its check outright (0.63): unmasked, everyone's revelations drifted to Wroe's
model. In the small-dose run, Snowden's letters model soaked up 57% of everybody's scripture
passages, including 48 of Joseph Smith's 51. With four times the text, every writer is found, and
he is found best of all. But Wroe has too little ordinary text for that run, so it has only four
others, one short of what the card needs for a verdict on him.

My reading is that the small-dose zero is an artifact of too little training text. I came to that
after seeing both runs, so it counts for less. The fair summary: the author models cannot tell,
and they lean the same way as the encoders.

**What it means, and what it doesn't.** The split the first study found, revelations one way and
letters the other, is not peculiar to Joseph Smith. On common words and on both encoders his gap is
typical of people who wrote in both voices. That makes "his revelations look like the Book of
Mormon" a weaker clue about a person than it first looked, because scripture voice pulls scripture
voice together for everyone. It doesn't say the Book of Mormon is or isn't his: the book was not
read or scored here. Six writers is a small group, so "typical" is a weak word. Four are read from
uncorrected scans. Trapnel wrote 150 years before the rest.

**What's left.** More two-voice writers with at least 15,000 words a side, so the larger-dose run
has enough of them for a verdict. More seeds and a dose in between. Two human readers for the voice
labels. The larger model sizes would need a priced GPU run.

### Warfare (BOM-115)

**The claim.** About a fifth of the Book of Mormon is war, and both sides have read it as
evidence. Dan Vogel (*Indian Origins and the Book of Mormon*, 1986) listed about 27 motifs that
1820s Americans already believed about the mound builders, among them forts of earth walls topped
with pickets. On the other side, the 1990 volume *Warfare in the Book of Mormon* (Ricks and
Hamblin, editors) reads its wars as ancient. Both are lists of examples. Neither gives a rate for
anything else.

**Their way first.** There is nothing to rerun. A list of parallels has no count to reproduce. So
this is not a replication. I set the question up so that every tradition the two sides point at
gets measured the same way: the Bible and Josephus; the American wars of 1775 to 1815, which the
book's first readers knew; the conquest of Mexico; and the 1810s and 1820s writing about
mound-builder forts and Indian wars.

**What I tried.** Take the war passages of every text by one rule: cut it into 500-word stretches
and keep a stretch if enough of its words are war words (battle, army, slain, siege, enemy and so
on). Then count a fixed list of war terms in those stretches: weapons, armour,
fortifications, how armies are organised, what happens to prisoners, months and seasons. Place
each text with the tradition whose word profile is closest. *The Late War* (Bible style, about the
War of 1812) and Spalding's novel ride along as controls. If Bible diction alone drags a war story
to the Bible, they will show it.

**The check.** Two parts. The war-passage rule had to pass at most 5% of stretches from plainly
non-war books (Job to the Song of Solomon, the New Testament) and at least half of the stretches of
plainly war books (Josephus's *Wars*, Ramsay's history of the Revolution). Then each text, held out
in turn, had to land with its own tradition: 75% on average and at least half in every tradition.

**When it failed: why, and what I changed.** The first part failed. The rule passed 2.6% of non-war
stretches, fine, but only 42.5% of war-book stretches. Looking at those books, Ramsay's first
volume is half the political road to the war. No war-word rule can pass half of it without also
passing the Psalms. So the bar of one half was badly set for books that aren't war from first page
to last. I lowered it to 0.4. I did that after seeing the miss, but before any Book of Mormon
passage was cut, and the threshold itself didn't move, so nothing downstream changed except
whether the check counted as passed. Then I found a bug (short end pieces were merged into the
wrong piece) and fixed it, and the check was rerun.

The second part passed: 85% of held-out pieces landed with their own tradition (American wars
100%, conquest 95%, Bible and Josephus 84%, mound-builder writing 60%). Two weak spots. The
mound-builder group only just formed: five texts, and their war passages are mostly Indian wars
and travel, not descriptions of earthworks. And the native annals in English were too short to
form a group at all.

**The result.** The Book of Mormon has 103 war stretches, about 51,500 words.

| Tradition | How close the Book of Mormon's war vocabulary is (1.0 = identical) |
| --- | --- |
| Bible and Josephus | 0.66 |
| Mound-builder and Indian-war writing | 0.62 |
| Conquest of Mexico | 0.62 |
| American wars, 1775 to 1815 | 0.40 |

It is nearest the Bible and Josephus, but the gap to second place (0.04) is smaller than the gap
any held-out Bible text shows to its own runner-up (0.07 at the least). So the first three are not
separated. What is clear is the last row. There are no muskets, cannon, guns, bayonets or
tomahawks, and no months named.

The controls matter here. *The Late War* lands with the American wars (0.665). Spalding's novel
lands with the mound-builder writing (0.69, from one piece). Both sit further from the Bible
(0.58, 0.59) than the Book of Mormon does. So Bible diction does not by itself drag a war story to
the Bible.

Some words are its own. "Title of liberty", "arm-shield" and "thick clothing" appear in no
comparison tradition. "Cimeter", "heap of earth", "picket" and "decoy" are in it and not in the
Bible or Josephus. The Bible has things it lacks: spear, dagger, helmet, trench, garrison, ambush,
tribute.

**The fortifications, and a second wrong turn.** Alma describes cities fortified with a ditch, a
bank of earth, timbers, pickets and towers, the very features Vogel pointed to in 1820s
descriptions. I looked for those five together. The measure on the card was 500-word windows, and
it found none anywhere: not in the Book of Mormon, not in any comparison text, not in 300 library
books. Everything scored zero, which says nothing. So after that first run I added a second
measure, the same for every text: the shortest stretch of words that holds all five.

| Text | Shortest stretch with all five |
| --- | --- |
| Book of Mormon (Alma, 1830 chapters 21 and 22) | 507 words |
| Josiah Priest, *American Antiquities* (1833) | 1,419 |
| John Haywood on Tennessee (1823) | 1,888 |
| Tightest of 300 ordinary library books | 3,204 (only 14 of the 300 have all five at all) |

No comparison text packs them as close. The nearest is writing about American antiquities, and the
very nearest, Priest, was printed three years after the Book of Mormon. The nearest from before
1830 is Haywood.

**Army sizes.** The typical army figure in the Book of Mormon is 6,000, against 1,000 in the Bible
and Josephus, 500 in the American wars and 200 in the conquest of Mexico. Large round thousands,
like the Bible. That rests on eleven figures.

**What it means, and what it doesn't.** It is not the American wars of its own day, and Bible-style
writing about those wars does not look like it. Beyond that, its war vocabulary is about equally
close to the Bible, the mound-builder writing and the conquest of Mexico. The fortification
cluster is the one place it lines up with something unusual, and that something is American
antiquities writing, though the comparison group for it is thin. This is words in war passages,
not how anyone fought.

**What's left.** Real earthwork descriptions as their own group (Atwater's full text, the Ohio
surveys). A native war text of real size. Sorenson's 1990 seasons-of-war count, rerun against an
even spread. The nearest library passages to the fortification chapters, with their print dates.

### The inventory of things (BOM-111)

**The claim.** Every book set somewhere mentions the things of that place. In 1973 Michael Coe, a
Maya archaeologist, listed the Book of Mormon's horses, chariots, wheat, barley, cattle and metal
working as things that don't belong in ancient America. John Sorenson (*An Ancient American
Setting*, 1985; *Mormon's Codex*, 2013) argues the book fits Mesoamerica once its words are read
right. Both sides argue item by item.

**Their way first.** Coe's is a short list, not a method; I can only say whether the words are
there, and they are. Sorenson's correspondences are in a book I haven't bought, so his side is not
replicated until the book is bought.

**What I tried.** Put every item on one footing. An AI wrote, from memory, a list of about 2,000
things in six kinds: animals, plants and foods, metals and materials, tools and weapons, buildings,
clothing. It covers the Bible's world, Mexico and Central America, and New England. I counted them
in each text, weighted rare things more, and asked which of four worlds the Book of Mormon's
inventory is closest to: the Bible and Josephus; Mesoamerica (native texts in English and the
Spanish chronicles); American writing of the 1810s and 1820s about Indians and antiquities; and
ordinary English books of the period.

**The check.** Each comparison text, held out in turn, had to land in its own world: at least 75%
overall and at least half in each world. It passed: 154 of 173 (89%). Every Mesoamerican and every
Bible-world text landed home. *The Late War* went to the American world, Josephus to the Bible's.
Cut into 5,000-word pieces, 79% landed home.

**When it failed: why, and what I changed.** Three things. First, a bug. Seven words claimed by two
lists (jade as a horse and as a stone, among others) had been removed from both, so jade the stone
was missing. I found it when a test file failed, not from the book's counts. I fixed it, reran
everything, and nothing in the answer moved. The book has no jade either way.

Second, one check missed. A Mesoamerican profile built only from native texts doesn't recognise the
Spanish chronicles: 0 of 3. Built from chronicles only, it takes in all five native texts. The
native texts are full of feathers, flowers, maize, birds and flutes. The chronicles are full of
horses, ships, swords, artillery and gold. So "Mesoamerica" here partly means "how Spaniards and
their translators wrote about it", and any Mesoamerican verdict depends on which kind of text you
compare with.

Third, after I saw the book's counts, I noticed many of its commonest items aren't things in the
book at all: church, seed, fruit, flesh, wax. So I added two runs, one dropping the book's 20 most
frequent items everywhere and one dropping 16 words whose main sense isn't the thing. I chose those
after seeing the counts, so they count for less. Both still put the book with the Bible.

**The result.**

| World | How close the Book of Mormon's inventory is (1.0 = identical) |
| --- | --- |
| Bible and Josephus | 0.50 |
| Ordinary English books of the period | 0.40 |
| American writing about Indians and antiquities | 0.28 |
| Mesoamerica (native texts and Spanish chronicles) | 0.17 |

The Bible's world, clearly, in at least 99.8% of resamples, with and without the chapters that
quote the Bible. Ten of the book's twelve large pieces land there and none lands in Mesoamerica.
By kind of thing it is clear for plants and foods, buildings and clothing, and not clear for
animals, metals or tools and weapons.

The plainest number: things that existed only in the Americas before Columbus, like maize, cacao,
turkey, jaguar, jade, obsidian, maguey, tobacco and squash.

| Texts | New World things per 10,000 words |
| --- | --- |
| Native Mesoamerican texts and Spanish chronicles | 5 to 49 |
| American writing about Indians | 0.5 to 9.5 |
| Bible and Josephus | 0 to 0.13 |
| Book of Mormon | 0 |

**What about a translator's word choices?** A translator might write "sword" for an obsidian-edged
club or "corn" for maize. I measured what the real translators of Bernal Díaz, Clavigero and the
native texts did. When they used an Old World word, they almost never flagged it as standing for
something else ("a kind of sword which they call..."): 4% of the time in the chronicles, 10% in
the native texts, about the same as in books with no translating to do (2 to 4%). The Old World
words in the chronicles mostly mean the real Old World things: Bernal Díaz's horses are horses.
Then the stronger test: remove every such stand-in word from the Book of Mormon (sword, wine,
brass and seventeen others, 10% of its item words). Each closeness figure moves by one or two
hundredths and the order doesn't change. Mesoamerica gets slightly further away, not closer.

**What is missing.** Eighteen things appear in at least three quarters of the Mesoamerican texts
often enough that their absence means something, and are nowhere in the book: birds, feathers,
maize, flowers, drums, flutes, deer, maguey among them. But 35 things common in the Bible texts
are missing too (fortress, oil, lamp, camel, incense), so the book is not simply the Bible's
inventory either. And five words nobody can classify: cureloms, cumoms, neas, sheum and ziff.

**What it means, and what it doesn't.** The book's vocabulary of things is the Bible's, with no
New World items at all, and a translator's habits don't explain the gap. That is Coe's point, held
up across 2,000 items instead of six. But a word is not a thing, and this compares vocabularies,
not archaeology. The book's Bible style is itself a reason it would use the Bible's nouns. The
lists were written from memory by a model, not taken from a source. Only eight texts stand for
Mesoamerica, and that group splits by register.

**What's left.** Lists from published sources instead of memory. A third kind of Mesoamerican text
(Landa, Sahagún) to settle the register split. The book's figurative items sorted by hand.

### Do the speakers have their own voices? (BOM-121)

**The claim.** Nephi, Alma, Mormon and the rest differ from one another, in the small common words
nobody chooses on purpose, more than a novelist's characters do. The older form of this is Larsen,
Rencher and Layton in 1980. The newer one is Fields, Bassist and Roper, about 2021, reported by
Scripture Central: 28 distinct voices, and a spread of voices more than twice the average of eight
novels by Austen, Cooper, Dickens and Twain.

**Their way first.** The first study reproduced Larsen (BOM-22): with the speakers relabelled, 17
speakers differ, with odds against chance as extreme as theirs. The newer claim I could not rerun.
Its titles, word list and values are not published. So what follows tests the same claim my way;
it does not reproduce the paper.

**What I tried.** The question that matters is what one author writing many characters produces.
Novels of the right age with labelled speakers aren't in the library, but plays are, and in a play
every speech carries its speaker's name. I took 354 plays printed between 1660 and 1700. A voice is
a stretch of one speaker's words. The spread of five voices is how far apart they sit on the 150
most common words. Then compare the Book of Mormon's five largest speakers (Mormon, Nephi, Alma,
Moroni and the Lord, as labelled by an AI model in the first study and checked against Larsen's
word counts) with five characters from one play, five leads by one playwright, and five leads by
five playwrights.

**The check.** Before the book, the measure had to tell five different playwrights from one
playwright's five leads: the many-author set had to spread wider at least 70% of the time across
all plays, and 60% in comedies only. Two ways of measuring spread were on the card: the average
distance between voices, and the "volume" of the spread, which is the published study's own
description.

**When it failed: why, and what I changed.** At the card's setting, 1,000 words a voice, it missed:
0.66 against 0.70 on all plays. The volume measure missed everywhere. So the book was not scored.
A thousand words is short for this kind of measure, so I looked at longer voices on the plays only,
with the book untouched. At 2,000 words it passed, narrowly: 0.71 on all plays, 0.68 on comedies. I
made that change after seeing the miss, so it counts for less. I didn't take 3,000 words because
only five plays have five speakers that long. The volume measure never passed and isn't used. Even
passing, this is a weak instrument: at best it ranks five authors above one author 71% of the time.

**The result.**

| Five voices taken from | Spread |
| --- | --- |
| One play (one author's characters) | 0.72 |
| The leads of five plays by one author | 0.79 |
| The leads of five plays by five authors | 0.84 |
| **The Book of Mormon's five largest speakers** | **1.07** |

The book's speakers are further apart than the characters of any one playwright, and further apart
than five different playwrights. By the card's rule, "beyond". Taken alone that would look like the
claim confirmed. It holds with King James phrases taken out too (1.09).

It is not that simple, and the next table is why.

| What | Spread |
| --- | --- |
| Random 2,000-word stretches of the Book of Mormon, speakers ignored | 0.99 |
| Random stretches of one play, speakers ignored | 0.67 |
| Four Bible-style books of 1811 to 1822, by four different people | 0.97 |
| One writer in two kinds of writing (six writers, Joseph Smith among them) | 0.94 to 1.16 |

Any five stretches of the book are almost as far apart as its five speakers. Knowing who is
speaking adds 8 percent. The book is simply a varied book: sermon, war story, letter, prophecy,
quoted scripture. And a spread of about 1.0 is what one person produces by changing the kind of
writing, as Joseph Smith's own letters against his revelations show (0.97).

**What it means, and what it doesn't.** The speakers do differ more than a playwright's characters.
That part of the claim survives a fairer comparison. But most of the difference is the book
changing subject and kind, not the speaker changing. This test cannot tell several hands from one
hand writing in several kinds. Plays are verse and dialogue, not prose narrative, and a century and
a half older. The book's speaker labels are a model's labelling.

**What's left.** Compare windows within one narrator (Mormon across books) with windows across
narrators, to split "speaker" from "part of the book". A prose comparison with labelled speakers,
such as letter novels. The style encoders and author models on the same sets. Hilton's speaker
database as a second labelling.

### Do its debates date to the 1820s? (BOM-103)

**The claim.** In February 1831 Alexander Campbell reviewed the book in the *Millennial Harbinger*.
He said it decides "every error and almost every truth discussed in N. York for the last ten years",
and named twenty: infant baptism, ordination, the trinity, regeneration, repentance, justification,
the fall of man, the atonement, transubstantiation, fasting, penance, church government, religious
experience, the call to the ministry, the general resurrection, eternal punishment, who may
baptize, freemasonry, republican government and the rights of man. Dan Vogel (1993) made a
narrower form of it: the book's answers to universal salvation repeat the anti-Universalist talk of
early nineteenth-century America. The reply, from Martin Tanner and others, is that these are old
Christian questions, argued since the Reformation and before.

**Their way first, except I didn't do it first.** Campbell gave no method. He read the list off the
book and asserted it was New York's agenda, with no comparison to any other time. The honest order
would have been: check his list his way, then build something better. I did it the other way
round, and it took three designs to get back to him. Vogel's chapter I haven't bought, so his
version is not replicated until the book is bought.

**Design one: the nearest passages, by decade.** Take the book's passages on 17 debate topics. Find
the 100 nearest passages in meaning among 13 million from religious books printed 1640 to 1829.
See which decade they pile up in, corrected for how much each decade printed.

*The check.* First the same thing on books whose date I know, 20 in each group. At least 12 of 20
had to land within a decade of their print date, in every group.

| Books printed in | Dated to within a decade |
| --- | --- |
| 1650s | 7 of 20 |
| 1740s | 12 of 20 |
| 1780s | 10 of 20 |
| 1820s | 5 of 20 |
| 1780 to 1799, clean hand-typed text | 0 of 20 |

Only one group made it. I did not run the Book of Mormon.

*Why it failed.* The library is lopsided: 3.9 million religious passages from the 1820s, and only
22,000 to 49,000 from each decade of the middle 1700s. Correcting for size made the thin decades
win on a handful of neighbours. Nearly everything in modern spelling got dated to the 1750s, and
the clean hand-typed texts were pulled there hardest. The 1830 text I hold is clean too. It would
have landed in the 1750s whatever it says.

**Design two: an even library.** Those two causes, and nothing else, got fixed. Search 1780 to 1829
only, the issue's own scope. Use scanned text only in the library, so clean and scanned text aren't
mixed. Give every decade exactly the same number of passages, so chance is a flat 20% per decade.
I raised the bar (own or next-door decade at least 80%, own decade at least 40%) and said before
running that if it missed, this way of doing it was finished.

| Books printed in | Own or next-door decade | Chance |
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
would have come out 1810s or 1820s, and so would a reprint of a sermon from 1700. The lean moved
with the shape of the library; the date signal never showed up. Finding the nearest passages by
meaning does not tell you when something was printed. I did not run the Book of Mormon, and that
method was done.

One small thing did work, because it is only counting. Five of the book's doctrinal phrases, by
decade, in 31,901 religious books:

| Phrase (times in the Book of Mormon) | In print from | In the 1820s |
| --- | --- | --- |
| infinite atonement (3) | one book in the 1670s, then the 1730s on | a little above earlier decades |
| plan of salvation (3) | 1740s | steady since the 1750s |
| probationary state (3) | 1740s | steady since 1800 |
| demands of justice (4) | 1640s | commonest in the 1720s and 1740s |
| fall of man (5) | throughout | |

None of the five is new in the 1820s. That neither supports nor undoes Campbell. He said the book
took sides in the arguments of his day, not that it coined their words.

**Design three: back to the claim.** After two misses the owner asked me to go back to what
Campbell actually said. A research pass by an AI agent read his review again and made the point I
had skipped: he dated the book's *agenda*, the mix of questions, and every side agrees each question
on its own is old. So two parts: first his list his way, then a test of the mix.

*His list, his way.* Is each of his twenty topics in the 1830 text, by a written rule? Thirteen are.
Seven are not there at any real rate (under 3 mentions per 100,000 words): infant baptism, the
trinity, regeneration, justification, transubstantiation, penance and the call to the ministry.
Then the comparison he didn't make. Of his twenty, religious print of the 1640s holds 13, the 1740s
to 60s 15, the late 1700s 11, and American print of 1815 to 1829, 13. The 1640s cover his list as
fully as the 1820s do. One topic is different: oath-bound secret societies, which he called
freemasonry. The book has 14.5 per 100,000 words; no earlier body has more than 1.3. That fits the
"secret combinations" test, where the newspapers jump in 1828.

*The mix.* Take 39 topics from surveys of sects written at the time (1645, 1646, 1801, 1807, 1817),
not from the book, silences included. Ask whether a text's mix of topics places it in its era, with
six eras from 1640 to 1829 instead of decades, because a first look showed the 1810s and 1820s
can't be told apart. Its check was tougher than before: own era at least 55% in every era, old
reprints must not land late, the 1640s heresy catalogues must land early, and Joseph Smith's own
revelations of 1828 to 1835 must land late.

It missed every bar. Known texts landed in their own era 20 to 50 percent of the time; chance was
about 17%. The old reprints no longer landed late (1 of 20, against 15 of 20 before), which fixed
the second design's fault, but they scattered instead of landing in their authors' eras. Joseph
Smith's revelations were pulled early by their King James wording, one block of four landing where
it should. One thing I should say plainly: the topic rules were run as written, not first checked
by reading samples of what they catch. Those 4,680 readings are prepared and haven't been done.
Whether checked rules would pass is unknown. I didn't score the book.

**What it means, and what it doesn't.** Three designs, three misses. I think that is itself the
finding, and it is about the claim more than about my tools. If texts whose dates I know can't be
placed by which doctrines they discuss, then "it discusses the questions of the 1820s" can't carry
the weight Campbell put on it. Neither can "these are timeless questions" be shown this way. His
list, as a list, is not a fingerprint of the 1820s; most of it is what Protestants argued about for
two hundred years. The one topic that really is new in the book's era is the secret societies.

**What's left.** Which side the book takes on each question, read against writers whose positions
are on record (a simulated model reading, not built yet). The prepared rule-checking readings.
Vogel's chapter, once bought.

### Chiasmus, with something to compare it to (BOM-107)

**The claim.** A chiasm says things and then says them again in reverse order: A, B, C, then C, B,
A. John Welch found them in the Book of Mormon in 1969, and they have been offered ever since as a
mark of ancient Hebrew writing. The reply has been that chiasms turn up anywhere if you look. Boyd
and Farrell Edwards, two physicists, put a number on it in 2004: for a chiasm of n elements, the
chance of that order is one in a very large number, and they gave figures for famous cases (Alma 36,
with eight elements, at 0.00018). They argue the number shows design, not that it shows ancient
origin. What nobody had was the rate in ordinary books.

**Their way first.** Welch's chiasms are found by reading, so there is nothing to rerun. Edwards
and Edwards's formula I could check. Their program is no longer online, so I worked backwards: their
published chances for Alma 36 and Leviticus 24 each imply how many "opportunities" they counted
(365 and 338). One number reproduces both within 8%. So their arithmetic holds together, but I
couldn't reproduce how they counted.

**What I tried.** One fixed rule, run on everything. Reduce the text to its content words. Around
every point, count how many words repeat in mirror order going outward, each word exactly twice, one
on each side. Three or more levels is a chiasm. Then run it on the Book of Mormon, the King James
Bible, 360 library books, 120 translations, 25 Bible-style books and Joseph Smith's other
dictations. To control for how repetitive a text is, the card compared each text with a shuffled
copy of itself.

**The check.** Three parts, before the Book of Mormon was counted. Find at least 4 of 5 well-known
Bible chiasms (in Leviticus, Genesis, Matthew, Isaiah, Mark). Find at least 90% of chiasms I
planted in ordinary prose. And on ordinary library prose, don't fire much above the shuffled copy
(at most 1.25 times).

**When it failed: why, and what I changed.** It failed twice, and both fixes came before the book
was counted. First it found only 2 of the 5 Bible chiasms. Looking at them, short words kept their
endings ("lose" didn't match "loseth"), and a chiasm's span was measured to the wrong word, so every
famous case "spilled" outside its passage. I fixed both. I also tried letting a word repeat three
times, then put it back to exactly twice, because the two fixes alone reached 4 of 5. The miss is
Mark 2:27, where the next verse says "sabbath" and "man" a third time.

Then the plain-prose part failed: ordinary books came out at 1.30 times their shuffled copies,
over the bar. The reason is that shuffling sentences also breaks the way ordinary prose echoes a
word in the next sentence or two, so any real text beats its shuffle. The shuffle wasn't a fair
baseline. I replaced it with a better one: count the same repeated words at the same distances, but
in plain repeated order (A, B, C, A, B, C). For any set of repeated words, mirror order and plain
order are equally likely unless someone prefers one. I wrote the bar for that control before
looking at its number. Ordinary prose came out at 0.95, and the check passed: 4 of 5 Bible
chiasms, 300 of 300 planted ones. I changed this after the first check failed, so the plain-order
comparison counts for a little less than if I'd thought of it first.

**The result.**

| Text | Chiasms per 10,000 words (three levels or more, 40 words each side) |
| --- | --- |
| Book of Mormon | 34.7 |
| King James Bible | 36.4 |
| Library books | 34.7 |
| Translations | 36.6 |
| Bible-style books | 37.4 |
| Joseph Smith's other dictations | 37.4 |

The Book of Mormon sits in the middle of the library, at the 48th percentile. Against plain order,
mirror order comes out at 0.88 of plain order in the Book of Mormon, 0.94 in the King James Bible
and 0.95 in the library. If mirror order were being used on purpose, it should beat plain order.
Nothing is above 1. The same holds with the quoted Bible chapters taken out (0.88).

Alma 36 is the famous one. By this rule, in a tight window, its deepest mirror run is 5 levels, and
only 3 library passages in 1,000 of the same length do that. But the same chapter read in plain
order reaches 6. It is a very repetitive chapter, in both directions. And Edwards's eight-element
odds don't survive a wide window: by this rule, eight levels at the widest setting turn up in about
27% of library passages of the same length, because a wide window holds many repeated words.

**What it means, and what it doesn't.** Counted by repeated words, the Book of Mormon has no more
chiasmus than an ordinary book of its time, and neither does the Bible. That second half is the
limit. A rule that can't tell the Bible from ordinary prose is counting word repetition, not the
idea-level patterns Welch meant. So this says the word-level counts don't set the book apart, and
that odds computed for a single passage need the rate in other books beside them. It does not say
the chiasms people have found by hand aren't there.

**What's left.** Type up Welch's and Parry's published chiasms as test items, each scored against
library passages of the same length. Run the two published automatic detectors (Dubremetz and
Nivre; Schneider and others) as a second rule.

### Other books that were dictated or "received" (BOM-125)

**The claim.** Brian Hales made the case most fully in 2019, in *Dialogue* and again in
*Interpreter*: the Book of Mormon is unlike other books that were dictated, channelled or said to
be given by a spirit. It is longer, more complex, and was produced faster by a man with less
schooling. His figures for the book: 269,528 words, a reading level of about grade 11, 5,600 to
5,900 different words, 337 names. Scott Dunn argued the other side in 2002: automatic writing and
trance dictation do produce long, complex books from people with little schooling, so the Book of
Mormon is not unique in that way.

**Their way first.** Hales compared sixteen channelled texts by length, by how they were produced,
and by their makers' schooling. I could not get his table of sixteen, only his summary figures, so
his comparison itself is not rerun. What I could do was count his numbers for the Book of Mormon
again, on the 1830 text, with the rules written down:

| | Hales | Counted here |
| --- | --- | --- |
| Words | 269,528 | 265,197 |
| Different words | 5,600 to 5,900 | 5,818 |
| Names | 337 | 381 (a different rule) |
| Reading grade | about 11 | 15.6 |

The first three come out close. The reading grade does not, and the reason is printing, not
writing. The 1830 printer ran clauses together into very long sentences, 39.9 words on average,
and reading-grade formulas count sentence length. Hales used a modern edition.

**What I tried.** Hales's comparison is length and schooling. Dunn's is a list of cases. Neither
puts the books on one scale. So I collected 23 long books that were dictated or said to be
received, and measured every one the same way, 20,000 words at a time: Milton's *Paradise Lost*
(dictated blind), five works of Swedenborg, Andrew Jackson Davis's *Principles of Nature*, the
first volume of *Oahspe*, the Koran in Sale's English, Mary Baker Eddy, two Patience Worth novels,
three late novels Henry James dictated, Scott's *Bride of Lammermoor*, and the English prophets
Southcott, Brothers and Wroe, among others. The measures: how many different words, sentence
length, reading grade, names, how often the text repeats its own six-word phrases, and how much of
it is in King James phrasing.

**The check.** Before the Book of Mormon was measured, each measure had to get known cases right.
The six McGuffey readers, graded first to sixth by their compiler, plus Gibbon above them, had to
come out in order. They did, on every vocabulary and sentence measure (rank correlation 0.93 to
1.00, bar 0.85). The name count had to track the number of people and places a Bible
reference database gives for each book of the King James Bible; it did (0.99). And when I planted
repeated phrases and King James verses into Gibbon and the sixth reader, the measures had to find
them; they recovered 97 to 101 percent.

**What failed, and what I did about it.** One measure missed. I had a second way of counting
names, counting only names that turn up at least twice. It tracked the Bible database in order
but came out at about half its totals, short of the bar I had written down. So I dropped it. I did
not adjust it until it passed. Ten measures were left.

**The result.**

| Measure | Book of Mormon | The 23, middle | The 23, lowest to highest |
| --- | --- | --- | --- |
| Different words in 20,000 | 1,679 | 2,625 | 1,672 to 4,226 |
| Words per sentence | 39.9 | 24.4 | 11.3 to 44.8 |
| School grade needed to read it | 15.8 | 10.3 | 4.1 to 18.3 |
| Names in 20,000 words | 75 | 106 | 30 to 442 |
| Share of words in King James phrases | 24% | 2% | 0.4% to 26% |
| Share that repeats its own earlier phrases | 7.0% | 0.9% | 0 to 4.5% |

On eight of ten measures the Book of Mormon is inside the range of the other received books. On
two it is outside, and both point the same way. Its vocabulary is the second narrowest of all 24,
next to Swedenborg's *Divine Love and Wisdom* (1,672). On one version of the vocabulary count it
falls below the lowest received book by two and a half words. And it repeats its own six-word
phrases more than any of them. A typical book in the library uses 3,753 different words in 20,000.
The Book of Mormon uses 1,679. Its King James share is second only to Richard Brothers.

For scale: two Bible-style books of the 1810s and 1820s that were long enough use 2,387 to 2,555
different words in 20,000. Joseph Smith's other dictated texts, pooled, use 1,918, with 17 percent
King James phrasing.

**What it means, and what it doesn't.** By these counts the book is not more complex than other
dictated and received books. It is a long book made from few words, much repeated, with a quarter
of it in the Bible's phrasing. That cuts against the part of Hales's case that rests on
complexity of vocabulary and sentences.

It does not answer the rest of his case. His strongest points are things this cannot count: the
plot holding together across 265,000 words, the flashbacks, the speed of dictation. I did not
compute speed; no dated record was given to the test, and I won't take one from memory. Ten
measures are also really about five families of measure, so "eight of ten" is less independent
than it sounds. And the 23 are my list, not his sixteen. *A Course in Miracles* and the Seth books
are under copyright and not held. *The Urantia Book* is left out until I decide about it. *Oahspe*
is the first of seven volumes.

**One more text, added later.** *The Urantia Book* (1955) was left out at first because its copyright
was disputed. A US court held it invalid, and the foundation that publishes it gives it away, so
in November I added it, after the first result. It changed nothing. It is the richest vocabulary in
the set, 3,042 different words in a 20,000-word stretch against the Book of Mormon's 1,679, so it
widens the range on the far side. The book stays inside on the same eight measures and outside on
the same two. The first result is kept as it was; this one sits beside it.

**What's left.** Hales's own table of sixteen, the rest of *Oahspe*, a modern-punctuated Book of
Mormon for the sentence measures, and the same measures on the book's own parts.

### The geography (BOM-116)

**The claim.** People have fitted the book's lands to southern Mexico and Guatemala (John
Sorenson, 1985 and after, with the Isthmus of Tehuantepec as the narrow neck), to western New York,
to the Mississippi valley (the "Heartland"), and to the whole hemisphere with Panama as the neck.
Behind all of them sits a second claim. John Clark in 1989 and Sorenson in 2000 built a map from the
text alone, before putting it on any real ground. Clark boiled it down to ten points: a narrow neck
between an east sea and a west sea, the river Sidon running from a southern wilderness, Nephi
in a highland about three weeks' travel south of Zarahemla, and so on. Their point is that hundreds
of scattered passages in a long dictated book never contradict that map. Critics answer that a
careful storyteller can keep an invented map straight, and that the Mexican fit needs the book's
"north" turned by 45 to 90 degrees.

**Their way first.** There is no number to rerun here. On every side, the method is to read the
verses, draw a map, and compare it with a region point by point. Nobody has counted how many other
regions would fit as well. Sorenson's place-by-place placements are in books I have not bought, so
his model is not replicated until those are bought. Clark's ten points I keyed by hand from his
1989 article, and I come back to them below.

**What I tried first.** One fixed rule pulled out every sentence that places one named place
against another: north of, up from, by the sea, near, so many days' journey. Then, for a region, a
program found the best real towns for each place, and I compared the region's score with about 400
random patches of the earth. If Mexico or New York beat nearly all the random patches, that would
mean something.

**The check.** First, texts where I know the answer. Step one worked. Put the Bible's places at
their true coordinates and 71 percent of its statements hold, against 29 percent when the same
places are scattered at random. So the sentences do carry real geography.

Step two did not work. Each text had to pick out its own region ahead of 95 percent of the random
ones.

| Text | Its real region | Random regions that fit as well or better |
| --- | --- | --- |
| The Bible's narrative | Palestine | 149 of 398 |
| Josephus, *Antiquities* | Palestine | 119 |
| Josephus, *War* | Palestine | 296 |
| Clavigero's history of Mexico | Mexico | 50 |
| Ramsay's American Revolution | Philadelphia | 327 |

**Why it failed, and what I changed.** With a few hundred towns to choose from, the program could
make almost any set of directions fit almost anywhere. The random patches scored about as well as
the true region in every text. I didn't loosen the bar until the Bible passed; that would have been
fitting the check to its answer. (Tests written after the first run did find a bug, "from the land
of A" being missed, and I fixed it and reran. It missed by the same margin.) So the Book of Mormon
was not scored against any region.

What I could still say about the book's own statements: the rule found 33 of them about 23 places,
and none contradicts another. But they are few. The rule only reads sentences that name both
places, so it misses the long description in Alma 22. It also took Teancum and Moroni for places.
And the book is thin on directions to start with: 8.4 compass words per 10,000, against 23 to 37
in Lewis and Clark, Pike and Carver.

That told me what was wrong. Too few statements, read too crudely, against a map of towns that
gave the program too much freedom. So I tried again.

**A second design, on real terrain.** This time a model read every passage with a place in it
(simulated reading) and turned each into a typed statement: north of, up from, by the sea on which
side, a river running from here to there, so many days' travel. Then a program laid the places out
on real coastlines, rivers and elevation (Natural Earth and NOAA's ETOPO, both public), on circles of
land the size the text covers. The question changed slightly, and on purpose: not "which region
fits best" but "how many circles on Earth could hold the whole map at once?" If almost none can, a
fit means something. If a quarter of the earth can, a fit is cheap. That still answers the
original question, because it is exactly what a "fits region X" claim needs and never reports.

Before the Book of Mormon, five texts whose setting is known had to pass: the Bible's narrative
books, Josephus, Xenophon's march, Lewis and Clark, and *The Late War*. Each had to fit its own
region and fit at most 5 percent of the earth. And Clark's own method, tried on the Bible, had to
rebuild three plain features of Palestine.

None passed.

| Text | Circle size | Share of the earth's circles it fits | Its own region? |
| --- | --- | --- | --- |
| The Bible's narrative | 1,200 km | 58% | yes |
| Josephus, *War* | 4,800 km | 96% | yes |
| *The Late War* | 2,400 km | 93% | yes |
| Xenophon | 4,800 km | 12% | no |
| Lewis and Clark (338 statements) | 4,800 km | 0 of 25 | no |

Two more things failed. When the model read the same passages twice in different formats, the two
readings agreed barely better than chance (kappa 0.26, against a bar of 0.7). And Clark's method on
the Bible rebuilt one of the three Palestine features (the Jordan running south into the Salt Sea),
not the sea to the west or the hill country up from Jericho.

**The result.** The Book of Mormon was not scored on fit, either way. I got some side facts without
needing the reading. On Clark's own scale for the narrow neck, about 4 days' travel at 15 to 40 km a
day, no proposed isthmus fits across his east-west axis: Tehuantepec is 245 km across, Panama 231
km east to west, Niagara 272. Most of Clark's points cannot be graded at all without Sorenson's
placements. And the radiocarbon databases hold 5 dates from 1000 BC to AD 1000 within 300 km of
Tehuantepec, 0 near Panama and 398 near the Great Lakes, so dated occupation cannot be compared
fairly between the settings with open data.

**What it means, and what it doesn't.** I think the two failures are the finding. The more a text
says, the more chances one misread statement has to rule out every place, its own included. That is
what happened to Lewis and Clark. The less it says, the more places it fits. So the count measured
how much each text says and how well it was read, not where it is set.

For the debate: "the geography fits region X" needs two things nobody has shown, for any region, on
any side. One is a reading of the book's statements that two readers agree on. The other is a scale
at which even the Bible picks out Palestine from the rest of the world. That applies equally to the
claim that it fits nowhere.

**What's left, and in progress.** The second design has one more part, and it is running now. It
asks a different question: do real maps contradict themselves less often than invented ones
(*Gulliver*, *Treasure Island*, *The Mysterious Island*, Spalding's manuscript)? It has its own
check: real and invented maps have to separate cleanly before the Book of Mormon is placed between
them. A model is reading those texts now (3,687 questions, then 467 on the book). After that,
Sorenson's placements, once the books are bought.**The consistency half, read.** The other half of the second design asked a different question:
do real maps contradict themselves less than invented ones? Supporters often say the book's
geography is remarkably consistent. That only means something if invented geographies are not.

The model read every place passage in seven real first-hand travel accounts and ten invented
stories. The real ones gave plenty: Park's African travels 308 statements, Pike 158, the Bible
narrative 104. The invented ones gave almost nothing. *Gulliver* 9 statements. *Treasure Island*
2. The Oz books 2 and 1. Spalding's manuscript 4. Only *The Mysterious Island*, with 16, gave
enough for even one chance to contradict itself. The check needed six of each with a measurable
rate and got seven real and one invented, so it gives no verdict.

That is the finding. Invented stories in this set barely describe their geography at all, so
"the Book of Mormon's geography never contradicts itself" has nothing to be compared with here. The
book gave 29 statements, 2 chances to contradict, and 0 contradictions. A real comparison needs
invented worlds that are described in detail, the kind built on purpose with maps.



### "Secret combinations" (BOM-123)

**The claim.** The Book of Mormon calls the Gadianton robbers a "secret combination". In September
1826 William Morgan vanished in western New York after threatening to print the Masons' secrets,
and the anti-Masonic movement began. Dan Vogel argued in 1989 that around 1830 the phrase meant
Freemasonry "almost exclusively", so the robbers echo the anti-Masonic years. Daniel Peterson
(1990, 1992), Paul Mouritsen (2003) and others replied that it was an ordinary phrase for any
conspiracy. Peterson's example: Andrew Jackson, himself a Mason, used it of Henry Clay's
supporters in December 1826.

**Their way first.** Both sides argue from examples. Vogel quotes anti-Masonic newspapers using the
phrase of the Masons. Peterson and Mouritsen quote uses that have nothing to do with Masons. Nobody
reports a share by year, and that is the thing the dispute turns on. I have not read Vogel's article
itself, so his examples are not rechecked here. I went straight to the count both sides needed.

**What I tried.** I counted every use in 209,467 books printed 1700 to 1830 and 114,633 newspaper
pages from 1800 to 1830. There are 926.

| Years | Uses in books, per million words | Uses in newspapers, per million words |
| --- | --- | --- |
| 1780 to 1799 | 0.068 | none held |
| 1800 to 1819 | 0.036 | 0.050 |
| 1820 to 1825 | 0.084 | 0.039 |
| 1827 | 0.069 | (2 uses) |
| 1828 | 0.105 | 0.59 |
| 1829 | 0.060 | 0.54 |
| 1830 | 0.082 | 0.15 |

**The check, part one.** A counter has to see a real change when there is one. The word
"anti-masonic" had to rise; it went from 0.001 per million words before 1826 to 3.5 in 1827 to
1830, more than three thousand times. Steady phrases had to stay steady; "of the" and "in the course
of" stayed within 1.2 times their middle rate. Passed.

So two things are plain from the counts. The phrase was not new: it is in print through the whole
century before. In books its rate does not move when the Morgan affair breaks. In newspapers it
does jump, about tenfold, in 1828 and 1829.

**When it failed: the word rule.** The counts cannot say what each use is about, and that is the
whole dispute. My first try was a rule: call a use Masonic if a word like "mason" or "lodge" stands
within 30 words of it. I tested the rule on books whose titles settle the subject. In books about
Freemasonry it found only 16 of 37 uses, against a bar of 75 percent.

Reading the misses showed why. Anti-Masonic writers used "secret combination" as a *name* for
Masonry: "a powerful, secret combination", with no "Mason" anywhere near it, because the whole book
was about Masons. So the rule undercounts exactly the uses that matter. It also turned out that one
passage was reprinted in four or five books, so it counted four or five times. I did not use the
rule and did not go on to the Book of Mormon.

**What I changed, and why it still answers the question.** I changed this after seeing the first
result, so it counts for a bit less, and I allowed myself only one more try. A model (sonnet; this
is simulated judging) now reads 150 words each side of each use, enough to see what an epithet
refers to. It is not told the book's title or the year, since the title is how the check sample was
chosen and every Masonic-titled use is from 1827 on. Reprints count once. Two other changes: the
trade-titled check group had only 20 uses, so trade and politics were pooled, and the Masonic group's
minimum came down to 20 because counting reprints once shrinks it. I wrote all of that down before
asking the model anything.

On the way I found a flaw in my own title list: 13 of the 20 "trade" uses came from one captivity
memoir, there only because its title says "manners and customs". It doesn't matter for the check,
which only asks "not Masonic", but it is the kind of thing that hides in a word list.

**The check, part two.** The model called 21 of 26 passages in Masonic-titled books Freemasonry
(bar 75 percent), and none of the passages in trade or politics books. Passed. Then it read a sample
of 826 uses, up to 40 a year. That run was cut at 575 by a machine shutdown and picked up where it
stopped.

**The result.** Vogel's bar, written down before anything was read: at least 9 in 10 uses Masonic in
1827 to 1830 would be a yes; half or fewer a no.

| Years | Share of uses that mean Freemasonry |
| --- | --- |
| 1800 to 1825 | 0 |
| 1826 | 14% |
| 1827 | 19% |
| 1828 | 33% |
| 1829 | 50% |
| 1830 | 45% |
| 1827 to 1830, together | 38% (157 uses) |

The answer is a no. Before 1826 the phrase was almost always political: a faction, or a plot
against a government. After Morgan, a Masonic meaning grows, but it never becomes most uses.

Newspapers look different at first. Of 18 uses before Morgan disappeared, none are Masonic. Of 34
after, 28 are. That would be Vogel's pattern. But when I looked at where they came from, 23 of the 28
are from one paper, the *Pawtucket Herald and Independent Inquirer*, which we hold from September
1828 on. It is about anti-Masonry on 202 of the 279 pages we have. So the newspaper jump in the
table above is mostly one anti-Masonic weekly in a thin sample of seven titles. None of them is from
New York.

The Book of Mormon's own 20 uses read as robber bands (15), some other secret society (3) or
political plots (2), none as Freemasonry. Joseph Smith's other texts have 4, all crime or a society.
The Bible-style books have none at all.

**What it means, and what it doesn't.** Peterson's side is right that the phrase was old and
general. Vogel's side is right that a Masonic meaning rose after 1826, to about half the uses by
1829. "Almost exclusively" does not hold in the print we have.

What this cannot do is say what the writer of the Book of Mormon had in mind. The model reads the
literal referent. A writer describing robber bands bound by oaths, and meaning the Masons by
analogy, gets labelled "crime". That analogy is the actual argument, and counting cannot reach it.
Nobody has read the model's labels by hand yet.

**What's left.** A hand check of a sample of labels. New York papers of 1827 to 1830, which we do not
hold; the *Wayne Sentinel* and the Palmyra *Reflector* are the ones to find, and that is where the
question really sits.

### Joseph Smith's other dictated texts, and the Lectures on Faith (BOM-104)

**The claim.** Two questions that need the same tool. First: who wrote the
seven Lectures on Faith, printed in 1835? Alan Phipps's 1977 master's thesis gave six of them to
Sidney Rigdon, four of those with Joseph Smith editing, and Lecture 5 to Smith. Wayne Larsen, Alvin
Rencher and Tim Layton in 1980 gave five to Rigdon, Lecture 2 to Smith and Lecture 5 to W. W. Phelps.
So the "Lecture 2 or 5" puzzle I had from the summaries was really two studies giving different
answers. Noel Reynolds in 2005 gave all seven to Rigdon. Second: do Smith's later dictated texts,
the Book of Moses, the Book of Abraham and the revelations, sit near the Book of Mormon, near his
ordinary writing, or near someone else?

**Their way first.** I now have all three studies in the original, and they are more alike than I
thought.

Phipps used the same five men I did: Smith, Rigdon, Oliver Cowdery, W. W. Phelps and Parley Pratt.
A historian, Peter Crawley, had proposed them to him. He took about 12,000 words from each man (twice
that for Smith) and cut the quotations out by hand. That left 12,006 words of lectures. He counted
738 small words and phrases and used the 50 commonest. For each word and each pair of men, the
question was simple: is the lectures' rate above or below the middle of the two men's 2,000-word
blocks? Then he multiplied the odds together. Taken as one text, the lectures went to Rigdon over
everyone: 291 to 1 over Smith, 1,694 to 1 over Cowdery, 174,883 to 1 over Pratt. Lecture by lecture
it came apart. On Lecture 2, five of his six tests named Smith, but his final table still gives it
to Rigdon, with Smith editing. As far as I can see, he never tried the method on writing whose
author he already knew.

Larsen's paper is mostly about the Book of Mormon, but a one-page appendix takes up the Lectures.
They used Phipps's own computer disk for the five men, so the texts are his. The method was
different: a discriminant analysis on eight words the computer picked from their list of 38. Their
answer: Rigdon for 1, 3, 4, 6 and 7, at probabilities of .988 to 1.0. Smith for 2 at .524, with
Rigdon second at .339. Phelps for 5 at .461, with Pratt next at .367. They put 88.9% of the men's
own blocks back with the right man, but those were the blocks the method was built from. None was
held back.

Reynolds is mostly history, but not only that. He paid a reader to go through Rigdon's essays and
pick out his habits of phrase. The reader found 38, things like "the sacred writers" and "saints of former
days". They come 163 times in about 77,000 words of Rigdon, 98 times in the Lectures, and never in
about 79,000 words of Smith's letters and diaries.

Reading them taught me two things. Pratt was never a decoy. Phipps and Larsen both had him as a
candidate, and he is Larsen's second choice for Lecture 5. And the "Rigdon" in all three studies is
the same unsigned 1833 to 1835 newspaper series I added in my second try: Phipps's whole Rigdon
sample, and the core of Reynolds's. Everyone, me included, takes that attribution on trust.

So did I reproduce them? I tried, and wrote down before I started what would count. First I rebuilt
Phipps's five samples from his tables, because all three studies used them. Most of it is held. The
church papers I took from a clean transcription of each issue online, because my scan of them runs
the columns together. Three things I had to fudge, and I'll say so each time. Pratt's 1835 pamphlet
on the Kirtland outrage, a quarter of his sample, I don't have, so later pages of his *Voice of
Warning* stand in for it. Six of Smith's letters I don't have, and for the biggest, his December
1838 letter to the church, I used his March 1839 letter to the church from the same jail. And
Phipps cut quotations out by hand. I can only cut what matches the King James Bible or the other
scriptures, so quotations from anywhere else stay in. That made Smith's articles a bit short: three
2,000-word blocks instead of four.

Larsen's way did not come back. I gave the computer his 38 words and let it pick eight the way his
did. It picked when, upon, unto, the, it, now, that and yea. Then I put each lecture to it. It agreed
with Larsen on three of seven: Rigdon for 1, 3 and 4. It gave 2, 6 and 7 to Phelps, and 5 to Smith.
The bar I set was six of seven. It also showed why their 88.9% says little. Put back on the blocks it
was built from, mine scores 97%. Hold one block out at a time and pick the eight words again without
it, and that drops to 67%. On new blocks of each man's writing that it never saw, it got 10 of 19
right. Guessing gets about 4. So that kind of analysis, on samples this size, can be pushed a long
way by which texts go in.

Phipps's way held up better. I could only use 24 of his 50 words; the other words he sorted by
hand into grammar types, and I can't redo that. On the Lectures as one text, Rigdon beats Smith
1,582 to 1. Phipps had 291 to 1. Rigdon beats everyone else too, but by far less than Phipps found:
7 to 1 over Pratt where he had 174,883 to 1. Lecture by lecture, Smith against Rigdon comes out the
same way as his table on six of seven. The one that flips is Lecture 4, which I give to Rigdon at
about 5 to 1 where he gave it to Smith at 13 to 1. My odds are tens to one, not millions. Then the
step he skipped. I gave the same test new blocks of each man's own writing, blocks it had never
seen. The true author won 76% of his match-ups. Smith against Rigdon, it was right eight times out
of eight.

Reynolds's count came back too, with one catch. His reader's phrases come to 1.6 per 1,000 words in
Rigdon's three series (Reynolds had 2.1) and 4.1 per 1,000 in the Lectures (he had 4.1). In Smith's
letters and diaries I don't get his zero: 28 hits in about 97,000 words, 0.29 per 1,000, which
misses the bar I set of under 0.2. But every one of those
comes from seven plain words and pairs that I could only search for bare, like "facts" or
"calculated". A program can't tell when "facts" is a debating trick, as his reader could. Then I
counted the same phrases in Cowdery,
Phelps and Pratt, the test he never ran. With every phrase in, Cowdery reaches 94% of Rigdon's rate
and Phelps 52%, which by my own rule would mean the list marks the 1830s sermon, not Rigdon. I had named the seven plain words before the run and said I'd report them apart, but my rule was
written on the full list, so what follows counts for less. Take out the seven plain words and the
picture flips. The other 31 phrases come to about 1.0 per
1,000 in Rigdon, 3.0 in the Lectures, none in Smith, and only 0.1 in each of the other three men. The
specific phrases really do mark Rigdon and the Lectures and almost no one else here. One caution:
they were picked from Rigdon's own essays, so his count is partly built in. The Lectures and the
other three men were not used to pick them.

So, side by side: Phipps's main answer reproduces, and his method passes a check he never ran.
Larsen's does not reproduce on rebuilt texts. Reynolds's phrases reproduce, and they pass his
missing control once the plain words are set aside. My own lean from the second try agrees with my
rerun of Phipps's Smith-against-Rigdon odds on five lectures (1, 2, 3, 4 and 7) and differs on 5 and
6. All three studies, and both my tries, lean on the same unsigned Rigdon series, so that shared
starting point is still taken on trust.

**What I tried.** Before asking who wrote the Lectures, I asked whether any measure could tell the
candidates apart on writing I know is theirs. Five men: Smith, Rigdon, Oliver Cowdery, W. W. Phelps
and Parley Pratt. Pratt I first called a decoy, thinking no published study named him; reading the originals later showed that Phipps and Larsen both had him as a candidate. Six measures: common words
counted two ways, the study's two style encoders, and small author models at two training sizes.
King James phrases were cut out of everything first.

**The check.** Ten held-back 1,000-word pieces from each man; every measure had to say whose they
were. Guessing gets 2 in 10. The bar was 8 in 10 on average, and no one below 5.

| Measure | Smith | Rigdon | Cowdery | Phelps | Pratt |
| --- | --- | --- | --- | --- | --- |
| Common words | 5 | 1 | 6 | 6 | 7 |
| Common words, second way | 9 | 2 | 7 | 6 | 6 |
| Style encoder one | 6 | 3 | 8 | 0 | 8 |
| Style encoder two | 7 | 6 | 6 | 1 | 8 |
| Author models, light tuning | 6 | 1 | 7 | 1 | 2 |
| Author models, heavier tuning | 10 | 4 | 8 | 1 | 6 |

**When it failed, and why.** Nothing reached the bar. Rigdon, the man the published studies name,
was the hardest to recognise, and Phelps was nearly invisible. So I scored neither the Lectures nor
the dictated texts, and at that point this could neither confirm nor contradict the Rigdon
attribution.

The likely reason was the samples. Rigdon's signed writing here came to about 20,000 words. Four of
the five men were printed in the same two church papers, perhaps through the same editor's pen.
Smith's known writing is letters and a history, not doctrine.

I also got one thing wrong in the procedure. The author-model program scored every text in one
pass, so numbers for the Book of Mormon and the Lectures were computed and saved before the check
had been read. I have not looked at them, and the program now refuses to read them when the check
fails. It should have been two passes, and in the second design it was.

**What I changed.** I changed this after seeing the first check fail, so it counts for less, and I
allowed one more try only. The change was the one the failure pointed to: more text. I added 18
more of Smith's letters and notes, and two long series from the 1833 to 1835 church paper that the
editor of Rigdon's collected writings gives to Rigdon. They are unsigned, so that attribution is the
editor's, not the paper's. Phelps had too little text to meet the new size rule and was dropped.
Every man got 20 training pieces instead of 8. And because Rigdon's series quote the revelations, I
cut any eight-word run a candidate shares with the scripture texts, so nobody looks close to a
target just by quoting it.

**The check, again.** One measure of six passed: common words, counted the first way, at exactly 8 in
10 (Smith 9, Rigdon 5, Cowdery 9, Pratt 9). Move one piece and it fails. The encoders and the author
models, the tools behind the main study's findings, all missed again. So everything below rests on
one measure that barely qualified. Read it as a lean.

**The result.**

| Lecture | Closest | Next | Phipps 1977 | Larsen 1980 |
| --- | --- | --- | --- | --- |
| 1 | Rigdon | Pratt | Rigdon | Rigdon |
| 2 | Smith | Pratt | Rigdon, Smith editing | Smith (Rigdon close) |
| 3 | Rigdon | Pratt | Rigdon, Smith editing? | Rigdon |
| 4 | Rigdon | Pratt | Rigdon, Smith editing? | Rigdon |
| 5 | Pratt | Smith | Smith | Phelps, then Pratt |
| 6 | Rigdon | Pratt | Rigdon, Smith editing | Rigdon |
| 7 | Rigdon | Pratt | Rigdon | Rigdon |

(Reynolds: Rigdon for all seven.)

Five of seven go to Rigdon, as both earlier studies said. Lecture 2 going to Smith matches Larsen,
and five of Phipps's six lecture-by-lecture tests, though not Phipps's final answer. But every margin is thin, and in Lectures 3 and 4 the 1,000-word pieces
vote for Pratt even though the whole lecture goes to Rigdon. The runner-up is nearly always Pratt,
whom no study chose for any lecture, and Pratt also takes Lecture 5, the shortest at 650 words.

For the dictated texts, the same measure puts the revelations of 1828 to 1834 with Smith's own
letters (47 of 52 pieces), the Book of Moses nearest the Book of Mormon, and the Book of Abraham
nearest Pratt. None of these is firm enough to call by the rule I set. I see no drift away from the
Book of Mormon over the years. Rigdon is never the closest to any of them.

**What it means, and what it doesn't.** A man no study chose who keeps coming second is the measure recognising a
kind of writing, the doctrinal essay of the 1830s, more than a man. And the Rigdon text I added is
that same kind, from those same years, which favours him on genre as much as on person. So: a lean
toward Rigdon for most of the Lectures, on one measure that barely qualified. It neither settles the
question nor overturns the earlier studies.

On the dictated texts, the revelations sitting with Smith's letters by common words does not
contradict the main study, which put the revelations with the Book of Mormon. That finding came
from the encoders and author models, and those did not pass this check.

**What's left.** An interval on each lecture's winner. Pratt's 1835 pamphlet and the missing Smith
letters, if a free copy turns up. Phipps's other 25 words, with the grammar coding done by a simple
tagger. And Reynolds's 31 specific phrases counted across the library's other 1830s preachers,
not just these five men.

### Does it read like a translation? (BOM-102)

**The claim.** Two versions of one claim. The broad one: translated books carry marks of
translation, and the Book of Mormon has them. The narrow one, made by John Tvedtnes (1970, 1991),
Donald Parry (2002), Daniel Peterson (2002) and Royal Skousen (1994): it has particular Hebrew turns
of phrase. "Plates of brass" for "brass plates", "dreamed a dream", "and it came to pass". And the
one Skousen stresses most: "if ... and" sentences, like "if ye will ..., and ye shall ...", which he
says the original text had and later editions removed. Tvedtnes gave a count too: "land of promise"
22 times against "promised land" 10.

The hard part of both versions is the same. Plenty of Americans before 1830 wrote whole books in
Bible style on purpose: *The Late War*, the *Chronicles of Eri*, *The First Book of Napoleon*. None
had a Hebrew original. A test that cannot tell those from real translations only detects Bible
style.

**What I tried first.** I skipped their way at first, which was a mistake I fixed later. Two parts.

The broad part: I trained a classifier on 695 books the library catalogue marks as translations and
1,387 written in English. To pass, it had to be right on books it had not seen, call the King James
Bible, Sale's Koran and Whiston's Josephus translations, and *not* call the Bible-style imitations
translations.

The narrow part: ten rules, one for each claimed construction. A rule was kept if the construction
is at least twice as common in the King James Old Testament as in ordinary prose of the time.

**The check, and the first failure.** The classifier was right 88 percent of the time on unseen
books. But no version did all three things at once. As written, it called all the real translations
translations but let most imitations through as well: it scored *The Late War*, a history of the War
of 1812, as more of a translation than the King James Bible. I tried one fix, after seeing that
result: train only on the books whose catalogue record is firmest. That pushed every imitation below
the line, but it pushed both Josephus translations below the line too. Missed again. So I did not
score the Book of Mormon on "reads like a translation".

The narrow part did run. Seven of ten rules passed their check. Per 10,000 words:

| Construction | Book of Mormon | King James Old Testament | Highest Bible-style imitation | Other translations from Hebrew | Ordinary prose |
| --- | --- | --- | --- | --- | --- |
| "it came to pass" | 59.3 | 8.7 | 38.8 | 0.6 | 0.1 |
| "of" + material ("rod of iron") | 2.8 | 5.7 | 4.7 | 1.3 | 1.0 |
| "dreamed a dream" kind | 0.36 | 0.54 | 1.36 | 0.07 | 0.05 |
| "by the hand of", "from before" | 4.5 | 3.6 | 4.2 | 0.5 | 0.1 |
| "and ... and ... and" | 13.3 | 18.2 | 47.1 | 1.6 | 2.4 |
| "his ... and his ... and his" | 11.9 | 9.1 | 19.1 | 1.7 | 1.2 |
| "because that" | 1.2 | 0.25 | 0.64 | 0.02 | 0.06 |

On four of the seven, some English imitator with no Hebrew in front of him uses the construction as
much as the Book of Mormon does, or more. On the other three ("it came to pass", the compound
prepositions, "because that") none quite does.

Look at the fifth column, though. Translations from Hebrew other than the King James Bible barely
have any of these. So they are not marks of Hebrew coming through into English. They are marks of
the King James Bible's English. The Book of Mormon overshoots the Bible on three of them: "it came to
pass" at seven times the Old Testament's rate. Joseph Smith's Book of Moses does the same (27.8).

And the rule Skousen cares about most, "if ... and", could not be tested at all. The King James
Bible does not have it (it is said to have been translated away), so my check, which leaned on the
King James rate, had nothing to stand on.

**What that told me, and what I changed.** Two things. First, I had not gone back to the claim and
checked their own examples, which is where every test should start. Second, any feature the King
James Bible carries is useless for this question, because an imitator copies it straight from the
Bible. The one route left is constructions the King James translators *removed*. An imitator of the
King James could not have picked those up from it. I built the second design after seeing the
first results, so it counts for less.

**Their way, this time.** I keyed every verse that Tvedtnes, Parry, Peterson and Skousen cite for a
Hebraism, 170 items, and checked each in the 1830 text.

| Source | Found as cited | Reads differently in 1830 | Not found |
| --- | --- | --- | --- |
| Tvedtnes 1991 | 80 | 11 | 2 |
| Tvedtnes 1970 | 6 | 0 | 0 |
| Parry 2002 | 47 | 5 | 3 |
| The if-and lists (Skousen 1994, Parry 2007) | 12 | 0 | 0 |

So their examples are there, nearly all of them. Most of the "reads differently" are spelling
("marvellous"). "Land of promise" is 22 times, as claimed; "promised land" is 20, not 10. Parry's
counts of "and"s in his long verses are exact. One if-and case (Helaman 12:13) I could not locate.
The eleven that should be in the 1830 text are there, and all eleven are in the printer's manuscript.
Peterson's point that English Bibles do not have if-and at his Genesis verses holds: the King James
and Young's translations read "then" or nothing. A fourteenth case needs Skousen's *Analysis of
Textual Variants*, which I have not bought, so that one is not replicated until the book is bought.

**The second check.** I built the list of removed constructions from the Hebrew text itself. The
King James keeps the doubled verb ("dying thou shalt die") in about 1 percent of the Hebrew places,
the "in his eating" kind in none, and if-and in about 1 percent. Four parts had to pass, and two
missed.

Very literal English translations from Hebrew were supposed to show these constructions at three
times the King James rate. Two of three did: Ainsworth's 1627 translation has the doubled verb 35
times as often; Young's has "in his eating" 27 times as often. The third did not, and it is the one
that matters most to the claim. Ainsworth and Young, the two most literal English translations I
have, use if-and no more than the King James does. English translators of Hebrew, even stubborn
ones, just did not write it. My if-and rule also finds only 4 of the 11 cited cases in the Book of
Mormon, so the rule is weak too.

And books that only pretend to be translations were supposed to score like the King James. *The Late
War* did, the hard case from the first design. But Macpherson's *Ossian* scored 3.8 times the King
James level, and the fake *Book of Jasher* of 1751 scored 3.0. Neither came from Hebrew. One came
from an imagined Gaelic, and one from nothing.

So I did not score the Book of Mormon.

**What it means, and what it doesn't.** Their examples check out, almost to the verse. Finding the
examples is the easy half, though. The claim is that an English author would not have produced them,
and on that the two designs say:

- The features people usually cite are King James English. Imitators produce most of them, and other
  translations from Hebrew don't. They show closeness to the King James Bible, which nobody disputes.
- English writers reaching for an ancient sound produce some of the removed constructions on their own.
  That is a point against using them as marks of Hebrew.
- If-and, the star example, is so rare even in literal translation that there is nothing to compare
  the book's eleven cases to. That cuts both ways. I cannot show an imitator would write it, and I
  cannot show a translator would.

**Checking the rules' hits.** All the second-design counts came from rules nobody had checked. So a
model read the hits, up to 150 per feature and book, and said whether each is the real construction
(simulated judging). First it had to pass its own check on made-up sentences with known answers. It
did: 20 of 20 on the doubled verb, 20 of 20 on if-and, 18 of 20 on "in his eating", against a bar of
18. Then the hits themselves:

| Feature | Where the rule found it | Real, as the model read them |
| --- | --- | --- |
| Doubled verb | Ainsworth | 98 of 104 |
| Doubled verb | Young | 24 of 35 |
| Doubled verb | King James | 3 of 11 |
| "In his eating" | Young | 145 of 150 |
| "In his eating" | King James | 12 of 21 |
| "In his eating" | *Ossian* | 2 of 43 |
| "In his eating" | *A True Relation of the Holy War* | 2 of 16 |
| If-and | Young | 3 of 18 |
| If-and | Ainsworth | 0 of 4 |
| If-and | King James | 0 of 15 |

Two things come out of that. First, *Ossian*'s high score was mostly the rule's mistake: 41 of its 43
"in his eating" hits are not the construction. So the second part of the check that failed, the fake
translations scoring high, failed partly on false matches. The rule picked up things that look like
the construction and aren't.

Second, if-and. The literal translations barely have it, and now even the few hits mostly aren't
real: 3 of 18 in Young, none of 4 in Ainsworth. That was the part that could not be rescued, and it
isn't. The test needs three features that literal translators keep and the King James drops, and
with if-and gone there are only two. So the check still fails, and the Book of Mormon is still not
scored. The design also asked for a person to check 50 hits per feature by hand. That has not been
done, so this is the model's reading only.

**What's left.** A person's check of a sample of hits, if wanted. A better if-and rule, and a third
removed construction that literal translators keep (casus pendens, the cognate split), as a new
design written before it runs.

### Spoken or written? (BOM-106)

**The claim.** Everyone who was there said the book was spoken aloud to scribes. William Davis argued
in 2020 that it shows the habits of a practised oral performer, especially "laying down heads": the
preacher's trick of announcing an outline, then expanding each point.

**Their way first.** Davis gives examples, not a rate. I have not bought his book, so his "heads"
passages are not keyed and his examples are not checked. Not replicated until the book is bought. I
could count one simple version, numbered heads like "firstly ... secondly", and I did (below). But the
broader question, does the text itself read like speech, needed something nobody had built: speech
from the time to compare with.

**What I tried.** The best spoken English there is from the period: a million answers given by
witnesses at the Old Bailey in London, taken down in shorthand as they spoke; trials reported the same
way; and sermons taken down by shorthand writers in the pews. On the other side, printed sermons and
ordinary written prose. I counted 25 marks of speech in 1,000-word pieces (short words, few new
words, repeated phrases, "did", "that", restarts like "I say" and "or rather") and trained a simple
score on them. Zero is the middle of the written texts and one is the middle of the spoken ones. All
punctuation was stripped first, since the original manuscript has none.

**The check.** It had to tell speech from writing on texts it had not seen, at least 85 times in 100.
It did, 96. The hard case was a sermon taken down from the pulpit against a sermon written for print.
The bar was 75. It got 76, which just clears. I set one more rule before
looking at the book. If the King James Bible or the Bible-style imitations scored as speech, the score
would only be reading Bible manner, and the answer would be "cannot tell" whatever the book did.

**What went wrong on the way.** After the first full run I found a reading bug. The scribes wrote "&"
for "and", and my reader was dropping it. The original manuscript came out with 4.4 "and"s per 1,000
words, which is impossible for this text. I fixed it and reran everything, the check included. The
check barely moved (96 and 76 both times). Only the manuscripts and Smith's revelations changed much.

I also added two things after seeing the check, so they are extra, not part of the verdict: a scale
set by the sermons alone, and a breakdown of which marks lift each score.

**The result.**

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
courtroom testimony, well above the Bible, and far above the imitations of the Bible. Every main
narrator does (Nephi 0.98, Jacob 0.81, Mormon 0.85, Moroni 1.07), and the book's sermons score about
the same as its narration (0.82 against 0.90). Taking the "and" marks out changes nothing (0.95).

Davis's heads, counted the simple way: the book announces numbered points 0.03 times per 1,000 words.
Printed sermons do it 0.19 times. So on that narrow version, the book does it less than written
sermons do. That doesn't test his fuller claim, an outline announced in plain words and then filled
in, which needs his passages.

**What it means, and what it doesn't.** What lifts the score is mostly repetition: few new words, the
same four-word phrases coming round again, "that", "did". Those are marks of speech. They are also
marks of this particular book, as the test on dictated books showed (it has nearly the narrowest
vocabulary of 24). The plain marks of someone talking, the restarts and "I say", are rare in it. So
"like speech" here means "repetitive and formulaic the way speech is", not "full of slips".

And dictating does not by itself make a text score as speech. Milton dictated *Paradise Lost* and it
scores as the most written thing on the list. Henry James and Scott dictated novels that score as
writing. A composed work stays composed when spoken to a secretary. So the score does not measure
whether a text was dictated. It measures whether it was put together the way people talk, in the
moment, leaning on formulas. On that, the Book of Mormon sits with the talkers.

Bible style alone does not get a text to 0.88. The imitations copy the Bible's "and"s and its cadence
and score 0.17. But the King James Bible itself sits at 0.46, just under the line I drew at 0.5, so
the score does read part of the Bible's manner. And the check passed narrowly on the case that matters
most, sermons against sermons. The score tells courtroom talk from print far better than it tells
preached speech from print.

**What's left.** Refit with the repetition marks and "did" taken out, to see whether the book still
clears the Bible. More shorthand sermons for the weak side of the check. A person to read the list of
titles the rule sorted (nobody has yet). And Davis's heads, counted properly, once his book is bought.

### The Isaiah chapters and Adam Clarke (BOM-122)

**The claim.** About a third of Isaiah is quoted in the Book of Mormon, mostly word for word from the
King James Bible, but not entirely. Colby Townsend argued in 2025 that some of the changes follow Adam
Clarke's commentary, the big Methodist Bible commentary that was coming out in the 1820s. Kent
Jackson replied the same year that none of Townsend's cases shows dependence on Clarke. Both argued
from about a dozen verses.

**Their way first.** I now have Townsend's article itself: "Early Nineteenth-Century Biblical
Scholarship and the Production of The Book of Mormon", *Journal of the Bible and its Reception* 12
(2025), pages 57 to 84. Until now I had built his list of examples from Jackson's reply. So I went
through the article one example at a time.

First, how strong his claim is, in his words. The summary says Smith "likely used" Clarke's
commentary. On page 66 he says he is "convinced, based on the evidence," that Smith dictated Isaiah
straight out of Clarke's volume. In the conclusion, Clarke's notes would have been what Smith needed
"if he ended up using it" (p. 82). He also says Smith did not copy Clarke slavishly. So many of his
examples are partial on purpose: Clarke's note suggests one thing, and the book does something
related.

His method is close reading. He gives no counts. He doesn't say how many of the book's changes he
checked against Clarke, or how many matched, and he doesn't hold any other commentary up beside
Clarke. He does make one claim I can test: on page 64 he says he could not find these phrases in any
other English commentary on Isaiah before 1830. He worked from the 1825 New York printing of Clarke,
which is the same printing I have.

He discusses twelve passages. He ties eleven to Clarke. The twelfth, "ships of the sea" at Isaiah
2:16, he says Clarke does *not* explain, and he points to Wesley's notes, William Lowth, Thomas
Scott and others instead. There's no appendix with more. Jackson's reply answers the same eleven, so
the list I'd built from Jackson was complete.

Then I looked each one up in what I already had: my list of the book's changes, the wording search
of the whole library, and the model's reading of twelve commentaries' notes at each change
(simulated judging). I ran no new model. Across his twelve passages he names 25 changes, and 18 of
them are in the set I searched.

| Isaiah | What Townsend says Clarke has | What I found | Jackson's reply |
| --- | --- | --- | --- |
| 11:6 (2 Ne 30:12) | "then shall the wolf" | Clarke never asked (bad scan, below); other works 0 of 10 | "then" is added in four other places too |
| 11:4 (2 Ne 30:10) | cross-references | not in my set: a 40-word addition, and the claim is about cross-references, not a reading | it's Nephi's own comment |
| 50:2 | "their fish is dried up" | model read Clarke's note: no. Other works 0 of 8 | in the book the waters dry up, not the fish |
| 2:10, 19, 21 | a line Clarke restores to verse 10 | verse 10's addition is too long to search; "shall smite them" at 19 and 21: Clarke no, other works 0 of 11 each | no words in common |
| 2:12-14 | cedars mean princes, hills mean kingdoms | "upon all the nations": Clarke no, other works 0 of 11 | no shared wording |
| 2:16 | Townsend says not Clarke | too long to search | not discussed |
| 9:3 | "thou hast increased their joy" | **Clarke yes; the other eleven works all no** | Clarke reads "its joy", which isn't the same as dropping "not" |
| 14:3-4 | "in that day" | Clarke never asked (bad scan). Printed at this verse by 2 older books, 1669 and 1682 | "in that day" is common in Isaiah |
| 14:32 | "the ambassadors of nations" | Clarke never asked (bad scan). "Messengers of the nations" is printed at this verse in 16 books before 1830 | the plural is the commoner phrase |
| 48:11 | "my name be blasphemed"; first person | Clarke never asked (bad scan); other works 0 of 6 | one shared pronoun |
| 49:1 | "O ye distant lands" | the verse itself is unchanged; the new words sit before it | same point |
| 29:11 | "I cannot read it; for it is sealed up" | 2 Nephi 27 rewrites Isaiah 29 too freely to line up | "read it" comes after a long insertion |

Of the 18 changes in my set, Clarke prints none of them word for word. The model was asked about
Clarke's note at 9 of the 18 and said yes once, at 9:3. At those same 18 changes the other eleven
works were asked 171 times and said yes zero times. So 9:3 still stands as the one real example. At
50:2 and at the "nations" lines of 2:12-14, the model read Clarke's notes and didn't find the book's
reading.

Townsend's page 64 claim doesn't hold for two of his examples. "In that day" at 14:3 is printed at
that verse in Arthur Jackson's *Annotations upon Isaiah* (1682) and in a 1669 book by Increase
Mather. "Messengers of the nations" at 14:32 is in 16 books before 1830, Catholic Douay Bibles and
Matthew Henry among them.

**What I tried.** One commentary checked alone tells you nothing. The question is whether Clarke has
more of the book's changes than any other book does, beyond chance. So I lined up every quoted verse
against the King James text and found 552 changes in 263 of the 420 verses. One thing shows at once,
and it is not new but it is stark: 30 percent of the King James words the book changes or drops are
words the King James printers put in italics (words the translators supplied). Of the words it keeps,
2 percent are italic.

Then I searched all 252,431 books in the library printed before 1830 for each changed reading, in its
verse. To know what a match is worth, I also made up changes the Book of Mormon does not make, and
searched for those too. A book that reworded Isaiah freely will "match" by accident, and the made-up
changes measure how much.

**The check.** Bishop Lowth published his own translation of Isaiah in 1778. Given Lowth's changes as
if they were the Book of Mormon's, the search had to find the other printings of Lowth at the top,
with real changes far ahead of made-up ones, and the made-up changes had to turn up somewhere in the
library less than 10 percent of the time.

**When it failed, and what I changed.** The first two parts passed by a mile. The top six books in
the whole library were all other printings of Lowth, and the best matched about a thousand times more
real changes than made-up ones. The third part missed. 13.5 percent of Lowth's made-up changes turned
up somewhere.

Looking at which ones, the reason was plain. They were short, ordinary strings: "is born to us a"
was in 285 books, "the leopard lie down" in 220. With a quarter of a million books, a four-word
made-up change often matches somebody's ordinary English or a common misquotation of a famous verse.
Four-word made-up changes matched somewhere 56 percent of the time, six-word ones about 1 percent. So
the bar was measuring how common a phrase is, not whether the search can find a source, which parts
one and two had already shown. I had set that bar badly.

I changed it after seeing that result, so it counts for less, and I allowed no third try. The
changes: readings are widened to at least six words; every book is judged against its own rate of
made-up matches, not the library's; and words merely split or joined ("for ever" and "forever") count
as spelling, not changes. The Book of Mormon had not been searched yet when I made them.

**The check, again.** Passed. Given Lowth, the top four books were printings of Lowth, the best with
3,533 real matches and no made-up ones, and 6 percent of made-up changes turned up anywhere.

**The result.**

| | Book of Mormon's real changes (523) | Made-up changes (1,080) |
| --- | --- | --- |
| Found in Clarke's commentary | 2 | 4 |
| Found in any printing of Lowth | 13 | 4 |
| Found in some book somewhere | 36% | 17% |
| Found nowhere | 333 | |

Clarke matches 2 of the real changes and 4 of the made-up ones. That is chance. By matches net of
made-up ones he ranks about 3,300th among the books in the library. The two he matches are small and
common: "in the generations of old" dropped, and "briers" spelled "briars", which is in 45 books.

No other single book stands out either. The best any one book does is 16 of 523, and the books near
the top are annotated family Bibles and old commentaries, like a *Complete Family Bible* of 1785 and
Day on Isaiah of 1654. About two thirds of the changes are in no book I hold.

There is a useful comparison. I put 60 sermons of the 1820s through the same steps, using their own
Isaiah quotations. Their changes are found in print 71 percent of the time, against 36 percent for
the Book of Mormon's. Preachers misquoting Isaiah mostly misquote it the way others already had. The
Book of Mormon's changes mostly are not in print anywhere I can see. Clarke is at chance for the
sermons too.

**What it means, and what it doesn't.** By wording, Clarke is not a source of the Isaiah changes, and
neither is any other single book. (The reading of the notes, below, came later and agrees, with one
exception at Isaiah 9:3.) For Townsend's case, that is a no on the part that can be counted.
For Jackson's, it agrees.

One real limit, and it matters. This finds shared wording. Nearly all of Townsend's examples are a
different kind of claim: that Clarke's note *argues* for a reading in his own words, and the Book of
Mormon then has that reading. A word search cannot see that.

**Reading the notes: the check passed.** For that kind of claim a model reads Clarke's notes, and
those of eleven other commentaries and annotated Bibles, at each verse, and says whether the note
proposes the book's reading (simulated judging). Before any of it counts, the model had to say no to
200 made-up readings and yes to 76 readings that are printed word for word, with bars of 90 and 80
percent. On 23 November it said no to all 200 made-up readings and yes to 63 of the 76 (83 percent).
So the full reading goes ahead.

**The result of reading the notes.** All 4,680 questions were answered, and none were left open. For
each of the book's Isaiah changes, the model read the note in each of twelve commentaries and
annotated Bibles at that verse and said whether the note proposes the book's reading (simulated
judging). It said yes to none of the 60 made-up readings mixed in among Clarke's questions.

| | Notes read | Propose the book's reading |
| --- | --- | --- |
| Clarke | 237 | 2 (0.8%) |
| The other eleven, together | 4,754 | 93 (2.0%) |

Clarke ranks tenth of the twelve. The best is an annotated family Bible of 1796, at 17 of 445. By the
rule I wrote down first, Clarke does not stand out. If anything his notes propose the book's
readings less often than the others do.

But one of his two yeses is the one Townsend names. At Isaiah 9:3 the King James says "and not
increased the joy", and the Book of Mormon drops the "not". Clarke's note, following Lowth and the
manuscript collations, argues for exactly that reading. None of the other eleven works says so at
that verse in the passages read. His second named example, Isaiah 50:2, finds no support in Clarke
or anywhere else. Clarke's other yes is a spelling, "briars" at 5:6, which 45 books share.

So Townsend's case comes back as one real example, not a pattern. Clarke's commentary did contain
an argument for one of the book's readings that the others lacked. Across the hundreds of other
changes, his notes are no closer to the book than other commentaries of the time, and most of the
changes are argued for in none of them.

**When it failed: a hole in my own test.** At 9 of the 18 changes, Clarke was never asked at all.
That surprised me, so I looked. The question list only asks about a book where it can find that book
printing the verse, and Clarke's scan mangles exactly those lines: "lorp" for "lord" at 14:3 and
14:32, page-margin dates dropped into the middle of 11:5-6, "zt" for "it" at 48:11. Every time
Clarke was asked, the King James line was clean in his scan. Every time he wasn't, it wasn't. A
plain word search of his scan shows his notes do carry several of the readings Townsend quotes, like
"then shall the wolf" and "I cannot read it". So for four of Townsend's main examples (11:6, 14:3,
14:32, 48:11), my reading of the notes tells you nothing about Clarke either way.

The hole is bigger than Townsend's list. Clarke's scan has the King James wording for only 239 of
the book's 523 changes, and he was asked about 237 of them. Every other work was asked about between
397 and 484. Each work is scored on the share of yeses among the questions it was asked, so the
comparison isn't simply wrong. But Clarke was read at fewer than half the changes, and I can't tell
whether the ones his scan lost would have gone his way.

I changed one more thing after seeing the first output, so it counts for less. I'd written down that
each example would be classed by whichever of its changes came out best. But at 14:32 and 48:11 a
small change next door ("one" dropped, "to" added) was asked about and got a no, while the change
Townsend actually ties to Clarke was never asked. Under my first rule, those examples would have
read "not supported". So beside that rule I also class each example by the one change Townsend ties
to Clarke. By that change: by Clarke's note, 1 (9:3); not supported, 2 (50:2, 2:12-14); Clarke never
asked, 4; outside what a word-by-word test can line up, 4 (11:4, 2:10, 49:1, 29:11); credited by
Townsend himself to other books, 1 (2:16). Under the rule as I first wrote it, the counts are 1, 5,
2, 3 and 1.

**What's left.** Fix the hole first, and that's now under way. I'm doing it after seeing the result,
so it counts for less, and the first result stays as it was. Where Clarke's scan garbles the King
James line, his verse is now found by matching overlapping three-word runs, so one broken word
doesn't hide it. That finds 191 of the 286 changes he was never asked about; 95 still can't be
found. Those 191 go to the same model with the same question, along with 20 made-up readings as a
check, and all four of Townsend's lost examples (11:6, 14:3, 14:32, 48:11) are among them.
Separately, the five passages a word-by-word test can't line up (the cross-references at 11:4, the
long additions at 2:10 and 2:16, the words before 49:1, the rewrite of Isaiah 29) are arguments
about ideas, not readings, and this test can't settle them. And a person should check the model's
yeses.

### Can the scripture voice be subtracted out? (BOM-100)

**The claim.** This one is ours, not anybody's published argument. The two-voices test (BOM-99)
had shown the weak spot in the first study's main tool. An author model learns a person from their
ordinary writing and is then asked about a text in scripture voice. The voice is so strong that it
can swamp the person. My idea, raised on 18 November: measure each author model not against the
plain, untuned model, as the study did, but against a model of scripture voice in general,
learned from Bible-style books by other people. Whatever is left over should be the person.

**Their way first.** Here "their way" is the study's own rule. Before changing anything I reran
the study's scoring on the same six writers, the same passages and the same author models from the
two-voices test, with the plain model in the slot where the new reference would go. It gave back
the earlier numbers exactly. So any difference below comes from the reference and nothing else.

**What I tried.** I tuned a scripture-voice reference on equal shares of nine Bible-style books
printed before 1827 by people outside the six writers: *The Late War*, *The First Book of
Napoleon*, the *Chronicles of Andrew*, Dodsley's *Chronicle of the Kings of England* and others.
It got exactly as much training as each author model, at both training sizes the two-voices test
had used. A second version left out only the writer being tested and used everyone else's
scripture voice. Thirteen reference models in all, 15 minutes on the Mac.

**The check.** The test is the check here, because the answers are known. Each writer's
scripture-voice passages go to the six ordinary-voice author models, and the right writer has to
win. Chance is 17 to 20 percent. To count as working, the new scoring had to beat the study's rule
at both training sizes, with the gap clear of zero, and not lose ground on ordinary passages. I
wrote that down before training anything.

**What went wrong on the way.** Nothing broke. But part of the answer is arithmetic I should have
seen sooner, and I wrote it on the card before running. The study's rule asks "which of six author
models fits this passage best". Subtracting the same reference from all six cannot change which
one wins. So for the study's own pick-the-best rule, the reference could never matter. It can only
matter where scores are compared from one passage to another, which the study does when it puts
each model on its own scale. That is where I measured it.

**The result.** It does not help.

| Training size | Study's rule, right writer picked across voices | With the voice subtracted | Leaving out only the writer tested |
| --- | --- | --- | --- |
| Small | 28.5% | 28.0% | 29.0% |
| Four times larger | 70.5% | 70.3% | 72.7% |

Every difference sits inside its own range of error, which runs across zero. Writer by writer the
reference moved people both ways: Joanna Southcott's scripture passages found her more often,
Richard Snowden's less. Ordinary passages were not harmed.

There was also a decoy step. Take a writer's own model out of the line-up and see whether the
other models still "confidently" claim that writer's passages. They did, 73 to 100 percent of the
time, under every scoring. So the tool still accepts a writer who is not on the list at all, which
is the first study's "none of these" problem again. It did not separate the scorings.

**What it means, and what it doesn't.** Two things stand. The tool does carry a person across
voices better than chance: 70 percent at the larger training size. And how much each model is
trained matters far more than anything I did to the reference: 28 percent against 70. That
instability, found in the two-voices test, is what needs fixing. The reference was a fix for the
wrong part.

It does not show that no reference could work. Mine was tuned lightly, at the same small dose as
the author models, and its scores were only a little below the plain model's. Its books are mostly
eighteenth-century political satire in Bible style, not revelation. Smallest model size only, one
seed. The Book of Mormon was not touched, because the check said no.

**What's left.** The dose question, in its own issue. Optionally one reference trained to the full
on a large sample of scripture-voice writers who died before 1827, about 20 minutes on the Mac.
The check against the 55 benchmark authors was not run.

### Can a model be trained to ignore the voice? (BOM-101)

**The claim.** Also ours, the other half of the same idea. The style encoder is the tool that
turns a passage into a fingerprint of its writer. Train it on pairs where the same person writes in
two registers, a sermon and a letter, a history and a poem, and tell it those are the same. Pair
different people writing in the same register and tell it those are different. It should learn to
keep the person and drop the register.

**Their way first.** The baseline is the two encoders the study already has. Before training I
reran both on the same six writers from the two-voices test and on the study's "none of these"
check. The second encoder gave 0.955 on "none of these", the number already published for it, so
the measuring stick was the same one.

**What I tried.** First I had to find the pairs. The library gave 50,968 candidate pairs of one
author's books in two different registers. Then I threw out every pair where one book contains the
other. The first rule I planned, the library's own list of duplicates, removed none. A text check
that looks for long runs of shared words removed 4,343, 8.7 percent. They were mostly collected
"Works" volumes holding another of the author's books, and extracts and reprints under new titles:
Hopkins's *Exposition of the Ten Commandments* against his *Works*, for example. I had set a bar of
5 percent for what the duplicate rule could miss, so the plan's rule alone failed that bar. The text
check was part of the plan from the start and catches all of them, so I kept going with the three
rules together. I decided that after seeing the 8.7 percent, and the card says so.

That left 45,364 pairs from about 4,500 authors. I trained on the Mac for eleven hours, starting
from the second encoder. Southcott and Elias Smith were kept out of the new training so they
could be tested on.

**The check.** Three conditions, written before the first training step. The new encoder had to
find the six writers across their two voices better than both old encoders, with the difference
clear of zero. It had to keep finding writers within one voice. And on library authors it had never
seen, it had to match people across registers at least as well as the second encoder.

**The result.**

| Measure | First encoder | Second | New |
| --- | --- | --- | --- |
| Six writers, found across their two voices | 0.700 | 0.749 | 0.735 |
| Held-out library authors, across registers | 0.801 | 0.809 | 0.796 |
| "None of these", all books | 0.954 | 0.955 | 0.954 |

It met none of the three. So I did not point it at the Book of Mormon. Worse, it got slightly worse
on its own practice set from the very first snapshot and never recovered. The best snapshot was
the least trained one, after 250 of 1,600 steps.

**The leads, and why they are only leads.** Two things leaned the other way. I looked at both
after the rule had already failed, so they count for less. On the four writers no encoder had ever
trained on, the new one does a little better, 0.71 against 0.66, mostly because Joseph Smith's
revelations now find his letters (0.93 against 0.69). And on 62 known books written across genres,
it accepts fewer false matches, 43 percent against 67. Against that, Joanna Southcott got worse:
her scripture passages found her ordinary writing half the time, down from 0.83.

**What it means, and what it doesn't.** At the size I could afford, training against the voice
did not help. It does not show that it cannot. Eleven hours on the Mac is about 2 percent of the
training the second encoder had, with 15 decoy writers in each batch instead of 63. And
"religious" in the library's labels means sermons: the library has almost no writers with a
scripture-voice book and an ordinary one, which is the exact case in point. Only three of the
pairs had a Bible-style book in them.

**What's left.** A full-size run needs a rented GPU for about five hours, roughly 15 to 20 dollars.
I have not done that. The cheaper way to test the Joseph Smith lead is to score more writers
neither encoder has seen with the snapshots I already have, no new training. Every snapshot is
kept.

### The 131 correspondences (BOM-112)

**The claim.** In 2019 Bruce and Brian Dale took Michael Coe's textbook *The Maya* and found 131
statements in it that they judged the Book of Mormon gets right. They also found 18 things Coe
says the Maya lacked that the book has. They gave each hit a weight of 2, 10 or 50 to one, by how
specific it was and how unknown in 1830, and each miss 50 to one the other way. Then they
multiplied them all together. With a starting assumption of a billion to one against, they
reported odds against the book being fiction of a number with 111 zeros. They also scored two
control books themselves: Spalding's manuscript (19 hits, 21 misses) and *View of the Hebrews*
(15, 9). Critics answered that the weights are arbitrary and that 131 items are not 131 separate
pieces of evidence.

**Their way first.** The paper is open access, so I keyed all 149 items from their appendices,
with each item's weight, category and page. I don't hold Coe's book, so every Coe statement is as
they quote it. Then I redid their sum. My first check asked for an exact match, and it missed
twice. Both misses were theirs, not the parser's. In the military category their summary counts
3, 5 and 4 items at the three weights, but their own list of twelve items has 3, 4 and 5. And
their headline rounds a middle step before the last multiplication. I changed the check to follow
their printed tallies and their rounding, after seeing the first result, and said so on the card.
Then it comes out as they printed it: 1 in 10^111. From their items as listed, it is about five
times stronger. So the arithmetic is honest. The question is what it rests on.

**What I tried.** It rests on two things: that the weights are right, and that the items are
independent. So I changed one assumption at a time and watched the headline. The column is the
odds that the book is fiction: a tiny number favours an ancient origin, a number above 1 favours
fiction.

| Change | Odds of fiction |
| --- | --- |
| As they published | 1 in 10^111 |
| Every weight capped at 2 to one, for and against | 1 in 10^25 |
| Hits capped at 2 to one, misses left at their 50 | about even |
| Drop the items also true of the Bible's world (39 of 131 left) | 1 in 10^11 |
| Drop the items true of most farming kingdoms anywhere (75 left) | 1 in 10^59 |
| Drop both, and the unclear ones (8 left) | 10^29 the other way |
| Count each of their six categories once | 400,000 the other way |

The answer swings across 140 orders of magnitude, in both directions, on choices no one can settle
by arithmetic. If "had kings", "kings were hereditary" and "some kings were wicked" are one
observation and not three, the result shrinks fast. It crosses even odds at about ten truly
independent items. By the rule I had set, that makes the headline fragile.

Which items are "also true of the Bible's world" was coded by the AI assistant from memory, with no
second reader: 92 of the 131 marked yes. That is the weakest part, and I would not lean on the
exact rows. The swing is the finding.

**The check.** The real test is the comparison the Dales did only for their own two controls.
Apply the same 131 items, by the same standard, to books we know were written in the 1800s: *View
of the Hebrews*, Spalding, *The Late War*, Snowden's Bible-style history, *Chronicles of Eri*, and
the Bible's own histories. Before a model judges any of those, it has to reproduce the Dales on
the Book of Mormon itself: say "the book plainly states this" for at least three quarters of
their 131 hits and three quarters of their 18 misses. All judging here is simulated: a model
reads, not a person.

**When it failed, the first time.** It missed. For each item the model saw three passages my
keyword search had pulled from the book. It said yes to 70 of the 131 hits, 53 percent. It said
yes to 17 of the 18 misses. So the control books were not judged.

Was it my search finding the wrong passages, or the Dales counting things the book only hints at?
The AI assistant read 15 of the 61 "no" items against the whole book, drawn at random. For 9 of
the 10 it looked up closely, the book does state the thing, and the passage was not among the three
my search had pulled. The king-men. Benjamin consecrating his son king. Reformed Egyptian. "Little
timber upon the face of the land." So the miss was mainly the search, not the reader. That
reading came after the result.

**When it failed, the second time.** So I changed only how passages are found, after seeing the
miss. Keep the three keyword passages and add the five passages closest to the item by meaning,
using the same "search by meaning" model the lab already uses. Same bars. Before asking any
questions, a smaller check: of the 8 items where the stating passage was known, the new search
had to show it for at least 6.

It showed 4. It found the king-men, "save it be upon plates", the little timber and the language
of Nephi taught among the Lamanites. It missed the rest by a long way: the coronation ranked 310th
of 4,536 passages by meaning, reformed Egyptian 866th, the list of tribal names 1,426th. That told
me something about the Dales' list. Many of their items are not stated in a sentence. They are
shown through names and events, and no passage search reaches those. The 149 questions of this
design were never asked.

**The third design: reading the whole book.** I asked whether to stop or to read the whole book,
and on 23 November the answer was to read it. This is also a change made after seeing a result, the
second one, so a pass will count for less, and the write-up will say that. Every text is cut into
equal sections of at most 12,000 words, 23 for the Book of Mormon, and the model reads every
section against every item. One sentence was added to the standard, because of what the diagnosis
found: a feature can be plainly described by the story, through named people, places or events,
and not only by a general statement.

Two guards were added, because reading 23 sections gives each item 23 chances to be accepted. I
wrote 20 made-up items in the same style that the book does not contain: blowguns, llamas,
hammocks, a sign for zero, knotted-cord records. The reader is not told which items are real. It
may accept at most 2 of the 20, anywhere. And a second, stronger model rereads three sections, and
the two readers have to agree well beyond chance. The bars for the Book of Mormon are unchanged.
The controls are read only if all of that passes.

**The check, third time: passed.** The model read the whole book, all 23 sections, against every
item (simulated judging; a second, stronger model reread three sections). It found 107 of the Dales'
131 items, 82 percent, against a bar of 75. It found all 18 of the items Coe and the Dales agree are
absent as absent, which here means the reader saw the book's own statements that they are not there.
It accepted none of the 20 made-up items, against an allowance of 2. And the two readers agreed on
421 of 447 section-and-item pairs, a kappa of 0.73 against a bar of 0.6. Neither reader accepted a
made-up item in any of the 60 places it was asked.

Because this is the third design, and the last two changes came after seeing results, a pass counts
for less than a first-time pass would. One item, A:2.13, is read as supported in one section and
contradicted in another; by the rule written beforehand the support stands and the contradiction is
reported beside it.

**The result: the controls.** Six books, read the same way, by the same reader, with the same
made-up items mixed in. Every one of them rejected all 20 made-up items, so every one is compared.
Two models were asked to reread three sections of each control, and they agreed well (kappa 0.65
to 0.83) everywhere but the King James historical books, where agreement was just under the check's
bar (0.59). The score is the Dales' own: multiply their odds for every item a book has.

| Book | The Dales' 131 items it has | Their rarest items (odds 1 in 50) | Dales' odds, as a power of ten |
| --- | --- | --- | --- |
| Book of Mormon | 107 | 44 | -125 |
| King James historical books (Joshua to Esther) | 88 | 31 | -95 |
| *Chronicles of Eri* (1822) | 63 | 21 | -69 |
| *View of the Hebrews* (1825) | 56 | 20 | -64 |
| Spalding's manuscript | 51 | 21 | -57 |
| *The Late War* (1816) | 29 | 9 | -32 |
| Snowden, *American Revolution* (Bible style) | 29 | 9 | -30 |

By the rule written before any control was read, no control reaches the Book of Mormon. The book
has more of the Dales' items than any other text, and the gap in their arithmetic is 30 powers of
ten to the nearest one. Leaving out the chapters that quote the Bible changes almost nothing (105
items, -123).

Two things sit beside that. The Dales scored two of these books themselves: Spalding at 19 items and
*View of the Hebrews* at 15. Read the same way as the Book of Mormon, they have 51 and 56. So the
controls were undercounted by about three times in the original. And the King James historical
books, which are not about the Americas at all, have 88 of the 131 "Maya" items, and 31 of the 58
the Dales rate rarest. The card said that if the Bible matched the rare items at a rate near the
Book of Mormon's, the "rare" label carries little. It matches about 70 percent as many.

**What it means, and what it doesn't.** The Dales' list does pick out something about this book:
no other text read here comes close to it, by their own arithmetic. That is the part of their claim
that survives a fair control. Three things limit it. Most of what the list measures is shared with
the Bible: the King James histories have two thirds of it, so a long book in Bible style about
kings, wars and cities starts far up the scale. The controls the Dales used were scored about three
times too low. And multiplying odds treats the items as independent, which they are not (a book
with kings has courts and taxes), so the powers of ten overstate every book, the Book of Mormon
included. What remains is a ranking, not a probability: on this list the Book of Mormon is first,
the Bible second. All of it is a model's reading, checked against made-up items and a second model,
not a person's. Coe's book itself was not read, so whether each item is a fair reading of Coe is
untested.

**What's left.** A second coder for the Bible-world field. A checklist drawn from ancient Israel, run the same way.

### The anachronism tally (BOM-113)

**The claim.** Matthew Roper's 2025 study lists everything critics have called out of place in
the Book of Mormon since 1830: horses, steel, wheat, silk, chariots, and about 220 more. He reports
that 174 of 226 have since been confirmed, 31 partly, and 21 not. And he reports the trend: of the
items raised by 1844, 7 confirmed; by 1965, 36; by 2024, 174. The list of problems shrinks as
archaeology goes on. It is one coder's tally, with no control.

**Their way first.** I did not hold his paper when I started. So the first run used a stand-in
list from Wikipedia, Coe and a few items from memory, with no statuses, just to build the counter.
That was a detour, and the stand-in is kept apart. Then I fetched his introduction and nine
chapters, which are open access, and keyed his own list.

I count 227 items in his headings, not 226, with 175 confirmed. The extra one is a "confirmed", and
the paper does not show which. His own charts do not agree with each other either. The chart for
2024 has only 213 labels. The 1844 chart, as the AI keyed it from the images, gives 101 of his 102;
the 1965 one gives 164 of 168, and three items sit in both the confirmed and unconfirmed columns. I
changed nothing to make it fit. It does not alter the picture.

**What I tried.** Two things his tally never had. First: is "confirmed" just "is in the Bible"? A
sword is easy to confirm. My guess going in was yes. Second: a control. How would books known to
be from the 1800s, set in antiquity, do on the same list?

**The check.** Before counting anything, the counter had to find words I planted: 113 of 113 found.
It had to find horses and chariots in the King James Old Testament (138 and 172), maize in the
Mexican native texts (168), and no New World word anywhere in the King James Bible (none). All
passed.

**A slip, and the fix.** On the first count, five items came out zero in the Book of Mormon though
the book names them. The 1830 spellings were missing: "firy darts", "breast-plates", "bellowses",
"leprous". I added those forms and reran. I made that change after seeing the count. No form was
added or removed because of a control book's count.

**The result, part one: the Bible guess was wrong.**

| | Confirmed by his count | Not confirmed |
| --- | --- | --- |
| Item is named in the King James Bible | 86 | 21 |
| Item is not | 26 | 11 |

Bible things are confirmed 80 percent of the time and the rest 70. That difference is what chance
gives (p = 0.25). Being biblical does not explain his confirmations.

What his own headings do show is where the confirmations are thin. For 59 items the heading says
what kind of evidence he means. The ones he ties to the New World are confirmed less often than the
rest: 2 of 6 that he places "in Book of Mormon times", and 20 of 34 where he names the New World
but no period. Against that, 9 of 10 Old World items are confirmed, and all 8 he confirms by reading
the word as something else (the "horse" that may be a tapir or deer). For the other 168 the kind
is not in the heading. Those go to a reader.

**The result, part two: the control.** I could count 144 of his items as words.

| Book | Share of his items that appear in it |
| --- | --- |
| *View of the Hebrews* (1825) | 58% |
| Mathews, *Behemoth* (1839, mound builders) | 58% |
| *The Late War* (Bible style, War of 1812) | 48% |
| *Chronicles of Eri* (1822) | 44% |
| *Book of Jasher* (1751) | 42% |
| Snowden (Bible style, the Revolution) | 39% |
| Spalding's manuscript | 38% |
| Hale, *Genius of Oblivion* | 31% |

So a nineteenth-century book set in antiquity uses 30 to 60 percent of the same things. The two
Bible-style books about their own day were put in as decoys. If they scored as high as the antiquity
books, the count would be following Bible diction, not setting. They do. That is only words in a
text. Whether those books' horses and steel would count as "confirmed" by Roper's standard is a
judgment about evidence, and that needs a reader.

**The reader's check passed.** Before a model reads Roper's items, it had to code 12 things whose
answer is not in dispute. Maize, cacao, turkey and jaguar in ancient Mesoamerica. Llama and potato
in the Americas but elsewhere. Wheat, war chariots and silk in the Old World only. Gunpowder, the
telescope and movable type nowhere before AD 421. It got all 12. That is simulated judging, a model
reading, not a person.

**A flaw found before the answers, and the change.** Before any answer came back I wrote how they
would be scored. Roper's tally "holds strictly" if at least three quarters of his 175 confirmed
items are coded as found in Mesoamerica in the book's period. Writing that showed me a flaw. The
control questions asked about Mesoamerica for every book, but Spalding and *Behemoth* are set in
Ohio country, and *Eri* and *Jasher* in the Old World. Asking whether Spalding's things are
confirmed in Mesoamerica is a harsh test for a book that never claims to be there. I asked whether
to rewrite the questions. The answer on 23 November was "can we do both?" So the controls are now
asked twice: once against Mesoamerica, as first written, and once against each book's own claimed
region and period. Both are reported side by side, and neither replaces the other. That was settled
before any control answer existed.

**The result, part three: the reading.** A model (sonnet) read every item in the passages where
the book uses it, and said where and when that thing is attested: in Mesoamerica in the book's
period, in the Americas at another time or place, only in the Old World, nowhere, or that the
question does not apply. It also said yes or no to a looser question: is it attested anywhere
before the book's period ends, in any sense of the word? That is simulated judging, all 227 items,
and every answer was read. One control answer gave two different codes in the same reply, so I
threw it out and asked again before scoring.

| Roper's items | Mesoamerica, in period (strict) | Attested somewhere, some sense (loose) |
| --- | --- | --- |
| The 175 he calls confirmed | 54 (31%) | 148 (85%) |
| The 31 he calls partly confirmed | 2 (6%) | 19 (61%) |
| The 21 he calls not confirmed | 0 | 14 (67%) |

By the rule I wrote down, his tally **holds only under the loose rule**: 85 percent of his
confirmed items pass that, but only 31 percent pass the strict one, far below the three quarters I
set. The most common code for his confirmed items is "Old World only" (60 of 175), and 39 more are
coded as not that kind of thing at all, mostly names and phrases. And the loose rule is generous: it passes two thirds of the items Roper himself calls not
confirmed.

By topic the pattern is plain. Animals: 28 of 28 pass loosely, 3 strictly. Metals: 16 of 16
loosely, none strictly. Customs and "other" things do best on the strict rule (41 and 33 percent).
By when the criticism was first raised, the newest ones are confirmed most, as Roper says: 93
percent loosely and 37 percent strictly for items first raised after 1965, against 72 and 24
percent for those raised by 1844. (The newest group is found by elimination from his charts, so
take its edges loosely.)

**The result, part four: the controls, read the same way.** The same reader coded 209 things from
five books of the 1800s set in antiquity. Each is compared with the book's 144 countable items:
20 percent strict, 82 percent loose.

| Control book | Loose, book's scale | Strict, Mesoamerica | Strict, its own claimed region |
| --- | --- | --- | --- |
| Spalding's manuscript (named in advance) | 89%, same | 32%, same | 30%, same |
| Mathews, *Behemoth* | 93%, same | 35%, higher | 40%, higher |
| Hale, *Genius of Oblivion* | 80%, same | 20%, same | 33%, same |
| *Chronicles of Eri* | 91%, same | (not set in the Americas) | 61%, higher |
| *Book of Jasher* | 83%, same | (not set in the Americas) | 76%, higher |

"Same" means Fisher's test finds no difference at the 0.05 level. Under the loose rule every control
book is confirmed as often as the Book of Mormon. Spalding, the control I named in advance, comes
out at 89 percent against the book's 82. On the strict rules the controls are as good or better:
the two Old World books do much better on their own region, because swords, kings and goats really
are attested in ancient Ireland and Israel. Asking the controls both ways, as Dave chose, made no
difference to the answer on Spalding.

**What it means, and what it doesn't.** Roper's list is real, and his trend is real in this
reading too: the later criticisms are the ones most often met. But "confirmed" in his sense is
mostly the loose kind: a thing attested somewhere, or in some sense of the word. Only about a third
of his confirmed items are attested in Mesoamerica in the book's period. And the loose kind of
confirmation comes just as easily to books written in the 1800s and set in antiquity: Spalding's
story gets it as often as the Book of Mormon does. So a high confirmation rate of that kind does
not tell an ancient record from a modern one. It cuts both ways. It does not count against the
book either: by the same reading, the Book of Mormon has no more out-of-place things than the
controls, and 54 of Roper's items do meet the strict test. What this test removes is the tally as
evidence either way. A model read every item; a person has not checked them.

**What's left.** A person's check of a sample of the codes, especially the "Old World only" ones and
the generous loose yeses. The strict rule against other proposed settings for the book (the Great
Lakes, Baja), which would need their own questions.

### Where the three worlds disagree (BOM-109)

**The claim.** This one is my own pulling-together of several claims, each of which looks at one
world. The Dales and Sorenson count matches with ancient Mesoamerica. Roper counts confirmations.
Vogel in 1986 argued the book's picture of ancient America is the one Americans of the 1820s already
had in print: mounds, forts, a fallen civilised race, Hebrew Indians. A match all three worlds share
tells nothing. Horses, coins and counting in tens are where the worlds disagree. So: take only those
features, and see which world each text sides with. The Bible's Near East, ancient Mexico as its
own texts and the Spanish chroniclers describe it, or ancient America as an 1820s American pictured
it.

**Their way first.** Each published list credits an item when the word or idea is in the book. None
asks whose it is. The plan is to rerun each list its author's way first. The Dales' and Roper's lists
are being read in BOM-112 and BOM-113. Vogel prints no list of motifs, so his way cannot be rerun as
he did it. With a yes on 22 November, we keyed 42 of his ideas from his chapters. That is our coding
of his prose, not his list, and it is labelled so. 66 of the 81 earlier sources he cites are in the
library. 1,301 questions for that are prepared, not run.

**What I tried first.** Count words. I built 56 features that can be counted, with each world's
value measured from its own books. After dropping the ones the worlds agree on or are split on, 31
were left. Before testing anything, the source texts made Mesoamerica "have" horses and wheat.
Those hits were Clavigero comparing Mexican animals with European ones, and he says plainly that
horses and wheat came from Europe in the 1500s. So I coded those two as absent from his own
sentence. I made that change after measuring the source books, before any test text was scored,
and labelled it.

**The check.** Eight texts whose world I know, none used to build the worlds. All eight had to side
with their own world.

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

**Why it failed, and what I changed.** Bernal Díaz was a Spanish soldier writing about Mexico. His
book is full of his own side's things: guns, coins, horses. He also mentions copper, canoes and
cotton, which are Mexican things the short native poems and myths never happen to name. On a word
count he looks like the 1820s picture, which mixes Old World and New World things the same way. A
Mesoamerican text and a text about Mesoamerica are not the same thing. The inventory test hit the
same wall.

There was a setting under which all eight pass: only read "absent" from texts over 50,000 words.
But then Díaz passes by a single feature, and I found it after seeing the result. An instrument
that flips on one setting is not ready to be pointed at the question. I did not adopt it.

**The second design: whose is it?** The word count gave a horse to whoever's book it was in. In
Díaz most horses are the Spaniards'. Could a simple rule tell them apart, by looking at nearby
words? I tried. Of 87 firearm mentions in Díaz, 30 could not be placed either way. Nearness is not
ownership. So this time a model reads each mention and says whose it is (the book's own people,
outsiders, the author's own world, a figure of speech, a prophecy) and what the passage says (they
have it, lack it, it was brought). The features were rebuilt, 45 of them, each from a published
source: the Dales, Roper, Coe, Vogel, a world ethnographic database. Díaz had to pass this time, or
the run stopped. Before any real reading, the model had to pass a check on 150 made-up passages with
known answers. And two readings of 100 real mentions had to agree.

**It missed, in two ways.** On "whose", the made-up passages were perfect: 150 of 150. On "what" it
got 109 of 150, under the bar of 85 percent. When I looked, every miss was a passage where my answer
key was arguable. "Strangers would bring horses into the land" I had keyed as saying nothing; the
model said "brought from outside", which is fair. Where the thing belongs to the book's own people,
which is the only place the score uses it, it was 60 of 60. That is my key's fault, not the
reader's, but I found it after the result.

The other miss is real. Two readings of the same 98 real mentions agreed on whose it is only 76
percent of the time (bar 80). Most of the disagreement is between "the people the book is about"
and "the author's own world". Much of it comes from *View of the Hebrews*, an essay where the author
talks about the Indians in his own voice. That line is hard to draw, and it is the line the test
turns on. So the Book of Mormon was not scored, and I did not spend the 45 hours of reading behind
it.

**The third design, being built.** On 23 November the choice was to try again rather than stop.
This is a change made after seeing the second check, so whatever it finds counts for less. What
changes, aimed straight at the two misses:

- The reader is graded the way the score uses it: is this the book's own people, yes or no. And on
  "what" only where the answer is yes. The key accepts every fair answer.
- A sharper written rule, with worked examples, for the line between the book's own people and the
  author's own world. 130 new made-up passages aimed at that line, none reused.
- The real mentions are read by two different models, not one model twice. They must agree on 80
  percent and well beyond chance.
- Two Mesoamerican sources that were out of reach before are in. Kirchhoff's 1943 list of
  Mesoamerican traits is now held. Roys's 1933 translation of the Chilam Balam of Chumayel is in too,
  since the copyright renewal records show it was never renewed. Kirchhoff's list maps onto 18 of
  our features; two of his traits nobody else listed, the ball game and raised-field farming
  (chinampas), are added, though they are so rarely mentioned they may not count for much.
- A new first step, the published readings their own way: for each feature, what the Dales, Coe,
  Roper, Vogel (as I keyed his prose) and Kirchhoff say, beside what our reading finds, so the
  places where we part ways are visible one by one.

It was built and its settings written down on 23 November, before any answer existed.

**The check, third time: passed.** On the 130 made-up passages the reader said whose correctly
every time, 130 of 130, and got "what" and "where" right on all 80 that have an answer. The bars
were 85 percent. On 100 real mentions, read by sonnet and again by opus (simulated judging, two
models), the two agreed on whose 89 times in 100, a kappa of 0.77, against bars of 80 percent and
0.6. Where both said the book's own people, they agreed on what the thing was 53 times in 54. The
line between the book's own people and the author's own world, the one that sank the second design,
held this time: of the 13 places where the two readers named different worlds, 2 were on that line. Because this is the third design, two
changes made after seeing results, the pass counts for less.

So the long reading goes ahead: about 13,500 questions, roughly 45 hours, queued behind the other
tests.

**What it means, and what it doesn't.** No answer yet on the Book of Mormon. What the failures show
is about the method, and it applies to every list on both sides: a word in a text is not a thing
its people had, and nobody's list has asked whose the thing is.

**What's left, in progress.** The long reading (queued), then Vogel's ideas and the Manchester
library list alongside.

### Words that were supposed to be dead (BOM-118)

**The claim.** Royal Skousen and Stanford Carmack list word uses and phrases in the Book of Mormon
that, by the dictionary's citations, had dropped out of English before the 1740s. "Arrive to" a
place. "It was desirous" for it was desirable. "Depressed" for weakened in body. Skousen's 2018
summary article puts it at 64 such items, 39 words and 25 phrases. If that holds, the vocabulary was
out of a man's reach in 1829. Their own 2020 recount, after wider searches, already moved some of
them later.

**Their way first.** Their evidence is the Oxford dictionary's dated citations, collected by its
readers, plus their own searches. The full list with their dates is in Skousen's book *The Nature
of the Original Language*, which I have not bought. So their dated citations are not replicated
until the book is bought. What I had was the open 2018 article: 48 of the 64 items, each with its
claimed sense and the verse it cites.

What I could check their way was the verses themselves. Four of the items rest on Skousen's
reconstruction of the original text, not on what the 1830 edition prints. Where he reads "sermon",
"depart", "great" and "raigned", the 1830 printing has "ceremony", "parted", "the governor" and
"arraigned". So those four, and two more that no search can separate from the ordinary sense ("about
to" and "but if"), could not be tested.

**What I tried.** The dictionary works from the citations its readers happened to collect. I have a
quarter of a million books. So: for each item, search the books of 1740 to 1830 and have a model read
the hits and say whether each carries the claimed old sense or the ordinary one. That is simulated
judging, a model reading, not a person.

**When it failed: the pilot.** I tried ten items first. The check was that the model read each item's
own verse in the claimed sense, and ordinary uses as ordinary. With a small model and 60 words of
context it read 7 of the 10 verses right, under my bar of 8. With a stronger model and the whole
paragraph it read 8. That change came after the first result, so the setting counts for less. The
bars were not changed. The pilot had a second, bigger lesson. Five random hits a decade never once
showed the old sense for five of the items. A rare sense does not turn up by chance. So the full run
had to aim.

**What I changed.** I cut each search down to the construction of the cited verse ("arrived to"
followed by a place, not every "to"), tested the patterns on a sample, widened the ten that found
nothing and narrowed the one that found too much. Then I scanned all 207,082 works printed 1740 to
1830 and had the model read up to 60 hits per item per decade: 8,444 passages.

**The check.** Per item, before any library passage was read: the model had to read the Book of
Mormon's own verse in the claimed sense and two ordinary uses as ordinary. 34 of 42 items passed.
Eight did not, "break" and "mar" among them, and are out.

**When the checking fell short.** The model said "claimed sense" 2,509 times. I had planned for a
person to check every one of those. Nobody has. I decided after the answers were in that a second,
stronger model would read each and sort it: the writer's own words, a quotation or reprint of
something older, or not the sense after all. Then the AI assistant, not Dave, read about 130 of the
deciding passages. That was every one for the items resting on a handful of books, and four from each
larger item.

That last step mattered. Three finds for "to that" meaning until were all the old long s: the
scanner read "so that" as "to that". Seven finds for "molten" as a verb were one speech by the Irish
lawyer Curran in seven editions, and it is the ordinary participle anyway. Every find for "give"
meaning describe was somebody who "gave the land the name of" something. Three of five "into a
effect" were smudged "into effect". That reading changed 71 verdicts. After it I also decided to
count a passage once however many editions reprint it, so "still in use" needs two separate
passages, not two books.

**The result.**

| Outcome | Items | Which |
| --- | --- | --- |
| Still in use 1740-1830, in the writer's own words, two or more separate passages | 21 | arrive to (316 passages), flatter into (120), on the Nth month (73), strong hold (55), do away (52), in the favor of (34), devour (24), extinct (23), be aware (18), hail (18), depressed (17), course (11), belief on (10), in the Nth day (10), desirous (7), for the cause of (5), begin to (3), call (3), hurl away (3), belove (2), into an effect (2) |
| Found once | 2 | counsel (1813), cross (1789) |
| Not found | 11 | molten as a verb, consigned, give, rebellion, rent, views, welfare, whereby, somewhat contentions, to that, where unto |
| Could not test | 14 | 6 with no workable search, 8 where the model missed the item's check |

Some of the 21 are everywhere. People "arrived to" an age or a height all through the period. A
senator in 1827 said "it was desirous they should be performed". Basil Hall in 1829 saw houses in
Rochester, New York, built on wheels "for the avowed purpose of being hurled away when the land
should be sold". All but one of the 21 are found as late as the 1820s.

The control books were thin. Only 10 items had any hits in the Bible-style books or Joseph Smith's
other texts. "In the fourth day" turns up 22 times in the Bible-style books, almost all quoting
scripture. By the two models' reading, Joseph Smith's own texts use "be aware" in the claimed sense
six times.

**What it means, and what it doesn't.** Of the 34 items I could test, about three in five had not
died. The dictionary's last citation is not the last use. That is the plain result, and it will not
surprise anyone who has used a big library against a citation dictionary. For the argument, it
means the list as a whole does not show vocabulary out of reach in 1829. It does not mean every
item was common.

Eleven items were not found, and that is real. But "not found" means not found by one construction,
with a cap of 60 passages a decade. The 14 I could not test are simply open, and there are 16 more
items I do not have. Five of the 21 rest on two or three passages (belove, into an effect, begin to,
call, hurl away), and for some the sense is a judgment call. Is "the call of its stomach" a need or
a demand? No person has checked any of it. The second model was wrong on about a third of the
passages the assistant read in the thin items, and on 8 of the 60 sampled in the larger ones. So the
passage counts in the table are too high by some margin, though not by enough to move a large item.
The list of all 2,509 is kept for anyone who wants to read them.

**What's left.** A person's check from the list. The 16 items and the dated citations, when the book
is bought. Wider searches for the 11 not found, and new checks for the 8 the model missed.

### Hebrew and Egyptian in the Uto-Aztecan languages (BOM-117)

**The claim.** Brian Stubbs, a linguist, spent decades on the Uto-Aztecan family: Hopi, Yaqui,
Nahuatl and about thirty more. In 2015 he published about 1,500 sets pairing their words with Hebrew,
Aramaic and Egyptian words, under a table of sound rules: this Hebrew sound becomes that Uto-Aztecan
sound. He reads it as a large layer of borrowed words from contact, not a shared ancestor. People
cite it beside the Book of Mormon. Critics, Chris Rogers and Magnus Pharao Hansen among them, said
the comparative method was not properly applied and that matches this loose turn up by chance.
Nobody, as far as I could find, had asked the question every linguist asks first: how many matches
like these turn up between languages that never met?

**Their way first.** Stubbs wrote two books that matter here, and I now have both.

The first is his life's work on the family itself: *Uto-Aztecan: A Comparative Vocabulary*. It
came out in 2011. The copy I bought is the revised online edition from 2020, so that is the one I
am describing. It has nothing about Hebrew or Egypt in it. It is the ordinary linguist's job: about
2,700 numbered sets, each one a reconstructed ancestor word (Proto-Uto-Aztecan) with the words in
the daughter languages that come from it, and a table of which sound in the ancestor becomes which
sound in Hopi, Yaqui, Nahuatl and the rest. He is careful in it. He says a set found in only one
branch of the family "can hardly be considered" an ancestor word until another branch turns up
(p. 1). He marks his own doubt in numbers: probable is 60-99%, possible 20-60%, less likely under
20% (p. 2). And he lists the ancestor's consonants he thinks are mostly secure: thirteen of them
(p. 12).

The second is the 2015 book, which is posted free for private reading. That is where the roughly
1,500 Hebrew, Aramaic and Egyptian sets are, with their own table of sound rules: this Hebrew sound
becomes that Uto-Aztecan sound. The 2015 sets point back to the vocabulary by number. 1,068 of the
1,522 sets I found cite at least one vocabulary set, 1,126 different ones in all. So the vocabulary
is the ground the Near Eastern claims stand on, and I could check the claims against it.

I did it his way, in three steps.

First, the 2015 book alone. I drew 150 of his sets at random and had a program read them against
his 2015 table. 71 were laid out clearly enough for a program to read. Of those, 41 follow his
table at every consonant, and 62 at the first one. Then a harder question, still on his terms: for
the same Uto-Aztecan word, how many *other* Hebrew or Coptic dictionary words would pass the same
rules? On sound alone, a median of 44. Once the meaning has to be at least as close as his, a
median of 1, and for 34 of the 71 there was no other candidate as good. So his meanings do real
work. The sound rules alone are loose.

That left 79 of the 150 that the program couldn't read: no tags, no index line it could parse, or
no way to tell which of his strands a set belonged to. So a model read those 79 for me (a simulated
reading, not a person's). For each set it pulled out the Near Eastern word, the Uto-Aztecan word,
their meanings and the strand, and I ran the same rule check on what it pulled out. It could place
42 of them. For 36 it said the strand was unclear, and one had a sound that isn't in his table. The
42 follow his table less often than the clean ones did: 12 at every consonant, 30 at the first.
Put together, that's 113 sets read: 53 follow his own table all the way through, and 92 at the
first consonant. So a little under half of his sets keep his own rules from start to finish. If I
take the 36 "unclear" ones and let each use whichever of his two Semitic columns suits it best,
which is as generous to him as I can be, 18 of them pass. I also had the model rate how close his
meanings are for the 71 clean sets. It called 37 the same meaning, 33 related, and just one
distant. That's closer than my program's rough word-matching thought: the model put 20 pairs closer
than the program had, and only 10 further apart. Hold the other dictionary words to that closer bar
and the median number of rivals drops from 1 to 0. For 47 of the 71 there is no rival at all, and
only 6 have ten or more. So on meaning, his pairs hold up better than my program gave them credit
for. Two cautions. This is a model's reading. In one set it called a Hebrew word Egyptian, so a
slip like that changes which column gets checked. And my program doesn't match "flies" to "fly",
so some of its "no link" sets are really closer than it says.

Second, the same sets against his own vocabulary. About one in five of the vocabulary sets that
the 2015 claims cite is found in only one branch of the family (19.4%, against 26.1% across the
whole vocabulary). By his own rule in the vocabulary, those are not yet ancestor words. His 2015
table also sends some Hebrew sounds to b, q and ŋ. None of those is among his own thirteen ancestor
consonants; in his vocabulary they turn up only in particular daughter languages. And when I swapped
in the vocabulary's own reconstruction for the form the 2015 book compares, fewer sets followed his
2015 table, not more: 25 of 56, against 30 of the same 56 with the 2015 forms. 38 of the 71 use the
vocabulary's headword form as it stands. The rest use a different form.

Third, the test his rules had never had. I took every ancestor word in the vocabulary that has a
meaning I could match to a standard word list. That came to 1,888 pairs. Then I asked how often his
2015 rules turn up a Hebrew word of the same meaning. And, the part nobody had done, how often the
same rules turn up a Finnish, Japanese, Tamil, Basque, Georgian, Hungarian, Korean or Quechua word
of the same meaning. These eight languages never met Uto-Aztecan. Each language was also compared
against itself with the meanings shuffled 10,000 times, because a language with lots of p's and
t's passes loose rules more often for no reason at all.

| List | Rules | Matches on the same meaning | With meanings shuffled | p |
| --- | --- | --- | --- | --- |
| Biblical Hebrew (Strong's), the one I picked in advance | his Semitic | 4.4% | 3.8% | 0.076 |
| Modern Hebrew (a standard word list) | his Semitic | 4.1% | 2.2% | 0.0002 |
| Arabic | his Semitic | 4.4% | 3.4% | 0.018 |
| Eight languages that never met Uto-Aztecan | his Semitic | 1.2% to 4.2% | | 0.064 to 0.85 |
| Coptic (late Egyptian), picked in advance | his Egyptian | 1.7% | 1.5% | 0.25 |
| The same eight | his Egyptian | 0.2% to 2.3% | | 0.060 to 0.80 |

By the rule I wrote down before running it, the answer is that his rules find look-alikes in
languages that never met Uto-Aztecan about as often as in Hebrew. Biblical Hebrew came out 0.58
points above its shuffled self. The best of the eight controls came out 0.56 points above its own.
That is a tie. Coptic showed nothing. None of the eight controls reached the bar either.

But one thing did not come out flat. The Modern Hebrew list stands out: 1.9 points above its
shuffled self, more than three times the best control, at p = 0.0002. Arabic leans the same way.
I only looked closely at this after I saw the numbers, so it counts for less, and what I saw cuts
both ways. Several of the matches are loose. One Hebrew word for "like" passes against four
different Uto-Aztecan "like" sets. Most of the gap comes from Modern Hebrew's low shuffled rate,
not from a high match rate. And my copy of the vocabulary is the 2020 revision, made after the
2015 book, so some of its reconstructions may already lean toward the Semitic reading. It is a lead,
not a finding. All of this is by rule; nobody has read the sets by hand.

So I gave the lead one fair chance, and I wrote the rules down before running it. I kept only the
ancestor words found in at least two branches of the family. That is his own standard for a real
ancestor word. And I used one pair per meaning, picking the Uto-Aztecan set found in the most
branches. That way four "like" sets could not all count. That left 578 meanings. Everything else
stayed the same: same rules, same lists, 10,000 shuffles. The lead would hold only if Modern Hebrew
beat every control *and* got under p = 0.01. It came close and missed. Modern Hebrew was still 2.0
points above its shuffled self, ahead of the best control (Hungarian, 1.3). But the p came out
0.0117, just over the line. Biblical Hebrew (p = 0.19), Arabic (0.055) and Coptic (0.26) showed
nothing either, and no control crossed the line. One more thing I checked, and said in advance I
would: are the Modern Hebrew matches even old words? By rule, 7 of the 16 have a Biblical Hebrew
word with the same consonants and meaning. The other 9 I could not find in the Biblical
dictionary. So even a pass would have rested partly on words from the wrong era. The lead does not
hold. I am not going to keep cutting the data until it does.

**What I tried.** The test linguists use, Kessler's. Turn each word into its broad consonant class.
Count how often the classes line up across shared meanings. Then shuffle the meanings 10,000 times
and see if the real lists line up better than the shuffled ones. Real loans should also show up more
in the meanings that are usually borrowed (trade words) than in the ones seldom borrowed (body
parts). And his own index says how big the layer should be: for Yaqui's 663 meanings, it gives a
Semitic or Egyptian source for 340.

**The check.** Before trusting it on Stubbs, it had to pass on pairs where the answer is known.
Hebrew and Arabic, which share a parent. Six pairs that borrowed heavily: Finnish and Swedish, English
and French, Yaqui and Spanish and others. And eight pairs that never met: Yaqui against Finnish,
Japanese, Korean and more. It had to pass at each list size I meant to use.

I wrote the card and fixed the settings minutes before the run, but did not commit them first. A
machine shutdown followed. So the file times are the only record that the rules came before the
numbers.

**It mostly failed.** Open word lists for the ancient languages are short: 26 to 38 meanings for
Aramaic, Late Egyptian and Stubbs's reconstructed Proto-Uto-Aztecan. At those sizes, and up to 115,
the test could not even find Hebrew and Arabic, except once at 87. It passed at one size, the long
lists (663 meanings), and only just. At 629 meanings, 34 fewer, it missed, because English and French
came out with the borrowing lean the wrong way. And at 663 one never-met pair, Yaqui and a Quechua
dialect, did come out as related. That was within the one allowed, and the likely cause is Spanish
loans left in the Quechua list, though I have not checked.

So I did not change the test after it failed. I did what the card said: score only at the size
where the check passed, and say "cannot tell" everywhere else. That is eleven of the twelve
comparisons, Yaqui against Hebrew at 629 among them.

**The result.** The one comparison that could be scored was Yaqui against Coptic, the last stage of
Egyptian. Nothing. The real lists lined up no better than shuffled ones (p = 0.49). The meanings
where loans usually fall showed no lean at all. When I planted fake loans in unrelated pairs at a
quarter of his predicted size, 85, the test found them every single time.

| Comparison | List size | Check at that size | Answer |
| --- | --- | --- | --- |
| Yaqui against Coptic | 663 | passed, barely | no layer of the size his index implies |
| Yaqui against Biblical Hebrew | 629 | missed | cannot tell |
| The other ten (Late Egyptian, Aramaic, Proto-Uto-Aztecan, the family together) | 26 to 115 | missed | cannot tell |

**What it means, and what it doesn't.** A layer of hundreds of Egyptian words in Yaqui, the size his
index implies, should have shown up, and it did not. That is the one firm thing. Two limits on it.
The 340 counts meanings with a Near Eastern source anywhere in the family, not words Yaqui itself
carries from Egyptian. If Yaqui has fewer than about 85, this test does not speak to it. And my fake
loans follow a perfectly regular rule, which real loans do not, so finding them every time
overstates how well the test would find real ones. Coptic is also only a stand-in for the Egyptian of
600 BC, and its words were matched to meanings by gloss without a reader's check. Even a positive
result would not have said who, when, or by what route. For the other eleven, the honest answer is
that open word lists this short cannot settle the claim either way.

**What's left.** The model questions on how the Hebrew and Coptic dictionary words were matched to
meanings (prepared, not yet run). A person's check of a sample of the model's readings of his sets,
if wanted. The 2011 printing's reconstructions, from before the 2015 book, if I can get a copy. A
Yaqui-only count of his sets, with fake loans planted at that size. A check that works on 40-word
lists. *Changes in Languages* is not replicated until bought.

## What I would want a reader to take from the whole set

TBD. This section gets written when enough tests are in to see a pattern, or to see that there
isn't one.

## How to check any of this

Every test has an issue on GitHub with its plan (BOM-99 to BOM-127), a command in the run guide
(`eval/README.md`), and a result file under `data/lab/`. Every outside source is listed with its
address in `data/lab/sources.json`. The texts under copyright are not published; the steps to
obtain them are in `docs/replication.md`.
