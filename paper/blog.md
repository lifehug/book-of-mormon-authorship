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

**The paperwork, so far.** HathiTrust answered the next day. The email became a support
ticket (GS-17502) and came back with a two-page form to sign, the "Researcher Agreement for
HathiTrust Dataset", non-Google version. I'm putting the whole thing in the repo as
`docs/hathitrust-researcher-agreement.md`, because if you ever want to repeat this study, this
is the gate you walk through, and nobody tells you what's on the form until you ask.

Here is what it says, stripped of the legal cadence. The text is a loan, not a gift: it's for
this one project, and when the project ends I delete it. I can't pass the files to anyone;
if you want them, you ask HathiTrust and they'll rsync you the same set. If a volume later
turns out to be in copyright, they email me, I delete it and email back to say so. If I move,
change affiliation, or change what the study is about, I have to tell them. And the data sits
only on machines I control. All of that is fine. It's roughly how I already treat the Harvard
books.

The one line that gave me pause is the signature block. Researcher 1 is defined as "the
responsible permanent full-time faculty or staff member." I'm not one. I wrote "Independent"
under institution, left the title blank, signed it on the 16th and sent it back. The form
was clearly designed for a university, and whether HathiTrust accepts a person with no
university behind him is exactly the question I said I'd report on. The signed copy stays off
GitHub (it has my phone number on it); the wording is public. Next, if they say yes: give them
a fixed IP address for the Mac mini, then rsync about 31,000 volumes by their pairtree paths.

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

### BOM-10, second half: what the three priority states actually gave me

The New York, Pennsylvania, and Ohio pull finished on the laptop: 3,466 of 3,472 pages, about
14 million words, 84 MB of plain text. The other six return a server error from the Library's
text service on every try, so those scans are broken on their end and are logged as missing. Here is what the "priority
states" turn out to mean in practice:

| Paper | Where | Pages |
| --- | --- | --- |
| *The National Republican and Ohio Political Register* | Cincinnati | 1,828 |
| *Gazette of the United States, & Daily Advertiser* | Philadelphia | 532 |
| *Philanthropist* | Mount Pleasant, Ohio | 410 |
| *Gazette of the United States, & Philadelphia Daily Advertiser* | Philadelphia | 376 |
| *Freeman's Chronicle* | Columbus | 273 |
| *The Rights of All* | New York City | 40 |
| *Ulster County Gazette* | Kingston, NY | 7 |

Seven titles. The two New York papers are a 40-page run of *The Rights of All*, an
abolitionist paper from 1829, and a single 1800 issue of the *Ulster County Gazette*. Nothing
west of the Hudson. So "New York" in this corpus means New York City, not the Finger Lakes,
and the point from the first half stands: the Palmyra-area papers are a separate job.

The OCR quality varies a lot by date, which matters for anything that counts words. Here is
the top of the 1800 *Ulster County Gazette*, where the printer still used the long s:

```
E"'H K hoar Raving arrived w hxch,fi'i'b
"4 Piefident appointed, Mr SpEaxsr
atte Ided by the members present, proceeded
2¢ the President's house to present him their
addréss in'answer to his slvc'g'*ch;at the ape
```

"Piefident" is "President" with a long s; "seflion" two lines later is "session". The 1829
*Rights of All*, set in modern type, is nearly clean: "The history of this individual will
furnish a theme for the admiration and gratitude of posterity." Anything built on this corpus
needs a cleaning pass that knows about the long s, and the early pages should carry a
quality flag. I'll handle that in the normalization step (BOM-15) rather than here.

## The mini turned out to be the mini I already own

The budget said buy a Mac mini M5 Pro, 64 GB, 1 TB, about $3,199. I never bought it. When I
actually looked at the machine the data was supposed to live on, it's an M4 with 10 cores,
16 GB of memory and a 256 GB disk. Less than half the memory the plan called "too small".

So I changed the plan instead of the hardware. Use this machine, rent an H100 when a job needs
one, and buy the one thing that genuinely can't be worked around: a 2 TB external SSD, $150 to
$200. That saves about $3,000 up front and moves a few hundred of it into rented compute, paid
only when a job actually needs it. The thing a drive can't fix is memory. Two jobs want more
than 16 GB: passim, the text-reuse alignment, and the FAISS index for the passage search. Both
were already partly cloud lines in the budget, so the total moved by a few hundred dollars, not
a few thousand.

First I had to find room on the 256 GB disk. 48 GB free isn't enough for anything. The culprit
was a Colima VM I'd stopped using on October 5th, sitting there at 53 GB. Worth knowing:
`colima delete` doesn't actually give you the space back. It removes the VM and leaves the Lima
datadisk orphaned in `~/.colima/_lima/_disks/` — 85.9 GB on paper, 53 GB real, with its
`in_use_by` symlink dangling at nothing. I deleted that by hand. Ollama and one model I hadn't
touched in seven months went too. 59 GB back, 107 GB free.

Then I talked myself into a mistake worth writing down. The Harvard dataset is 946 GB. I
noticed that the publication date and the language are their own columns in the Parquet files,
which means you can read just those two columns and find your slice without downloading any
book text. It works beautifully: all 9,831 shards scanned in about 1.3 minutes. So I told
myself the pull was only about 25 GB of transfer and the 700 GB in the budget was wrong.

It isn't wrong. Each shard is a single row group of 100 volumes. Column pruning gets you the
metadata cheaply, but there's no row-level pushdown — to pull the text of one volume you read
essentially that whole 87 MB shard. The slice is 31,958 volumes out of 983,004, which is 3.3%,
and at that rate roughly 96% of the shards hold at least one book I want. So you read almost
all of them. About 700 GB of transfer for 44 GB of text, exactly as written. The cheap trick
was real and the conclusion I drew from it was not.

The pull is running now, against the internal disk, and I'll move `data/corpus/` to the SSD
when it shows up.

## Thirty-two thousand books

The Harvard pull finished at 5:38 in the morning. Eleven hours and thirty-eight minutes, all
9,831 shards, 31,958 books, nothing failed. About 700 GB came down the wire to keep 73 GiB.

Two things I had wrong. The first: I'd budgeted 44 GB and it came in at 73 GiB, because the
dataset ships two versions of every book — Harvard's raw OCR and their cleaned OCR — and the
pull keeps both. I'm glad it does. BOM-14 is supposed to clean up OCR, and now I can measure
whether my cleaning actually beats Harvard's instead of assuming it does. But it means every
storage number in the budget needs checking for how many versions a source ships, not how many
books. TCP ships XML *and* extracted text. That one will double too.

The second thing is stranger. The drive said 130 GiB used when the books only account for 73.
I went looking for the missing 57 and found it in `.Spotlight-V100`. macOS had been quietly
indexing the full text of thirty-two thousand 19th-century books so I could search them from
the menu bar, and built an index over half the size of the corpus to do it. It was also
competing for the disk the whole time the pull was running. Turning it off for that volume is
one command, and it's now in the setup doc.

The nice surprise was the T7. Hashing 37 GiB to build a checksum manifest took 79 seconds,
about 470 MB/s, and I had budgeted ten to twenty minutes. That matters more than it sounds:
Phase 2 reads this corpus repeatedly, and the drive is not going to be what slows it down.

## Eleven days for a quarter of a million books

Next on the list was the Internet Archive: 251,204 English books printed between 1780 and 1830
that Harvard doesn't have. Mostly American pamphlets and small imprints, which is exactly the
material the Harvard collection is thin on and exactly where a book printed in Palmyra in 1830
would live.

I started it expecting about three days. The Archive asks you to keep to roughly one request a
second, and a quarter of a million seconds is seventy hours. Then I measured what it was
actually doing: ten and a half books a minute. That's sixteen days. I let it settle and
measured again an hour later: 16.2 a minute, so about eleven days. Some of the early slowness
was the Archive throwing 500 errors and the fetcher politely backing off for five, then ten,
then fifteen seconds.

Eleven days instead of eleven hours, for a sixth as many books. The difference is the shape of
the thing. Harvard handed over its entire collection in 9,831 big bundles, and I could pull
several at once. The Archive has no bundle. It's one book, one request, 251,204 times, with a
deliberate pause between each so I'm not hammering a nonprofit's servers.

The question I actually cared about was whether eleven days was costing me anything. It isn't.
It's a Python script making HTTP requests and writing text files. There's no AI involved in any
of those 251,204 downloads. It could run for a month and the bill would be electricity. Worth
writing down because "the computer is working on it for eleven days" sounds expensive and isn't.

The other question was whether I'd get the same thing if I ran it again. Mostly. The list of
books comes from a catalog file that's committed to the repo, so the *selection* is fixed —
re-running next month picks the same 251,204. The fetching is best-effort: the script skips
anything already on disk, logs every failure to `failed.txt` with its HTTP code, and remembers
404s as permanent so it doesn't spend the next run retrying books that will never exist. So I
won't end up with exactly 251,204 files. I'll end up with that minus the failures, and a list
of which ones and why. That's the right trade. It fails where I can see it.

I decided to wait out the eleven days rather than narrow the list. I could cut it to the
`americana` collection, 86,600 items, and be done in a third of the time — but then the paper
has to explain why I excluded 165,000 books, and "it was taking a while" is not a reason I want
to defend. A complete corpus needs no excuse.

## Three servers at once

Then I caught myself being stupid about it.

I'd been treating the remaining downloads as a queue: Internet Archive, then the newspapers,
then the Text Creation Partnership, one after another. Eleven days, then two, then however long
TCP takes. But they're four different organizations on four different servers. The politeness
limits are per-host. The only thing they share is my mini, and all three jobs are sitting
around waiting for the network rather than doing any real work.

So they're all running now. The Archive pull, the rest of the Chronicling America newspapers
(159,146 pages), and the TCP texts (61,315 of them — early modern English, Evans' American
imprints, and the eighteenth-century ECCO set). Three downloads, three servers, no contention.
TCP had 438 files down in the first four minutes, which tells you how much of the eleven days
is the Archive specifically rather than anything about my setup.

