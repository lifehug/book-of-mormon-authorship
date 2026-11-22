# Redesign: the Uto-Aztecan test (BOM-117)

Research and design only, 2026-11-22. Nothing here has been run. No Book of Mormon text is
involved: this test checks a claim often cited beside the book, not the book itself. No licensed
or copyrighted text was fetched. Only small metadata files (concept lists, language lists) were
read from open datasets, and every address is listed under Sources.

BOM-117 was never started, so there is no failed check to diagnose. The sections "What we did"
and "What the failure says" say what the first plan (the issue body) would have run into.

## The claim and where it comes from

**Who and where.** Brian D. Stubbs, *Exploring the Explanatory Power of Semitic and Egyptian in
Uto-Aztecan* (Provo: Grover, 2015; 2nd ed. 2023). Background: his *Uto-Aztecan: A Comparative
Vocabulary* (2011), a reconstruction of Proto-Uto-Aztecan words (PUA, the common ancestor of the
family). A popular version: *Changes in Languages from Nephi to Now* (2016; 2nd ed. 2020). His
reply to critics: "Answering the Critics in 44 Rebuttal Points", *Interpreter* 37 (2020).

**What he asserts.** About 1,528 sets, each pairing a Uto-Aztecan word (often a PUA
reconstruction) with a Hebrew, Aramaic or Egyptian word, under a table of regular sound
correspondences (his Appendix A). He calls the sources two Semitic strata (a "Semitic-p" and a
"Semitic-kw" language, Northwest Semitic, leaning toward Aramaic) and one Egyptian stratum (Late
Egyptian). He says this is **contact and mixture, not a common ancestor**: in his reply to Rogers
he rejects the description "a long-distance genetic relationship between Afro-Asiatic and
Uto-Aztecan". His supporters date the contact to the first millennium BC (Robertson 2020's
abstract). In a 2022 blog reply he says Semitic and Egyptian material makes up about 35-40% of
Uto-Aztecan vocabulary, and that of 26 sets found in all 11 branches, 25 are Semitic or Egyptian.
He gives probability figures (about 1 in 17 million for one example) and says a similar list was
not found in more than 50 other families.

**The evidence he uses.** Inspection: his sets, his correspondence table, seven old puzzles of
Uto-Aztecan sound history that he says the loans explain, and the pronouns. No control
comparison is published: nobody has run his procedure on a pair of languages with no proposed
link and counted what comes out.

**The critics.** Chris Rogers, "A Review of the Afro-Asiatic: Uto-Aztecan Proposal", *Journal of
Book of Mormon Studies* 28 (2019): the comparative method was not properly applied; chance
resemblance at this scale is expected. Magnus Pharao Hansen, "An Evaluation of the Nahuatl Data in
Brian Stubbs' Work on Afro-Asiatic/Uto-Aztecan", *Nahuatl Studies* blog, 12 Sept 2019: of 14
items resting on Nahuatl alone, most compare a word made of several parts (root plus suffixes)
with a whole Semitic root, rely on doubtful glosses, or use forms that are late in Nahuatl's own
history. He reports Rogers's estimate of 1-3% chance matches per language pair, and argues that
with about 30 Uto-Aztecan languages, several Near Eastern ones and loose meanings, the number of
chance matches expected exceeds 1,528. Reviews more open to the proposal: Dirk Elzinga (*BYU
Studies* 55:4, 2016) and John S. Robertson (*Interpreter* 25, 2017; 34, 2020). Jonathan Green
questioned the probability arithmetic (comments on Times and Seasons, 2022).

**If he is right,** a large layer of Uto-Aztecan vocabulary came from Near Eastern languages
about 2,600 years ago. A layer that big, that recent, should be easy to see: it should beat chance
in a fair test, beat it in the meanings that are most often borrowed, and look like known contact
cases of similar age. **If the critics are right,** a fair test finds the Uto-Aztecan-Semitic
pair inside the range of pairs that never met, and the 1,528 sets are what a large search with
loose meanings yields between any two big vocabularies.

**What other fields do with this kind of claim.** Historical linguistics has a forty-year
literature on telling real relationship from chance:

