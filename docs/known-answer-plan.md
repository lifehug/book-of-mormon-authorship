# Known-answer controls: the plan, written before any test runs on them (BOM-61)

Committed 2026-10-31, before any borrowing, dating, language-model or style test has been run on
these texts (none of those tests exists yet). No Book of Mormon text is used.

## The question

The Book of Mormon presents itself as an English translation of an ancient record. Phases 4 to 6
measure what its English draws on: wording, stories, vocabulary, themes, period. A result bears
on the translation question only if the test can tell, on texts whose answer is known,

- **(a) a genuine English translation, made in the period, of a text composed in antiquity**, from
- **(b) a composition of its own century presented as a translation or transcription of an old
  record.**

Both kinds are written in period English by period writers, so a test that only detects period
English will put both on the same side. That is the failure this plan exists to catch.

## The set

`eval/known_answer.py` (`SET`) lists every text, its edition and volumes, why it is in, and the
scholarly consensus; `python -m eval.known_answer build` writes `data/known_answer/set.jsonl`.

**Primary set, which decides whether a test separates the groups:**

| Group | Texts |
| --- | --- |
| Genuine translations (9) | *Testaments of the Twelve Patriarchs* (1791); Laurence's *Book of Enoch* (1821); Hone's *Apocryphal New Testament* (1820); Whiston's Josephus (1794); Sale's Koran (1800); Beloe's Herodotus (1791); Pope's Homer (1783); Elton's Hesiod (1815); Jones's *Sacontala* (1792) |
| Presented as ancient (3) | Macpherson's *Ossian* (1800); Chatterton's "Rowley" poems (1794); Ilive's *Book of Jasher* (1751, the 1829 reprint) |

**Secondary set, reported but not part of the verdict:** W. H. Ireland's Shakespeare papers (1796)
and Walpole's *Castle of Otranto* (1782). Both were presented as old records, but neither as
ancient, and *Otranto* was acknowledged as fiction within a year.

**How it was chosen.** The genuine group leans toward the Book of Mormon's register: three
biblical-register texts outside the King James Bible, Josephus's retelling of biblical history,
and a scripture claiming revelation (the Koran), with classical history and verse beside them.
The Apocrypha was considered and left out: the registered King James mask (4.4) covers the
Apocrypha, so masking would remove most of its text. Left out of the presented-as-ancient group:
Psalmanazar's *Formosa* (1704, before the period, and not presented as ancient); Spalding's
*Manuscript Found* (a candidate in this study, so it cannot also be a control); and openly
imitative works such as *The Late War*, which do not claim to be ancient (they are the
pseudo-biblical controls of Amendment 6).

**Known weaknesses, stated now.**

- **Three texts is a small group.** Few modern texts were presented as ancient in English in this
  period, and the corpus holds the three best-known. A test can show it separates *these* texts,
  not that it separates every such text.
- **Rowley is written in invented 15th-century spelling** (about 60% of its tokens are ordinary
  words, against 87-99% for every other primary text). A word-based test may separate it for
  that reason alone. Every test therefore also reports its scores with Rowley left out; see the
  rule below for how that is used.
- **Editions carry their editors' apparatus** (Whiston's dissertations, Sale's Preliminary
  Discourse, Beloe's notes, Ilive's invented testimonies). Volumes are used whole, as the
  Book of Mormon is. Modern apparatus in a genuine translation makes it look more modern, which
  works against separation, so it cannot make a test look better than it is.
- **The corpus holds two of Beloe's volumes of Herodotus**, not all of them.

## Processing

Exactly as the Book of Mormon is processed for the test in question: the same normalisation, the
same King James mask (4.4; the controls are masked with the registered settings before any test
reads them), the same sample sizes and chunking, the same null and the same exclusions. A test
that excludes the Book of Mormon's own copies from document frequencies excludes each control's
own copies the same way.

## The rule for "this test separates the groups"

1. **Before a test runs on the set**, its issue commits a line to the table below: the score it
   gives each text (one number per text; where the test scores chunks, the mean over chunks) and
   which direction means "draws on its own time". Once the line is committed it is not changed.
2. **Separation** is the one-sided Mann-Whitney statistic of the 3 presented-as-ancient texts
   against the 9 genuine ones in the declared direction, with its exact permutation p-value over
   all 220 ways of choosing 3 texts of 12. **A test separates the groups when p <= 0.01**
   (`known_answer.separation_p_provisional`). With 3 against 9 that allows at most one of the 27
   genuine/presented pairs to fall the wrong way.
3. **Rowley.** If the test separates only with Rowley in (fails with Rowley's score set to the
   genuine median), the result is reported as "separates, possibly on spelling alone", and the
   test's Book of Mormon result carries that caveat.
4. **What follows.** A test that separates the groups is reported with its Book of Mormon result
   read in the declared direction. A test that does not is reported as **uninformative on the
   translation question**, whatever it says about the Book of Mormon; its result may still bear
   on other questions (which candidate is closest, which source is borrowed), and the report says
   which.
5. **Order.** Each test's known-answer result is published before its Book of Mormon result is
   interpreted; the two may come from one run, but the known-answer line is written up first.
6. Every score for every text, primary and secondary, is published.

## The tests and their scores

Filled in at each test's issue, before it runs on the set. The expected direction is noted now so
it cannot drift.

| Test | Issue | Score per text | "Its own time" means | Committed |
| --- | --- | --- | --- | --- |
| Exact text reuse | BOM-23 | share of the text aligned to period works other than its own copies and the King James Bible | higher | - |
| Rare phrases | BOM-24 | the strongest period source's rare shared 4-grams per 10,000 words, by text | higher | - |
| Semantic and story parallels | BOM-25 | strongest period source's parallel score | higher | - |
| King James italics | BOM-62 | share of the KJV's italic (added) words reproduced where the text runs parallel to the KJV | higher | - |
| Period-only language model | BOM-27, 28 | to be set at BOM-27 | to be set | - |
| Linguistic dating | BOM-29 | predicted composition date | later | - |
| Thematic dating | BOM-63 | to be set at BOM-63 | to be set | - |

## Registration

The set and the rule above are not yet registered (`pending_amendment`: `known_answer.design`).
They are fixed here before any test runs on the set, and an amendment registers them before any
test's Book of Mormon result is interpreted.