Which leaves HathiTrust. I've signed their researcher agreement for the non-Google-digitized
volumes and I'm waiting on a decision — ticket GS-17502. They hold 107,178 period volumes
Harvard doesn't, which is four times the Harvard slice, but 75,984 of those are Google scans
that need a separate agreement Google may not give an independent researcher. The useful part:
24,261 of them were digitized by the Internet Archive, and the pull that's running right now is
already fetching them. So the waiting costs nothing either.

## Two hundred and nineteen days

The newspapers went wrong. The fetcher asks the Library of Congress's text service for one page
at a time, and that service started returning HTTP 500 errors — not "slow down", just "broken".
My code did the polite thing and backed off: five seconds, then ten, twenty, forty, eighty. Most
pages did eventually arrive, 96% of them, but each one cost about a minute of sleeping. The rate
fell to half a page a minute. All 159,146 pages would have taken **219 days**.

The Internet Archive was failing the same way, though not as badly. Same 500s, same backoff, 25
days to finish. Two different organizations having a bad day at the same time, which I'd have
guessed was my network if a third download hadn't been running at full speed the whole time.

The Archive was the easy fix. Their own developer guidance says about four concurrent downloads
with a one second delay, and warns that more than three or four connections can itself trip rate
limiting. I'd been running one. Four workers means the ones that aren't asleep in a backoff keep
fetching. It went from 7 items a minute to 53, so 25 days became about four. If they ever answer
429 or 503 — the codes that actually mean slow down — every worker stops. That's the line: 500s
are their fault and worth retrying around, 429s are them asking, and you don't argue.

The newspapers needed a different idea, so I went and read. It turns out the Library of Congress
publishes all of this in bulk, as batch archives, specifically for text and data mining. I
checked our catalog against the batch list: every one of our 159,146 pages sits in just **76
batches**, about 69 GB. Hours, not months.

Then I did something stupid. To find out how big those 76 files were I sent 76 requests, eight
at a time. The Library of Congress rate-limited me, which is exactly what should happen, and I
deserved it. One request would have told me the average and I could have multiplied by 76. I
backed off, waited twenty-five minutes, tried once more, still blocked, and stopped.

But the block turned out not to be about the rate at all. The download URL answers scripted
requests with a Cloudflare "Just a moment..." challenge — a 5.6 KB HTML page where the 3 MB file
should be. A real browser passes that check. A human can download these; a script can't.

So I made a list — all 76, sorted by how many of our pages each one holds, with a running total
so you can stop early — and clicked through them myself over about an hour. The first batch
alone, 0.74 GB, holds 10,096 of our pages: four times what the per-page fetcher had managed all
day. Twenty-five batches got us past three quarters. All 76 came in at 68.8 GB, and every one
matched the byte-exact size the Library publishes.

That hour of clicking replaced 219 days.

Two small things I had to fix along the way, both the same bug in different clothes. Chrome
writes an in-progress download as `Unconfirmed 286909.crdownload`, hiding the real filename
until it finishes, so my "what's still missing" script couldn't see what was in flight and kept
handing back files that were already downloading. That cost about 5 GB of duplicate downloads
before I noticed. It now counts the hidden ones and skips that many places down the list, which
costs nothing and can't collide.

## Checking the shortcut was really the same thing

A faster route to the same data is only useful if it *is* the same data. We had 4,286 pages
fetched both ways — slowly through the API, and now out of the tarballs — so I compared them.

1,319 identical, 1,066 different. That's a bad feeling for a second.

The differences were one to three bytes each, and all of them were blank lines. The API returns
a page as JSON segments and my code joins them with a newline, so an empty segment leaves an
extra blank line that isn't in the original file. Compare the two ignoring blank lines and all
2,490 overlapping pages match, word for word, with zero exceptions.

So the bulk text is the same text. Worth the half hour to prove rather than assume, because
"I switched to a faster source" is exactly the kind of decision that quietly changes a corpus.

## The three bugs were all mine

The Internet Archive pull died overnight. My code stopped it, and the message it printed was
"the Archive answered 429 or 503, re-run later with fewer workers". So I nearly halved the
workers. Then Dave asked a good question: it ran seven hours at four, why change it?

He was right. I looked properly. Every one of those 503s was the *same file* — `b21442502`,
retrying five times — and there were no 429s at all in seven hours. The Archive never asked us
to slow down. One broken item had tripped a global stop.

Fixing that uncovered two more, and the clue was a contrast: the pull was managing one item a
minute, while twelve randomly chosen pending items fetched instantly when I tested them by hand.
If the Archive were down, the random twelve would fail too. So the problem had to be *where the
work list was*, not the service.

It was. The catalog is grouped by collection, so working through it in order meant hitting a
long run of 1782-83 British Library items that all returned 500 — and with four workers all in
the same bad neighbourhood, everything stalled together. Worse, each of those cost 75 seconds:
six retries with escalating sleeps to learn what the first attempt already knew. I checked one
of them, `threetreatisesfi1783harr2`: its metadata lists the text file, so it exists, the
Archive just can't serve it.

Three fixes. A 429 still stops everything immediately, because that one is unambiguous; a 503
only counts once three *different* items have thrown one. Server errors give up after two tries
and get recorded for a later pass, since the job is resumable and a second run costs only what's
missing. And the work list is shuffled with a fixed seed, so a bad collection spreads out
instead of blocking every worker at once.

One a minute became forty-six a minute. Two hundred and thirty-four days became three and a half.

The thing worth writing down: for about twenty minutes I believed the Internet Archive was
rate-limiting us, and the evidence for that was a message my own code had written.

## A quarter of a million books

The Internet Archive pull finished at 99.48% — 249,906 items of 251,204, 99 GB. It took four
days and the supervisor restarted it twenty-six times, which tells you most of the story.

The fetcher had three bugs and I found all of them by asking why a number looked wrong rather
than by reading the code. The pull was managing one item a minute while twelve items I picked
at random downloaded instantly by hand; that contradiction was the whole clue. One broken file
was tripping a global stop. Unservable items were costing seventy-five seconds each in retries
to learn what the first attempt already knew. And the work list was ordered by collection, so
four workers would hit the same bad neighbourhood together and stall as one. One a minute
became seventy-six.

The best fix was not a fix at all. I had the stop-on-throttle logic wrong twice, and the second
time I stopped tuning it and wrote a supervisor instead: restart after any exit while the work
list is still shrinking, give up only when a restart gains nothing. The heuristic is still
imperfect — it tripped twice more overnight — but a false alarm now costs five minutes instead
of a night. It also stopped the job cleanly this morning when the remaining items genuinely
would not come, which is exactly what it was for.

Then Dave asked whether the items with no OCR were scans we could OCR ourselves. They weren't
scans. Of thirty I sampled, twenty-eight had OCR sitting right there under a different
filename — named for an internal barcode, or a stripped prefix, `jstor-30074678` filed as
`30074678_djvu.txt`. Our URL assumed every item's text file was named after the item. That
assumption had been quietly discarding about eight thousand five hundred books, 3.4% of the
corpus. The 404 count fell from 9,127 to 1,550 once the fetcher learned to ask.

Worth noticing what that was: a question about the wrong thing that found the right thing.

What's left out is honest and written down. 4,822 items did not come: 4,703 the Archive
answered with a server error, 1,188 that genuinely have no OCR at all — maps, deeds,
manuscripts — and 251 restricted. Every one is in `failed.txt` with its code. The server errors
may clear in a week and the pull is resumable, so the tail is a command, not a project.

Across four days and roughly a quarter of a million requests, the Archive never once returned
429. Every stop was our own code being wrong about what its errors meant.

## Which model should do the boring work

The corpus needs a genre on every one of 560,000 records, because genre-matched controls are
what stop biblical *style* being mistaken for a biblical *author*. That is the fix for the flaw
that sank the 1980 study, so it has to be right, and it is far too much to do by hand.

First thing I checked was how much needs a model at all. Not much, as it turns out. Every
Chronicling America page is a newspaper page — we know that from which archive it came out of.
A title reading "The Hive 1804-07-25: Vol 2 Iss 6" is a periodical issue and says so in its own
name. Rules like that settle **49.5%** of the corpus without asking anything. The other half
needs judgement.

Then the question was which model. Haiku is the cheap one, so I tried it first and measured
rather than guessed: 60 records, stratified across all four sources, against labels I had made
by hand.

Haiku got **65%**. Worse, look at *how* it failed. Asked to pick from a closed list of eight, it
answered "poems" — a label that does not exist. For a volume of medical transactions it replied
"Wait, the label must be exact: scientific_medical", correct answer wrapped in its own
deliberation. And it reached for "other" six times where an obvious category fitted, which is
the quiet kind of wrong: "other" does not look like an error downstream, it just silently
shrinks the control sets.

Some of that was my fault, not the model's. I had given it eight bare label names and no
definitions. Writing one line per category, forbidding explanation, and matching the reply
against the list instead of trusting it took Haiku to **72%** with zero invented labels and the
"other" problem gone.

But the remaining errors were not mechanical. Haiku filed a book titled simply *Poems* under
sermons, and the *Daily National Intelligencer* — a newspaper — under medicine. No prompt fixes
that. Sonnet on the same prompt and the same 60 records: **87%**, at 0.36 seconds each with
eight running at once. About a day and a bit for all 282,566.

So: rules for half, Sonnet for the rest, and Codex as an adversary on the validation sample,
because it is a different model family and its mistakes will not be correlated with Sonnet's.

The 87% is agreement with *me*, which is not the same as being right. I am one person reading
titles. The number that gets published comes from Dave working through a sample and saying
agree or disagree, and that is the one the paper will have to defend.

## Five days of paperwork, twenty-four minutes of data

HathiTrust came through. I asked on the 15th, signed their researcher agreement on the 16th,
and on the 20th Janet at HathiTrust wrote back: "You're all set up now." They did something
generous I had not expected — rather than making me produce a static IP, they allow-listed my
ordinary dynamic home address. It expires on the 30th of November.

Then the actual download took **twenty-four minutes**. 31,194 volumes, nineteen gigabytes, over
rsync.