- *Ringe (1992)* computed the binomial chance of initial-consonant matches on Swadesh lists.
  Criticised for treating matches as independent and for ignoring that some sounds are common
  (Baxter and Manaster Ramer 2000). *Ringe (1999)* showed how easy it is to match consonant
  skeletons of CVC roots, which bears directly on matching Semitic three-consonant roots.
- *Oswalt (1970)*, the shift test: count matches between two lists, then shift one list against
  the other by one meaning, two, and so on; the shifted counts give the chance level for those
  two particular sound systems. Weakness: low power, and nearby meanings in a list are not
  independent.
- *Baxter and Manaster Ramer (2000)*: permutation over meanings, with sound classes, applied to
  English-Hindi. Their point: the test must use the two languages' own sound frequencies.
- *Kessler (2001, 2008)*: the permutation test. Shuffle meanings many times, recompute the match
  score each time, and see where the real score falls. Scores can be a contingency of initial
  sounds, so it detects regular correspondences that are not sameness (Latin *p* to English *f*).
  Kessler insists every test run, failed or not, is reported. Known weakness: on 100- or 200-word
  lists it loses power at depths past several thousand years. Kessler and Lehtonen (2006) extend
  it to many languages at once.
- *Turchin, Peiros and Gell-Mann (2010)*; *Kassian, Zhivlov and Starostin (2015)*: consonant
  classes (after Dolgopolsky) on the first two consonants of 110-item lists, with a permutation
  baseline; criticised in the same journal issue for the coding choices and for which list items
  are allowed.
- *Nichols (1996)*: individual-identifying evidence. A match counts only if its probability is
  below a threshold (she uses about one in a hundred for a paradigm, far lower for a single word)
  and the shape is too odd to recur by chance. Grammar paradigms (pronoun sets, irregular
  alternations) carry the most weight. Criticised as hard to make objective.
- *ASJP* (Holman, Wichmann and others; 40-item lists for over 11,000 doculects) and *Jäger
  (2015, PNAS)*: automatic distances from aligned word forms. Good inside families; at great
  depth the distances sit near the noise floor, and Jäger's macro-family results were disputed.
- *Loanword detection*: Miller, Tresoldi, Zariquiey, Beltrán Castañón, Morozova and List (2020,
  PLoS ONE) found that a single language's word shapes are a weak clue to loans; multilingual
  comparison is needed. *WOLD* (Haspelmath and Tadmor 2009) codes loans in 41 languages, and
  Tadmor, Haspelmath and Taylor (2010) rank meanings by how often they are borrowed.
- A 2024 likelihood-ratio test of relationship (arXiv 2404.00284) and a calibrated weighted
  permutation test (Kassian et al., *Journal of Historical Linguistics*, 2021-2023) are the
  newest variants.

The shared lesson: a match count means nothing without the count the same procedure gets on
pairs that are known not to be related, using the same lists, the same freedom of meaning and the
same sound classes.

## What we did and how it failed

Nothing was run. The issue's plan was: program Stubbs's rules and his allowed meaning latitude,
check the program recovers his sets, then run it on Uto-Aztecan against unrelated languages and
with shuffled meanings.

That plan would have hit three walls, found while preparing this redesign:

1. **His rules are fitted to his sets.** The correspondence table was derived from the 1,528
   matches. Applying it back to the same words is circular: it will "recover" them by
   construction. Applying it to a control language is not possible either, because the rules name
   Semitic sounds. A fair control needs a rule table of the same permissiveness, built the same
   way, for the control pair.
