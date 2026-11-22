# Redesign: where the three worlds disagree (BOM-109)

2026-11-22. Research and design only, asked for by the owner. Nothing here was run on the Book of
Mormon, and no AI judge was called. Counts marked "feasibility" were taken on the real files in a
few minutes, on comparison texts only. Web sources were read by an AI research agent and not
checked by a person; "to verify" marks what was not reached or not confirmed.

This redesign is meant to serve the whole family of setting tests, not only BOM-109: BOM-111
(inventory of things), BOM-112 (the Dales' checklist), BOM-113 (Roper's anachronisms), BOM-114
(numbers) and BOM-115 (warfare). They share one weakness, set out below.

## The claim and where it comes from

BOM-109 is our own synthesis, not a published paper. It asks: on the points where the Bible's
ancient Near East, ancient Mesoamerica, and the 1820s American picture of ancient America differ,
which does a text side with? The published versions of the same idea each look at one world, or
two, and argue by item lists:

- **Dale and Dale 2019**, "Joseph Smith: The World's Greatest Guesser", *Interpreter* 32:77-186.
  131 positive and 18 negative correspondences between the book and Michael Coe's *The Maya*
  (9th edition). Each item gets a likelihood ratio (0.5, 0.1 or 0.02 for positives, by how
  specific and how unknown in 1830 they judged it; 50 for each negative). Multiplied as
  independent, with a prior of 1 in a billion against, they get about 1 in 10^111 that the book is
  fiction. Controls: Spalding (19 positive, 21 negative) and *View of the Hebrews* (15, 9), coded
  by the same authors. A sequel (Scripture Central, 2021) extends it to Coe's later edition.
- **Roper 2025**, *Anachronisms: Accidental Evidence*, *Interpreter* 65. 226 items once called
  anachronisms. His tally: of those raised by 1844, 7 confirmed; by 1965, 36; by 2024, 174
  confirmed, 31 partial, 21 not. Claim: the list of problems shrinks as archaeology advances.
- **Sorenson**, *An Ancient American Setting* (1985) and *Mormon's Codex* (2013): "some 420"
  correspondences with Mesoamerica, by topic (geography, writing, warfare, religion ...). No
  statistic; argued by reading.
- **Rasmussen**, "Estimating the Evidence" series (Interpreter Foundation, 2021-2023). One
  episode (14, to verify) redoes the Dales' sum with more conservative ratios and weighs the
  critics' anachronisms, arriving near 10^-28.
- **The critics.** Coe himself (1973, "Mormons and Archaeology: An Outside View", *Dialogue*
  8/2; 2011 interviews on Mormon Stories): no horses, chariots, wheat, barley, cattle or the
  metallurgy described, no trace of the book's peoples. Vogel 1986 (*Indian Origins and the Book
  of Mormon*): about 27 motifs (earth-and-picket forts, mounds, a civilised race destroyed by a
  savage one, Hebrew customs among the Indians, an Egyptian-like script) already in print before
  1830. The Wheat and Tares reply to the Dales (2019): arbitrary ratios, 131 positives against 18
  capped negatives, items not independent, generic details credited, and a ten-detail invented
  story scoring about one in 625 billion by the same rules. No journal-published statistical
  critique of the Dales was found.

What the world would look like, if each side were right: if the book was written from inside an
ancient Mesoamerican world (in translation), the things, practices and institutions it gives its
own people should match that world where it differs from the others, including in points not
in print in English by 1829. If it was written from the 1820s picture, it should carry that
picture's distinctive beliefs (beliefs neither real world supports) and only what the 1820s
could have read. If it follows the Bible, it should carry the Bible's world, and its New World
content should be thin. A mixture is possible too, and is itself a finding.

## What we did and how it failed

The first design (card `2026-11-21-three-worlds`, `lab.threeworlds`) built 56 countable features
from marker words. A text stated a feature *present* with 3 or more hits (and 0.1 per 10,000
words), *absent* with none in at least 10,000 words. Each world's value was the majority of its
source texts. 31 features stayed after dropping those the worlds agreed on (9) or that were
unsettled (16).

