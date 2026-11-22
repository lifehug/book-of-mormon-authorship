# Redesign: do the book's debates date to the 1820s? (BOM-103)

Written 2026-11-22 at the owner's request, after two designs failed their known-answer check.
Research and design only. Nothing here was run on the Book of Mormon, no AI judge was called,
and nothing was committed. The draft test card is in the private repository,
`lab/owner/2026-11-22-debates-redesign/card.md`.

## The claim and where it comes from

**Alexander Campbell, "Delusions", *Millennial Harbinger* 2:2 (7 February 1831); reprinted as a
pamphlet in Boston, 1832.** In point 7 of his review, one paragraph, Campbell says the book holds
"every error and almost every truth discussed in N. York for the last ten years", and that it
"decides all the great controversies". He then lists twenty: infant baptism, ordination, the
trinity, regeneration, repentance, justification, the fall of man, the atonement,
transubstantiation, fasting, penance, church government, religious experience, the call to the
ministry, the general resurrection, eternal punishment, who may baptize, freemasonry, republican
government, and the rights of man. He adds that "all these topics are repeatedly alluded to".
Nearby, in point 10, he points to a few phrases ("salvation is free", "your own eternal
welfare") as modern. Those are phrase anachronisms, which is a different claim. (Wording read
in our fetched copy of the 1832 pamphlet, `data/corpus/lab/sources/debates/`.)

**Later forms of the claim.**
- Thomas O'Dea (*The Mormons*, 1957) says the book reflects the political and religious issues
  of its day. Bushman (1976) tests O'Dea's political half (see below).
- Robert Hullinger (*Mormon Answer to Skepticism*, 1980; reissued 1992 as *Joseph Smith's
  Response to Skepticism*) reads the book as a defence of Christ's divinity against deism of the
  *Age of Reason* kind.
- Dan Vogel ("Anti-Universalist Rhetoric in the Book of Mormon", in Metcalfe, ed., *New
  Approaches to the Book of Mormon*, 1993, 21-52; also *Religious Seekers and the Advent of
  Mormonism*, 1988) argues that the book's arguments against universal salvation (Nehor,
  Korihor, Alma 11:34-35) repeat the anti-Universalist rhetoric of early-nineteenth-century
  America. He supports this with people in Joseph Smith's circle who were Universalists.