Set that against the Internet Archive: four days, a supervisor restarting it twenty-six times,
three bugs in my own fetcher. Same job, different plumbing. The Archive is a public website and
I was asking it for a quarter of a million files one at a time; HathiTrust hands researchers a
dataset built to be copied in bulk. The bottleneck here was paperwork, and the paperwork was
five days.

Of the 107,178 volumes I asked for, 75,984 did not come. Those are the Google-digitized ones,
which are not in this dataset and need a separate agreement with Google. I have emailed them,
and I am not waiting: the corpus is finished without those volumes and if an agreement ever
arrives they are a later addition.

Then the number that made me stop. Of the 31,194 that did arrive, **21,810 I already had** —
pulled from the Internet Archive last week, because the Archive digitized them on HathiTrust's
behalf. So a dataset I spent five days of correspondence on contributed **9,384 volumes** I did
not have. Under two percent of the corpus.

Worth it? I nearly wrote that it was marginal. But I had the wrong frame. Those 21,810
duplicates are not waste — they are the same book scanned once and OCR'd twice, by two different
organisations with different software. BOM-14 has to clean up OCR and then prove the cleaning
helped, and proving that normally means hand-correcting pages to have something to measure
against. Instead I now have twenty-one thousand pairs for free.

A caution on that number, because I got it wrong first. My initial check said the overlap was
zero. Zero is a suspicious answer when you expect twenty thousand, so I looked: the mapping file
calls the field `ia_identifier` and my code asked for `ia_id`, so every lookup quietly missed and
returned nothing. If the bug had produced "18,000" instead of "0" I might have believed it.

## Writing down everyone else's claims before I have any answers

A thought I had this week: when this finishes, people will want to know what it says about the
specific arguments already out there. The CES Letter says the Book of Mormon leans on *The Late
War* and *View of the Hebrews*. Skousen and Carmack say its grammar is early modern English that
nobody in 1829 could have faked. Those are testable, and I will be able to speak to them.

The trap is obvious once you see it. If I wait until I have results and *then* decide which
claims to address, I will pick the ones I have something interesting to say about. Not
dishonestly — it just happens. You answer the questions your data answered.

So the list is written now, before any result exists, and frozen with a hash the same way the
analysis thresholds are. Twelve claims so far across eight sources, and each one carries, in
advance, what would count as supporting it and what would count as contradicting it. Four
critical, seven apologetic, one academic — the apologetic side outnumbers the critical side
because Skousen and Carmack make more specifically falsifiable claims than the CES Letter does.

Writing it turned up something I did not expect. Carmack's central argument is that the text's
syntax appears in neither the King James Bible, nor Joseph Smith's own writing, nor the
pseudo-biblical books of his era, but was ordinary in the late 1500s. That names three
comparison sets I already hold and one period I already hold. And the imitation test — which I
designed months before reading him, to check whether a deliberate forger could fool each method
— turns out to be its decisive test. If King James pastiche *can* shift the dating classifier,
his claim fails. If it cannot, his claim is supported by a method built without reference to it.

Four of the twelve are marked untestable and will stay that way. Most of both documents is
historical or doctrinal and no amount of word-counting touches it. Those get reported as
untestable with the reason, not quietly dropped, and the write-up has to say plainly that being
untestable is not the same as being disproved. A document that answered only one side would read
as advocacy for the other, which is the one thing this project cannot afford to be.

## Two kinds of "add more workers"

A small technical thing worth writing down because it cost me a wrong assumption twice.

When I parallelised the Internet Archive fetcher, going from one worker to sixteen was nearly
linear, because every worker spent its time waiting on the network while the Mac sat idle. The
limit there was a policy — the Archive asks for about four concurrent downloads — not the
hardware.

When I benchmarked the local models, I assumed the same shape and it is the opposite. Four
workers and eight workers finished within three seconds of each other, because every request
runs on the same GPU. They are not waiting, they are queueing. More threads just add memory
pressure for the key-value cache, and on sixteen gigabytes that is the thing that bites.

So: remote work is limited by what the other end will tolerate, local work by what the silicon
can do, and the answer to "can we add more threads" is a different answer each time. Measure it;
the intuition transfers badly.

## What 300 records taught me about my own benchmark

The 60-record test said Sonnet 87%, Llama 83%, so I nearly wrote down "use Sonnet". Then I
did the arithmetic I should have done first. Fifty-two out of sixty against fifty out of
sixty is a two-record difference. At that sample size the error bars are about nine points
wide. The two models were indistinguishable and I had been about to choose between them on
noise.

So I ran three hundred instead, and built it differently. Sixty of those records came from the
half the rules already decide — a Chronicling America page *is* a newspaper page, we know that
from which archive it arrived in — so for those sixty there is something close to a right
answer to measure against.

Against that: **Sonnet 98%, Llama 97%.** Still indistinguishable, but now both demonstrably
good rather than merely similar.

The interesting number was the other one. On the 239 records that genuinely need judgement, the
two models agreed only **72%** of the time. Two models that are each ~97% accurate on easy
records disagree on more than a quarter of hard ones.

I went and read the disagreements expecting to find one model losing. That is not what is
there:

> *Philosophical Transactions of the Royal Society* — Sonnet says newspaper_periodical, Llama
> says scientific_medical
>
> *Encyclopaedia Britannica* — Sonnet says other, Llama says history_chronicle
>
> *Curtis's Botanical Magazine* — Sonnet says newspaper_periodical, Llama says scientific_medical

Nobody is wrong. The *Philosophical Transactions* is a scientific journal: it is a periodical
and it is scientific, and my label set makes you choose. Those are not model errors, they are
holes in a taxonomy I wrote in an afternoon. A third of what looked like model disagreement is
really me not having said what happens when two categories both apply.

That is worth more than knowing which model to buy. A label scheme that forces arbitrary
choices produces arbitrary control sets, and the control sets are the whole defence against
mistaking biblical *style* for a biblical *author*.

So two changes. The label definitions get a precedence rule — if a work was issued in numbered
parts it is a periodical first, whatever its subject — and that rule goes in the registered
method, not in my head. And the validation sample has to over-sample the ambiguous categories,
because a random three hundred mostly tests the easy cases.

On the original question: Llama runs free and unmetered on the mini for three and a half days;
Sonnet runs in one and a bit but spends subscription. They are the same accuracy. So the cheap
model does the corpus, and the expensive one is kept for the records where a second opinion
actually buys something.

## The corpus, as it now stands

| Source | On disk | Files |
| --- | --- | --- |
| Internet Archive | 99 GB | 249,906 |
| Harvard Institutional Books | 73 GB | 31,958 volumes, two OCR versions each |
| HathiTrust Extracted Features | 23 GB | 105,888 |
| Text Creation Partnership | 22 GB | 61,310 texts, XML and extracted text |
| Chronicling America | 4.4 GB | 158,960 pages |
| **Total** | **221 GB** | |

That is most of what was printed in English between 1780 and 1830 that has been digitised,
which is the thing none of the earlier studies had.

## What's next

The extraction is running: each tarball is checked against the SHA-256 the Library publishes,
only the 1800-1830 pages get pulled out, and the archive is deleted afterwards so 69 GB of
tarballs doesn't have to live on the disk forever. Then Phase 2: deduplicate, fix the OCR,
normalize the spelling, mask the King James quotations, and cut the text into segments.
HathiTrust (BOM-08) resolves whenever it resolves.

---

## The Phoenix that isn't there, and the paper that is

BOM-41 started as a hunt for two newspapers W. W. Phelps edited before 1830, because Phelps is
a named candidate with zero pre-1830 words in my inventory. The *Ontario Phoenix*, his
Canandaigua paper, eleven miles from the Smiths, was the prize. The *Lake Light*, his first
paper in Trumansburg, was the consolation.

It came out the other way round. The Phoenix is not digitized anywhere: not in Chronicling
America (the catalogue record is there, zero pages), not in NYS Historic Newspapers (I had Dave
read the title index in a browser, since the site blocks scripts), not in HathiTrust or the
Internet Archive. Then the New York State Library's union list told me why it would not have
mattered much. The only continuous run anyone holds, on microfilm at the Ontario County
Historical Society, starts 7 July 1830, after the Book of Mormon was on sale and after Phelps
had bought his copy. Before 1830 there are about twenty scattered paper issues in four
libraries: Rochester Public Library has fifteen or so from July 1828 to January 1829, and the
whole of 1829 is three single issues. The "two years of a weekly, tens of thousands of words"
I wrote into the issue never existed. Twenty four-page issues, of which only the editorial
matter is his, and he shared the masthead with Bloomer until 1829. That is the correction, and
it goes in the paper as a gap with a cause.

The Lake Light is the opposite story. The Ulysses Philomathic Library in Trumansburg put its
newspapers online through a small commercial archive host, and that host does not sit behind
Cloudflare. Every page is a PDF behind a predictable name,
`lake_light_usa_new_york_trumansburg_18271126_english_3`, so the fetcher just asks the viewer
for every date and page number in the range and takes what answers. 168 pages, 42 issues, 10
October 1827 to 19 November 1828, the same run the State Library has on film. The site says
336 pages. That number is the same 168 pages digitized twice: an old ABBYY scan from the first
round and a 400 dpi Tesseract scan from a second one. The old scan also files the 3 December
issue as pages 5 to 8 of 26 November, which is how I noticed. I keep the new scan and ignore the
old one.

The text layer is what you would expect from microfilm. The masthead page of the first issue
yields six words. A good page gives 3,400, most of them wrong in small ways: "secret influence
of masonry exerts) river to Easton." That is fine. The 400 dpi images are the input the OCR
correction stage was built for, and the measurement never runs on raw text.

Reading the NYSHN title index also corrected something older. BOM-10 found 47 New York pages in
Chronicling America for 1800-1830 and called New York a hole. It is a hole in Chronicling
America. The state's own program has the Palmyra Register (1817-1821), the Palmyra Herald
(1822-1823), the Canandaigua Ontario Repository (1824-1829), the Rochester Antimasonic Inquirer
(1828-1830) and a few dozen more period titles. Whether to pull them is a scope decision I have
put on the issue. The pull itself needs a browser that has passed Cloudflare once; there is now
a script that drives one.

