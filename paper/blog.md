# Who wrote the Book of Mormon? I'm going to let the text answer, and show my work.

*A running post. I add to it as the project moves. Last updated 2026-10-15.*

## Why I'm doing this

Back in 2016 a friend and I wrote a little Java program that pulled the 1830 Book of Mormon,
stemmed the words, counted them, and compared the counts against Joseph Smith's journals. It
was a weekend thing. It never answered anything, and the repo sat there for ten years.

The question didn't go away. Who wrote the English text of the Book of Mormon is one of
those arguments where both sides have run the numbers, both sides got the answer they wanted,
and nobody changed their mind. I think that's a design problem, not a math problem. So I'm
doing it again, in the same repo, with the tools that exist now, and with the rules written
down before I touch the data.

One thing up front: I'm not arguing about whether the book is inspired. That's not a question
a word-counter can answer, and I'm not going to pretend it can. What I can do is ask whether
the English text looks like any specific person's writing, whether it borrows from specific
books, and when its language comes from. If the answer to all three is "we can't tell," that's
a real answer and I'll publish it.

## The three questions

1. **Attribution.** Does the text resemble the writing of Joseph Smith, Oliver Cowdery,
   Sidney Rigdon, Parley P. Pratt, W. W. Phelps, Solomon Spalding, Ethan Smith, or Gilbert
   Hunt? "None of the above" is always on the table.
2. **Borrowing.** Which earlier books share wording or ideas with it, and is the overlap more
   than you'd expect by chance from two religious books of the same era?
3. **Dating.** Does the grammar look like 1600s English, or like someone in the 1820s
   imitating the King James Bible?

## Why it's still open after 45 years of stylometry

Here's the short version of what's been tried.

- In 1980 three BYU statisticians counted function words and found the book's narrators
  differ from each other and from 19th-century candidates. Critics pointed out their word
  lists were dominated by *unto*, *behold*, and *yea*. That's the King James register, not
  a person.
- In 2008 a Stanford team ran a classifier and got Rigdon and Spalding. But the classifier
  had to pick somebody from the list, and Joseph Smith wasn't on the list.
- In 2011 BYU redid it with a method that allows "nobody on the list" and got a different
  answer.
- In 2013 the Johnsons searched rare four-word phrases across 110,000 old books and found
  *The Late War*, an 1816 schoolbook written in Bible style. The rebuttal: the same score
  rates the Gospel of Luke even higher. Without a baseline for what "unusually similar" looks
  like, the method can't tell a hit from noise.

Here's how bad the register problem is. In the 1830 text, the five-word phrase *it came to
pass that* appears 1,290 times. *And it came to pass* appears 1,169 times. Any method that
doesn't deal with that is measuring the Bible.

Every one of these is a design flaw, and design flaws can be fixed in advance.

## What's different now

Three things exist in 2026 that didn't in 2013.

**Scale.** Harvard released 983,004 public-domain books with cleaned OCR. Add HathiTrust,
the Internet Archive, and old newspapers, and I can compare against most of what was printed
in English between 1780 and 1830, not four hand-picked books.

**A language model that has never read the Book of Mormon.** Every commercial model has
memorized the Book of Mormon and the Bible, so you can't use them to ask "how surprising is
this text." I'm going to train a small model from scratch on 1780-1830 text only, with the
Book of Mormon held out, then fine-tune one copy per candidate author. Then attribution is a
measurable question: which author's model finds the text least surprising? A Dartmouth team
did exactly this in 2025 to confirm who wrote the 15th Oz book. Nobody has done it here.

**Semantic search.** Sentence embeddings can find paraphrase and shared story structure, not
just identical strings.

## The rules I locked myself into

- **The plan is pre-registered.** The hypotheses, methods, and the thresholds that count as
  a match or a non-match are frozen on OSF: https://osf.io/6ugxc/. If I change anything, it's
  a dated public amendment. There's already one, see below.
- **The text is sealed.** The Book of Mormon doesn't touch any model training or tuning until
  the blind run near the end.