**The reply.** These are perennial Christian questions, argued since the Reformation and before.
Martin Tanner answered Vogel (*Review of Books on the Book of Mormon* 6, 1994, 418-433): ideas
of universal salvation existed in the ancient world. Richard Bushman ("The Book of Mormon and the
American Revolution", *BYU Studies* 17/1, 1976) compared the book's politics with American
writing about the Revolution. He found that most of the Revolution's principles are slighted, and
that the Nephite order looks more like Hebrew and ancient monarchy.

**What the world would look like.** If Campbell is right in the strong sense, the book's *mix* of
controversies, and the sides it takes, should look more like American religious print of about
1815-1830 than like any earlier time. That includes the questions it ignores. If the reply is
right, the mix should fit several eras about equally, or fit an earlier one better. Both sides
agree that each topic on its own is old. So a test that dates topics one at a time cannot settle
this. The 2026-11-21 phrase counts showed that: all five phrases were in print by the 1740s.

## Replicating their approach

**Campbell.** He used no method that could be rerun. He read the book, listed what it discusses,
and asserted that this was New York's agenda of 1820-1830. He gave no evidence about New York and
no comparison with other times or places. And his list was read off the book itself. So "the book
has these topics" is true by construction. Only "these were New York's topics, more than other
places' and times'" is a claim, and he did not test it. The nearest faithful replication has two
steps:
1. *His step, his way:* for each of his twenty topics, is it in the 1830 text, by a written
   rule? (Seventeen already have rules in `lab.debates.topics`. Repentance, penance, religious
   experience, the call to the ministry and the rights of man still need rules.)
2. *The comparison he left out:* the same presence check, with the same rules, in other bodies of
   religious print of similar size: American works of 1815-1829, English works of 1640-1659,
   works of 1740-1769. How many of the twenty are present in each? The prediction to beat:
   all twenty are present everywhere. If so, his list cannot pick out the 1820s. That would
   point to a flaw in how the claim was argued. It would not show the claim is false.

**Vogel (1993).** This is an argument by parallel examples: rhetorical criticism, with no counts
and no outside baseline (from the open summary at bhroberts.org; the chapter itself was not read
for this note). The nearest faithful replication: list each anti-Universalist argument he pairs
with a Book of Mormon passage. Then count, decade by decade, how often each argument occurs in
works that argue about universal salvation, from the 1650s (Winstanley; the "restoration" writers)
through 1829. Does each argument first appear, or peak, in American print after 1790? The chapter
is under copyright. It is held only as a user upload on the Internet Archive, which the owner
cleared on 2026-11-18 for reading a topic list (not for adding to the corpus). His item list
has to be taken from it by hand. That makes it worth buying (see the end).

**Hullinger (1980).** Also argument by reading. The nearest faithful replication would do the
same for Korihor's and Sherem's arguments against deist writing of 1690-1829 (Toland, Blount,
Paine, Ethan Allen, Palmer). This is the "named opponents" angle below. It is kept for a later
card.

**Bushman (1976).** A qualitative comparison of positions (republican or monarchical ideas). It is
the one precedent that compares *positions* with an outside baseline. Part B below makes it
countable for the "kings and government" topic.

**Have we done any of this?** Not as replication. Design 1 and design 2 asked a different
question (the print decade of the nearest passages by meaning). The phrase counts tested the
critics' phrase-anachronism claim (`docs/research/2026-11-20-studies-to-rerun.md`), not Campbell's
topic claim.

## What we did and how it failed

- **Design 1** (`lab.debates check`; card `lab/owner/2026-11-21-debates/card.md`). Seventeen topics
  by term rules. For each topic passage, the 100 nearest passages in the meaning index among
  13.2 million religious passages of 1640-1829. Each decade's count was divided by that decade's
  share of the gallery. Bar: 12 of 20 control works within a decade of their print decade, in
  every group. Result: 7, 12, 10 and 5 of 20 for the 1650s, 1740s, 1780s and 1820s groups, and 0
  of 20 for clean hand-keyed text. Almost everything peaked in the 1750s. Those decades hold only
  22,000-49,000 passages each, so a few neighbours give a large ratio.
- **Design 2** (`check2`; card `lab/owner/2026-11-21-debates-2/card.md`; post hoc). OCR works of
  1780-1829 only, every decade sampled to the same size. Now almost everything peaked in the
  1810s-1820s. That included 15 of 20 works by authors dead before 1760 (reprints) and 12 of 20
  keyed works of 1780-1809. Only the 1810s and 1820s groups passed, because everything lands
  there.
- **Phrase counts** (same run): "infinite atonement" from the 1730s, "plan of salvation" and
  "probationary state" from the 1740s, "demands of justice" from the 1640s, "fall of man"
  throughout.

## What the failure says

**(a) About the published claim.** Not much, and that matters. The failure belongs to our
instrument, not to Campbell. Two things do bear on the claim:
- Each of the critics' five doctrinal phrases was in print 80 to 180 years before 1830. Read as
  "the theology's vocabulary is of 1800-1830", that claim is not supported. Campbell never made
  it; he dated the agenda, not the words.
- Campbell's evidence (a topic list read off the book, with no comparison) cannot tell the 1820s
  from any other period of Protestant controversy. Our own feasibility look (below) finds the
  English 1640s-1650s covered his list at least as fully. This is a flaw in how the claim was
  argued. It says nothing yet about whether the claim is true.

**(b) About our instrument only.**
- The wrong question. "Which decade is this passage nearest to in meaning?" measures how a passage
  sounds and how the search set is built. It does not measure which controversies were live.
  A sermon on infant baptism from 1650 and one from 1825 are about the same thing. A meaning model
  is built to put them close together.
- The wrong baseline. The lean followed the gallery's shape: thin decades in design 1, crowded
  and varied decades in design 2. The decoys (old works reprinted late) landed late. This is
  lesson 7 again: there was no baseline that the reprints could fail.
- Text kind. Clean keyed text and OCR text behaved differently, and the 1830 text we hold is clean.
- Unit. 128-word passages, one at a time, cannot see a *bundle*. The claim is about which topics
  appear together and in what proportion.

**(c) Still unknown.** Whether the book's agenda (its mix of topics and of sides) is closer to
the 1820s than to other eras. Whether its sides on universalism, baptism, deism and the rest
match any 1820s party better than earlier ones. Whether its silences (temperance, missions,
Bible societies, Sabbath mails, Unitarianism by name, revivals) count against the claim or only
reflect its scriptural register.

## Angles considered

1. **Decade of the nearest passages by meaning** (designs 1 and 2). Failed twice. Retired.
2. **Time-locked language models** on each topic's passages. These date *language*, and the
   study's section 8 already does that. They do not measure which debates were live, so they do
   not answer this question. Rejected for this test.
3. **The agenda as a bundle (chosen, part A).** Each era's religious print has a profile: what
   share of its controversy goes to each topic. Infant baptism takes 13% of topic passages in a
   sample of 1650s works and 1-3% in most other decades. "Popery" takes 10% in the 1680s.
   Regeneration takes 24% in the 1740s. Missions and Bible societies take 8% in the 1820s and
   almost nothing before 1790. A topic is perennial; its *share* is not. The question becomes:
   which era's profile does a text's profile match, over a topic list fixed from outside the
   Book of Mormon, silences included? This needs no meaning index and no AI judge. Reprints have
   a fair chance to fail it: a 1680 work reprinted in 1825 should still carry 1680 proportions.
   Precedents: topic shares over time as a historical signal (Blei and Lafferty 2006, dynamic
   topic models). Word-category profiles tracking historical change (Klingenstein, Hitchcock and
   DeDeo 2014, Old Bailey). Novelty and resonance measured as surprise against past and future
   texts (Barron, Huang, Spang and DeDeo 2018). We use fixed written rules in place of fitted
   topics, so the categories are set before any result and are open to inspection.
4. **Which sides, and which sides together (chosen, part B, after A).** Campbell said the book
   "decides" the controversies. Which side it takes, and above all which *combination* of sides,
   is more telling than the topics. Methodists were against Calvinism and against universal
   salvation, but they baptised infants. Calvinist Baptists rejected infant baptism. Free Will
   Baptists were against both. The Campbellites were against the clergy and infant baptism, but
   held that miracles had ceased. A combination such as "believers' baptism, Arminian, against
   paid clergy, against universal salvation, gifts not ceased" can be looked for in each era.
   The seventeenth-century General and Six-Principle Baptists are an obvious earlier candidate.
   Part B needs stance reading, so it needs the paced AI judge (simulated judging) with its own
   known-answer check.
5. **Named opponents' arguments, first attestation.** For each argument put in the mouth of
   Nehor, Korihor, Sherem or the Zoramites, find its earliest and peak decades in the library.
   This gives an earliest possible date, which is sound logic: a book cannot answer an argument
   not yet made. But only arguments first attested late carry weight, and it is the most reading.
   It reuses the BOM-118 machinery. Kept for a later card (and Vogel's list needs the book).
6. **Region and denomination: New York against elsewhere.** Not feasible with what we hold.
   Chronicling America has no New York pages in the 1810s-1820s (7 in the 1800s). Of 32,146
   religious works, publication place is known for HathiTrust only: 48 printed in New York in
   the 1820s. "New York" in an imprint mostly means the city, not the burned-over district.
   Place could be added from Internet Archive metadata or by re-fetching HathiTrust's full
   catalog records (MARC 260, place). That is a later step. Denomination is not catalogued. It
   can be hand-coded for a fixed list of periodicals (Methodist Magazine, Utica Christian
   Magazine, Christian Baptist, Gospel Advocate, Christian Disciple and others are held).

## The proposed design

**Step 1: reproduce their result their way.** Campbell's twenty-topic presence check on the
1830 text, then the same check on four comparison bodies (above). Vogel's argument list, once it
is keyed from the chapter, counted by decade. This is reported first, whatever it shows.

**Part A question (one sentence):** Over a topic list fixed from period sources rather than from
the Book of Mormon, is the book's profile of controversy (share of its topic passages per topic,
silences included) closest to religious print of 1815-1829, or to an earlier era?

**Measure.**
- *Topic list.* The union of (i) Campbell's twenty, (ii) the controversies named in
  period surveys of sects, read by hand for their headings only: Pagitt's *Heresiography*
  (1645) and Edwards's *Gangraena* (1646) for the 1640s; Hannah Adams's *View of Religions*
  (1801, 1805) and the 1817 *Dictionary*; John Evans's *Sketch of the Denominations* (1795 and
  later). All are held in the library, public domain. (iii) The issue's list. About 30-35
  topics. The 1820s markers (temperance, missions and Bible societies, Sabbath, revivals,
  Unitarianism, slavery) are included, so silences count.