Later the same night the script ran for real, on the paper that matters most: the *Wayne
Sentinel*, Palmyra's weekly, printed by the man who would print the Book of Mormon. Dave
started Brave with a debugging port, passed the Cloudflare check by hand, and the script drove
that window through the site's browse pages: one page per month, one per issue, one per
newspaper page, and for each of those the site's own OCR text view. The first pass came back
with a quarter of the issues, every one from October, November or December, which is the kind
of pattern that means a bug and not a gap: the site zero-pads its month numbers and I did
not. Fixed, the run found 376 issues from 1 October 1823 to the end of 1830, which is a weekly
missing four weeks in seven years. 1,429 pages, eleven million "words", a good share of them
OCR confetti. Nine pages have no text on the site at all. The page PDFs stayed behind: each
one sits behind its own Cloudflare Turnstile, which solves itself in a real browser about one
time in three, so I left them and took the text. It is 44 MB and goes in git, so the mini
gets it with a pull.

## Counting Joseph Smith's own words

With the Joseph Smith Papers pages finally down, BOM-13 came to the part I had been putting off:
how many words does each candidate actually have? The inventory had estimates. Estimates from
page counts turned out to be generous.

The Papers make one thing easy that I expected to be hard. Every stretch of text in Joseph
Smith's own hand is wrapped in a tag, `<span class="josephswriting">`, word by word. So the 1832
History, which he and Frederick G. Williams wrote in turns, splits cleanly: 981 words in his
hand, 1,049 in Williams's. The Journal has 9,000 words and 1,661 of them are his; the rest are
clerks, often writing about him in the third person, and those count for nobody. Letterbook 1
holds 17 letters the Papers attribute to him. Two are in his hand.

Hand is not authorship, though. Joseph copied Oliver Cowdery's 1829 letters into the
Letterbook himself, so those pages are full of "josephswriting" tags around Cowdery's words.
The rule I wrote before counting says the title decides who composed a text and the tag only
decides whose pen it was. Those letters go to Cowdery.

The wrong turn this time was in my own reader. Checking the hand split against the plain text,
the numbers did not agree, and pulling on that found three things the old text extractor did:
it dropped every word the Papers had linked to a glossary popup ("Kees", for keys), it counted
footnote numbers as words, and it counted hidden biographical notes ("27 Aug. 1793–27 May 1840.
Hatter.") as if Joseph had written them. Small per page; up to a tenth of a short letter. The same
extractor built the Book of Mormon manuscript text back in BOM-05, where it also split words
that the site breaks across two tags. I first put that at 2,188 words in the original
manuscript, which sounded alarming. It was wrong: that was a count of whitespace pieces, and
most of them were punctuation cut loose from a word. Rebuilt and run through the alignment's own
tokenizer (BOM-52), the original manuscript changed by eight words ("ap point" became
"appoint"), the printer's manuscript by 63 (39 glossed place names restored, 24 split words
joined), one paragraph's page mapping moved, and twelve paragraphs got very slightly more
similar to the 1830 text. Worth fixing, nothing like what I first said. The lesson is the usual
one: measure with the instrument the analysis uses, not a rough proxy.

The result, before any masking of Bible quotations:

| | before 1830 | after |
| --- | ---: | ---: |
| Joseph Smith, own hand | 0 | 6,158 |
| Joseph Smith, dictated | 2,844 | 5,402 |
| Oliver Cowdery, own hand | 1,443 | 0 |
| Solomon Spalding | 44,279 | - |
| Ethan Smith | 299,398 | - |

The preregistration's floor is 10,000 words. Every one of Joseph Smith's samples is under it, and
the pre-1830 dictated revelations, the only pre-1830 text he has, are a quarter of what I had
estimated. That is not a surprise in kind, the plan said "likely under 10,000", but it is a
surprise in size, and it is exactly the sort of thing the "unreliable sample" flag exists for.

## Signed is a stricter word than it sounds

Phelps had zero words at the end of the morning. His candidate texts were whole newspaper runs,
and a newspaper is mostly other people. The rule I wrote first: count only a letter, essay or
address that ends in one candidate's name. No committee addresses, no minutes he signed as
chairman, no unsigned editorials, because the *Star*'s publisher line says "W. W. Phelps & Co."
and the *Messenger*'s editor changed three times.

A script found 67 lines that look like a signature, and most of its guesses about where each
item starts were wrong: it kept latching onto the running head, which the OCR spells
"MESJSKNGKR AND ADVOCATE". So every span got read and fixed by hand (by an agent, with me
checking its line numbers against the file and reading the longest ones myself). Phelps's own
name was the next problem. It comes out as "W. W. F helps:" in one letter and "As ever, W. W.
PIIELP8." in another, on the same line as his last sentence, where no pattern looking for a
name on its own line will see it.

Then four of Cowdery's eight famous letters to Phelps turned out to have no signature at all.
Letter V just stops: "Accept assurance of my esteem as ever." The strict rule would have thrown
out half of a series whose author nobody doubts. I had named the series in the rules before
extracting, so I wrote down a clarification saying the series counts whole, and said in the
same place that it was written after seeing the data. The check that it worked: the eight
letters come to 23,499 words, against 24,040 in the later book reprint, which has a title page
and preface the newspaper does not.

One more thing the reading turned up. Letter I opens with an editor's note that "our brother
J. Smith jr. has offered to assist us" with the history the letters tell. Signed by Cowdery,
helped by Smith. That goes in the record next to the count.

Phelps ends at 31,538 words, Rigdon at 23,478, Cowdery's printed sample at 48,002. All after
1830, all before masking. Nobody but the three outside authors has 10,000 words written before
the Book of Mormon.

## Deciding not to click through 300 records, yet

The validation page came up on the laptop with no text in it, because the excerpts only live on
the mini. The mini committed the filled page to the private repo and I pulled it. First record:
James Mill's *Analysis of the Phenomena of the Human Mind*, 1829. Llama says
scientific_medical plus newspaper_periodical, Sonnet says sermon_devotional. Both wrong. It is
a philosophy book, and the taxonomy has no slot for philosophy. That is going to come up a lot.

Then I asked the question I should have asked first: how much does this matter? The genre
labels never touch authorship. They build the genre-matched control pools, so a style match can
be shown to be authorial and not "both are sermons." Amendment 4 already made the real test a
perturbation: corrupt the labels at the measured error rate, rerun, see if anything moves. The
300 hand-judged records exist only to supply that rate. And I already have a worst case for it:
the two models disagree on 28% of the hard records and about 3% of the easy ones.

So the plan is now: run the perturbation at the worst case first. If the conclusions hold, the
labels don't matter and nobody judges 300 Tudor pamphlets. If they move, the real rate is
needed and the hour of clicking is worth it. That is BOM-53, blocked on BOM-40, and the trigger
is written into the issue so it comes back on its own.

To make the hour short if it does come back, I had Claude draft a label and a one-line reason
for every record under a written rule sheet. The draft sides with Llama on 151, Sonnet on 87,
and neither on 62. The 62 are mostly taxonomy holes rather than model mistakes: philosophy,
almanacs, playbills, a cricket scorecard, an alchemical treatise, Johnson's collected works.
The draft is committed and labeled as what it is, an AI drafting aid for a human to agree with
or override, not a judgement.

## Closing the catalog with one thing still undone on purpose

BOM-12 is done, and it is done with a known hole in it. The catalog has 559,986 rows, 502,134
of them with text. Every row has two genre labels or a rule, and 7,413 works sit in 3,336
near-duplicate groups with the earliest copy marked to keep. Nothing was deleted.

The hole is in the dedup. It only catches copies from the same source. Across sources, 300 pairs
I checked by eye as the same book scored a median of 0.164 on a 0-to-1 similarity, against a bar
of 0.8. Not one cleared it. That is not bad OCR so much as two different bad OCRs: a five-word
run survives two independent passes about a third of the time. The fix is to run it again after
the text is cleaned (BOM-14) and the spelling normalized (BOM-15), so that re-run is now a
checkbox on BOM-15 instead of a reason to hold this issue open on work that can't happen yet.
The other direction is wrong too: one "duplicate" group has 173 members, and they are different
volumes of *The Public Statutes at Large*, collapsed together by shared boilerplate.

One small thing turned up while I was building the review page. Three records showed no text at
all. The excerpt code skipped any line under 40 characters, which is every line of a poem. The
first was a 1522 romance:

> O Myghty fader in heuen on hye / One god and perſones thre / That made bothe daye & nyght

That was easy to fix on the page. The same 40-character rule also fed the genre model its
prompt, so verse probably got labelled from the title alone. That is a question for later, not
something to quietly patch now, because patching it would change what a rerun of the labels sees.

Last, housekeeping I should have done earlier: the catalog folder had no checksum manifest and
its SOURCES.md never mentioned any of the eleven files this issue made. Both are fixed.

## Measuring how bad the OCR is, without reading any of it by hand

The pre-registration says to drop any volume with more than 10% of its characters wrong. That
sounds simple until you ask: wrong compared to what? You need a correct copy of the same page.
I didn't have the hours to type up hundreds of pages, and it turned out I didn't need to.

The Text Creation Partnership spent years having people hand-key early American and British
books. Some of those same books are also in my OCR pile, scanned from a different copy. So I
matched them up by title, author and year, got 2,108 pairs, and lined up 20 short passages in
each. That's a real error rate, measured, on 1,883 books. The median book was 9.9% wrong
before cleaning and 8.3% after. 38% of them are still over the 10% line after cleaning.

Cleaning is mostly boring and mostly works: running heads like "THE HISTORY OF" at the top of
every page come off, words split across lines get joined back, and the long s that OCR reads as
an f ("confeffion") gets put back. Over the whole corpus that was 349 million long-s fixes.

Then the trick: I can't measure every book that way, only the ones with a hand-keyed twin. So I
fit a small model that guesses the error rate from things I *can* count in any text, like how
many words are in a period dictionary, and checked it by holding books out. It's decent, not
great. It ranks books well (Spearman 0.78), but it puts about one book in five on the wrong side
of the 10% line. Those near the line get a `near_cutoff` flag so later analysis can test whether
it matters.