- **Everything is validated first.** Every method has to recover known authors from the
  Federalist Papers, from pseudo-biblical books with known authors, and from dictated texts,
  and it has to say "none of the above" when the real author is hidden. Anything that fails
  gets dropped before it ever sees the questioned text.
- **It's me and AI.** No advisors, no second analyst, no journal. I'm honest about that: the
  adversarial review is simulated (I wrote the strongest objections three kinds of scholar
  would raise, then answered them), the blind run is sealed by a script instead of a second
  person, and peer review will be an AI reviewer that only sees the released materials.
  That's a real limit on independence and it's stated everywhere. Anyone who wants to supply
  the missing scrutiny can open a pull request.

Here's what a pre-registered decision rule actually looks like, so you can see this isn't
hand-waving:

> A candidate is *supported* only if at least two independent method families (classical,
> authorial model, embedding) return *match* on both the discovery and confirmation halves.
> H1b holds if no candidate is supported.

## How I work

The whole project is 39 GitHub issues in 8 phases. I pull one, finish it, publish what it
produced, close it, move to the next. The repo is public:
https://github.com/lifehug/book-of-mormon-authorship. The budget is about $500-900 in cash on
top of a Mac mini, because the corpora are free and the models are small on purpose.

That Mac mini thing was a real decision. Training the base model takes 15-25 hours on a
rented H100. On a Mac mini it's three to four weeks. On a $6,800 Mac Studio it's about a
week. So: Mac mini for everything, rent an H100 for about $100 for the one job that needs it.

## What's done so far

### Phase 0: the foundations (BOM-01 to BOM-04)

Reset the repo, wrote the plan, registered it on OSF, wrote and answered the simulated
review, set the budget, opened the accounts. One day.

The simulated review changed the plan in eleven places. The one I'm gladdest about: a null
result for Joseph Smith gets reported as "untestable," not "not a match," because his
undisputed pre-1830 writing is tiny and every method falls apart under about 5,000 words.

### BOM-05: the three earliest texts

There are three witnesses to the earliest English text: the original manuscript Joseph
dictated in 1828-29 (about 28% of it survives), the printer's manuscript Oliver Cowdery copied
from it, and the 1830 Palmyra printing. The Joseph Smith Papers have page-by-page
transcriptions of both manuscripts online, 468 pages and 231 pages. I pulled all of them,
one page every 1.5 seconds, and parsed the 1830 edition into 15 books, 114 chapters, and
1,189 paragraphs.

Then I lined them up. The trick is five-word phrases that occur exactly once in each text.
*Had commanded us and searched* is a good anchor; it appears once in the manuscript and once in
the 1830 text, so it pins those two spots together. *It came to pass that* is useless; it's
in 1,290 places. Chain up all the unique anchors in order and you can map any manuscript
page to the 1830 paragraphs it carries. The printer's manuscript gave 186,331 anchors and all
but 66 of them fell in order.

Here's what the comparison looks like for one paragraph. The 1830 text, 1 Nephi chapter 3,
page 21:

> And now I, Nephi, proceed to give an account upon these plates, of my proceedings, and my
> reign and ministry; therefore, to proceed with mine account. I must speak somewhat of the
> things of my father, and also of my brethren.

The printer's manuscript, page 18, Oliver Cowdery's hand:

> and now i nephi procede to give an account upon these plates of my procedings and my reign
> and ministry wherefore to procede with mine account i must speak somewhat of the things of
> my father and also of my brethren

Four differences: *procede* twice, *procedings*, and *wherefore* became *therefore*. Three of
those are the typesetter fixing Cowdery's spelling. One is a word change. Across the whole
book, 3.5% of words sit in a changed region between the printer's manuscript and the printing,
and most of that is spelling and punctuation.

The original manuscript is a different animal. Here's how its first surviving page opens:

> [ 2 pages not extant ] that [h]e should take his family & depart into the wilderness [& it
> ca]me to pass that he was obediant unto the word of the Lord wherefo[re he] did as the Lord
> commanded him