2. **Meaning latitude is not written as a rule.** His semantic links (for example "bury" with
   "tamale", "wine-skin" with "prickly pear", in Hansen's list) are judged case by case. A program
   would have to invent a latitude, and then the result is about our latitude, not his.
3. **No large open Uto-Aztecan lexicon.** His 2011 vocabulary is not open. The open Uto-Aztecan
   lists are 33-121 meanings (see Feasibility), too few to rerun a search across a whole
   vocabulary.

## What the failure says

**About the published claim.** No result exists yet, so nothing is shown against or for it. But
preparing the test shows that the claim as published has **no control**: no count of how many
sets the same procedure finds between languages that never met. The probability figures he gives
are for single resemblances after they were found; they do not count the size of the search
(about 30 daughter languages, several donor languages, thousands of roots on each side, loose
meanings, and vowels largely free). That is the gap Rogers and Hansen point to, and it is a gap
in the evidence, not a finding that the sets are chance.

**About our instrument.** The first plan copied his method (search with his rules) instead of
asking his question (is there a signal above chance?). A copied method inherits its circularity.
That is our design's fault, not his.

**What stays unknown.** Whether Uto-Aztecan holds a Near Eastern layer above chance. Whether a
fair test is powerful enough to see a 2,600-year-old loan layer at all.

## Replicating his approach (owner's rule 1) and checking his examples (rule 2)

**What is open of his data.** More than expected:

- The whole 2015 book is posted chapter by chapter, free, on the Book of Mormon Central (Scripture
  Central) archive, "publicly available for non-commercial, private use". The set chapters (2: pp.
  65-84; 4: pp. 87-156; 5: pp. 157-302), the correspondence table (Appendix A, p. 362) and the
  indexes (Appendices B-D) each have a PDF. Their existence and sizes were checked by header
  request only (chapter 5 is 14 MB, probably page images needing OCR); none was downloaded.
  The text is copyrighted. Reading it for research is within the stated terms; publishing a
  table of his sets is not, and would need his permission.
- ASJP version 21 (held, CC BY 4.0) carries a `PROTO_UTO_AZTECAN` list of 45 forms over 33
  meanings whose source is **Stubbs 2011** itself. So a small sample of his own reconstructions is
  openly licensed and already on disk.
- Not open: the 2011 comparative vocabulary and the 2016 / 2020 *Changes in Languages*.

So the replication does not need a purchase. It does need the owner's yes to download
copyrighted chapters into the private data repository (`data/private/lab/`), with the steps to
obtain them written in `docs/replication.md`, as for Grunder's book. Until that yes: **not
replicated (to-do)**. The 2011 vocabulary and *Changes* stay "not replicated until the source is
bought (to-do)".

**Replication, his way.** A seeded random sample of 150 of his sets, transcribed privately
(references and our codes only in any public file). For each set: (a) does it obey his own
Appendix A table, sound by sound; (b) is the Uto-Aztecan side supported by independent data:
the same cognate set in Greenhill et al. 2023 / Miller 1984 (held, lexibank), and the word
analysed into root and suffixes as Hansen asks; (c) how far apart are the two meanings, measured
by whether the two meanings are expressed by one word anywhere in the world's languages (CLICS
colexification network, open). This reproduces his finding as he states it, and Hansen's check at
ten times the sample.

**The exhaustive check on his rules: "how many other matches were there?"** For each sampled
set, count every Hebrew word (Open Scriptures Hebrew Lexicon: Brown-Driver-Briggs and Strong's,
public domain text, CC BY 4.0 files) and Coptic word (Coptic Dictionary Online) that would pass
his own table against the same Uto-Aztecan word, at the same meaning distance he accepted. If a
typical Uto-Aztecan word has dozens of passing partners, the one he chose carries little weight;
if it has none or one, the match is specific. The same count with meanings shifted (Oswalt's
idea) gives the chance level for that latitude. This is the look-elsewhere count the published
figures leave out.

## Angles considered