One check I liked because it's independent: Harvard scores its own OCR, and I never used those
scores. Across 31,958 Harvard books, my estimate and theirs move together (Spearman -0.58).

Here's what a book over the line looks like. This is an 1800 broadside, *The last dying speech
and confession* of a man hanged for murdering his wife, estimated at 18% wrong:

> Last D ing Speech and Confeſſion, ... the UNFOQORTUNATE. GEORGE DING L. ER. ... was able to
> converſe, and walk acro:s

It isn't thrown away. It's flagged `ocr_excluded`, and that's all. The split by source:

| Source | Volumes | Over 10% |
| --- | --- | --- |
| Harvard | 31,958 | 2.5% |
| HathiTrust | 31,194 | 11.9% |
| Internet Archive | 249,906 | 24.9% |
| Chronicling America | 158,960 | 27.8% |

The newspaper number is a guess on top of a guess. The keyed twins are all books from 1780 to
1800, so a newspaper from 1825 is outside what the model was trained on, and its rows say so.

Two wrong turns. First I tried letting Sonnet fix the OCR. On 100 passages the median error
dropped from 9.4% to 6.1%, which looks great, but four of its answers came back more than twice
as long as the passage, padded with text it made up, and the average got *worse*. A fixer that
sometimes invents text is no good for a study that is about who wrote which words, so it's not
used. Second, my first error model worked on the raw number and was badly pulled around by a few
hopeless books; working on a log scale fixed it.

The Wayne Sentinel needed its own repair. Its website delivers text with words broken into
letters, and I put the pieces back with a dictionary of period word frequencies:

> before: `n that Jo h n R a n d o lp h has b een re -e le cted , Tfcout o p p o s i t i o n`
>
> after: `n that John Randolph has been reelected , T fc out opposition`

On keyed text broken up the same way on purpose, that gets 93% of words back, up from 62%.
"Tfcout" (without) is still wrong. That's the OCR, not the breaking, and it stays.

## Spelling, and the tool I used wrong

Old books spell things their own way. A 1550 chronicle says "vnto" and "haue" and "hym". If I'm
going to compare word habits across three hundred years, "vnto" and "unto" need to be the same
word. The plan said to use MorphAdorner, a tool Northwestern built for exactly this, for anything
printed before 1700. For 1780 to 1830, the books the study actually cares about, only the
printing quirks get fixed: the long s that looks like an f, and joined letters like "ﬁ". Their
spelling stays as printed, because "publick" versus "public" might be part of someone's habit.

My first pass was wrong, and it looked fine until I read the list of what it had changed.
MorphAdorner ships a big two-column table of old spelling to new, and I applied it word by word.
Near the top of the list of changes:

> `part` → `partly`, 1,009,519 times

A million nouns became adverbs. The table isn't meant to be used alone. MorphAdorner first works
out what part of speech each word is, and only then picks the spelling: "part" the noun stays,
"part" the adverb becomes "partly"; "ye" is "you" when it's a pronoun and "the" when it's an old
way of writing "the". So I ran the real tool instead, which took four hours on the mini. Now
`part` → `partly` happens 352 times, and "ye" splits 882,357 to "you" and 105,434 to "the".

The real tool has habits of its own, and I've left them alone on purpose. It turns the article
"an" into "and" 3.3 million times, and "whether" into "whither" half a million times. That's
the method the plan names, so it stays, and I've written down a proposed fix for the owner (me)
to make officially. It only touches the pre-1700 reference books, and the original text is kept.

Then I tripped twice putting MorphAdorner's output back into the books. It hands back a list of
words, and I walk through the original text swapping each one in place, so the lines and
paragraphs survive. Where the text has ". ." split across a line, MorphAdorner writes "..". My
walker went looking for the next "..", found one a hundred characters on, and from then on it was
always a little ahead, grabbing the next "the" or "of", until it ran off the end of a book with
two million words still unplaced. The fix was a rule: you can't skip past words you haven't
accounted for, and after a stumble the next three words have to line up too. Final count: 0.03%
of 1.38 billion words couldn't be placed, and those keep their printed spelling.

The last check was the one I'd been waiting for since the catalog. The duplicate finder only
caught copies of a book from the same source, and I'd said that cleaning the OCR and fixing the
spelling first would let it see across sources. It doesn't. On 300 pairs of what look like the same
book in two sources, similarity rose from 0.12 to 0.18. The bar is 0.8, and not one pair clears
it. Two different bad OCRs of the same page still share too few five-word runs. That's now
written down as a known gap, with a possible fix that would need an official change to the plan.

## Reopening the catalog for the books I forgot

I closed the catalog a day early, and it was missing a whole source. HathiTrust's volumes, the
ones I'd signed a researcher agreement for, had been downloaded and never merged in. I found it
while checking something else, which is the uncomfortable way to find most things. So the
catalog went from 559,986 rows to 695,021, with 31,194 more books that actually have text.

Adding them meant labelling them. The local Llama model did 29,696 of them overnight, about one
a second, and a rule handled the rest. Then the second-opinion sample had to be drawn again,
because the plan says 5,000 records stratified by source, and a sample with no HathiTrust in it
doesn't meet that. Same seed, same procedure; 2,349 old answers carried over because the same
books came up with the same first label.

The second pass is Sonnet, a different model family, labelling the same 5,000 records blind.
The two agree on at least one label 84.9% of the time. HathiTrust comes in at 83.9%, right
with the others, which is the main thing I wanted to know. In 15% of cases they share no label
at all, and those are the only ones worth a third look. Opus took that look, on 757 records.
That's a simulated tiebreak, another model, not a person. It sided with Sonnet 553 times and
with Llama 62 times. Some of what it was looking at:

> *The inaugural address, delivered in Brunswick, September 9th, 1802* -- Llama: history and
> law. Sonnet: sermon. Opus: sermon.
>
> *The cottage fire-side* (1822) -- Llama: newspaper. Sonnet: sermon. Opus: fiction.
>
> *An essay on the best means of ascertaining the affinities of oriental languages* (1828) --
> Llama: newspaper and science. Sonnet: history. Opus: history.

So where they really disagree, the cheap model is usually the one that's wrong. That's about 12%
of the sample, and the genre-dependent results will be stress-tested against a worse error rate
than that before anyone leans on them.

Two of my own mistakes along the way. The tiebreak was set to look at every record the two
models didn't match exactly, 2,461 of them, when only the 757 with no label in common are real
conflicts. I caught it in the first minute and cut it down, which saved two-thirds of the calls.
And a wait loop I'd written to tell me when the overnight labelling finished never fired: tmux
matched the name `genre_ht` to a different session called `genre_ht_commit`, so the loop
thought the job was still running for three and a half hours after it was done.

## Amendment 6, and counting a book once

Building the corpus meant making about a dozen small decisions the plan never covered. How many
times does a word have to appear in hand-typed books before I trust it as a real word? What do I
do with books printed between 1700 and 1780, when the plan only talks about before 1700 and after
1780? Each one went on a list as I made it, and today I registered the whole list on OSF as
Amendment 6, before anything has been measured on the Book of Mormon. That's the point of doing
it now: nobody can say I picked the settings after seeing which way they pushed the answer.

Two of the changes are real decisions, not housekeeping.

The first is the pseudo-biblical control, the books written to sound like the King James Bible.
The rule I'd registered matched any book where the genre model put "pseudo-biblical" as either of
its two labels. That gave 3,727 books, and when I read the titles they were mostly *about* the
Bible: commentaries on the Psalms, a synopsis of the four gospels, a defence of Calvinism. A test
against those would let biblical style alone make the Book of Mormon look different, which is
exactly what this control is supposed to rule out. So the control will be a curated list chosen by
a rule written down in advance, with two different AI models checking each candidate and the
four books the plan names (Leacock, Snowden, Linning, Hunt) as a test the method has to pass.

The second is counting a book once. The duplicate finder compares five-word runs, and two
different OCR readings of the same page share too few of them, so a book held by two libraries
counted twice. Amendment 6 adds a second pass: same title, same author, same year, in different
sources, counts as one. I checked a sample of 200 of those groups against the actual text, and
almost all are the same text; the few that aren't are other volumes of the same work, like
volume 1 and volume 2 of *Sketches of Persia*, which shouldn't count as two independent books in
a control sample either. The sermons control lost 179 books this way.

The amendment also fixed something I'd flagged earlier. The spelling tool for pre-1700 books turns
the word "an" into "and", 3.3 million times. Now "an", "whether" and "fall" keep their printed form.

I filed it myself through OSF's API, with Dave's go-ahead, and this time the script that does it is
saved in the repo. The last three amendments each cost a round of rediscovering how OSF's
undocumented write path works.

## Log

- **2026-10-27, night.** Amendment 6 filed and approved (OSF revision 6ae16f41...): corpus choices registered, curated pseudo-biblical control (BOM-54), second dedup pass (BOM-55), an/whether/fall kept as printed. BOM-55 closed: metadata pass 4,697 groups; combined 19,692 groups, 24,779 non-keepers; controls count each work once (sermons -179, pseudo-biblical -55).
- **2026-10-27, later.** BOM-12 closed again, with HathiTrust: catalog 695,021 rows (533,328 with text), genre pass 1 for all, pass 2 redrawn (84.9% either-label agreement, HathiTrust 83.9%), 757 contradictions adjudicated by Opus (simulated; Sonnet 553, Llama 62). BOM-14 closed with it.
- **2026-10-27, afternoon.** BOM-15 done pending its dependencies: OCR sources artifact-only, 53,486 pre-1700 texts through MorphAdorner's own adorner (the table-only first pass superseded; its part -> partly and ye -> you errors kept on record); an -> and and similar MorphAdorner choices listed for amendment. Dedup re-run on normalised text: 19,916 groups; cross-source pairs 0.117 -> 0.180 median, none at 0.8. BOM-17 chunks and split built (split sha256 9fdffa56...). Control lists built and committed; control masking running (long volumes now aligned in overlapping 150,000-word pieces after passim ran out of memory).
- **2026-10-27, night.** BOM-14 closed: 472,018 volumes cleaned; error rate measured on 1,883 hand-keyed twins (median 0.099 raw, 0.083 cleaned); estimated for every volume and flagged, never deleted (Harvard 2.5%, HathiTrust 11.9%, Internet Archive 24.9%, Chronicling America 27.8% over 0.10). LLM correction tried and rejected (invents text). Wayne Sentinel re-segmented (62% -> 93% words recovered).
- **2026-10-27, later.** BOM-13 closed with BOM-12 (its only open dependency); candidate table unchanged since 65d4a9c. Pre-1830, only Spalding, Ethan Smith and Hunt clear the 10,000-word floor.
- **2026-10-27, later.** BOM-12 closed: catalog 559,986 rows (502,134 with text), genre pass 1 and pass 2, dedup (3,336 groups, same-source only; re-run moved to BOM-15), author word counts (64,710). Catalog manifest and SOURCES.md section added. Three empty validation excerpts (verse) fixed.
- **2026-10-27.** Genre validation deferred (BOM-53). Page pulled from the private repo,
  300 AI-drafted labels committed with a rule sheet (151 side with Llama, 87 with Sonnet,
  62 with neither). Perturbation will run at a worst-case 28%/3% bound first; the hand
  sample is drawn only if the genre-dependent conclusions move. Bound added to
  `pending_amendment`.