The brackets are the editors filling in letters the water and mold ate. The alignment found
27.6% of the 1830 paragraphs in what's left of it, which matches Royal Skousen's published
estimate of 28% almost exactly. That's the kind of check that tells me the tool is honest.

The manuscripts also tell you who was holding the pen. Page 161 of the printer's manuscript
carries the note *Oliver Cowdery handwriting ends; scribe 2 begins.* Every aligned paragraph
now has its scribes attached: Cowdery wrote 388 of the 468 printer's pages, an unidentified
"Scribe 2" wrote 80, Hyrum Smith wrote 7. On the original, Cowdery wrote 209 of 231, John
Whitmer 13, a "Scribe 3" 13, and Joseph Smith himself exactly one. That matters later, because
if style shifts track the scribe instead of the narrator, that's a finding.

The transcripts are copyrighted, so they live in a private repo and only their checksums are
public. Anyone can re-fetch them with the script and prove their copy is byte-identical.

| Text | Pages | Aligned | 1830 paragraphs covered | Words changed vs 1830 |
| --- | --- | --- | --- | --- |
| Printer's manuscript | 468 | 463 | 99.7% | 3.5% |
| Original manuscript | 231 | 207 | 27.6% | 18.6% (mostly spelling and damage) |

### BOM-06: the Bible that was on the table

The Book of Mormon quotes the King James Bible at length, whole chapters of Isaiah, the
Sermon on the Mount, Malachi. Any authorship test on the raw text would partly be measuring
the 1611 translators. So before anything else I need the exact Bible, verse by verse, to mask
those spans out later.

I used eBible.org's clean digital 1769 text, which is what every American Bible of the 1820s
reprinted, including the Apocrypha, which most digital Bibles leave out. 80 books, 36,822
verses, about 934,000 words. One record per verse looks like this:

```json
{"book": "ISA", "chapter": 48, "verse": 1, "section": "OT",
 "text_marked": "Hear ye this, O house of Jacob, which are called by the name of Israel, ... [but] not in truth, nor in righteousness."}
```

The brackets mark words the translators supplied; I keep a version with and without them.

Here's why this matters. 1 Nephi chapter 6 in the 1830 printing, page 52:

> Hearken and hear this, O house of Jacob, which are called by the name of Israel, and are
> come forth out of the waters of Judah, which swear by the name of the Lord, and make
> mention of the God of Israel; yet they swear not in truth, nor righteousness.

That's Isaiah 48:1 with about six words changed. A stylometry tool that didn't know this
would credit "the author" with Isaiah's phrasing.

I also grabbed a scan of the actual edition the Smith family bought in October 1829: the
1828 H. & E. Phinney Bible from Cooperstown, New York, with Apocrypha. The OCR is rough. The
same verse comes out as:

> APTER XLVHI. God saveth his people for his own sake. EAR ye this, O house of Jacob, which
> are called i by the ' name of Israel, and are come forth out ' of the waters of Judah ;
> which swear by the name of | the Lord, and make ^ mention of the God of Israel, but not in
> truth nor in righteousness.

You can see the chapter heading, the drop-cap H that OCR lost, and column noise. I'm not
parsing that. I used it for one thing: check that the 1828 printing carries the same 1769
text. Two-thirds of the verses are found verbatim inside that noisy OCR even without caring
about order, evenly across Old Testament, Apocrypha, and New Testament, which is what a
reprint of the same text looks like through a bad scanner.

Small confession: my first version of that check reported 133% of words changed, because a
scanned Bible has two columns and marginal cross-references, and my diff was sweeping the
margins into every verse. Nonsense number, caught it, replaced the measure. The point of
writing this stuff down as I go is that you get to see the wrong turns too.

### BOM-07 and BOM-11, first half: knowing what to download before downloading it

The comparison corpus is the big one, and my MacBook has 130 GB free, so I did the part that
doesn't need disk space. Harvard publishes the catalog of all 983,004 books separately from
the text, as one 300 MB file, no sign-up required. I pulled that and filtered it to English
volumes dated 1780 to 1830:

| | |
| --- | --- |
| Volumes | 31,958 |
| Tokens | 10.5 billion |
| Text on disk | about 44 GB |
| Median OCR quality score | 99 out of 100 |
| Flagged as likely duplicates of another volume | 2,732 |

Half what I'd guessed, which is a nice surprise. One catalog row looks like this, and it's a
book that matters for this project:

> `View of the Hebrews; or, The tribes of Israel in America`, Ethan Smith, 1825, 
> about 64,000 tokens, OCR score 99

That's the 1825 second edition of the book people have argued since the 1920s was a source for
the Book of Mormon. Harvard has the 1823 first edition too. Both will be in the corpus without
me hand-picking them, which is the point: the comparison set is everything printed, not the
books one side or the other wants to talk about.

My first cut of that filter kept 32,132 volumes. Then the test download handed me Michael
Faraday's collected papers, printed in 1859. The catalog has two date fields, and for reprints
and collections the second one holds the original date; Faraday's said 1821, and my rule took
the earlier of the two. Wrong rule. What I want is what was printed in the period, so the
filter now uses the publication date only, and 174 reprints and collections dropped out. The
catalog also flags about 13,000 volumes of periodicals, where the date on record is the year
the periodical started, not the year of that volume; sorting those out is a job for the
deduplication step.

The text itself is gated behind a terms-of-use click (noncommercial, no redistribution), so
the actual 44 GB pull is a one-line command queued for the Mac mini, and the text will never
be in the public repo. Only the catalog and the checksums are.

Same pattern for the early modern set. The Text Creation Partnership keeps 61,315 hand-keyed
transcriptions on GitHub, one repository per book: 53,830 from Early English Books Online
(1473-1700), plus 5,012 early American imprints and 2,473 eighteenth-century texts I hadn't
counted on. The American set alone has 1,982 texts from 1780-1800. I wrote the fetcher,
tested it on three, and the first one it grabbed was the Bay Psalm Book of 1640:

> THE VVHOLE BOOKE OF PSALMES Faithfully TRANSLATED into ENGLISH Metre.

That's the first book printed in British North America, keyed by hand, dropping into my
corpus folder. Those 25 GB are queued for the mini too.

### BOM-08: HathiTrust, or the one I expected to skip

I assumed HathiTrust would add little, because Harvard's scans are in HathiTrust and both come
from the same Google Books scanning. So I checked before deciding. HathiTrust publishes its
entire catalog as one 1.2 GB file every month, 19.7 million rows. I filtered it the same way
as Harvard's: English, public domain, published 1780 to 1830.

| | |
| --- | --- |
| HathiTrust volumes in the window | 135,035 |
| Of those, already in the Harvard slice | 27,857 |
| Not in Harvard | 107,178 (87,200 books, 18,317 serial volumes) |

Four times what Harvard alone gives me. The biggest contributors of the extra volumes are the
New York Public Library (20,161), Michigan (14,496), and the University of California
(19,157 across two campuses). That's a lot of American printing Harvard didn't shelve. So the
"probably skip" became "definitely get," with one catch: HathiTrust doesn't let you bulk
download full text without a Research Center account. The open alternative is their Extracted
Features set, which gives word counts per page for every volume but not the running text.
Word counts are enough for the classic stylometry and part of the dating work; they're useless
for finding borrowed passages. So the request goes in, and the word counts fill the gap meanwhile.

Then it got more specific. HathiTrust's dataset program is an emailed proposal, and the
answer depends on who scanned the book. Of the 107,178 volumes Harvard lacks, 75,984 were
scanned by Google, and Google-scanned text only goes to institutions that have signed an
agreement with Google, which an independent researcher hasn't. Another 24,261 were scanned by
the Internet Archive, and those I can get from the Archive directly. The remaining 7,000 or
so, scanned by Yale, McGill, the Getty, Cornell and others, anyone can download in full. So
the honest expectation is: about 31,000 of those volumes for sure, 76,000 more if HathiTrust
says yes to a person without a university behind him. I'll report what they say.