- *Register-neutral wording.* Each topic's rule must match both King James-style and
  plain-prose wording ("them that are sent forth to preach" as well as "missionary"). Each rule
  is checked for precision on 20 hits per era by hand before any count is used. This matters
  because a scripture-style text cannot say "Unitarian".
- *Unit and profile.* 128-word passages; a passage counts for every topic whose rule matches.
  A text's profile is its topic-passage counts, subsampled to the same number of topic passages
  for every text (100, seeded, 20 repeats). That gives equal precision. Smoothed shares follow.
- *Reference eras* (built from religious works, `dup_keeper`, registry `year`, Bibles out,
  reprints out: an author dead more than 30 years before printing is excluded):
  E1 1640-1659, E2 1660-1699, E3 1700-1769 (thin: keyed text only), E4 1770-1799, E5 1800-1814,
  E6 1815-1829. Each control is scored against references with its own work and author left out.
- *Score.* The Jensen-Shannon distance (a standard distance between two sets of shares) from the
  text's profile to each era's profile. Reported: the nearest era, the rank of E6, and the gap
  between the nearest era and E6. A "fits no era" flag is raised if the nearest distance is beyond
  the 95th percentile of control texts' distances to their own era.

**Data.** All held: the registry and normalized text (`lab.door`), `lab.debates.topics`, the
1830 text (`semantic.search.bom_queries`), TCP collection codes (Evans for American imprints to
1800, ECCO for British). Nothing needs fetching for part A. Optional, free: HathiTrust's full
catalog records for MARC 260 (place) and 650 (subject, e.g. "Universalism -- Controversial
literature"), from the same open API `lab.sources marc` already used
(https://catalog.hathitrust.org/api/volumes/full/json/). That gives a second, independent
measure of what was argued when.

**Part B (only if part A's check passes).** Stance on eight controversies (infant baptism;
universal salvation; free will against predestination; paid clergy; gifts and revelation ceased;
the Godhead; church government; kings against judges), read by the paced AI judge (simulated
judging). Readings cover the book's topic passages and reference passages from writers whose
positions are on record. Reference writers: Wesley (Methodist); Ballou's *Treatise on Atonement*,
1805 (Universalist); Jonathan Edwards (Calvinist); Campbell's *Christian Baptist*, 1823-1830;
Barclay's *Apology* (Quaker); Grantham's *Christianismus Primitivus*, 1678 (General Baptist);
a Free Will Baptist and a Shaker source. Report which reference writer's combination of sides is
nearest, and the earliest era in which the book's combination is attested. About 2,000-2,500
readings, about 8 hours of free judging.

## Known-answer check

Fixed before any count. Seeded draws of 20 control texts per group. Each must have at least 100
topic passages. In E3 (1700-1769) fewer than 20 may qualify; the shortfall is reported and the
group gets no bar.
- **Era groups:** E1, E2, E4, E5, E6, each 20 texts. Bar: in every group at least 55% placed in
  their own era (chance about 17% among six eras), and at least 80% in their own or an adjacent
  era.
- **Hard decoy 1, old works reprinted 1815-1829** (author dead before 1760). This is the group
  design 2 got wrong (15 of 20 late). Bar: at most 25% placed in E6, and at least 50% placed in
  the era of the author's life.
- **Hard decoy 2, the Interregnum's heresy catalogues and polemics** (Pagitt 1645, Edwards 1646,
  and 18 more E1 works with at least 6 of Campbell's 20 topics). They cover Campbell's list.
  Bar: at least 70% placed in E1 or E2 and none in E6.
- **Register control, Joseph Smith's own revelations of 1828-1835** (Revelation Book 1, held;
  King James register, known date): a single text cut into four blocks, each with at least 100
  topic passages if available. Expected E6. Bar: at least three of the four blocks in E5-E6. If it
  misses, the instrument reads register, not agenda, and the book is not scored.
- **Bible-style books** (the eight held: Dodsley 1741, Snowden 1793, *First Book of Napoleon*
  1809, *American Chronicles* 1812, *Chronicles of Eri* 1822, *Book of Nullification* 1830 and
  others). Descriptive only, because most are political, not doctrinal. They show where an
  imitation-scripture text's profile falls.
- **Genuine translations** (catalog-marked, religious, printed 1815-1829, of works first
  written before 1700). Descriptive: do they place by first writing or by printing?

If any bar is missed, the Book of Mormon is not scored and the miss is reported.

## What each outcome would mean

- **Leans to Campbell:** the book is nearest E6, with E6's distance clearly below E1-E4 (beyond
  the 95% range of the repeat subsamples). A late placement is meaningful only because decoy 1
  passes. Part B then asks whether its sides match an 1820s party.