1. **His rules on control languages (the issue's plan).** Rejected as the main test: circular
   rules, no written latitude, no large open lexicon. Kept in the form above (alternatives per
   set), which needs no control language.
2. **Permutation test on basic vocabulary (Kessler / Baxter-Manaster Ramer).** Fair, rule-free
   (it learns no correspondences from his data, so no circularity), standard. Weakness for this
   claim: basic vocabulary is the part least often borrowed, and the open lists are short. Kept,
   but as a power-limited first look.
3. **Permutation test on the largest meaning-matched lists, calibrated on known contact pairs of
   similar age, with a borrowability signature.** Chosen. A claimed mixture should be tested where
   mixture shows: across the general vocabulary, and most strongly in meanings that languages
   borrow often. Known contact pairs of about the same age tell us whether the instrument can see
   such a layer at all.
4. **Chronology check.** If loans are 2,600 years old but sit in sets found in all 11 branches and
   reconstruct to PUA with regular correspondences, then PUA must be younger than the contact.
   Greenhill et al. 2023 date PUA to about 4,100 years ago (range about 3,300-5,000). Cheap to
   check once his index is read. Kept as a side check, labelled as resting on a model-based date.
5. **Automatic distances (ASJP LDND, PMI alignment).** Rejected as main test: near the noise floor
   at great distance, and not designed for a loan layer. Reported as a secondary figure only.
6. **Grammar (pronoun paradigm, Nichols's threshold).** His pronoun chapter is three pages, and
   Hansen argues the Nahuatl forms are late. Kept within the replication sample, not a separate
   statistical test: one paradigm cannot be put into a null distribution of its own.

## The proposed design

**Question.** Do Uto-Aztecan word lists match Hebrew, Aramaic and Egyptian in sound and meaning
more often than chance, by more than unrelated pairs do, and in the meanings where loans usually
fall, at the size a 35-40% mixture would imply?

**The key point: what signal size a 2,600-year mixture implies.** Measured in minutes on the held
ASJP data: for unrelated pairs (Finnish-Japanese, Hopi-Tamil, Nahuatl-Finnish, Proto-Quechua-
Hungarian, Yaqui-Japanese, Tamil-Lithuanian), the chance that two words of the same meaning start
with the same broad consonant class is about 11% (range 8.6-13.2%). With that rate, a one-sided
test at p < 0.01 needs:

| Meanings compared | Chance matches | Needed | True matches needed above chance |
| --- | --- | --- | --- |
| 40 | 4.4 | 11 | about 7, or 16% of the list |
| 100 | 11 | 20 | about 9, or 9% |
| 600 | 67 | about 86 | about 19, or 3% (approximate) |
| 1,000 | 111 | 136 | about 25, or 2.5% |

Stubbs's figure of 35-40% of the vocabulary is enormous by these standards. But loans are rare
in basic vocabulary: English, about 41% loans overall in WOLD, has only a handful of loans in its
100 most basic words. If a Near Eastern layer behaved like that, a 33- or 40-meaning list would
hold perhaps 2-4 loan items, below the 7 needed: **a basic-list test could miss a real layer.**
On 600 general meanings the same layer would give dozens of items, far above the roughly 19
needed. So basic lists are the wrong main instrument for a claimed mixture, unless the mixture
reached basic words. Stubbs says it did (the 25 of 26 most widespread sets; the pronouns), and
his own English index (Appendix B) says exactly how many of our list meanings he claims. That
number, read before any test, fixes the predicted effect, so the claim is tested at the size it
states.

One more caution about depth. Correspondence detection weakens as both sides change. 2,600 years
is shallow for a family relationship but not for loans seen through 30 daughter languages and
through Hebrew forms that have changed too. Hence the depth-matched calibration below.

**Measures.**

1. *Primary: Kessler-style permutation test* on meaning-matched lists. Each word coded to broad
   consonant classes (Dolgopolsky-style: labial, dental, sibilant, velar, nasals, liquids, glides,
   laryngeal or none). Score: the contingency (chi-square) of first-consonant classes across
   meanings, plus a second score on the first two consonants. Null: 10,000 shuffles of meanings.
   Because the score is a contingency, a regular change (Semitic *b* to Uto-Aztecan *kw*, say)
   counts as much as sameness. No rule is taken from Stubbs's sets.
2. *Borrowability signature.* Each meaning gets its WOLD borrowing score (Tadmor et al. 2010).
   For each pair, compare the excess of matches in the most borrowable third of meanings with the
   least borrowable third. Real loans skew to the borrowable end; inheritance to the stable end;
   chance is flat.
3. *Multilateral version.* Following Kessler and Lehtonen 2006, the 46 Uto-Aztecan varieties of
   Greenhill et al. against each donor at once, with the same permutation, so that no single
   daughter is picked after the fact.
4. *Secondary:* ASJP's automatic distance for the same pairs, reported only.

**Data.**

| Role | Lists | Size | Licence | State |
| --- | --- | --- | --- | --- |
| Uto-Aztecan, large | WOLD Yaqui | 1,609 entries; documented Spanish loans flagged | CC BY 4.0 | to fetch (lexibank/wold) |
| Uto-Aztecan, many daughters | Greenhill et al. 2023 (lexibank utoaztecan) | 46 varieties, 121 meanings, mostly Miller 1984 | CC BY 4.0 | held |
| Uto-Aztecan, Stubbs's own PUA | ASJP `PROTO_UTO_AZTECAN` (from Stubbs 2011) | 33 meanings | CC BY 4.0 | held |
| Hebrew | Open Scriptures Hebrew Lexicon (BDB, Strong's) | about 8,600 entries, English glosses | CC BY 4.0 (public-domain text) | to fetch |
| Hebrew, Arabic, controls | NorthEuraLex | 107 languages incl. Hebrew, Arabic, Finnish, Lithuanian, Latvian, Swedish, Basque, Spanish, Japanese, Tamil, Korean, Georgian, Hungarian; 1,016 meanings | CC BY 4.0 | to fetch |
| Aramaic, Akkadian, Egyptian, Coptic | ASJP | 33-40 meanings each (Ancient Aramaic 40, Syriac 40, Middle Egyptian 39, Late Egyptian 36, Coptic 37) | CC BY 4.0 | held |
| Coptic, large | Coptic Dictionary Online (Feder et al.) | several thousand entries, English glosses | stated CC BY-SA 4.0 (verify) | to fetch |
| Egyptian, large | Thesaurus Linguae Aegyptiae (Earlier and Late Egyptian, Demotic) | lemmatised corpus | CC BY-SA 4.0 | held |
| Meaning distance | CLICS colexification network | | CC BY 4.0 | to fetch |

Glosses from the Hebrew, Coptic and Egyptian lexicons are mapped to Concepticon meanings with
Concepticon's own automatic mapper, then a paced model judge checks each mapping (simulated
judging; it sees glosses only, never a candidate Uto-Aztecan word). Recent loans are removed
before testing: WOLD's Spanish loans from Yaqui (they include words of Arabic origin that came
through Spanish, an in-data trap), and European loans from Modern Hebrew where Biblical forms
exist.

**Comparisons.** Yaqui (Spanish loans removed) against Biblical Hebrew, Coptic and Late Egyptian
on all shared meanings (up to about 600 by Concepticon overlap); the 46 Greenhill varieties
against Hebrew and Arabic on 115 shared meanings and against ASJP Aramaic, Egyptian and Coptic on
about 30; Stubbs's PUA against Hebrew, Ancient Aramaic, Late Egyptian and Coptic on 26-33 meanings
(reported, labelled underpowered unless his index claims at least seven of those meanings).

**Controls.** The book's three controls (Bible-style books, genuine translations, Joseph Smith's
other dictations) do not apply: no English text is scored. The setting rule "all three settings
scored together" does not apply either. The controls here are language pairs, below.

