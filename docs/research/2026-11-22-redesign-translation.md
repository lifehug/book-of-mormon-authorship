# Redesign: does it read like a translation? (BOM-102)

Written 2026-11-22 at the owner's request, after the first design's known-answer check missed.
Research and design only: nothing here was run on the Book of Mormon, no AI judge was called,
and the Book of Mormon figures quoted come from the 2026-11-21 run already on file
(`data/lab/translation/result.json`). Feasibility counts below were taken on control texts
only (Bibles, imitations, spoken English), in minutes, with throwaway scripts kept outside the
repository. They are raw pattern counts with no check on precision, so treat them as leads.

## The claim and where it comes from

Two claims, one strong and one narrow.

- **Tvedtnes** (1970, *BYU Studies*; 1991, chapter 8 of *Rediscovering the Book of Mormon*)
  lists about a dozen kinds of "Hebraism" in the English text: the construct state ("plates of
  brass", "rod of iron"), "with" or "in" plus a noun for an adverb ("with joy"), cognate
  verb-and-noun pairs ("dreamed a dream"), compound prepositions ("by the hand of"), heavy use of
  "and", "and" where English wants "but", "because that" and "after that", displaced relative
  clauses, extraposition ("saw the light, that it was good"), repeated possessives. His case is
  made by examples. It has one count: "land of promise" 22 times against "promised land" 10.
  He argues that these show the English "reflects the Hebrew words and word order of the
  original".
- **Parry** (2002, in *Echoes and Evidences*) repeats most of these. He adds two general claims
  that can be tested. (1) The if-and conditional ("if ye shall ask ..., and he will manifest")
  is "common in the Hebrew Bible" but "never appears in any biblical translation into English".
  He lists eleven Hebrew cases in Genesis. (2) These forms are "generally uncommon in, if not
  altogether foreign to, the English of Joseph Smith's day".
- **Skousen** (1997 and 1998, cited by Parry) found fourteen if-and conditionals in the
  manuscripts. Most were printed in 1830 and edited out in 1837 (Helaman 12:13-21 seven times,
  Moroni 10:4, 1 Nephi 17:50, and others).
- **The reply** is that these are King James English, copied by a writer steeped in the Bible,
  as many pre-1830 American imitators did. A critical blog post at the Interpreter Foundation
  (author not confirmed) adds two points. The manuscript has about 39 if-then conditionals beside
  the 14 if-and. And the if-and turns up elsewhere in Joseph Smith's own language.

**If the strong claim is right**, the text should carry Hebrew interference that copying the
King James surface would not supply. **If the reply is right**, every Hebrew-looking feature
should be one the King James Bible already has, at rates an imitator could reach, or should
also appear in Joseph Smith's other dictations or in ordinary spoken English.

## Replicating their approach

The owner asked that every test first redo the original authors' own approach, then ours.

| Author | What they did | Data and numbers | Can we redo it? | Done? |
| --- | --- | --- | --- | --- |
| Tvedtnes 1970, 1991 | Gave examples by category, with verse references. No control texts. | About 60 cited verses; one count: "land of promise" 22, "promised land" 10 | Yes. We hold the 1830 text and the manuscripts. We can check that each cited verse says what he quotes, and redo the 22-to-10 count. | No. Part B counted rule-based versions of his categories, not his cited verses. |
| Parry 2002 | Examples, plus two general claims (above) | Eleven Genesis if-and cases in Hebrew; no counts in English texts | Claim (1) yes: we read his Genesis verses in every English Bible we hold or can fetch. Claim (2) yes: spoken and written English of 1780-1830 is held. | Partly, as a feasibility check below: King James and Ainsworth for the Genesis verses. |
| Skousen | Compared the manuscripts with the printed editions and counted if-and cases | 14 in the manuscripts; most printed in 1830 and removed in 1837 | Yes. We hold the Joseph Smith Papers transcripts of both manuscripts (private) and the 1830 text. His own list is in his *Analysis of Textual Variants*, which we do not hold. The verses are named in the open summaries. | No. |

This is mostly an argument by examples, with no method to rerun. The closest faithful
replication has three steps: (a) confirm that each cited instance is in the 1830 text (or the
manuscript) and reads as quoted; (b) redo their few counts (22 to 10; Skousen's 14; the critic's
about 39 if-then); (c) add the control they lack by counting the same instances' patterns in the
King James Bible, the imitations, and period English. Step 1 of the design below is (a) and (b).
Part B of the first run was in effect (c) for seven categories.

## What we did and how it failed

**Part A** trained a classifier on function words and sentence shape. It used 695 books the
catalogue marks as translations into English and 1,387 English originals, 1700-1830. On held-out
authors it scored AUC 0.876 (0.88 means it ranks a random translation above a random original
88 times in 100). Its known-answer check also required two things at once: call the King James
Bible, Sale's Koran and Whiston's Josephus translations, and call at least half of eleven
Bible-style imitations not translations. No version did both. In the version as written, *The
Late War* (1816) scored 0.75 and the King James Bible 0.62. The Book of Mormon was not scored.

**Part B** counted ten claimed constructions per 10,000 words. Seven passed a check (at least
twice as common in the King James Old Testament as in period prose). English imitators reach the
Book of Mormon's rate on four of the seven. Translations from Hebrew other than the King James
Bible show almost none of the seven.

## What the failure says

**About the published claims (a).**

- The lists have no control group. Apart from the 22-to-10 count, none of the three authors
  counted anything in the King James Bible, in imitators, or in period English. Part B supplied
  that control for seven categories. Four are reached by imitators, so they cannot separate the
  two explanations.
- The seven are not marks of Hebrew as such. They are marks of the *English Bible tradition*. In
  Part B, nine other translations from Hebrew show them at one tenth of the King James rate or
  less. A feasibility count adds a sharper case. Henry Ainsworth's 1627 Pentateuch and Psalms,
  the most literal English version of the period, renders the Hebrew *wayhi* as "and it was".
  So it has "came to pass" 0.3 times per 10,000 words, against 7.0 in the King James Bible.
  "It came to pass" is Tyndale's and the King James translators' choice of English, not the shape
  of the Hebrew.
- Parry's claim (1) holds on the cases checked. The King James Bible renders his Genesis if-and
  cases with "then" or with nothing (Genesis 18:26, 24:8, 31:8, 34:17, 44:26, 47:6 all read
  "then"). So does Ainsworth (18:26, 24:8, 31:8 read). That makes the if-and a construction the
  English Bible tradition *removed*. That is exactly the kind of feature that could separate
  translation from imitation. But Part B's check ("at least twice the King James rate") threw it
  out, because the check was built to need King James support.
- Parry's claim (2) is open to doubt. A strict pattern search of Old Bailey courtroom testimony
  (1780-1830, 12.7 million words) finds 43 candidates of the shape "if ..., and I will". Several
  look like genuine spoken if-and sentences ("if you like, and I will ..."). Others are indirect
  questions. None has been hand-checked. If even a few are genuine, the form was not wholly
  foreign to spoken English of the time. What matters then is the rate, not mere presence.

**About our instrument only (b).**

- Part A asked a question the research says has no source-free answer. Translation studies find
  that much of what marks a translation is interference from its particular source language.
  Translations from different languages are "dialects" of translationese (Koppel and Ordan
  2011), and the source language can be recovered from them (van Halteren 2008; Rabinovich,
  Ordan and Wintner 2017). Our translated class was French 229, German 86, Latin 47, Greek 35,
  and *one* book from Hebrew and three from Arabic. At best it could learn "reads like it came
  from French or Latin". It could never learn "came from Hebrew". The failure is ours, not the
  claimants'.
- The originals held no King James-register English (Bible-style books and scripture titles were
  kept out). So "biblical register" fell on the translated side. That is why *The Late War* scored
  high.
- Part B's rule check (King James Old Testament at least twice period prose) cannot keep a
  feature the King James Bible suppressed. It dropped the if-and (1.0x) and the resumptive
  pronoun (0.9x) for that reason. Yet those are the features that could discriminate.
- The if-and pattern was imprecise. Of its 19 hits in the King James Bible, most of those read
  are "if X, Y, and Z" sentences: a normal apodosis followed by a second clause joined by "and".
  They are not if-and conditionals. The Koran's 17 hits are mostly the same.
- The other Hebrew translations were counted with their English notes and prefaces, which dilute
  them.

**What stays unknown (c).** Whether the Book of Mormon carries Hebrew constructions that the King
James Bible removed, at rates above imitators, spoken English and Joseph Smith's other
dictations. Whether such interference would survive at all through a translator who wrote in
King James style: Noah's 1840 *Book of Jasher*, a real translation from Hebrew in King James
style, is the natural test. And what the overuse of "came to pass" (6.8 times the Old Testament)
means.

## Angles considered

1. **Translated or not, repaired.** Add King James-register English (scripture-heavy sermons,
   the imitations) to the originals and retrain. *Rejected as the main design.* It is still the
   wrong question. A source-blind detector trained on French, German and Latin translations says
   nothing about a Hebrew or Egyptian source, and we hold almost no Hebrew-source books outside
   the Bible to train on.
2. **Which source language does the interference point to?** Train on translations labelled by
   source language and ask where the Book of Mormon falls. The cleanest form uses Bible versions
   as parallel text: same content, different immediate source. The King James Bible is from
   Hebrew; the Douay-Rheims and Challoner are from Latin (of the Hebrew); Thomson 1808 is from
   Greek (the Septuagint); the New Testaments are from Greek. *Kept as a secondary check only.*
   The Hebrew-source class is almost entirely Old Testament. Imitators copy the Old Testament.
   So the classifier would likely learn "Old Testament register" again, and imitations would
   land on the Hebrew side. It can run only if the imitations fall on the non-Hebrew side first.
3. **Leaks the King James Bible did not have (chosen).** Interference that imitating the King
   James surface cannot supply: Hebrew constructions the King James translators regularly
   rendered away, which a literal translator from Hebrew keeps. This asks directly whether it is
   "King James English produced by imitation or by translation", and it uses the controls we
   hold. The test is not "is the Book of Mormon Hebrew-like" but "does it have Hebrew features
   that its English model lacks".
4. **Salience.** People imitating a variety overuse its noticeable markers and miss or misuse
   the unnoticed ones (Trudgill 1986 on salience; hypercorrection). Imitators would then overshoot
   on "came to pass" and "behold" and make agreement slips with thou/ye and -eth/-est. *Reported,
   not gating.* A translator who adopted a fixed formula would also overshoot, so overuse alone
   does not decide anything.
5. **Pseudo-translations as decoys.** Books presented as translations with no source (Toury 1995;
   Large 2018): Macpherson's *Ossian*, Walpole's *Castle of Otranto* (presented as from the
   Italian), Ilive's *Book of Jasher* (1751), Psalmanazar's *Formosa*, O'Connor's *Chronicles of
   Eri*. They copy the features readers notice as "translated". *Used in the known-answer check.*
   All are held.

## The proposed design

**Question.** Does the 1830 text use Hebrew constructions that the King James translators
regularly rendered away (so copying the King James Bible would not supply them) more than Bible
imitators, pseudo-translations, spoken English of the period and Joseph Smith's other dictations
do, and as much as literal translations from Hebrew do?

**Step 1. Reproduce their result their way** (see "Replicating their approach"). Check each of
Tvedtnes's and Parry's cited verses in the 1830 text and the manuscripts. Recount "land of
promise" against "promised land". Find Skousen's 14 if-and cases and the critic's if-then cases
in the manuscript transcripts. Report agreement or disagreement with their numbers before
anything else.

**Step 2. Build the inventory from the Hebrew, not from the English.** Take every construction
on the claimed lists, plus a few Hebrew features no one claimed (calibration, below). For each,
find instances in the Hebrew Bible. Use Open Scriptures Hebrew Bible lemma and morphology where a
rule can find them: infinitive absolute with a finite verb of the same root; cognate verb and
noun; construct chains with a material noun; a conditional particle followed by an apodosis
opening with *waw*. Use Parry's eleven Genesis cases as a seed. Read each instance's King James
verse (aligned by reference). **Retention** is the share of instances where the King James Bible
keeps the literal English shape. Sample up to `retention_sample` instances per construction.
Score by rule where possible, otherwise by the paced AI judge (simulated judging, labelled so),
with `retention_hand` hand-checked. A construction with retention at most `suppressed_max` is
**suppressed**. One at least `carried_max` is **carried** and is reported only, since Part B
already showed carried features cannot discriminate. Cognates are split into pairs the King
James Bible has and pairs it never has.

**Calibration features.** The claimed lists were drawn up by people reading the Book of Mormon,
so they are picked to fit it. A real translator from Hebrew would also leak suppressed features
that nobody claimed. The clearest is the doubled verb ("dying thou shalt die", "returning return",
"blessing I will bless"). The design reports the whole profile: claimed and unclaimed suppressed
features side by side. A text that shows only the picked items and none of the unpicked ones does
not look like general interference from Hebrew.

**Step 3. Measure.** For each suppressed feature, a high-recall finder (pattern plus spaCy parse)
proposes candidates in every text. Each candidate is checked by the AI judge against a fixed
definition with worked examples. A hand check of `precision_hand` candidates per feature
measures precision. A feature below `precision_bar` is dropped and named. Report rates per 10,000
words with exact Poisson intervals, in units of `unit_words` words. Book of Mormon King James
passages are masked.

**Texts.**

| Group | Texts | Held? |
| --- | --- | --- |
| Literal translations from Hebrew (known yes) | Ainsworth 1627 (TCP; translation lines separated from notes); Young's Literal 1862, Old Testament; Noah's *Book of Jasher* 1840 (non-biblical Hebrew narrative, King James-style translator: the hard positive); Lowth, Blayney, Horsley and others with notes stripped | Ainsworth and the nine yes; Young and Jasher to fetch |
| Semitic analogue | Sale's Koran 1734 (Arabic) | yes |
| Translations from other sources | Douay-Rheims 1609-10 (TCP), Challoner 1821 (Latin); Thomson 1808 (Greek Septuagint); secular French, German, Latin, Greek sample | yes, except Thomson (library record, no text) |
| The King James Bible | Old and New Testaments | yes |
| Imitations (known no) | the 14 Bible-style books | yes |
| Pseudo-translations (hard decoys) | *Ossian* (1819 ed.), *Otranto*, Ilive's *Jasher*, Psalmanazar's *Formosa*, *Chronicles of Eri* | yes |
| English baselines | period prose (300 works); Old Bailey testimony 1780-1830 (spoken); Early Modern English prose 1550-1650 from TCP (the Early Modern English explanation, Carmack) | yes |
| Joseph Smith's other texts | revelations 1828-31, Book of Moses, Book of Abraham (dictated); letters and history (his own English) | yes (private) |
| Target | 1830 Book of Mormon, King James passages masked; also the manuscripts for the if-and | yes |

## Known-answer check

All bars are fixed on the card before any Book of Mormon count.

- **K1, the inventory is real.** Every kept feature has King James retention at most
  `suppressed_max`. At least one literal Hebrew translation (Ainsworth or Young) shows it at or
  above `literal_ratio` times the King James Old Testament rate, with non-overlapping 95%
  intervals. Feasibility, raw and unchecked: the doubled verb runs 1.51 per 10,000 words in
  Ainsworth against 0.17 in the King James Bible (about 9x), 0.59 in Douay 1656, 0.19 in
  Challoner, 0.02 in the Koran, and 0 in 445,000 words of imitations.
- **K2, imitation does not supply it.** The imitations pooled, and each pseudo-translation with at
  least `min_words` words, stay at or below `floor_ratio` times the King James Old Testament rate
  on the composite. **The hard decoy is *The Late War***, which the first design scored as more
  of a translation than the King James Bible. It must sit at the floor. *Ossian*, the most famous
  pseudo-translation, must too.
- **K3, precision.** At least `precision_bar` on the hand check, per feature.
- **K4, separation.** On units of `unit_words` words, a composite (sum of suppressed-feature
  rates, each scaled by its King James Old Testament rate) ranks literal Hebrew translation units
  above imitation and pseudo-translation units with AUC at least `auc_bar`.
- **Hard positive, reported, not gating:** Noah's 1840 *Jasher*. If it falls at the floor, then a
  King James-style translator from Hebrew also removes these features. A Book of Mormon at the
  floor would then not count against translation. The write-up must say so.

If K1 to K4 are not all met, the Book of Mormon is not scored. The secondary source-language
check (angle 2) runs only if the imitations fall on the non-Hebrew side on held-out data.

## What each outcome would mean

- **Within the imitation and King James range** on the suppressed features (interval overlaps
  the floor): no sign of Hebrew interference beyond King James English. This fits imitation. It
  does not rule out a translator who smoothed the text as the King James translators did, and
  the Jasher result says how much that matters.
- **Above the imitations, spoken English, Early Modern English prose and Joseph Smith's own
  letters, and in the literal-translation range, on several features including unclaimed
  ones:** the text has Hebrew-shaped constructions that the King James surface does not supply.
  Dictation style and the dictator's own idiolect remain to be weighed through the Joseph Smith
  control.
- **High, but Joseph Smith's other dictations equally high:** the features go with the dictator,
  not with a source specific to this book. That is the critic's point, now measured.
- **Only the if-and is high, nothing else:** cannot tell. A single construction with about 14
  cases is a lead, not a profile.
- **Too few candidates in the controls to set the floor:** cannot tell.

## Risks

- **Rarity.** About 14 if-and cases in roughly 270,000 words. Intervals will be wide. The design
  leans on the profile across features for that reason.
- **Speech.** Run-on "if ..., and" occurs in courtroom speech. A dictated text may share it. Old
  Bailey testimony and Joseph Smith's dictations are the controls, but the Old Bailey was taken
  down in shorthand and edited, so it may smooth such forms away.
- **Marginal notes.** Many Bibles printed the 1611 translators' margin notes ("Heb. dying thou
  shalt die"). An imitator with such a Bible could copy a suppressed Hebraism from the margin.
  Check whether each Book of Mormon instance matches a King James margin note: we need a 1611
  text with margins (look in TCP first).
- **Ainsworth's notes.** The translation is interleaved with long commentary that quotes rabbis.
  The translation lines must be split out, or the commentary's own English will dilute or
  inflate the rates.
- **Judge error.** AI judging is simulated and can be wrong. It is bounded by the hand check, and
  a feature that fails precision is dropped.
- **The Hebrew side.** Automatic detection of the *waw* apodosis in the Hebrew is imperfect.
  Parry's eleven cases plus a judged sample bound the retention estimate. The ETCBC database has
  clause labels if needed (CC BY-NC 4.0).
- **Picked features.** Handled by the calibration features. Even so, the claimed list will
  dominate the inventory.
- **OCR.** The Challoner, Thomson and Jasher texts are scans. The Ainsworth and Douay 1656 texts
  are hand-keyed (TCP), but in old spelling ("yf", "-eth" forms). The finders need old-spelling
  variants.

**Cost.** Mac only, no GPU, no paid calls. Fetching and parsing: under an hour. Inventory: about
15 constructions × 100 Hebrew instances, roughly 1,500 judge questions (about 5 hours at 300 an
hour). Verification: a few thousand candidates across all texts (about 8 to 12 hours of judging).
Hand checks: about 15 features × 50. Building: a day of code.

## Sources (URLs)

Claims and replies:
- Tvedtnes 1991, "The Hebrew Background of the Book of Mormon", *Rediscovering the Book of
  Mormon*, ch. 8 (held privately; Book of Mormon Central archive): http://bookofmormoncentral.org/
- Tvedtnes 1970, "Hebraisms in the Book of Mormon", *BYU Studies* (held privately).
- Parry 2002, "Hebraisms and Other Ancient Peculiarities in the Book of Mormon", in *Echoes and
  Evidences of the Book of Mormon* (held privately); the conditional section summarised at
  https://fairlatterdaysaints.org/evidences/Source:Echoes:Ch2:20:Hebrew_conditional_sentences
- Skousen, "Hebraic Conditionals in the Book of Mormon", *Pressing Forward with the Book of Mormon*
  (FARMS 1999) 201-3 (not held); summaries at https://rsc.byu.edu/preserved-translation/conditional-clauses
  and https://scholarsarchive.byu.edu/insights/vol17/iss6/3
- FAIR summary of the if-and cases: https://www.fairlatterdaysaints.org/answers/Book_of_Mormon/Evidences/Hebraisms/If-and_conditionals
- "Silk or Sow's Ear: The Apologetic Use of the If-and Construction", Interpreter Foundation blog
  (author not confirmed; the print page returned 404 on 2026-11-22): https://interpreterfoundation.org/?p=13472
- Carmack 2018, Early Modern English argument: https://scholarsarchive.byu.edu/interpreter/vol28/iss1/14
- Carmack 2021, list of Bible-style imitations: https://scholarsarchive.byu.edu/interpreter/vol49/iss1/5

Translationese and source-language identification:
- Koppel and Ordan 2011, "Translationese and Its Dialects": https://aclanthology.org/P11-1132/
- Rabinovich, Ordan and Wintner 2017: https://aclanthology.org/P17-1049/
- Rabinovich and Wintner 2015: https://aclanthology.org/Q15-1030/
- Volansky, Ordan and Wintner 2015, "On the features of translationese", *LLC* 30(1), DOI
  10.1093/llc/fqt031 (paywalled; thesis version https://cs.haifa.ac.il/~shuly/publications/vered-thesis.pdf)
- Baroni and Bernardini 2006, DOI 10.1093/llc/fqi039 (paywalled, not read)
- Pylypenko and others 2021: https://aclanthology.org/2021.emnlp-main.676/
- Amponsah-Kaakyire and others 2022: https://arxiv.org/abs/2210.13391
- van Halteren 2008 (cited through Koppel and Ordan; not read).

Pseudo-translation and salience:
- Toury 1995, *Descriptive Translation Studies and Beyond*, ch. on pseudotranslation (print).
- Large 2018, "What remains: pseudotranslation as salvage": https://research-portal.uea.ac.uk/en/publications/what-remains-pseudotranslation-as-salvage/
- Overview: https://en.wikipedia.org/wiki/Pseudotranslation
- Trudgill 1986, *Dialects in Contact* (print), on salience in accommodation.

Data to fetch (all open):
- Open Scriptures Hebrew Bible (WLC text with lemma and morphology, CC BY 4.0): https://github.com/openscriptures/morphhb
- ETCBC BHSA (clause labels, CC BY-NC 4.0), only if needed: https://github.com/ETCBC/bhsa
- Young's Literal Translation, 1862 text (public domain): https://sacred-texts.com/bib/ylt/index.htm
  (ebible.org's files are the 1898 revision: https://ebible.org/details.php?id=engylt)
- *The Book of Jasher*, New York 1840 (Noah and Gould; public domain): https://archive.org/details/bookofjasherrefe00sefe
- Thomson's Bible 1808 (public domain): library record `internet_archive:holybiblecontain01thom`
  (no text in our library); fetch the OCR from https://archive.org/details/holybiblecontain01thom

Held and used in feasibility: King James Bible (`data/kjv/kjv.jsonl`); Ainsworth 1627
(`tcp:A11649`); Douay 1609-10 in the 1656 printing (`tcp:A11777`); Challoner 1821
(`internet_archive:holybibletransla00chalrich`); Sale's Koran
(`data/corpus/lab/sources/names/koran_sale.txt`); the imitations (`lab.translation.imitations`);
*Ossian* (`institutional_books:HXQ93I`); Ilive's *Jasher* (`internet_archive:bookofjasherwith00iliv`);
*Otranto* (`internet_archive:10750813bsb`); Psalmanazar (`tcp:K010899.000`); Old Bailey Corpus 2.0
testimony through `lab.spoken`.

## Feasibility counts (controls only, raw patterns, precision unchecked)

| Text | Words | Doubled verb /10k | If-and, loose pattern /10k | "Came to pass" /10k |
| --- | --- | --- | --- | --- |
| King James Bible | 934,226 | 0.17 | 0.20 (19 hits, mostly false) | 7.0 |
| Ainsworth 1627 (with notes) | 1,142,703 | 1.51 | 0.10 | 0.30 |
| Douay 1656 | 1,075,132 | 0.59 | 0.28 | 1.65 |
| Challoner 1821 | 1,013,254 | 0.19 | 0.20 | 2.64 |
| Sale's Koran | 420,405 | 0.02 | 0.40 | 0.43 |
| Imitations pooled | 445,210 | 0 | 0.09 | 8.8 |
| *Ossian* 1819 | 166,568 | n/a | 0 | 0 |
| Ilive's *Jasher* | 37,900 | n/a | 0 | 17.4 |
| Old Bailey testimony | 12,727,877 | n/a | 0.09 (43 strict candidates; some look genuine) | n/a |

Library labels: of the 695 catalogued translations in Part A, one is marked from Hebrew and three
from Arabic. Hebrew-source training data outside the Bible essentially does not exist in our
labelled set. That alone rules out angle 1.