- **Leans to the reply:** the book is nearest an earlier era (named), or E6 ranks no better than
  third.
- **Cannot tell:** E6 and an earlier era within the subsample range of each other, or "fits no
  era". Its silences on the 1820s markers are reported either way. Whether they come from the
  register can be judged only against the register control.
- Even a clear E6 placement would *suggest* the book's agenda matches its publication period. It
  would not show where the content came from, or rule out any account of its origin.

## Risks (how it could mislead)

1. **Register.** A King James-style text lacks modern labels, so it may be pushed away from E6
   whatever its content. The register-neutral rules and the Smith-revelations control are the
   defences. If that control fails, stop.
2. **Rule drift.** A word changes meaning over two centuries ("revival", "mason"). Hence the
   precision check per era per topic.
3. **Selection.** Campbell's list came from the book. Fixing the list from period surveys of sects
   reduces this; the book's own topics are included but do not define the list.
4. **Thin eighteenth century.** 1700-1779 rests on keyed TCP text alone (150-600 religious works a
   decade). E3 is reported without a bar.
5. **Text kind.** Keyed and OCR text differ. In the feasibility look, 1790s Evans (keyed) and
   1790s OCR profiles were about as far apart as two random halves of one decade, which is
   encouraging. It must still be checked per group.
6. **One book against many.** A long, many-sided book may sit between eras. That is why "fits no
   era" and the subsample range are reported.