## Known-answer check

Bars fixed here, before any target pair is scored. All on the same coding, list sizes matched by
subsampling to the target's meaning count.

- **Positive, inherited:** Hebrew-Arabic (NorthEuraLex; split about 3,000-4,000 years). Must give
  p < 0.01.
- **Positive, contact between unrelated languages, similar age (the depth calibrators):**
  Finnish-Lithuanian and Finnish-Latvian (Baltic loans in Finnish, about 2,500-3,500 years old);
  Finnish-Swedish (Germanic loans, about 2,000-2,500 years); Basque-Spanish (Latin and Romance
  loans, up to about 2,000 years). Younger: English-French (about 950 years); Yaqui-Spanish with
  loans kept (about 450 years). Bar: at least 4 of these 6 at p < 0.01, **and** at least one of the
  three Finnish pairs, and each passing pair must show the borrowable-end skew. If no Finnish pair
  passes, the instrument cannot see a layer of the claimed age, and any null on the target is
  "cannot tell".
- **Negative, unrelated, no contact:** Yaqui against Finnish, Japanese, Tamil, Basque, Georgian,
  Hungarian, Korean and Imbabura Quechua. Bar: at most 1 of 8 at p < 0.01.
- **Hard decoys with famous lookalike lists:** Japanese-Hebrew (the subject of published
  "common ancestry" word lists) and Japanese-Tamil (Ohno's proposal of several hundred
  correspondences, not accepted by most linguists). Both must give p > 0.05. A Stubbs-style search
  with loose meanings would produce long lists for both; that is exactly why they are here.