- **2026-10-26, evening.** BOM-13 signed periodical items: rules 11-17 written (17 dated as a
  clarification after extraction began), 77 signature lines, 43 items admitted. Phelps 0 →
  31,538, Rigdon 5,613 → 23,478, Cowdery printed 24,040 → 48,002 (post-1830, raw OCR).
- **2026-10-26, later.** BOM-52 closed: BOM-05 manuscript text rebuilt offline with the fixed
  reader. Effect is tiny (original 8 tokens, printer's 63, one paragraph mapping); my earlier
  "2,188 split words" was a whitespace count, mostly punctuation. Gap markers all kept (51).
- **2026-10-26.** BOM-13 word counts. Rules written first (docs/candidates.md, rules 1-10), then
  counted by JSP's own hand markup: Joseph Smith 0 words in his hand before 1830, 6,158 after;
  2,844 dictated before 1830. Fixed the JSP text reader (glossed words dropped, editorial notes
  counted); the same bug in the BOM-05 manuscript text is BOM-52.

- **2026-10-24, night.** Dedup running, and three days of labelling behind me. Writing it down
  while the machine chews through 185 GB.
  Pass 1 finished: 282,462 records in 82 hours on the local Llama, 100% of the catalogue
  covered. 7,040 came back as parse failures, which sounded alarming until I looked. 96% of them
  are records with no text on disk — the prompt hands the model an empty excerpt and it replies,
  reasonably, by asking for the missing text: *"To classify the work, I need to see the excerpt."*
  Only 267 failures are records that actually have text, which is 0.05% of the corpus that can be
  analysed at all. The no-text ones became `uncertain`, which is what Amendment 3 already says to
  do when the evidence doesn't support any category — a record with no text has no evidence. That
  needed no amendment, just reading the one we have.
  Then pass 2, and a bad afternoon. I ran 5,000 records through Sonnet at eight workers, and 3,027
  came back unparseable. I'd run out of subscription usage mid-run and every failed call got
  written down as `PARSE_FAIL`, as though the model had considered the question and had no answer.
  Re-running those same records the next day worked fine. So the data was durable and the
  *failure* wasn't: a resume looked at 3,027 outage casualties and saw finished work. There's now
  a separate `RETRY` state, and anything unparseable gets its raw text logged, because that run
  left me nothing at all to diagnose — I found the cause by re-running rows by hand and watching
  them succeed.
  The first agreement figure came out at 7.4% and I nearly reported it. Two models that both score
  97% against ground truth cannot disagree 93% of the time. Half of it was the outage. The other
  half was me measuring the wrong thing.
  Here's the part worth keeping. Sonnet kept giving one label where Llama gave two —
  `newspaper_periodical,legal_political` against just `legal_political`. I was scoring that as
  disagreement, which is daft: one model being more willing to add a second category isn't the
  other being wrong. And Amendment 3 had already settled how to score it, back in October:
  *"Analyses needing a single value use the primary; genre-matched control sets match on either."*
  Two registered ways the label gets used, so two agreements that matter. I didn't invent a
  kinder metric — I went back and read what we'd committed to.
  Real numbers, then: **75.0%** agreement on the primary label, **84.8%** where the label sets
  overlap at all, and **15.2%** outright contradiction where the two share no label and one of
  them is simply wrong. Chronicling America is 98.4% and 1.1%, which is the sanity check passing —
  both models know a newspaper when they see one. The damage concentrates: sermons 2.5%
  contradiction, scientific works 2.6%, but `other` at 37.4%. That category is behaving as a
  dustbin despite the prompt explicitly telling the model to prefer a specific label, and early
  modern English from the 1640s runs 22-25% against the 1820s' 7%. Worth knowing before anything
  gets built on these labels.
  Two mistakes today, both mine, both caught by Dave. I estimated the dedup run at 25-35 minutes
  and it's 2.6 hours — I'd benchmarked on ten documents picked at random, averaging 390 KB, when
  an Institutional Books volume is 1.4 MB and a newspaper page is 26 KB. Documents vary forty-fold
  in size; counting them tells you nothing. Measure the bytes.
  And the one I'm least pleased about. I declined to put the validation excerpts on a hosted page
  because thirty of the three hundred records are Harvard's, whose licence says no
  redistribution. Then I committed the same 131,000 characters to the public repo about two
  minutes later. Dave asked whether it was in git. It was. What's committed now is an index —
  which records, which categories, what each model said — and I checked that the excerpts
  regenerate byte-identically from the record ids alone, fifty out of fifty. So it's still fully
  replicable by anyone with their own copy of the texts, which is the only way they could
  lawfully have them anyway.

- **2026-10-20, night.** I told Dave the project wasn't replicable because the corpus can't be
  redistributed, and he told me I was wrong. He was right. The bar I was using — can anyone
  download the bytes — isn't the bar anyone else uses. Clinical trials, census microdata, UK
  Biobank, dbGaP: none of them ship their data, all of them count as replicable, because what
  gets published is the protocol, the code and the *access procedure*. Five of our eight sources
  need no permission at all. One needs a free Hugging Face account. Only HathiTrust takes an
  application, and `docs/hathitrust-request.md` already had the whole thing written down. So the
  README now says the corpus is obtainable rather than unavailable, `docs/replication.md`
  collects every access path in one place, and the audit finding is corrected in place rather
  than deleted, since the correction is the more useful record. Then Dave asked whether the
  download scripts were actually committed, and that turned up something worse: `ht_pull.py`,
  the script that fetched 31,194 HathiTrust volumes, was sitting in a handoff folder on this
  machine and nowhere else, while `SOURCES.md` cheerfully told a replicator to "run
  `ht_pull.py` from the handoff folder." A folder only I have. It's in the repo now, along with
  the rsync instructions and the actual email thread, because the shape of a successful
  application is the hardest part for someone to guess. And checking those files for anything
  that shouldn't be public turned up my own residential IP address and personal email, already
  pushed, in two documents — the allow-listed IP from the HathiTrust approval. Scrubbed from the
  working tree, then scrubbed from the history too: `git filter-repo` over 135 commits, verified
  that the rewritten tree was byte-identical to the old one apart from those two strings, and
  force-pushed. Worth knowing for anyone who does this: the force-push is not the end of it.
  GitHub keeps the old commits reachable by their SHA until it garbage-collects, and I confirmed
  the data was still readable at the old hash minutes after the push. Only GitHub Support can
  trigger that collection. A rewrite gets you out of `git clone`; it does not get you out of
  GitHub until you ask.
- **2026-10-20, night.** Dave asked the obvious follow-up to the power problem: Joseph Smith
  wrote a great deal *after* 1830, so why not use it? Because he spent fourteen years preaching
  and quoting the book. If his later writing resembles it, that's equally consistent with his
  having written it and with his having absorbed it — the causal arrow points both ways and the
  resemblance can't tell them apart. But the contamination only runs one direction, toward
  resemblance, and that's exploitable: if the most contaminated version of his corpus *still*
  doesn't match, that's stronger evidence than a clean small sample could give, while a match
  proves almost nothing. So it goes in the registration as a one-directional test — non-match
  counts, match doesn't — fixed in advance so I can't pick the direction after seeing which way
  it fell. Two other things fell out of working it through. Most of "all of Joseph Smith's
  text" isn't his language at all: the History of the Church was largely written by Willard
  Richards and W. W. Phelps, and the King Follett discourse survives as a composite of four
  listeners' notes. So everything gets tiered by provenance and only holograph and dictated
  material is scored. And the whole idea rests on an assumption I can actually test without
  touching the Book of Mormon — build a profile from Rigdon's or Pratt's later writing and see
  whether it identifies their earlier writing. If authorial signal survives that gap, using
  later text is defensible and I have the number. If it doesn't, I have a quantified reason not
  to. Dave was clear this is *in addition to* the registered analysis, never instead of it,
  which is the only version that's filable: Amendment 5 adds analyses and adds constraints on
  them, and changes no decision rule. Recorded honestly in the draft: this helps least where
  it's needed most. Smith is both the shortest of text and the most exposed, so his is the one
  expansion confined to the one-directional rule, while the cleanest expansions belong to
  published authors who probably already have enough words. It is not going to rescue the
  Joseph Smith question, and saying so now means nobody can later pretend it did.
- **2026-10-20, night.** Stopped and audited the whole plan against its own goal, now that
  Phase 1 is nearly done and nothing analytical is built yet (`docs/audit.md`). Five gaps, five
  new issues. The one that could change what this paper is about: there's no power analysis.
  Section 10 of the pre-registration already admits Joseph Smith's undisputed pre-1830 writing
  is under 10,000 words and he'll "likely fall under the sample floor for most methods" — which
  means the question everyone actually wants answered may not be answerable, and under the plan
  as written I'd find that out at BOM-21, after building the corpus, the models and the
  benchmark. It can be known in a fortnight instead, using Federalist papers and known
  pseudo-biblical authors, with no Book of Mormon text involved and no seal broken. If Smith
  can't be tested, that gets said up front and the paper is about the open-set result, the
  dating, and the candidates who can be — which is still worth doing, and reads very differently
  announced in advance than discovered late. Second gap: I've been calling this replicable and
  it isn't, quite. Harvard, HathiTrust and the Joseph Smith Papers all forbid redistribution, so
  nobody can rebuild the corpus from the repo. The fix is better than a disclaimer — publish the
  derived tables the analyses actually read (4-gram document frequencies, feature matrices, the
  genre catalog), which aren't reconstructable back into readable text and so aren't what the
  licences restrict. Also: the borrowing null is built from "at least 500" volumes, which puts
  about five observations in the tail of a 99th percentile, and I have half a million volumes sitting
  on a disk doing nothing. And I named what gets cut first if this stalls — the from-scratch
  300M model and its per-candidate fine-tunes, the only rented GPU in the budget — while that's
  still a judgment call rather than a retreat.
- **2026-10-21, end of the day.** Dave stopped me mid-tangent and asked whether I was still
  working on the thing I'd set out to do, which I wasn't. The question was simple: is the
  Chronicling America OCR good enough? Answering it needs page images. I'd gone off after the
  deleted ALTO instead, which was a real problem and worth fixing, but it was not the question.
  Worse, I'd half-answered from the ALTO — mean word confidence 0.493, half the words under a
  half — and written in the repo that the reference was "a low bar". So back to the actual test.
  The images turned out to be fetchable after all: the Library of Congress blocks its PDF and
  JP2 downloads behind Cloudflare, but its IIIF image service answers fine, and I'd got a 403
  earlier only because I guessed a URL instead of asking the API for the real one. I pulled a
  column crop of a page at full resolution and could read it as easily as a book.
  Then the test. Pick phrases off the scan before looking at the text, then search the OCR for
  them. Typical page: eight of ten exact, and the two misses were "fled" read as "lied" and
  "ancestors" read as "ancestor". Then the worst-scoring page in the entire five-thousand-page
  sample: fifteen of sixteen, the only miss being "95th" read as "95eh". Single characters. You
  could reconstruct every one of them from context without thinking about it.
  So Chronicling America is fine, and I have to withdraw the "low bar" line I wrote three hours
  earlier. The OCR engine's own confidence score says half its words are doubtful; the page
  images say the text comes back almost verbatim. The confidence number is useful for sorting
  pages but it is not a verdict, and I reported it as one.
  Two things actually matter from all this. Chronicling America needs no re-OCR — though for the
  4-gram borrowing work a single wrong character still destroys a 4-gram, so that stage loses
  real matches and I should measure how many rather than wave it away. And the Wayne Sentinel is
  in a different world: zero of ten on a page I can read with my own eyes. That one needs
  re-OCR from the images, which at 1,429 pages is a perfectly tractable job.
- **2026-10-21, later still.** Went to check whether Chronicling America's OCR is any good —
  it's the yardstick I'd measured everything else against, and after the Golden Bible business I
  no longer trusted that I'd ever verified it. The Library of Congress is behind Cloudflare now,
  same as NYSHN, so no page images. Then I remembered the bulk tarballs ship an `ocr.xml`
  beside every `ocr.txt`, and ALTO carries the OCR engine's own per-word confidence. Perfect:
  a quality measurement for all 158,960 pages with no images needed at all.
  Except we don't have it. My extractor matched only `ocr.txt`, counted every single `ocr.xml`
  as "skipped", and then deleted the tarball it had just read — by default, no flag required.
  One archive survives because a run got interrupted. There's no Time Machine destination, no
  snapshot, and 240 GB has been written over those blocks since the sixteenth. It's gone, and
  getting it back means Dave re-downloading seventy-six archives through Cloudflare by hand.
  What makes this worse than clumsy is that the rule was already written down. `CLAUDE.md` says
  keep originals and intermediate artifacts, flag rather than delete. Dave had said the same
  thing to me in plainer words a few days ago. I wrote the convention and then wrote the code
  that broke it, on a disk with 1.6 terabytes free. So the rule is now a test: anything in the
  pipeline that calls `unlink` or `rmtree` fails the build unless it's on an allowlist with a
  written reason. A comment in a docstring clearly wasn't enough to stop me.
  The one surviving batch did answer the question, though. Four hundred pages, a million and a
  half words: mean word confidence 0.493, and 53% of words below a half. The yardstick is bent.
  To be fair to it, that number is the vendor's own heuristic rather than a measured error rate,
  so it doesn't mean half the words are wrong — but it does mean "as good as the Library of
  Congress" is a much lower bar than it sounded when I wrote it this morning.
- **2026-10-21, later.** Dave pulled the 26 June 1829 page himself and it settles the thing I
  couldn't. Page 3, column 2: an editorial notice about "a pretended discovery, through
  superhuman means, of an ancient record" that is "generally known and spoken of as the *Golden
  Bible*", and then the entire Book of Mormon title page, ending "by JOSEPH SMITH, Junior,
  Author and Proprietor." Clear type. Perfectly legible. Grandin printed it nine months before
  he printed the book.
  But the real lesson is what the OCR did to it. I searched that exact page for ten things I can
  now see with my own eyes on the scan — Golden Bible, Book of Mormon, hand of Mormon, plates of
  Nephi, Lamanites, Moroni, abridgment, Joseph Smith, Author and Proprietor. Every single one
  returns zero. "Golden Bible" comes out of the text layer as `gattlmbible`. Not fragmented,
  not spaced oddly — just gone.
  Which means I have to withdraw something I wrote this morning. I'd reported that the Golden
  Bible terms found nothing across the whole 1823-1830 run and offered an explanation for it:
  that the famous Golden Bible coverage belongs to the Palmyra Freeman and the Rochester papers
  rather than the Sentinel. I hedged it — said treat it as "not found", not "not printed" — but
  I still gave the reasoning, and the reasoning was wrong. The Sentinel printed the phrase. The
  OCR lost it. Six hits is a floor, not a census, and I can't say anything about what this paper
  *didn't* carry without looking at the images.
  One smaller thing I also had backwards. I'd said the OCR interleaved the title page with an
  apothecary advertisement, as though the page itself were a mess. It isn't. The item sits in
  the news column; the cloves and pepper are in columns four through seven, inches away. The
  extraction did that, not the printer.
- **2026-10-21.** Picked up the two newspapers from the laptop and put them through OCR
  scoring, the access index, and the Phelps rule. Both verified clean against their manifests
  first, 1,429 and 168 files, no problems. Then three things went wrong in a row, and each one
  was worth more than the thing I was trying to do. First: my OCR score said the Wayne Sentinel
  was six times worse than Chronicling America, which would have down-weighted the single most
  important newspaper in the study — Grandin's own paper, the one that printed the title page
  and the sale notice. It isn't worse. Thirty per cent of its tokens are lone letters because
  NYSHN's text view delivers words as `t h e b o o k`, and I'd counted that as OCR error. On
  the signal that actually means garbling, vowelless tokens, it scores 0.009 against the
  reference's 0.008. The Sentinel's word recognition is as good as the Library of Congress's.
  Second: writing a test for that, I found the letter-and-digit check had never worked — the
  tokenizer took letters only, so "m0rm0n" was split into pieces before the test could see it.
  It had been scoring 0.000 on every source and I'd read that zero as a result rather than as a
  dead branch. Third, and this is the one that matters: the index couldn't confirm the 26 June
  1829 title page. I checked all four pages of that issue by hand. The only candidates are the
  word "mormon" sitting inside a garbled advertisement for tinctures and essences, and some
  genuine title-page language spliced together with a cloves-and-pepper ad because the OCR
  interleaved two columns. The text is almost certainly there and the microfilm has destroyed
  it. I've recorded it as unconfirmed rather than absent, because those are different, and
  neither gets counted until somebody looks at the scan. What the index did find is a week
  a week earlier than the sale notice we had on record — not earlier than the June 1829 title
  page, which we always knew about, and I've no idea whether it's new to the historians, who have
  gone over this printing in detail. It's 19 March 1830, the book "will be ready for sale", and
  then the title-page advertisement with its BY JOSEPH SMITH, JUNIOR byline running five
  straight weeks. Last job was the Phelps rule for the Lake Light, written before a word of it
  enters his sample. It came out stricter than expected. I'd gone in knowing there were two
  publishers on the masthead; what I hadn't known is that the paper changed hands. Phelps &
  Bloomer to 18 February 1828, then Clark & Bloomer, dissolved that May, with Phelps already
  off to the Ontario Phoenix. Fifteen of forty-two issues are even eligible, and inside those,
  unsigned matter is out because two men could have written it. I've written down in advance
  that this will probably admit nothing at all, so that a disappointing yield can't later
  become an argument for relaxing the rule.
- **2026-10-20, night.** Amendment 4 filed and approved (OSF revision
  `6ad844dc2aba3079ce0da955`). Dave asked a question I should have asked myself: is the second
  labelling pass actually buying a better result, now that works can carry two labels? It
  isn't. Amendment 3 made two changes at once, and the first undercut the second — allowing two
  labels removed most of the disagreement that double-labelling was there to find. Worse, I had
  registered a *census*: every one of 282,462 records labelled twice. Nobody reports annotator
  agreement on a census; you report it on a sample, because that's all the statistics needs. At
  5,000 records the confidence interval is under a point, and the saving is 29 hours of Sonnet
  down to half an hour. Checking what genre is actually *for* settled it: all three uses
  (imposter pools, rare-phrase normalization, the stratified null) are pool-level. Not one
  decision rule reads an individual record's label. So the apparatus was measuring a quantity no
  conclusion depends on. The amendment spends the saving on a test that was missing: corrupt the
  labels at the error rate validation measures, drawn from the confusion the model actually
  makes rather than uniformly, and re-run the genre-dependent analyses a hundred times. If the
  99th percentile of the null doesn't move, the labelling is good enough and we can prove it.
  One more thing had to be nailed down first: pass 2 can't be the same model. At temperature 0
  Llama reproduced 19 of its own 20 labels, so self-agreement would have measured floating-point
  arithmetic. And Dave's "am I correct?" was worth taking seriously rather than agreeing with —
  a census does catch one thing a sample can miss, a failure confined to a single source or
  decade, which isn't category-shaped. The fix was one clause: stratify by source and decade too,
  and publish the per-stratum table. Filed tonight rather than Saturday, deliberately, because
  nothing from pass 1 has been looked at yet and an amendment written after seeing the output
  would be worth much less.
- **2026-10-20, night.** Started the genre labeller on the local Llama and immediately found I
  was running it eight times slower than I thought. Ollama ships with `OLLAMA_NUM_PARALLEL=1`,
  so my eight worker threads were queuing for a single slot -- the log only ever said
  `launch_slot_: id 0`. Eight slots took it from 1.47 to 1.16 seconds a record, 4.8 days to 3.6.
  Less than I hoped, and the per-request timings say why: a request is about 520 tokens of
  prompt against 7 tokens of answer, and three quarters of the second is spent reading the
  prompt back. There's a real fix in there somewhere (the first 353 tokens are the same every
  time and do get cached) but not one worth another evening. A week of this machine's time is
  free; my time isn't. Also a scare on the way: a 64-record check came back 91% two-label and I
  thought the model had started treating the comma as the default. All 64 were consecutive
  volumes of *The New annual register, or, General repository of history, politics, and
  literature*, and "newspaper_periodical, history_chronicle" is just what that is. `--limit`
  takes the first N rows in catalog order, so a small sample lands inside one serial. Noted in
  the module so I don't scare myself with it twice.