7. **Part B depends on simulated judging.** It needs its own known-answer check: at least 85%
   agreement with positions on record, including passages that *quote* an opponent.

## Feasibility (measured 2026-11-22, minutes of Mac CPU; no Book of Mormon profile computed)

- Religious works in the gallery filter, 1640-1829: 32,146 (TCP 16,633; Internet Archive 11,691;
  Institutional Books 2,591; HathiTrust 1,231). The 1700s-1770s hold 153-457 a decade.
- A look at 80 sampled works per cell, 31 topics (17 existing rules plus 14 trial rules), 34
  seconds. Between-era profile distances (Jensen-Shannon 0.07-0.13 between distant eras) exceed
  the within-era split-half noise (0.05-0.08). Neighbouring decades are not separable (1810s
  against 1820s: 0.035). Hence eras of 15-40 years, not decades. Known shifts appear unprompted:
  infant baptism 13% in the 1650s; popery 10% in the 1680s; regeneration 24% in the 1740s;
  slavery 11% in the 1770s; Unitarian 4-6% and missions or Bible societies 3-8% in the
  1810s-1820s. This look was seen before the bars above were set. The bars come from chance and
  from design 2's decoy failure, not from these numbers.
- Works with at least 100 topic passages: about 5-11% of 17th-century works, 27-29 of 80 in the
  1810s-1820s, 3-5 of 80 in the 1740s-1790s keyed cells. E1, E2, E5 and E6 have far more than 20
  candidates; E3 and E4 may fall short.
