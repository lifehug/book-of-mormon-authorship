# Amendment 6: corpus preparation choices, and a curated pseudo-biblical control

*Filed and approved 2026-10-27, OSF revision `6ae16f4142a77759f3e18539`. Evidence in the SOURCES.md files of `data/catalog`, `data/ocr_quality`, `data/normalization`, `data/kjv_mask` and `data/controls`; owner decisions recorded in BOM-54.*

---

**Amendment 6, 2026-10-27, before any calibration or Book of Mormon scoring.** The Book of Mormon
text remains sealed under 4.2 until BOM-32 (its KJV masking and segmentation are the operations
4.4 and 4.5 register, and no feature of it has been computed); no method has been calibrated and
no candidate scored. No hypothesis, decision rule or threshold of section 6 changes.

**What prompted this.** Building the corpus (stages BOM-12 to BOM-19) required choices the
registration leaves open, and showed that one registered rule, Amendment 3's either-label
matching, does not produce the control it was meant to for pseudo-biblical texts. Each is
registered here before it can affect a Book of Mormon result. Every value below is in the
project's configuration file and is stamped on every output.

**Change 1: a curated pseudo-biblical control.** Applied to the pseudo-biblical set, Amendment 3
admits 3,727 volumes, most of them commentary and religious prose *about* scripture rather than
text written in imitation of it; such a set would let biblical style alone separate the Book of
Mormon from its control. The confirmatory pseudo-biblical set is instead chosen by this
procedure, fixed now and run before any scoring:

- *Candidates:* works 1780-1830 whose primary genre label is pseudo-biblical, the four works
  section 3 names and their editions, and works scoring high on published KJV-style markers
  ("and it came to pass", -eth and -est verb forms, thee/thou/ye, chapter-and-verse numbering),
  excluding works whose text is mostly verbatim KJV (4.4's masks).
- *Judgement:* each candidate is judged from its title and several passages of its text against
  a written rule sheet (in: sustained KJV diction and narrative frame presented as new text; out:
  biblical commentary, sermons quoting scripture, paraphrase editions of the Bible, hymns), by two
  language models of different families independently, disagreements to a third. This is a
  simulated judgement under Amendment 1 and is labelled as such; every decision and reason is
  published.
- *Known-answer gate:* the procedure is used only if every edition of the four named works is
  admitted and a published set of commentaries and sermons is rejected.
- *Thresholds* for the markers are a selection procedure in the sense of Amendment 2: chosen on
  the named works and the rejection set only, published with the list before the benchmark runs.
- Cross-source copies of a work count once. The list and its SHA-256 are published before the
  benchmark runs. The either-label set (Amendment 3) and the primary-label set are reported as
  sensitivity analyses. Amendment 3 is unchanged for every other control set.

**Change 2: control pools sampled.** The history and general-prose pools (about 40,000 and
340,000 volumes, some 20 billion words) are drawn down to 3,000 and 5,000 volumes by a sample
seeded with the registered seed and stratified by source and decade in proportion, so that every
member can be KJV-masked under 4.4. Amendment 2's draws of 100 imposters per trial are unaffected.

**Change 3: the 4.2 contamination check.** Read literally, "a 12-token string shared with the
Book of Mormon" includes the KJV chapters the Book of Mormon reproduces, and flags thousands of
sermons that quote Isaiah. The check uses 12-token strings from the Book of Mormon's original
spans (outside 4.4's KJV masks) that do not occur in the KJV, and a volume is contaminated when
it shares at least 20 distinct such strings. Measured: no control-pool volume shares more than
9; the six copies of the Book of Mormon in the corpus share 109,011 to 174,655. Copies identified
by title are excluded regardless.

**Change 4: OCR cleaning and the period lexicon.** 4.3's cleaning is rule-based and its
thresholds are registered as implemented: long s read as f is repaired when the s-form occurs in
at least 100 times as many hand-keyed texts as the form as read; running headers are lines in the
top or bottom two lines of a page, of at least six letters, recurring there on at least three
pages and 5% of pages; newspaper single pages skip header removal. The word list consulted is
Webster's dictionary plus every word in at least two hand-keyed TCP texts dated 1700 or later.
Text delivered with words broken into letters (one newspaper source) is re-segmented by a
dictionary segmenter, keeping a split only where it raises the share of letters in known words.
An LLM correction pass was tested and is not used: it improved the median error but inserted text.

**Change 5: spelling, 1700-1779.** The registration names regimes before 1700 and from 1780 and
is silent between. Text printed 1700-1779 receives the artifact-only regime (long s and
ligatures), the reading that changes least.

**Change 6: MorphAdorner's standard spellings.** The pre-1700 regime is MorphAdorner 2.0.1's Early
Modern English adorner, run as distributed (part-of-speech tagging, then standard spelling). Three
of its mappings replace a word with a different word rather than a spelling with a spelling: the
article *an* to *and* (3.28 million tokens across 53,486 texts), *whether* to *whither* (571,000)
and *fall* to *fallen* (345,000). These three keep their printed form; every other MorphAdorner
standard spelling is applied as produced. MorphAdorner's unaltered output is kept and reported
alongside.

**Change 7: passim implementation details.** Under Amendment 2's registered settings: passim's own
minimum alignment, counted in characters, is set to 20 so that the registered eight-token
minimum, enforced on tokens, decides; the document-frequency cap stays at passim's default of
100; the relative overlap of 0.5 applies to source and target alike; a span must contain an
unbroken run of matching tokens at least as long as the n-gram order. Texts are aligned in batches
of about 720,000 words; a text over 150,000 words is aligned as pieces of that length overlapping
by 500 words, with spans mapped back to the whole text, and a batch that cannot complete is
aligned again with each text cut into thirds, at most twice (listed in the masking report). No
Book of Mormon or candidate text is long enough to be cut.

**Change 8: genre reliability, as run.** Amendment 4's second pass uses Claude Sonnet (a different
family from pass 1's Llama 3.1 8B). The perturbation test is first run at a worst-case bound taken
from measured inter-model disagreement (28% on model-decided records, 3% on rule-decided), with
the confusion drawn from observed pass-1/pass-2 disagreements; the hand-adjudicated sample
Amendment 4 names is drawn only if a genre-dependent conclusion moves under that bound.

**Change 9: a second deduplication pass across sources.** 4.3's MinHash deduplication (5-gram
shingles, threshold 0.8) catches copies within a source but not the same work digitised and read
by OCR independently in two sources: on 300 pairs sharing a normalised title and author across
sources, median similarity is 0.117 on raw text and 0.180 after cleaning and normalisation, and
none reaches 0.8. The MinHash pass is kept unchanged, and a second pass is added: works in
different sources with the same normalised title, normalised author and year of publication form
a group, the earliest-catalogued member is kept, and nothing is deleted. A work counts once in
every control set and null sample. Groups the two passes form are reported separately, and a
sample of the metadata groups is checked against the text before use.

**Still open.** The size of the borrowing null sample (6.5, a floor of 500) is fixed by a later
amendment from the variance curve measured in BOM-45, before any borrowing score is computed.