- **2026-10-20, night.** BOM-41: *Wayne Sentinel* pulled from NYS Historic Newspapers through a hand-unlocked Brave window (`scripts/nyshn_browser_pull.py`): 376 issues, 1,429 pages, 1823-10-01 to 1830-12-31, a weekly run with four single-week gaps, 11.3 million words of microfilm OCR, nine pages without text on the site. Text and page index in `data/newspapers/wayne_sentinel/` (in git), manifest `data/manifests/wayne_sentinel_text.jsonl`; no PDFs (per-page Turnstile). First pass had only Oct-Dec of each year: the site zero-pads months, the script did not.
- **2026-10-20, evening.** BOM-41: *Ontario Phoenix* not digitized anywhere and, per the NYSL union list, surviving pre-1830 only as about twenty paper issues; recorded as unavailable. *Lake Light* digitized at the Ulysses Philomathic Library's archive and pulled: 168 pages, 42 issues, 1827-10-10 to 1828-11-19, 565,630 words of microfilm OCR (`ingest.advantage_archive`, `data/newspapers/lake_light/`). NYSHN title index read: Wayne Sentinel yes, Phoenix no, Lake Light no, plus dozens of 1800-1830 New York titles BOM-10 had counted as missing; that finding corrected in `docs/new-york-newspapers.md`. `scripts/nyshn_browser_pull.py` written for the browser-driven NYSHN pull.
- **2026-10-20, evening.** BOM-08 done: HathiTrust approved (GS-17502, dynamic IP
  allow-listed, access to 2026-11-30) and 31,194 volumes pulled in 24 minutes, 19 GiB. 21,810
  duplicate the Internet Archive pull and 9,384 are new, but the duplicates give 21,810
  two-OCR pairs of the same book, which is a free test set for BOM-14. Emailed Google's library
  partner team about the 75,984 Google-digitized volumes; not waiting on a reply. Phase 1
  corpus now 242 GiB across six sources.