- **Planted signal (power):** in each negative pair, plant k synthetic "loans" with a regular
  but non-identical correspondence and random vowel change, where k is the number implied by
  Stubbs's index for that list; the test must detect it in at least 80% of 200 plantings. Without
  this, a null cannot be read as "no layer of that size".
- **Leakage trap:** Yaqui-Hebrew with WOLD's Spanish loans left in, reported beside the cleaned
  run, to show the cleaning matters.

If the inherited and contact bars are missed, the target is not scored on that list size.

## What each outcome would mean

- **Signal (target p < 0.01 after Holm correction across target tests, on a list size whose
  check passed, with the borrowable-end skew).** "Uto-Aztecan and these Near Eastern lists match
  above chance in the pattern contact leaves." It would not say when, who, or by what route, and
  it would call for the replication sample to show which items carry it.
- **Signal without the skew,** or only on the first-two-consonant score: reported as unexplained;
  no verdict.
- **No signal, with the depth calibrator passed and the planted signal at Stubbs's implied size
  detected:** "No sign of a Near Eastern layer of the size claimed, in the lists tested." It would
  not rule out a smaller layer, or one confined to vocabulary outside the lists.
- **Calibrators failed:** "cannot tell". That would itself be worth saying: the standard tools
  cannot see a 2,600-year loan layer in lists this size.
- **Replication sample (rules 1-2):** reported as shares: sets that obey his table; sets whose
  Uto-Aztecan side is supported by independent data; median number of alternative Hebrew or Coptic
  partners per set under his own rules; meaning distances. No yes/no bar: it describes how
  constrained his matching was.
- **Chronology check:** the share of his sets on our list meanings that sit in cognate sets
  spread across both northern and southern branches. A high share means the claim needs PUA to be
  younger than about 2,600 years, against the published dating; reported with that date's range.

## Risks

- **Short lists.** Only Yaqui, Hebrew (lexicon), Coptic (lexicon) and the NorthEuraLex controls
  reach hundreds of meanings. Aramaic and Egyptian enter only through 30-40 meanings unless the TLA
  glosses map well.
- **Gloss mapping.** Lexicon glosses are not list meanings. A loose mapping inflates matches on
  every pair equally, but adds noise; the judge checks are labelled simulated.
- **Stubbs's PUA is his own reconstruction.** It may lean toward his Semitic forms. The Greenhill
  data (mostly Miller 1984) and Yaqui are independent of him; the PUA list is reported, not relied
  on.
- **Modern versus ancient donors.** NorthEuraLex Hebrew and Arabic are modern. Biblical Hebrew
  from the lexicon is the main Semitic donor; Modern Hebrew only for the inherited check.
- **The calibrators are not perfect matches.** Finnish-Baltic contact was long and intense; a
  shorter contact would leave less. The planted-signal check covers this gap only in part.
- **Sound classes are coarse.** Two languages with similar sound systems (both rich in *k* and
  *t*, say) match more by chance; the permutation keeps each language's own frequencies, which is
  the standard answer, but list-internal structure (many words of one shape) can still bias it.
- **A null is not proof of absence.** Kessler's own point: one cannot show two languages are
  unconnected. The result is stated as "not detected at this size, with this power".
- **Copyright.** Any transcription of Stubbs's sets stays in the private repository, and public
  files carry set numbers and codes only.

## Feasibility (measured 2026-11-22, minutes of Mac time)

- ASJP v21 unpacked: 11,540 doculects, 100 meanings (40 in most lists). 80 Uto-Aztecan doculects,
  41 with 35 or more meanings.