Two things I could do without asking anyone, so I did them. HathiTrust's research center runs
an open file server with "extracted features" for 18.7 million volumes: for every page, how
many times each word appears and what part of speech it is, but never the running text. I
fetched three volumes to check the format. Lord Lyttelton's letters, 1807, 304 pages, and
page 11 has 204 tokens including *exposures* once and *writing* twice. That's enough for the
word-frequency methods, which is most of the classical toolkit, so all 107,178 volumes go in
that form. And the 26,000-odd volumes that the Internet Archive scanned for HathiTrust still
exist on the Archive under their own names; I matched them up by their ark identifiers, and
25,689 were already sitting in the Archive catalog I'd built an hour earlier. So the
"reachable" number is real, and most of it was reachable all along.

### BOM-20, built early: the classic toolkit

The classical stylometry methods don't need the corpus to be written, only to be run, so I
built them ahead while the downloads wait. Four methods, each with tests on made-up authors
whose word habits I control, so I know what the right answer is:

- **Burrows' Delta** and its cosine and Eder variants. Take the few hundred most frequent
  words, turn each text into a profile of how often it uses them, standardize, and measure
  distance. On five synthetic authors it got 20 of 20 attributions right.
- **General Imposters.** The open-set one. Instead of asking "which candidate is closest," it
  asks "is the candidate closer than a crowd of random imposters, and does that hold up when I
  keep changing which words I look at?" The score is the fraction of trials the candidate
  wins. True author: 1.0. Someone else: about 0.03.
- **Nearest shrunken centroids** with the "none of the above" extension that the 2011 BYU
  study introduced. My version of their rule is written down in the code with the reasoning,
  because I couldn't check it against their paper line by line yet; the replication step will.
- **A decision rule** that turns a score into match, non-match, or inconclusive using
  thresholds calibrated at 5% false positives and 5% false negatives, exactly as the
  pre-registration says.

One sanity check on real text: run the word-frequency profiler over Genesis, Exodus,
Matthew, and Romans, and *the* ranks first and *unto* lands in the top 30. That's the
biblical register showing up in the numbers, which is the whole reason the masking step
exists.

### BOM-13, first half: what the candidates actually left behind

Before any attribution test can run, each candidate needs a pile of their own words. I went
looking for every digitized text by the eight of them, with who physically wrote it, when, and
whether anyone is allowed to redistribute it. Thirty-eight sources. Here's the part that
matters:

| Candidate | Words written before 1830 | Words total |
| --- | --- | --- |
| Joseph Smith | about 11,500, all dictated to scribes; none in his own hand | about 20,000 |
| Oliver Cowdery | about 2,500, much of it quoting the Book of Mormon | about 25,000 |
| Sidney Rigdon | none digitized | about 55,000 (1836-40) |
| Parley P. Pratt | none (nothing published before 1835) | about 98,000 |
| W. W. Phelps | none digitized | about 15,000 |
| Solomon Spalding | about 40,000 (one manuscript, c. 1812) | about 40,000 |
| Ethan Smith | about 400,000 | about 400,000 |
| Gilbert Hunt | about 60,000 (*The Late War*, 1816) | about 60,000 |

Three things fall out of that table. First, the pre-registration's warning about Joseph Smith
was right: there's no pre-1830 text in his own handwriting at all, and the dictated material
sits right at the floor where methods stop being reliable. Second, for Rigdon, Pratt, and
Phelps, everything we have was written after they'd read the Book of Mormon, and exposure to
a text can pull your style toward it. Phelps ran a newspaper in Canandaigua from 1828 to 1831,
the *Ontario Phoenix*, which would be perfect, and nobody has digitized it. Third, the two
non-Mormon candidates, Ethan Smith and Gilbert Hunt, are the best-documented people in the
list by a mile, which is the opposite of what you'd want if you were trying to rig this.

One small call I had to make: Joseph Smith's 1829 preface to the Book of Mormon is in his
voice and predates publication, and I left it out of his sample, because it's part of the book
being tested and that text is sealed.