Known answers: 7 of 8 sided with their own world (bar: 8 of 8). 1-2 Kings agreed with the Near
East on 29 of 30; the Annals of the Cakchiquels with Mesoamerica on 23 of 27. **Bernal Díaz**, an
eyewitness of the conquest of Mexico, sided with the 1820s (24, against 15 for Mesoamerica). He
agreed with the 1820s alone on firearms, coins, printing (the Spaniards' things) and on copper,
canoes and cotton (Mesoamerican things the short native poems and myths never mention, so
Mesoamerica had been measured as *absent*). Solis, a conquest history from books, landed the same
way. Reading absence only from texts over 50,000 words gave 8 of 8, by one agreement; that was
chosen after the result and not adopted. The Book of Mormon was not scored.

The sister tests failed in the same place:

- **BOM-111.** A Mesoamerican profile built from native texts took in 0 of 3 chronicles (all went
  to the background); built from chronicles it took in 5 of 5 native texts. Native things
  (feathers, flowers, maize, flutes) are not the chronicles' things (horses, ships, swords, gold).
- **BOM-114.** The whole-number profile missed (0.71 against 0.75; Mesoamerican texts 3 of 7);
  *The Late War* went with the Near East: the profile read Bible style.
- **BOM-115** passed, but native annals formed no tradition and the mound-builder group was weak
  and mixed with Indian-war narrative.
- **BOM-112** and **BOM-113** reproduced the published tallies (below), and their judging halves
  wait.

## Replicating their approach

The owner asks that each test first reproduce the original authors' result their way, then apply
ours. For this family:

| Work | What exactly they did | Reproducible with what we hold? | Done? |
| --- | --- | --- | --- |
| Dale and Dale 2019 | Read the book against Coe's *The Maya*; list 131 + 18 items; assign each a ratio; multiply; same for two controls | The arithmetic, yes (paper held, open access). Their reading of Coe, only as they quote him: *The Maya* is not held | **Yes, the headline** (BOM-112): from their tallies 1.02 x 10^-111 (they print 1.03, a rounding chain). Two slips found (a military subtotal; the 12 podcast negatives print as 3.13e15, their ratios give 4.0e10). Sensitivity table: capping ratios moves the answer from 10^-111 to about even odds; even odds at about 10 effectively independent items. **Not yet**: their item codings checked against the book by a second reader (149 judge questions prepared), their two control codings redone, Coe's text itself |
| Rasmussen (Estimating the Evidence) | Same multiplication with his own, more conservative ratios | If his per-item table is printed (to verify) | No |
| Roper 2025 | One coder; each claimed anachronism marked confirmed / partial / not, from the literature, at three dates | His list and tallies, yes (open access) | **Partly** (BOM-113): 227 headings keyed (his 226); 175/31/21 against his 174/31/21; his 1844 and 1965 figures to within 1 and 4 items. **Not**: his verdict on each item checked by another reader (12 known-answer and 436 item questions prepared); the same tally for a control book |
| Sorenson 1985, 2013 | Reading; about 420 correspondences listed by topic | No: *Mormon's Codex* is not held (in copyright; worth buying, below) | No |
| Coe 1973, 2011 | A short list of missing things (horse, chariot, wheat, barley, cattle, metallurgy) | Yes: the words are countable, and BOM-111/113 already counted them | Counted, not reported as a replication; to do as step 1 |
| Vogel 1986 | About 27 motifs, each with pre-1830 printed sources he names | Yes, mostly: many of his sources are in our library (Atwater 1820, Boudinot 1816, Ethan Smith, Adair, Haywood, McCulloh, Clinton, Harris 1805) | No. The faithful replication: for each motif, find his named source in our library, confirm the motif is there, record the print date |

The replication for BOM-109 therefore has three parts, done their way before ours: finish the
Dales' and Roper's own codings on the book and on their own controls with the prepared judge
questions (that *is* their method, with a second reader); check Vogel's 27 motifs in his named
sources; and report Coe's short list as counts. None of these needs anything new except
Sorenson's book.

What the replications cannot give: a fair comparison across worlds. Each looks at one world. The
Dales' controls are scored only on Mesoamerican items; Vogel's motifs are scored only on 1820s
sources; Roper has no control text at all. That gap is what BOM-109 was for.

## What the failure says

**(a) About the published claims and methods.** The failure exposes something every item list in
this debate shares: an item is credited when the *word or idea is present*, without asking *whose*
it is. Díaz's book is full of horses, guns and coins, but they belong to the Spaniards, not to the
Aztecs he describes. A checklist that ticks "has horses" or "has metal coins" would, like ours,
send the best eyewitness account of Mesoamerica to the wrong world. The same blindness runs the
other way: the Dales credit a correspondence when the book mentions something Coe also mentions,
without asking whether the 1820s books say it too, or whether it is said of the book's own people
or of someone else (a simile, a prophecy, a Bible quotation). This does not show their
correspondences are wrong. It shows the method cannot tell "a text written from inside this
culture" from "a text that mentions this culture's things". Roper's "confirmed" (attested
anywhere in the ancient record) has the same gap: it does not ask whether an item attested in the
Old World but used of New World people is a match or a mismatch. And the 1820s side in Vogel and
the critics is built from motifs, not measured against what was *also* true or *also* in the
Bible; the 1820s picture borrowed from both (Lost Tribes from the Bible, Mexican antiquities from
Clavigero and Humboldt), so many "1820s" motifs are not distinctive at all.

**(b) About our instrument only.** Most of the failure is ours:

- *Wrong unit.* We counted words, not attributed mentions. The feasibility check below shows that a
  word-window rule cannot fix this.
- *Unequal reference sets.* Mesoamerica was measured from short native texts of myth and poetry
  (10,000 to 110,000 words) whose genre does not mention canoes or copper; absence there is
  silence, not a fact. Its reference set mixed native and outsider texts without saying so.
- *The 1820s world was not a picture of ancient America.* It mixed antiquities books with
  writing about contemporary Indians (Seaver's Mary Jemison, Cusick), and the books' own modern
  things (settlers' guns, coins, printing) counted as features of "ancient America".
- *No fourth place to go.* A text whose things are modern European or American (Díaz's Spaniards,
  *The Late War*) had nowhere to land but the 1820s world.
- *Absence from words.* "Absent" meant "the word does not occur", which depends on length and
  genre more than on the world.

**(c) Unknown.** Whether, with attribution, any text-only instrument can tell an imitation of a
native record (written from the period's picture) from a genuine native record in translation,
when both are about the same world. We have imitations of the 1820s kind (Spalding claims to be a
translated ancient American record; *Behemoth*), and of other worlds (Ossian, *The Chronicles of
Eri*, Psalmanazar's *Formosa*), so this can be tested, but nobody has. Also unknown: how much of
the Mesoamerican world can be read from texts at all, given that the native record in English is
small.

## Angles considered

1. **Tune the old instrument** (absence only from long texts; drop native poems). Rejected: the
   sensitivity run showed pass or fail flips with one setting, and choosing the setting that
   passes is choosing by the result. It also leaves the real fault (whose things?) untouched.
2. **Attribute each mention to the people it is said of, and split each world's reference set by
   who wrote it** (native, outsider eyewitness, outsider from books, imitation). Chosen. It
   answers the miss directly: Díaz's guns go to the Spaniards, his canoes and cotton armour to
   the Aztecs. It is how historians already read such texts (the emic and etic distinction;
   Snodgrass 1974 read Homer's society item by item, asking which period each belongs to, and
   found a composite of several periods rather than one historical society).
3. **"Could the 1820s have known it?"**: for each feature on which a text matches a real world,
   was that fact in print in English before 1830? This is the method of Hans Ulrich Vogel's
   *Marco Polo Was in China* (Brill, 2012/13): compare each detail of currencies, salt and
   revenue against Chinese sources and against what any other Western, Arab or Persian writer of
   the time reported, and give weight to details no outside source carried. Our dated library of
   about 250,000 works is the right tool for the "in print before 1830" half. Chosen as the
   second part.
4. **Whole-text similarity** (meaning index, style encoders, cosine of thing-vocabulary). Rejected
   as the main design: BOM-111 shows it reads register and Bible diction (*The Late War* and the
   number profile), and it cannot attribute.
5. **Third-party coding of the worlds** instead of our own lists: Kirchhoff's 1943 culture-area
   traits for Mesoamerica; D-PLACE's Standard Cross-Cultural Sample codes for the Aztec (SCCS153,
   focal year 1520) and the Hebrews (SCCS44, focal year -800), coded by anthropologists for other
   purposes (CC BY). Adopted as a source of features and as an independent check on our world
   values, not as a test on its own.
6. **Repair the Bayesian checklist** (BOM-112's sensitivity work). Kept in BOM-112; it is the
   replication, not the redesign.

## The proposed design

**Question (one sentence).** Of the things, practices and institutions a text gives to *the people
it is about*, which world's profile does it match where the Near East, Mesoamerica and the 1820s
picture of ancient America disagree; and, for its matches with a real world, could an English
reader of 1829 have found them in print?

### Step 1: reproduce their result their way

Before our own instrument, and reported in full whatever it later shows:

1. **Dales:** run the prepared 149 questions (their items on the book) and their control items on
   Spalding and *View of the Hebrews*, by their rules, as a second reader; report how many of their
   codings a second reader reproduces, and their product recomputed from the second reading.
   Already done: their headline arithmetic (BOM-112).
2. **Roper:** run the prepared 12 + 227 questions; report agreement with his verdicts; the same
   tally for Spalding as a control (prepared).
3. **Vogel:** for each of his 27 motifs, locate his named pre-1830 source in our library and
   record whether the motif is there and the date (minutes per motif by search, then a judge
   question per hit, at most 20 a motif).
4. **Coe:** report his 1973 list as counts in the book and in the controls (already counted in
   BOM-111/113).

Known answer for step 1: the published figures themselves (reproduced, or the difference
explained), as in BOM-112.

### Part A: attributed three-world profile

1. **The unit is an attributed mention.** Candidate passages are found by marker words (as now,
   from a sourced lexicon). For each, the judge (`lab.judge`, simulated judging by an AI model)
   answers fixed questions: *whose is it?* (the people the text is about; outsiders in the story,
   such as the Spaniards; the author's or translator's own world, as in a comparison or a gloss
   like "which they call"; figurative; prophecy or the future; not said); *what is said?* (they
   have or use it; they lack it; it was brought from outside); and *where is the scene set?* (the
   main setting; elsewhere, such as Jerusalem in 1 Nephi or the tower in Ether). Only mentions
   given to the subject people, in the main setting, count toward a feature.
2. **A feature is stated present** when at least `k` attributed mentions say the people have it;
   **stated absent** only when the text says they lack it, or when the text is long, discusses the
   topic (another item of the same topic is attributed at least `m` times) and never gives this
   item. Silence in a short text of myth is no longer "absent".
3. **Features from outside sources first.** Each feature records where it came from: Kirchhoff
   1943 (Mesoamerica; trait list to verify against the essay); D-PLACE codes for the Aztec and the
   Hebrews; Coe 1973; the Dales' 149; Roper's 226; Vogel's 27; the first design's 68 only where
   none of these covers the topic. Features are of three kinds, decided before scoring: Near
   East only, Mesoamerica only, and **1820s-picture only** (beliefs neither real world supports,
   such as a white civilised race destroyed by savages, iron and steel tools in the mounds,
   mammoths as beasts of burden, Hebrew rites among the ancient Americans). The third kind is
   what makes the 1820s picture a world of its own rather than a blend of the other two.
4. **Reference sets in a grid** (standpoint by world), each value measured on attributed
   mentions:

   | | Near East | Mesoamerica | 1820s picture of ancient America | Contemporary (European or American things) |
   | --- | --- | --- | --- | --- |
   | Native, in translation | King James Bible units, Apocrypha, Josephus | Christenson's Popol Vuh, Brinton's Maya Chronicles, Nahuatl poetry, Rig Veda Americanus; Roys's Chumayel (1933, to verify public domain) | (none exists: a picture has no natives) | - |
   | Outsider, eyewitness | (travellers saw a later Near East: reported only) | Díaz (held out), Gage 1648, Solis | (none) | - |
   | Outsider, from books | Calmet, Harmer, Burder (biblical customs) | Clavigero vol. 1, Robertson, Humboldt 1814, Spinden 1917 (archaeological summary, public domain) | the rule-drawn 1820s set (below) | a sample of 1800-1829 American travel and history |
   | Imitation (claims to be native) | - | - | Spalding (held out), *Behemoth* (1839, held out) | - |

   The fourth column catches modern things so that Díaz's guns and *The Late War*'s muskets have
   somewhere to go. A world's value is measured separately in each standpoint row; the profile used
   for scoring pools the rows, and every result is also given per row.
5. **A fair 1820s reference set.** Drawn by rule, not picked: works in the library dated
   1775-1829, printed in America or reprinted there, whose subject is the *ancient* inhabitants of
   the Americas. Candidates by title and genre filter (feasibility: 101 title matches, about 9
   million words, before collapsing copies), then one judge question per candidate on its title
   page and first pages ("is the subject the ancient inhabitants of America?"), copies collapsed
   by author and title. Four strata, reported separately and pooled with equal weight: learned
   antiquities (Atwater 1820, Clinton 1811 and 1818, Harris 1805, Madison 1809, Brackenridge
   1818, McCulloh 1817 and 1829, Haywood 1823, del Río 1822 in English); Indian origins and the
   Lost Tribes (Adair 1775, Ingram 1792, Boudinot 1816, Ethan Smith 1823); fiction and verse
   (Hale 1823, Sigourney 1822); and newspapers (Chronicling America pages 1815-1829 with mound or
   antiquities terms, sampled). Writing about *contemporary* Indians (Seaver, Heckewelder,
   captivity narratives) is a separate stratum, reported but not pooled: the first design mixed
   it in. A sensitivity run restricts the set to titles in the Manchester (New York) library
   catalogue as published by Paul 1982, as a stand-in for "what was at hand".
6. **Scoring as before, on attributed features.** Keep only features on which the world values
   disagree; a text agrees with a world where its stated value equals the world's; it sides with
   the world with most agreements, with a bootstrap over features. Also reported: sole agreements
   by kind (Near East only, Mesoamerica only, 1820s only), so a composite text, one with many sole
   agreements in two worlds, is seen as such and not forced to one side.
7. **Standpoint signature** (description, no verdict): share of mentions given to outsiders, the
   author's own world, glosses and comparisons, and things "brought from outside". Native texts
   should be low on all four, outsider texts high. This tells whose eyes a text is written
   through; it cannot tell a genuine native record from a good imitation (see Risks).

### Part B: could 1829 have known it?

For every feature on which a text agrees with Mesoamerica alone: the earliest English print date
in the library of a passage stating it of the ancient Americans (search by markers, then a judge
question per hit, at most 20 hits a feature, earliest first). Each Mesoamerican match is then
"in print before 1830" or "not found before 1830". The same for the 1820s-picture features in
reverse (first print date; anything first printed after 1830 is flagged). This is the column the
Dales coded from their own judgement ("known in 1830?") and Roper from his headings; here it is
measured and dated. A "not found" is only as good as the library: it says "not found in about
250,000 works", never "unknown in 1829".

## Known-answer check

Bars fixed here, before anything is computed for any text.

**The judge first.** 150 made-up passages written for the purpose (as BOM-122 did), with known
answers for whose / what / where, including traps (a simile: "fierce as a Spanish horse"; a gloss:
"a bread which they call tortilla"; a prophecy of ships coming; a Bible quotation inside a
narrative). Bar: at least 0.85 agreement on *whose*, 0.85 on *what*. Then 100 real mentions from
the known texts hand-coded by the owner or a second AI reading (labelled), bar 0.8. If the judge
misses, stop.

**Known texts** (none in any reference set; each scored with the same features and world values):

| Text | Expected | Why it is certain |
| --- | --- | --- |
| 1-2 Kings | Near East | native, the world itself |
| Josephus, *Wars* | Near East | native, translated (the translation control) |
| Annals of the Cakchiquels | Mesoamerica | native, translated |
| **Bernal Díaz (Keatinge 1800)** | **Mesoamerica** | eyewitness of the Aztec world; **the hard decoy the first design got wrong** |
| Gage, *The English-American* (1648) | Mesoamerica | a second outsider eyewitness (colonial Guatemala; later and mixed, so its bar is lower: beats the 1820s) |
| Spalding, *Manuscript Story* | 1820s picture | an imitation of an ancient American record |
| *View of the Hebrews* (1825) | 1820s picture | the Lost Tribes picture |
| *Behemoth* (1839) | 1820s picture | mound-builder fiction |

**Bar:** every text except Gage sides with its own world on attributed features, leading the next
world by at least `margin` agreements and in at least 0.9 of bootstrap resamples; Gage beats the
1820s picture. **Díaz must pass**: if he does not, the attribution step has not done its job and
the run stops, whatever the others do.

**Controls and decoys, reported with expectations, no bar on the book:**

- *Bible-style books* (*The Late War*, *The First Book of Napoleon*, Snowden's *American
  Revolution*, *Chronicles of Eri*): must not side with the Near East once figurative and
  quotation mentions are removed; expected: the contemporary column. If they side with the Near
  East, Bible diction still carries a text there, and that is printed beside the book.
- *Genuine translations*: the standpoint signature of the King James units, Josephus and the
  Popol Vuh shows what a translator's glosses add; the book's signature is read against them.
- *Joseph Smith's other dictations*: the Book of Abraham and the Book of Moses (private copies),
  each scored on its own setting (expected: Near East), to show how the same dictator's texts
  give things to an Old World people.
- *Imitations of other worlds*: Psalmanazar's *Formosa* (1704) and Ossian. Their standpoint
  signatures are reported to show whether imitations look native on that measure (expected: yes,
  which is why the signature is description only).
- *Place, not period*: Maundrell (1697, Ottoman Levant) is reported only: same place, a later
  world, it should not side cleanly with the ancient Near East.

**Book of Mormon**, only if the check passes: whole text, without the Bible-quoting chapters,
and Old World scenes separately.

## What each outcome would mean

- **Sides with one world** (clear lead, 0.9 of resamples, same with and without the quoted
  chapters): the things the book gives its own peoples match that world's where the worlds
  differ. Read with Part B: Mesoamerican matches that were in print before 1830 count for less
  than ones not found.
- **Sides with the 1820s picture**, with sole agreements on 1820s-only features: the book
  carries beliefs of the period that neither real world supports.
- **Sides with Mesoamerica on matches not found in print before 1830**: reported as such; that
  is what the Dales claimed, now with controls and a measured date column.
- **Composite** (many sole agreements in two worlds): the book's world is a blend; which blend
  (Near East plus 1820s, Near East plus Mesoamerica) is the finding. The 1820s picture was itself
  a blend of the Bible and Mexican antiquities, so a Near East plus Mesoamerica blend must be
  compared with the 1820s set's own blend before anything is said.
- **Sides with the Near East only**: the book gives its peoples the Bible's world; New World
  content is thin. BOM-111 already points this way on raw vocabulary; attribution may strengthen
  or weaken it.
- **Cannot tell**: the check missed, or the leader changes with and without the quoted chapters,
  or resamples are split.

## Risks

- **The judge knows the book.** An AI judge reads passages, and may recognise the Book of Mormon
  and its debates. Mitigation: the judge sees passages without titles, known texts first, and the
  questions are about grammar of attribution (who has the thing), not about worlds. Still a risk;
  stated with every result. Simulated judging is labelled as such.
- **The worlds are uneven.** The native Mesoamerican record in English is small and mostly myth,
  poetry and annals; the Near East is the whole Bible. Part A's "stated absent" rule protects
  against reading silence as absence, but a world with few statements will have many unsettled
  features.
- **Imitation versus genuine native.** The standpoint signature cannot separate them, and Part A
  only separates them if the imitation draws on a different world (the 1820s picture). A careful
  imitation of the Bible world would side with the Near East. This is a limit of the design, said
  in advance.
- **The 1820s picture is partly the other two.** Its books borrowed from the Bible and from
  Clavigero and Humboldt. The 1820s-only features carry the weight; if there are few, the 1820s
  world will be hard to tell from a blend.
- **Feature lists from interested parties.** The Dales, Roper, Sorenson, Coe and Vogel each chose
  items for an argument. Using all of them, with provenance, and Kirchhoff and D-PLACE, which were
  made for other purposes, spreads that risk; it does not remove it.
- **Library gaps.** Part B's "not found before 1830" depends on what the library holds; English
  only, and newspapers thin before 1820.
- **Translations of native texts were made by outsiders** (Brinton, Christenson, Roys) who add
  glosses; the standpoint signature measures that and the "author's own world" answer catches it.

## Feasibility (measured 2026-11-22, minutes of Mac time, comparison texts only)

- **A word-window rule cannot attribute.** In Díaz (Keatinge 1800, about 242,000 words), firearm
  words occur 87 times; with a rule that looks 12 words each side for "we, our, Spaniards, Cortés,
  soldiers" against "Indians, Mexicans, Montezuma, natives, caciques", 53 lean to the Spaniards, 4
  to the natives and 30 tie. Canoes: 76, of which 42 lean to the Spaniards (they travel in and meet
  canoes), 7 to the natives, 27 tie. In Solis, 93 of 118 firearm mentions tie. Nearness is not
  ownership: a reader is needed, so the judge is.
- **Old printings need the long-s repair.** "horse" counted 0 in both conquest texts without it
  ("horfe"); `lab.inventory`'s repair handles this and must be applied before candidate search.
- **Texts held and long enough** (library words): Gage 1648, 197,000; Psalmanazar 1704, 74,000;
  Maundrell (1823 printing), 49,000; Burder's *Oriental Customs* 1807, 120,000; Shaw's *Travels*
  1808, 121,000; McCulloh 1829, 242,000; Harris 1805, 62,000; del Río 1822, 39,000; Garcilaso's
  *Royal Commentaries* 1688, 704,000 (a native-authored Andean text: a portability check, not a
  Mesoamerican reference).
- **1820s candidates**: 101 title matches among 195,575 works dated 1775-1829, about 9 million
  words before copies are collapsed (Boudinot alone appears six times).
- **Judge load** (estimate): about 50 features, about 40 texts, at most 15 sampled mentions a
  feature a text, most features far fewer: roughly 12,000-16,000 questions for the references and
  known texts, about 750 for the book, 800 for Part B, 600 for Vogel, 300 for the judge's own
  check. At 300 an hour, about 50-60 hours of free judging, run in order (judge check, known
  texts, references, then the book).

## What to fetch or buy

- **Fetch (public domain or open):** Spinden, *Ancient Civilizations of Mexico and Central
  America* (1917), Project Gutenberg 54550; Roys, *Chilam Balam of Chumayel* (1933), sacred-texts,
  only after its public-domain status is verified (the site says the copyright was not renewed);
  D-PLACE data for SCCS44 and SCCS153 (CC BY); Kirchhoff's 1943 essay (Spanish reprint, to locate)
  for the trait list only; Paul 1982 (BYU Studies, open) for the Manchester catalogue.
- **Worth buying** (the owner decides): Coe, *The Maya* (9th edition, the one the Dales used),
  which would let the Dales' readings of Coe be checked against Coe; Sorenson, *Mormon's Codex*
  (2013), the largest correspondence list, needed to replicate Sorenson at all. Neither text
  would be stored publicly.

## Cost

Build: a few hours of AI time (attribution questions and parser, grid of reference sets, Part B
search; most counting code exists in `lab.threeworlds` and `lab.inventory`). Machine: minutes of
Mac CPU. Judging: about 50-60 hours of free paced judging, simulated. No GPU, no paid API.

## Sources (URLs)

- Dale and Dale 2019: https://cdn.interpreterfoundation.org/jnlpdf/dale-v32-2019-pp77-186-PDF.pdf ; https://scholarsarchive.byu.edu/interpreter/vol32/iss1/9
- Dales' sequel (2021): https://scripturecentral.org/archive/articles/unpublished/joseph-smith-still-worlds-greatest-guesser-and-getting-better-all-time
- Wheat and Tares reply (2019): https://wheatandtares.org/2019/06/13/bad-book-of-mormon-apologetics/
- Rasmussen, "Estimating the Evidence" series: https://interpreterfoundation.org/category/estimating-the-evidence (episode on Mesoamerican correspondences, to verify)
- Roper 2025: https://cdn.interpreterfoundation.org/jnlpdf/roper-v65-2025-1-8-PDF.pdf
- Coe 1973: https://www.dialoguejournal.com/articles/mormons-and-archaeology-an-outside-view/
- Coe on Mormon Stories (2011): https://www.mormonstories.org/podcast/michael-coe-an-outsiders-view-of-book-of-mormon-archaeology/ ; transcript: https://medium.com/@jellistx/transcript-of-mormon-stories-2011-interview-with-michael-coe-73dc6438e99
- Sorenson, open letter to Coe (2012): https://scripturecentral.org/archive/periodicals/journal-article/open-letter-dr-michael-coe
- Sorenson, "Reading Mormon's Codex" (2012 talk; "some 420" correspondences): https://www.fairlatterdaysaints.org/conference/august-2012/reading-mormons-codex ; book record: https://search.worldcat.org/oclc/828334040
- Vogel 1986: https://user.xmission.com/~research/central/vogel1.htm
- Snodgrass 1974, "An Historical Homeric Society?", JHS 94: https://www.cambridge.org/core/journals/journal-of-hellenic-studies/article/an-historical-homeric-society/2E21FA900D44295E57834425604AA5B1 (not opened in full)
- Vogel, H. U., *Marco Polo Was in China* (Brill 2012/13): https://reviews.history.ac.uk/review/1667/print/ ; https://uni-tuebingen.de/uploads/media/12-04-16MarcoPoloengl.pdf
- Kirchhoff 1943 (secondary; the trait list to verify): https://www.d.umn.edu/claweb/faculty/troufs/anth3618/maKirchhof_handout.html ; https://www.ecured.cu/Mesoamericana
- D-PLACE: https://d-place.org/society/SCCS153 (Aztec, 1520) ; https://d-place.org/society/Cj3 (Hebrews, SCCS44, -800) ; https://d-place.org/source
- Spinden 1917: https://www.gutenberg.org/ebooks/54550
- Roys 1933, Chumayel: https://sacred-texts.com/nam/maya/cbc/cbc00.htm
- Paul 1982, Manchester library: https://scholarsarchive.byu.edu/byusq/vol22/iss3/6
- Earlier project notes: `docs/research/2026-11-20-the-books-setting.md`, `docs/research/2026-11-20-studies-to-rerun.md`
