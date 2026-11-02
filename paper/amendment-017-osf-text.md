# Amendment 17: the linguistic dating classifier

*Filed 2026-11-01. Evidence: `docs/dating-plan.md`, `dating/features.py`.*

---

**Amendment 17, filed 2026-11-01, before the dating classifier is fitted or any validation text is
scored.** It fixes the details of 5.3 that Amendment 2 left open, and publishes the grammatical
feature list Amendment 2 requires before the benchmark. No hypothesis, decision rule or threshold
of section 6 changes.

**Text read.** MorphAdorner's standard spellings, registered for pre-1700 text, replace
grammatical forms as well as spellings (doth to does 1.27 million times, ye to you, saith to says,
maketh to makes), while later text keeps them as printed. So the grammar model reads the printed
text through one orthographic fold applied to every date (lower case, long s and ligatures, u/v
and i/j merged), which changes letters, never words. The lexical model reads the registered
normalised text, with every word the grammar model reads, and every standard spelling substituted
for a grammatical form, removed.

**Grammatical features.** 61 rates per 1,000 tokens, closed word lists and short word patterns, no
tagger, drawn from Nevalainen and Raumolin-Brunberg (2003), Ellegård (1953), Kytö (1991, 1997),
Rissanen (1999), Lass (1999), Barber (1997), Görlach (1991), Busse (2002), Österman (1997) and
Arnaud (1998): third-person -th and -s forms, second-person verb forms, thou/thee/thy/thine/ye/you,
mine/my before vowels, its, pronominal adverbs, do with and without negation, lexical verb plus
not, contractions, be- and have-perfects of mutative verbs, the progressive, modals, subjunctive
be, relativizers (which, who, whom, whose, that, the which) and function-word forms (unto, upon,
whilst, betwixt, ere, an before h). The list is in `dating/features.py`; none is selected on
performance.

**Data.** Every eligible dated volume from 1473 to 1830 (corrected years), less Bibles, the Book of
Mormon's copies and contamination hits, the pseudo-biblical controls, and every text a later test
scores (benchmark authors, candidates, known-answer texts): 256,655 volumes. Bins: 1473-1529, then
decades to 1820-1830 (31). 20% of authors held out by seeded hash. Per bin, up to 1,500 training
and 375 validation volumes, each giving up to two 2,000-token segments at seeded positions (not
the first or last of four or more), used only if at least 20% of tokens are function words.

**Models.** For each feature set, L2-regularised multinomial logistic regression on standardised
log(1 + rate), the penalty chosen from 0.01, 0.1, 1 and 10 by 5-fold author-grouped
cross-validation; lexical vocabulary the 5,000 most document-frequent training words. A segment's
median year and 90% interval read off its bin probabilities, uniform within bins. The grammar model
decides 6.4 and H3; the lexical model and the transformer cross-check are reported beside it.

**Validation.** Held-out authors (error, interval coverage, 6.4's window rule on 1780-1830 and on
earlier text); keyed against OCR volumes of 1780-1809; King James imitation (the pseudo-biblical
primary controls, King James spans removed, against held-out ordinary 1780-1830 volumes, 10,000
permutations; and the King James text); Amendment 9's separation, scoring each text by its median
predicted year minus its printing year.