- `PROTO_UTO_AZTECAN` (source: Stubbs 2011): 33 meanings. Shared meanings with it: Hebrew 33,
  Biblical Hebrew 26, Ancient Aramaic 33, Late Egyptian 29, Middle Egyptian 32, Coptic 32,
  Proto-Semitic (Kogan 2011) 20, Classical Arabic 33; controls Finnish 33, Japanese 31, Tamil 33,
  Proto-Quechua 28.
- Chance first-consonant-class match on six unrelated pairs: 8.6-13.2%, mean 11.1% (shuffled
  meanings only; no target pair scored).
- Concept overlap by Concepticon ID: NorthEuraLex 954 concepts, WOLD 1,458, Greenhill 121, ASJP
  100. NorthEuraLex and WOLD share 606; Greenhill and NorthEuraLex 115; Greenhill and ASJP 90.
  Yaqui's actual coverage of the 606 is not yet counted (needs the WOLD forms).
- Greenhill's Uto-Aztecan forms: 4,565 of 5,813 from Miller 1984; 13 from Stubbs 2011.
- The lexibank Semitic set held (Feleke) is Ethiopian Semitic only; not useful as a Hebrew source.

**Answer to "are the open lists large enough?"** For basic-vocabulary tests, only just: 33-40
meanings detect a layer only if it fills about one sixth of the list. For the large-list test,
yes for Yaqui against Hebrew and Coptic (hundreds of meanings), once three open datasets are
fetched.

## What to fetch or buy

- Fetch (open, CC BY 4.0 unless noted): WOLD (github.com/lexibank/wold); NorthEuraLex
  (github.com/lexibank/northeuralex); Open Scriptures Hebrew Lexicon
  (github.com/openscriptures/HebrewLexicon); Coptic Dictionary Online (CC BY-SA 4.0, to verify);
  CLICS (clics.clld.org). All small, minutes.
- Owner's decision, no money: download the free chapter PDFs of Stubbs 2015 from the Book of
  Mormon Central archive into the private repository for the replication sample, and record the
  steps in `docs/replication.md`.
- Not bought now (to-do): Stubbs 2011 *Comparative Vocabulary*; *Changes in Languages* 2nd ed.;
  the 2023 second edition of *Exploring* (to see what changed). Rogers 2019 is free on BYU
  ScholarsArchive but refused automated download (HTTP 403); read in a browser.
- Worth a linguist's review before results are believed (the issue already says so): the
  sound-class coding and the gloss mapping.

## Cost

Build: a few hours of assistant time (one module with the coder, permutation, borrowability split
and planted-signal check; tests). Gloss mapping: Concepticon mapper in minutes, then about 3,000
judge checks, about 10 hours paced and free. Permutation runs: about 40 pairs at 10,000 shuffles,
minutes on the Mac. Replication sample (if the owner says yes): OCR of three chapters on the Mac,
then 150 sets transcribed and checked, a few hours of assistant time plus judge time for meaning
distance where CLICS is silent. No GPU, no spending.

## Sources (URLs)