- **2026-10-20, later still.** BOM-42 filed: a register of twelve public claims from every
  side, each with its decision rule written before any result exists, frozen with a hash before
  the blind run. BOM-08 approved (ticket GS-17502, dynamic IP allow-listed, access to
  2026-11-30) and the rsync pull started. Credentials consolidated to one standard,
  ~/.config/<service>/token, after a repo .env held one; Codex authenticates by ChatGPT OAuth
  and is the adversarial labeller. Recorded that local and remote concurrency are different
  problems: 1 to 16 workers is near-linear against an API and flat against a local GPU.
- **2026-10-20, later.** Genre labeller benchmarked properly: 300 records instead of 60, with
  the rule-decided half used as ground truth. Sonnet 98%, Llama 3.1 8B 97% -- indistinguishable,
  and the earlier 87/83 split on 60 records was inside the noise. Inter-model agreement on hard
  records only 72%, and reading those disagreements showed a third are taxonomy holes rather
  than model errors (Philosophical Transactions is both a periodical and scientific; the label
  set forces a choice it never defined). Adding a precedence rule to the registered method and
  over-sampling ambiguous categories in validation. Llama runs the corpus free; Sonnet is kept
  for second opinions.
- **2026-10-20.** BOM-09 done: 249,906 of 251,204 Internet Archive items (99.48%), 99 GB, four
  days, 26 supervisor cycles, zero 429s. Three fetcher bugs fixed along the way, the largest
  being a filename assumption that was discarding ~8,500 books whose OCR was filed under an
  internal barcode rather than the item id. 4,822 misses documented by code in failed.txt.
  Phase 1 corpus now 221 GB across five sources.
- **2026-10-17, later.** Amendment 2 registered on OSF (revision 6ad3f82fc8f5176e336b2561,
  approved same day): about 28 operational analytic values pinned, three of them as selection
  procedures rather than numbers. The one that mattered was ENSC shrinkage, defaulting to 0.0 in
  our code, which means nearest *shrunken* centroids had been running as plain nearest centroids
  while BOM-22 replicates a study defined by that shrinkage. Filed through the OSF API; the write
  path is undocumented, so the payload shape came from reading OSF's own source. Base model fixed
  at 300M with the 125M pilot now a registered decision point, so the size is reported as a
  measurement rather than a preference.
- **2026-10-17.** BOM-11 done: 61,310 of 61,315 TCP texts, 22 GiB (EEBO 53,830, Evans 5,012,
  ECCO 2,473), two versions kept again. BOM-10 done: 158,960 of 159,146 newspaper pages
  (99.88%), 4.4 GiB; the 258 failures are absent from the batch archives and from the live
  service. BOM-09 recovered from 1 item/min to 46 after fixing three faults in our own
  fetcher — a single broken file tripping a global stop, 75s wasted per unservable item, and a
  work list ordered so one bad collection stalled every worker.
- **2026-10-16, later still.** BOM-10 switched from the per-page API to the Library of
  Congress's bulk batch archives: all 159,146 pages live in 76 batches, 68.8 GB, downloaded by
  hand in about an hour because Cloudflare blocks scripted access. 219 days of fetching avoided.
  Validated before trusting it: of 2,490 pages held both ways, every one matches word for word,
  the only difference being blank lines the API route introduces when joining JSON segments.
  BOM-09 parallelised to 4 workers per the Archive's published guidance (7/min to 53/min, 25
  days to ~4), stopping hard on 429/503. Got myself rate-limited by the Library of Congress
  first, by sizing 76 files eight at a time; recorded so it is not repeated.
- **2026-10-16, later.** BOM-09, BOM-10 and BOM-11 pulls all started and running together on
  the mini: Internet Archive (251,204 items, measured 16.2/min, about 11 days), Chronicling
  America (159,146 pages), TCP (61,315 texts). Separate hosts, separate rate limits, no reason
  to queue them. Decided against narrowing the Archive list to `americana` to save a week: a
  complete corpus needs no excuse in the paper. BOM-08's researcher agreement signed and
  awaiting a decision (ticket GS-17502); its Archive-digitized volumes are covered by BOM-09
  meanwhile.
- **2026-10-16.** BOM-07 done: 31,958 Harvard volumes, 9,831 shards, 73 GiB, 11h38m, no
  failures, two manifests committed. Storage estimate was half the truth because the dataset
  ships two OCR versions and the pull keeps both; budget corrected. Found a 57 GiB Spotlight
  index on the corpus drive and documented turning indexing off. T7 reads at about 470 MB/s.
  BOM-40 filed and its Phase 2 config slice built ahead of it (#50).
- **2026-10-16.** BOM-08 paperwork: HathiTrust opened ticket GS-17502 and sent the non-Google researcher agreement; signed as an independent researcher and returned. Form transcribed and glossed in `docs/hathitrust-researcher-agreement.md`. Approval, static IP, and rsync pending.
- **2026-10-15, later still.** Hardware decision revised (BOM-04): no $3,199 Mac: use the M4
  mini already on hand (10-core, 16 GB, 256 GB), buy a 2 TB external SSD, rent an H100 for the
  base model and for anything that won't fit in 16 GB. Budget drops from about $3,700-4,300 to
  about $650-1,300. 59 GB reclaimed on the mini (an orphaned Colima datadisk `colima delete`
  left behind, plus ollama). BOM-07 pull started against the internal disk.
- **2026-10-15, night.** BOM-10 three-state newspaper pull done on the laptop: 3,466 of 3,472 pages (6 broken at the source), 7 titles, about 14 million words; manifest `data/manifests/chronicling_america_nypaoh.jsonl`. New York contributes two city papers and nothing from the Palmyra area.
- **2026-10-15, later.** BOM-10 catalog built (159,146 newspaper pages; New York has 47). BOM-09 catalog built (307,567 Internet Archive items). BOM-13 sources inventoried (38; four candidates have no pre-1830 text). BOM-20 library built ahead of the corpus (37 tests). BOM-08 measured: HathiTrust holds 107,178 period volumes Harvard lacks. BOM-07 and BOM-11 catalogs built (31,958 Harvard volumes, 61,315 TCP texts) and the pull scripts written; the downloads themselves wait for the Mac mini.
- **2026-10-15.** BOM-01 to BOM-06 closed. Repo reset, plan registered on OSF (amendment 1
  the same day: one person plus AI, every human-review step replaced with a labeled
  simulation), budget set (Mac mini plus a rented H100), three Book of Mormon witnesses
  pulled and aligned, KJV with Apocrypha verse-indexed. Private data repo created for the
  copyrighted transcripts.