The fetcher is written and tested on two public items. Rigdon's 1838 Fourth of July oration
came down first, 5,621 words of OCR that open with the title page's epigraph: "Better far
sleep with the dead, than be oppressed among the living." You can also see the scanner's
work in it: the printer's line comes through as "fRINTED AT THE JOURNAL OEFICK." That kind of
noise is what the cleanup step in Phase 2 is for.

### BOM-09, first half: the Internet Archive, and why "more" isn't automatically better

The Internet Archive has no gate and no terms beyond "don't be a jerk," so I pulled its whole
catalog for English texts dated 1780-1830 through their scrape API. Five and a half minutes,
307,567 items. About 28,000 of them are the same title and year as something in Harvard's
slice; 251,000 are not, and would come to about 80 GB of OCR text.

That number is bigger than Harvard and HathiTrust put together, and it's also less trustworthy.
The top collections tell the story: 86,600 items in "americana," which is what I want, but
also 69,000 periodicals, 170,000 items from microfilm scanning projects, and a run of
European-library scans somebody tagged as English. And 11,896 items carry the date 1800
exactly, three times what a normal year gets. That's a placeholder date, not a publishing
boom. So the Archive gets pulled, but the catalog-cleaning step is going to earn its keep
on this one, and the counts above will shrink.

### BOM-10, first half: the newspapers, and a hole where Palmyra should be

The Library of Congress's Chronicling America holds digitized American newspapers with OCR,
and the plan wanted the papers circulating near Palmyra, New York, especially the *Wayne
Sentinel*, which printed the Book of Mormon's first advertisements. I cataloged every page
from 1800 to 1830: 159,146 pages, 39,538 issues, 138 titles. Then I looked at where they're
from.

| State | Pages, 1800-1830 |
| --- | --- |
| Virginia | 66,039 |
| District of Columbia | 27,955 |
| Rhode Island | 19,079 |
| New Hampshire | 12,176 |
| Ohio | 2,517 |
| Pennsylvania | 908 |
| New York | 47 |

Forty-seven pages from New York. For three decades. The *Wayne Sentinel* isn't there at all
for this period; New York's early papers were digitized by state projects that never fed into
the national collection. So the newspaper corpus will be heavy on Washington and Richmond
politics, which is fine as period prose, and the Palmyra-area papers have to come from
elsewhere, probably the New York State Historic Newspapers project, which is a separate job.
I'd rather know that now than find out when the borrowing search comes up empty for the
one town that matters.

The fetcher respects the Library's limits, which are strict: 20 catalog requests a minute,
150 text requests a minute, and an hour-long block if you exceed them. The three priority
states are 3,472 pages, about an hour, and that's running on my laptop as I write this. The
rest of the 159,000, roughly two days at the limit, waits for the mini.

## What's next

Set up the Mac mini, run the two corpus pulls there, then BOM-08 through BOM-10: HathiTrust
(probably skipped if it adds little over Harvard), the Internet Archive, and the Chronicling
America newspapers.

---

## Log

- **2026-10-15, later.** BOM-10 catalog built (159,146 newspaper pages; New York has 47). BOM-09 catalog built (307,567 Internet Archive items). BOM-13 sources inventoried (38; four candidates have no pre-1830 text). BOM-20 library built ahead of the corpus (37 tests). BOM-08 measured: HathiTrust holds 107,178 period volumes Harvard lacks. BOM-07 and BOM-11 catalogs built (31,958 Harvard volumes, 61,315 TCP texts) and the pull scripts written; the downloads themselves wait for the Mac mini.
- **2026-10-15.** BOM-01 to BOM-06 closed. Repo reset, plan registered on OSF (amendment 1
  the same day: one person plus AI, every human-review step replaced with a labeled
  simulation), budget set (Mac mini plus a rented H100), three Book of Mormon witnesses
  pulled and aligned, KJV with Apocrypha verse-indexed. Private data repo created for the
  copyrighted transcripts.