Claim and replies:
- Stubbs 2015, chapter list and free PDFs: https://scripturecentral.org/archive/books/book/exploring-explanatory-power-semitic-and-egyptian-uto-aztecan
- Chapter 5 PDF (header checked only): https://storage.googleapis.com/scripturecentral-prod-strapi-uploads/chapter_5_7b3e3d9d6c/chapter_5_7b3e3d9d6c.pdf
- Chapter 4 PDF: https://storage.googleapis.com/scripturecentral-prod-strapi-uploads/chapter_4_8568b702ae/chapter_4_8568b702ae.pdf
- Appendix A PDF: https://storage.googleapis.com/scripturecentral-prod-strapi-uploads/appendix_a_63b8bb03da/appendix_a_63b8bb03da.pdf
- Chapter 6 PDF: https://storage.googleapis.com/scripturecentral-prod-strapi-uploads/chapter_6_dbdc643ab7/chapter_6_dbdc643ab7.pdf
- Stubbs, clarifications (2022): https://archive.timesandseasons.org/2022/10/clarifications-on-uto-aztecan/index.html
- Stubbs's response to Rogers (2019 guest post): https://nothingwavering.org/2019/08/28/69003-guest-post-from-brian-stubbs-a-response-to-chris-rogers-a-review-of-the-afro-asiatic-uto-aztecan-proposal-in-the-journal-of-book-of-mormon-studies.html
- Stubbs's response PDF: https://www.jefflindsay.com/Brian-Stubbs-CRogerReview2019-2.pdf
- Rogers 2019, JBMS 28: https://scholarsarchive.byu.edu/jbms/vol28/iss1/12
- Hansen 2019: https://nahuatlstudies.blogspot.com/2019/09/an-evaluation-of-nahuatl-data-in-brian.html
- Elzinga 2016, BYU Studies 55:4: https://scholarsarchive.byu.edu/byusq/vol55/iss4/15
- Robertson 2017, Interpreter 25: https://scholarsarchive.byu.edu/interpreter/vol25/iss1/8
- Robertson 2020, Interpreter 34: https://scholarsarchive.byu.edu/interpreter/vol34/iss1/4
- Lindsay 2017, Interpreter 26: https://scholarsarchive.byu.edu/interpreter/vol26/iss1/8
- Peterson blog on "44 Rebuttal Points": https://www.patheos.com/blogs/danpeterson/?p=85649

Methods:
- Kessler 2008, Language and Linguistics Compass 2(5): 821-839 (record): https://dblp.org/rec/journals/llc/Kessler08
- Review of Kessler 2001, Computational Linguistics: https://preview.aclanthology.org/fix_video/J01-4008.pdf
- Kassian, Zhivlov, Starostin 2015 (PDF): https://cdstar.shh.mpg.de/bitstreams/EAEA0-FAC3-DC12-6CAA-0/Kassian2015.pdf
- Calibrated weighted permutation test (Kassian et al.): https://www.jbe-platform.com/content/journals/10.1075/jhl.00014.kas
- Likelihood-ratio test of relationship (2024): https://arxiv.org/pdf/2404.00284
- Miller et al. 2020, borrowing detection: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7725347/
- Tadmor, Haspelmath, Taylor 2010, Diachronica 27(2): https://www.jbe-platform.com/content/journals/10.1075/dia.27.2.04tad
- Haspelmath and Tadmor, Loanwords in the World's Languages (PDF): https://www.eva.mpg.de/fileadmin/content_files/staff/haspelmt/pdf/LWT.pdf
- Greenhill et al. 2023, Language 99(1): https://muse.jhu.edu/article/883069
- Not fetched, cited from the literature: Ringe 1992 (Transactions of the American Philosophical
  Society 82:1); Ringe 1999 (Transactions of the Philological Society 97); Oswalt 1970 (Computer
  Studies in the Humanities and Verbal Behavior 3); Baxter and Manaster Ramer 2000 (in Renfrew,
  McMahon and Trask, *Time Depth in Historical Linguistics*); Nichols 1996 (in Durie and Ross, *The
  Comparative Method Reviewed*); Turchin, Peiros and Gell-Mann 2010 (Journal of Language
  Relationship 3); Kessler and Lehtonen 2006 (in Forster and Renfrew, *Phylogenetic Methods and
  the Prehistory of Languages*); Jäger 2015 (PNAS 112:41); Campbell and Poser 2008, *Language
  Classification*.

Data:
- ASJP v21 (held): https://zenodo.org/api/records/16736409
- lexibank utoaztecan (held): https://github.com/lexibank/utoaztecan
- WOLD: https://github.com/lexibank/wold ; Yaqui vocabulary: https://wold.clld.org/vocabulary/32
- NorthEuraLex: https://github.com/lexibank/northeuralex
- Open Scriptures Hebrew Lexicon: https://github.com/openscriptures/HebrewLexicon
- Coptic Dictionary Online: https://coptic-dictionary.org
- Thesaurus Linguae Aegyptiae (held): https://huggingface.co/thesaurus-linguae-aegyptiae
- CLICS: https://clics.clld.org
- Concepticon: https://concepticon.clld.org