- The 1830 text: 2,158 passages; 304 match at least one of the existing 17 topics (enough for a
  100-passage subsample). No profile was computed.
- Held and checkable: Gangraena (1646), Pagitt (1645), Hannah Adams (1801, 1805, 1817 editions),
  Evans's *Sketch* (1795-1807 and later), Ballou's *Treatise on Atonement* (1805 on), the
  *Christian Baptist* (1823 on), the *Gospel Advocate*, the Methodist Magazine, the Utica
  Christian Magazine, the Panoplist, the Christian Disciple.

## Cost

Part A: about two to three hours to build. The rule precision checks take an hour of hand
reading, or one judge pass of about 600 readings (2 hours, free). The run is about 30 minutes of
Mac CPU over 32,000 works. Part B: about 8 hours of free judging and an hour to build. No
rented GPU.

## Worth buying

Metcalfe, ed., *New Approaches to the Book of Mormon* (Signature Books, 1993), for Vogel's chapter,
so his argument list can be keyed faithfully. Optional: Hullinger (1992), for the deism
arguments of angle 5.

## Sources

- Campbell, "Delusions", *Millennial Harbinger* 1831: https://archive.org/details/millennialharbinger1831 ;
  1832 pamphlet: https://archive.org/details/delusionsanalysi00camp (held, read 2026-11-22)
- Vogel 1993, summary: https://bhroberts.org/records/2ftKjf-Fk1KQb/dan_vogel_argues_that_the_book_of_mormon_reflects_the_19th_century_debates_concerning_universalism
- Tanner 1994 reply: https://scripturecentral.org/archive/periodicals/journal-article/there-nephite-anti-universalist-rhetoric-book-mormon
- Dan Vogel (bibliography): https://en.wikipedia.org/wiki/Dan_Vogel
- Hullinger, review in *Dialogue* 13/3: https://www.dialoguejournal.com/wp-content/uploads/sbi/articles/Dialogue_V13N03_138.pdf
- Bushman 1976: https://byustudies.byu.edu/wp-content/uploads/2019/08/17-1_Article_Bushman_TheBookofMormonandTheAmericanRevolution.pdf ;
  https://scholarsarchive.byu.edu/byusq/vol17/iss1/2
- Givens, *By the Hand of Mormon* (Oxford, 2002), on the book's reception (not read here)
- Edwards, *Gangraena*: https://en.wikipedia.org/wiki/Gangraena ; text: https://quod.lib.umich.edu/e/eebo/A38109.0001.001
- Blei and Lafferty 2006, dynamic topic models: https://www.cs.columbia.edu/~blei/papers/BleiLafferty2006a.pdf
- Klingenstein, Hitchcock and DeDeo 2014: https://pmc.ncbi.nlm.nih.gov/articles/PMC4084475
- Barron, Huang, Spang and DeDeo 2018: https://pmc.ncbi.nlm.nih.gov/articles/PMC5939074 ; https://arxiv.org/pdf/1710.06867
- HathiTrust catalog API (for optional place and subject fields): https://catalog.hathitrust.org/api/volumes/full/json/
- Earlier attempts: `data/lab/debates/check.json`, `check_v2.json`, `phrases_v2.json`; issue BOM-103 (GitHub #114)
