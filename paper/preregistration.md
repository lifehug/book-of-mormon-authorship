# Pre-registration: Book of Mormon Authorship

**Status:** v0.2, registered on OSF 2026-10-15 as https://osf.io/6ugxc/ (frozen after the
48-hour approval window), revised after the simulated adversarial review in
`paper/adversarial-review.md`. This document is now frozen; later changes are dated amendments
listed in section 11.

**Author:** Dave Taylor. **Repository:** https://github.com/lifehug/book-of-mormon-authorship

## 1. Scope

This study measures the English text of the earliest Book of Mormon (original manuscript,
printer's manuscript, 1830 edition) against English print from roughly 1780 to 1830 and a dated
early modern English corpus. It asks three questions about the text and answers nothing else.
In particular it makes no claim about translation, inspiration, or the truth of the book's
contents. Stylometry measures whoever produced the English; it cannot see past that.

## 2. Questions and hypotheses

**Q1 Attribution (open-set).** Does the text resemble the writing of any pre-registered
candidate author?

- H1a: at least one candidate meets the match criterion in section 6.
- H1b: no candidate meets it ("none of the above").
- H1c: the internal narrators (Nephi, Jacob, Mormon, Moroni, and the Isaiah and KJV-derived
  spans excluded) are stylistically separable from each other at the level the benchmark
  shows for distinct known authors.

H1a, H1b, and H1c are not mutually exclusive, and each is reported on its own.

**Q2 Borrowing.** For each earlier text in the corpus, does the overlap in wording or ideas with
the Book of Mormon exceed what is expected by chance between two texts of the same genre,
length, and period?

- H2: a named source is a significant parallel if its score falls above the 99th percentile of
  the null distribution in section 6.5.

**Q3 Dating.** When does the text's grammar and vocabulary come from?

- H3a: the dating classifier places the majority of segments in the 1780-1830 window.
- H3b: it places them earlier (1473-1700).
- H3c: the Book of Mormon's date distribution is indistinguishable from that of the
  pseudo-biblical control set, which would mean KJV imitation alone explains the result.

## 3. Candidates, controls, and the rule for adding candidates

**Candidates** (fixed for the confirmatory analysis):

| Candidate | Corpus | Notes |
| --- | --- | --- |
| Joseph Smith | pre-1830 letters, 1832 history, early revelations | dictated and handwritten flagged separately; likely under 10,000 words |
| Oliver Cowdery | letters, 1834-35 history, editorials | principal scribe |
| Sidney Rigdon | sermons, letters, editorials | |
| Parley P. Pratt | pamphlets, autobiography drafts, editorials | |
| W. W. Phelps | editorials, hymns excluded, letters | |
| Solomon Spalding | *Manuscript Story* (Oberlin) | |
| Ethan Smith | *View of the Hebrews* and sermons | |
| Gilbert Hunt | *The Late War* | |

Each candidate corpus is KJV-masked and spelling-normalized the same way as the Book of Mormon.
A candidate with fewer than 10,000 masked words is scored but every result for them carries an
"unreliable sample" flag and is excluded from the Bayesian synthesis unless the benchmark shows
the method reaches the accuracy floor at that sample size (section 7). Joseph Smith's dictated
and handwritten texts are scored as two separate samples.

**Control groups:** pseudo-biblical texts (Leacock, Snowden, Linning, Hunt, and every other
example found in the catalog), 1820s sermons and tracts, histories and Native American origin
texts, and a general prose baseline of fiction and periodicals. Internal narrators are treated
as pseudo-candidates for H1c.

**Rule for adding candidates.** The corpus-wide author sweep (section 6.6) is exploratory. A
sweep lead becomes a confirmatory candidate only if all of the following hold: it beats the
lead threshold calibrated in section 6.6; it has documented historical plausibility (period,
place, or access, from the evidence table in BOM-33); it is added by a dated public amendment
to this document; and it is then tested with the confirmatory methods on the confirmation half
of the segments only (section 4.5), which the sweep never sees.

## 4. Data

**4.1 Sources.** Book of Mormon texts from the Joseph Smith Papers transcriptions. KJV from an
early 19th-century American printing including the Apocrypha. Period corpus from Harvard
Institutional Books 1.0, HathiTrust public domain, Internet Archive, and Chronicling America,
filtered to English, 1780-1830. Early modern corpus from EEBO-TCP Phases I and II. Every
ingested file is listed in a checksum manifest.

**4.2 Sealing.** The Book of Mormon text is excluded from all model training, tuning,
threshold setting, and feature selection until the blind run (section 8). The only exception
is the replication of prior studies with their published methods (BOM-22). A contamination
check searches every training set for Book of Mormon strings of 12 or more tokens and removes
any volume containing one.

**4.3 Quality and deduplication.** Volumes whose estimated OCR character error rate exceeds
10% (from the source's quality score, or from our own sample-based estimate where none exists)
are excluded. Reprints and later editions are collapsed to the earliest edition by MinHash
similarity above 0.8 on 5-gram shingles.

**4.4 KJV masking.** Book of Mormon, candidate, and control texts are aligned to the KJV with
passim. A span is a *verbatim quote* if it aligns with at least 90% token identity over at
least 8 tokens, a *close paraphrase* if it aligns with 60-90% identity over at least 8 tokens,
and *original* otherwise. Attribution (Q1) and dating (Q3) run on original spans only. Borrowing
(Q2) runs on the full text with KJV spans labeled, so a parallel that is itself biblical can be
recognized as such. The proportion of each text masked is reported.

**4.5 Segmentation and the discovery/confirmation split.** The Book of Mormon is segmented
three ways: by internal narrator, by dictation order, and by scribe, each also cut into fixed
2,000-word and 5,000-word chunks. Before the blind run, 5,000-word chunks are assigned to a
*discovery* half or a *confirmation* half by a seeded random draw stratified by narrator; the
assignment file and its SHA-256 hash are committed before any Book of Mormon scoring. The
author sweep uses the discovery half only. The confirmatory methods report on both halves
separately and on the whole.

## 5. Methods

**5.1 Classical stylometry.** Features: the 100, 300, and 1,000 most frequent words after
masking, with any word occurring in fewer than 20% of documents culled; character 3-grams and
4-grams; POS 2-grams and 3-grams; and a content-word set (nouns, verbs, adjectives) following
Huang, Murakami, and Grieve's finding that content words carry authorship signal. Methods:
Burrows' Delta and Cosine Delta; the General Imposters method with imposters drawn from the
genre-matched controls; and extended nearest shrunken centroids (ENSC) as in Fields, Schaalje,
and Roper (2011).

**5.2 Authorial language models.** A GPT-style model of 100-300M parameters is trained from
scratch on the 1780-1830 corpus with the Book of Mormon and all post-1830 text excluded, with
a tokenizer trained on the same data. One copy is fine-tuned per candidate and per control
group. A segment's score for a candidate is the log-perplexity ratio between that candidate's
model and the base model, computed over fixed 512-token windows and averaged, so length does
not drive the score.

**5.3 Linguistic dating.** A classifier trained on dated text from EEBO-TCP (1473-1700),
18th-century texts, and the 1780-1830 corpus, with grammatical features (verb inflection,
pronoun forms, auxiliary patterns, relative clauses) and lexical features as separate models.
Output is a predicted-year distribution per segment.

**5.4 Style embeddings.** An authorship-embedding model (LUAR-style) trained or adapted on
period text, used as an independent signal for Q1 and for the author sweep.

**5.5 Borrowing.** Exact and near-exact reuse by passim over the masked text against the
deduplicated corpus. Rare-phrase scoring: for each 4-gram in a source, its document frequency
across the corpus; a source's score is the length- and genre-normalized sum over shared
4-grams with document frequency at or below 5. Semantic parallels by sentence embeddings and
FAISS nearest-neighbor search at the passage level.

**5.6 Author sweep.** Every normalized author in the catalog with at least the minimum word
count from section 7 is indexed under style embeddings and one classical method. The sweep
returns the ranked nearest authors to the discovery-half segments.

## 6. Decision rules

All thresholds below are fixed here or fixed by the calibration procedure stated here, and the
calibration uses benchmark data only. No threshold is set or changed after the Book of Mormon
has been scored.

**6.1 Attribution match (per candidate, per method).** A method returns *match* for a
candidate when its verification score exceeds the threshold calibrated on the open-set
benchmark at a 5% false-positive rate; *non-match* when the score falls below the threshold
calibrated at 5% false-negative rate; and *inconclusive* between. For General Imposters the
score is the proportion of imposter trials the candidate wins; for the authorial models it is
the margin between the candidate model and the best control-group model; for embeddings it is
the cosine distance relative to the imposter distribution. The calibrated thresholds are
committed to the repository before the blind run.

**6.2 Attribution conclusion.** A candidate is *supported* only if at least two independent
method families (classical, authorial model, embedding) return *match* on both the discovery
and confirmation halves. H1b holds if no candidate is supported.

**6.3 Internal narrators (H1c).** Narrators are *separable* if the classical methods
distinguish them with accuracy at or above the benchmark's accuracy for distinct known authors
at the same sample size, and the dictation-order and scribe segmentations do not explain the
same variance better (compared by the same accuracy measure).

**6.4 Dating.** The text is dated to a window if at least 80% of segments' 90% intervals fall
inside it. H3c is accepted if a permutation test on the predicted-year distributions of the
Book of Mormon and the pseudo-biblical control set gives p above 0.05.

**6.5 Borrowing.** The null distribution is built by scoring at least 500 randomly chosen
period volumes, stratified by genre, exactly as candidate sources are scored. A source is a
*significant parallel* if its score is above the 99th percentile of that null. The Gospel of
Luke, *The Late War*, *View of the Hebrews*, and *Manuscript Story* are always reported with
their percentile whatever it is.

**6.6 Author sweep lead threshold.** Calibration: for 200 held-out books by known corpus
authors, record the rank of the true author; then remove the true author and record the best
false-match score. The sweep is *usable* if the true author ranks first in at least 70% of
queries. A *lead* is any author whose score for the discovery half beats the 95th percentile of
best-false-match scores under both the embedding and the classical signal.

**6.7 Synthesis.** Each method's likelihoods enter a Bayesian model with prior mass 0.5 on
"author not in set" and 0.5 shared equally among candidates with reliable samples. Method
weights are the benchmark accuracies from section 7, reduced as section 9 states. Sensitivity
analysis varies the prior on "not in set" from 0.2 to 0.8 and drops each method in turn.

## 7. Validation benchmark and pass criteria

Before any Book of Mormon scoring, every method runs on: the Federalist Papers; pseudo-biblical
texts with known authors, held out; dictated texts with known authors; and open-set cases
where the true author is removed from the candidate list.

A method *passes* if closed-set accuracy is at least 90% on 5,000-word samples, and at the
calibrated threshold its open-set false-positive rate is at most 5%. The *minimum sample size*
for a method is the smallest at which closed-set accuracy stays at or above 80%; candidates
below it are flagged unreliable for that method. A method that fails is reported and excluded
from the synthesis.

## 8. Blind procedure

A sealing script relabels the Book of Mormon segments with opaque identifiers and mixes in
decoy segments from known candidates and controls at a ratio of at least 1 decoy per 4
segments (amended from "a second person"; see section 11). The script writes the key to a
file outside the repository and commits the SHA-256 hashes of the key and of the relabeled
set. The analysis runs in a fresh session with no access to the key. All methods run on the
mixed set. Outputs are saved and their hashes committed before the key is
revealed. Decoys must be identified at the benchmark accuracy or the run is repeated with the
fault documented. Leave-one-candidate-out runs follow.

## 9. Imitation robustness

For known 1800s authors who wrote both imitation-biblical prose and ordinary prose, each
method's accuracy at identifying the author from the imitation sample sets its weight: full
weight at or above 80%, half weight from 60% to 80%, dropped below 60%.

## 10. Known limits

- Joseph Smith's undisputed pre-1830 writing is small. He will likely fall under the sample
  floor for most methods, and that is reported as such, not as a non-match.
- Dictation and multiple scribes stand between any author and the page. The scribe
  segmentation tests whether style tracks scribe.
- OCR noise in the corpus is uneven and is measured, not assumed away.
- A sweep with no leads says nothing beyond the corpus.
- The candidate corpora are themselves of uneven provenance (dictated, edited, posthumously
  published), and each sample's provenance is recorded.
- All review in this project (adversarial, draft, and peer) is simulated by an AI model and
  conducted by the same person who runs the analysis. It is not independent scrutiny.

## 11. Amendments

Every change is listed here with its date and reason, and the original stays on OSF unchanged.

**Amendment 6, 2026-10-27, before any calibration or Book of Mormon scoring.** Corpus-preparation choices the registration left open are registered as run: control pools sampled to 3,000 and 5,000; the 4.2 contamination check reads Book of Mormon strings outside the KJV, at 20 shared strings; OCR cleaning thresholds and the period lexicon; artifact-only spelling for 1700-1779; MorphAdorner applied as distributed except that *an*, *whether* and *fall* keep their printed form; passim implementation details, including aligning long texts as overlapping pieces; Sonnet as the pass-2 model and a worst-case perturbation bound. The pseudo-biblical control is chosen by a published curation procedure instead of Amendment 3's either-label rule, both earlier lists kept as sensitivity analyses, and a second deduplication pass by title, author and year across sources is added. No hypothesis, decision rule or threshold changes. OSF revision 6ae16f4142a77759f3e18539; text in `paper/amendment-006-osf-text.md`.

**Amendment 11, 2026-10-31, before any italic word is counted.** The King James italics test (BOM-62): within registered King James spans, the shares of italic (translator-supplied) and roman words a text keeps, with bootstrap intervals; its own known-answer check against independent period translations (translation text only) and King James quotations in 1820s sermons; the reading of the Book of Mormon's result fixed in advance. No hypothesis, decision rule or threshold changes. OSF revision 6ae62f2ca50d25933c296d01; text in `paper/amendment-011-osf-text.md`.

**Amendment 14, 2026-11-01, before any semantic search.** Semantic parallels (BOM-25, 5.5): the whole eligible corpus (278,796 volumes) cut into 128-word passages and embedded with bge-small-en-v1.5, chosen on a known-answer paraphrase test (an 1807 Psalms translation against the King James Psalms) repeated with a million corpus distractors, where re-scoring with a larger model made results worse; exact search in each target's date window; a parallel beats the query's best match among 10,000 random window passages; source score per 10,000 words of query passages, placed against 500 genre- and length-matched volumes; named sources against their registered control groups; Amendment 9's score and a positive control on biblical retellings (Josephus, Twelve Patriarchs). No hypothesis, decision rule or threshold changes. OSF revision 6ae7bc3c227eb64c6abde258; text in `paper/amendment-014-osf-text.md`.

**Amendment 15, 2026-11-01, before any compared text is read.** Story skeletons (BOM-25, added to 5.5): every compared text cut into 2,000-word blocks; a hosted model (claude-sonnet-5-5; simulated) lists at most 12 events per block with names replaced by roles, checked first on 20 King James chapters read twice (median agreement 0.92, 233 of 238 events supported); events match at bge-small cosine 0.700; Smith-Waterman local alignment with a 1,000-shuffle order test; the Book of Mormon against the named sources within their Amendment 14 control groups and the top 20 passage-search sources; positive control on Josephus, the Twelve Patriarchs and Jasher against their biblical ranges and 20 unrelated narrative books each; Amendment 9 not computable for this test. No hypothesis, decision rule or threshold changes. OSF revision 6ae7dbb60fa5f3ec4abde26d; text in `paper/amendment-015-osf-text.md`.

**Amendment 23, 2026-11-05, during Amendment 22's 125M run, before any of its scores were read.** At the owner's request, three secondary uses of the time-locked model on the same benchmark, both sizes, same pass rule; Amendment 22's ALM stays primary and every variant is reported with the number tried: V1, Amendment 22 at learning rate 1e-4; V2, a classifier head over the task's authors on mean final hidden states of 512-token windows (3 epochs, 1e-5); V3, the unchanged base model's hidden states as features in the benchmark's own 180 trials (cosine nearest centroid; General Imposters with the registered settings). OSF revision 6aed57846119836b77b6964f; text in `paper/amendment-023-osf-text.md`.

**Amendment 22, 2026-11-05, before any authorial language model is fine-tuned or scored.** Runs 5.2's authorial language models on the 6.1/7 benchmark at both sizes: the benchmark's tasks, authors and works as running text; for the Federalist and imitation-scripture tasks each testable author's last max(5, ceil(n/4)) 1,000-word blocks are held out and its tests are up to 20 distinct 5,000-word windows in that tail (Jay, untestable, is a candidate on all its text); dictated task as the benchmark (20 random samples per dictated volume); one fine-tuned copy per author (3 epochs, learning rate 1e-5, constant, AdamW, 1,024-token sequences, batch 8, float32 on the M4); score = mean over 512-token windows of the candidate model's minus the base model's log-loss; closed set by the lowest score; threshold and false-positive rate as General Imposters'; passes at 0.90 closed set and at most 0.05 open-set false positives. OSF revision 6aed5219b9cd9627025f6179; text in `paper/amendment-022-osf-text.md`.

**Amendment 21, 2026-11-05, after the named sources' direct scores and ranks were seen, before any null for them was computed.** Pins the null of Amendment 14 for a named proposed source: it is scored directly, like the source (fresh embeddings, same queries and bars), from 500 volumes of the Book of Mormon's window gallery (Bibles, sealed copies and the source's own copies out) with the majority genre label of the source's catalog copies (*View of the Hebrews* `sermon_devotional`; *The Late War* and *Napoleon* `newspaper_periodical`; the filed text counts *The Late War*'s as 3 of 5 Hunt printings, the catalog holds 4 of 6, same label) and its passage words within a factor of 2, seed `bom25-null:named:` plus the source key. Spalding has no catalog copy and ranks 12th, so no null. Also corrects the 2026-11-04 write-up, which wrongly said no named source ranked first (the 1825 *View of the Hebrews* does). OSF revision 6aec8dd3dd216354e1f383cc (its form stripped `<source>` from the seed name); text in `paper/amendment-021-osf-text.md`.

**Amendment 20, 2026-11-04, after the whole-corpus semantic search; post hoc.** The semantic positive control for the *Testaments of the Twelve Patriarchs* (Amendment 14) is decided with `tcp:A09151` left out of its draws: the 1576 printing of the same English translation, which the author/title rule misses and which BOM-23 recorded as a missed own copy on 2026-10-31. As computed, that copy is the strongest source in one draw and the control fails; with it out, the King James Bible is strongest in all three draws and the control passes (Josephus passes either way), so the test is taken as shown to find paraphrase. Both computations are reported. The known-answer separation fails either way (U = 14/27, p = 0.50), so the semantic table stays uninformative on the translation question. OSF revision 6aeb6364388d19d44e80bc2f; text in `paper/amendment-020-osf-text.md`.

**Amendment 19, 2026-11-02, after the dating validation and before any Book of Mormon scoring; post hoc.** 6.4's interval rule (80% of segments' 90% intervals inside the window) cannot date genuine text to 1780-1830 with the grammar model, whose honest intervals are about 85 years wide (14% of genuine 1780-1830 segments pass). H3a and H3b are now decided on segment median years, as section 2 words them: H3a if more than half fall in 1780-1830, H3b if more than half fall in 1473-1700, otherwise neither. On held-out volumes the rule calls 1,464 of 1,875 genuine 1780-1830 volumes H3a and 3,729 of 4,144 pre-1700 volumes H3b; the 25 pseudo-biblical controls split 10/7/8. The interval rule is reported beside the decision; H3c and everything else are unchanged. OSF revision 6ae89915263740bb19d84cc0; text in `paper/amendment-019-osf-text.md`.

**Amendment 18, 2026-11-01.** A known limit on replication (BOM-44): the corpus cannot be redistributed (Harvard, HathiTrust, Joseph Smith Papers terms), so derived tables that cannot be assembled back into text are published instead: the benchmark as 1,000-token blocks of counts over each task's 1,000 most frequent words; the rare-phrase scans as each volume's word count and the target 4-gram hashes it shares, for targets whose own text is open (a full hash list can be unrolled into its text, so Enoch and Josephus, from HathiTrust and Harvard copies, are withheld); the catalog labels; the dating rates. What an outsider can and cannot reproduce from these is listed. No hypothesis, decision rule, threshold or analysis changes. OSF revision 6ae8143cd1f5f0174dd84c7c; text in `paper/amendment-018-osf-text.md`.

**Amendment 17, 2026-11-01, before the dating classifier is fitted or any validation text is scored.** Linguistic dating (BOM-29, 5.3): MorphAdorner's pre-1700 standard spellings replace grammatical forms (doth to does 1.27 million times), so the grammar model reads printed text through one letter-only fold and the lexical model the normalised text without any grammar word; 61 grammatical features from the early modern English literature, no tagger, published in `dating/features.py`; 1473-1830 volumes less Bibles, the Book of Mormon, pseudo-biblical controls and every text a later test scores; 31 bins (1473-1529, then decades); 20% of authors held out; up to 1,500 training volumes a bin, two 2,000-token prose segments each; L2 multinomial logistic regression, penalty by grouped CV; the grammar model decides 6.4 and H3; validation on held-out authors, keyed against OCR text, King James imitation and Amendment 9. No hypothesis, decision rule or threshold changes. OSF revision 6ae8126f2d971de294296cfe; text in `paper/amendment-017-osf-text.md`.

**Amendment 16, 2026-11-01, before any language model is trained.** The time-locked base model (BOM-27, 5.2): training set of 202,816 volumes dated 1780-1830 by corrected year, newspapers out, the Book of Mormon's copies and 4.2's contamination hits removed, and every volume by a benchmark author, a candidate or a known-answer text removed so the base model has not read what it will score; 0.5% held out; tokenizer fit on a seeded 1 GB sample; pilot 124.5M (14x768), base 297M (24x960); one pass in seeded window order, 524,288 tokens a step, AdamW 0.9/0.95, weight decay 0.1, clipping 1.0, cosine to 10%, bf16. Amendment 2's settings stand. OSF revision 6ae7e7682a1c00cdd1bde281; text in `paper/amendment-016-osf-text.md`.

**Amendment 13, 2026-11-01, before the rare-phrase known-answer scans; partly post hoc.** The rare-phrase source list (BOM-24): population and document frequencies under Amendment 12's corrected dates, moved volumes listed separately; beside the registered result, post hoc after BOM-22's replication had ranked the Book of Mormon's sources: genre percentiles, 1,000-word block-bootstrap intervals, The Late War and The First Book of Napoleon ranked within the curated pseudo-biblical list; Amendment 9's score is the strongest source's rare shared 4-grams per 10,000 words in each matched draw, frequency counted within the draw. No hypothesis, decision rule or threshold changes. OSF revision 6ae7978847ce2102d62394f9; text in `paper/amendment-013-osf-text.md`.

**Amendment 12, 2026-11-01, before any volume is scanned.** The catalog date audit (BOM-64): volumes whose own text names years later than their catalog year (at least 10 mentions more than 2 years later, at least 20% of their year mentions) move to the latest year mentioned at least 3 times, in every date-window selection; nothing deleted; precision and miss rate from a seeded, model-assisted (simulated) sample. No hypothesis, decision rule or threshold changes. OSF revision 6ae768b9883b4fc0e7bde25d; text in `paper/amendment-012-osf-text.md`.

**Amendment 10, 2026-10-31, before any reuse run.** Exact reuse (5.5) is searched against the whole eligible corpus with a lossless prefilter and document frequency counted across the whole search; the known-answer score searches every text, the Book of Mormon included, against 2,000 volumes from the 70 years before its English was written (3 draws), and a separation counts only if it survives a spelling-era check among texts whose windows are mostly before 1700. No hypothesis, decision rule or threshold changes. OSF revision 6ae620454ae19487e2bde267; text in `paper/amendment-010-osf-text.md`.

**Amendment 9, 2026-10-31, before any Phase 4-6 test is run on the controls or the Book of Mormon.** A known-answer validation step: nine genuine period translations of ancient texts and three compositions presented as ancient (Ossian, Rowley, Jasher), two secondary; each test declares its per-text score and direction first and separates the groups at an exact one-sided Mann-Whitney p of at most 0.01; a test that does not is reported as uninformative on the translation question. No hypothesis, decision rule or threshold changes. OSF revision 6ae61ebeebfd59a7464e8fc4; text in `paper/amendment-009-osf-text.md`.

**Amendment 8, 2026-10-30, before any Book of Mormon scoring other than the registered replications.** Post hoc, Burrows' and Cosine Delta enter the synthesis as closed-set evidence only, with the paper stating beside every Delta result that they did not pass section 7 and reach 62-63% among 30 fresh authors; General Imposters (30% features) and ENSC as published, tested under a plan committed before the run on the benchmark and 30 fresh authors, are not repaired and are retired; post hoc, the 6.5 borrowing analysis counts document frequency by text (copies found by content) with the registered by-volume count reported beside it, because a reprinted source is otherwise invisible; and the improvement study (BOM-60) is a methods contribution not used on the Book of Mormon. No hypothesis, decision rule or threshold changes. OSF revision 6ae55e1b828dc3df8274a024; text in `paper/amendment-008-osf-text.md`.

**Amendment 7, 2026-10-30, before any Book of Mormon scoring other than the registered replications.** The section 7 minimum samples are measured on known authors (10,000 masked words of reference text; 5,000-word tests) and the expected consequence for each candidate is stated in advance; ENSC's alpha is the largest giving at most a 5% false-"none" rate on the benchmark, with proportional priors; no candidate is expected to clear Amendment 5's time-split gate (baseline 37-60%); the 6.5 null is the whole eligible period corpus with the target's own copies excluded and an empirical p-value at most 0.01; because only three authors wrote both imitation scripture and other prose, section 9's accuracies carry exact 95% intervals and 6.7 is also run at equal method weights; and, post hoc, the benchmark's construction and the topping-up of General Imposters' pseudo-biblical pool to the registered 200 are recorded, with General Imposters and ENSC failing section 7. No hypothesis, decision rule or threshold changes. OSF revision 6ae500f8f0e01c4f4105c6bd; text in `paper/amendment-007-osf-text.md`.

**Amendment 5, 2026-10-21, before any calibration or Book of Mormon scoring.** Expanded candidate corpora are registered as a secondary analysis. Section 3's corpora and every decision rule in section 6 are unchanged and remain confirmatory; H1a and H1b are decided on them alone, and nothing in this amendment may be substituted for the primary result, including where that result is inconclusive. Exposure tiers are fixed from the historical record; for an exposed candidate a non-match on the expanded corpus is evidence and a match is uninformative, since exposure biases toward resemblance. Later material is tiered by provenance and only holograph and dictated samples enter attribution. An expansion is used only where a time-split test on known authors shows the candidate's signal is stable across the same gap. At most ten sweep leads receive an expansion, and the total count of candidate-by-method tests is published. OSF revision 6ad8cc455301b781d55b34dc; text in `paper/amendment-005-osf-text.md`.

**Amendment 4, 2026-10-20, before the corpus is labelled.** Genre reliability moves from a census of second passes to a stratified 5,000-record sample scored by a different model family, and a label-perturbation sensitivity test is added. OSF revision 6ad844dc2aba3079ce0da955; text in `paper/amendment-004-osf-text.md`.

**Amendment 3, 2026-10-20, before the corpus is labelled.** Genre tagging becomes multi-label with an uncertainty option and few-shot prompting. OSF revision 6ad802954d710c8c6b00b651; text in `paper/amendment-003-osf-text.md`.

**Amendment 2, 2026-10-17, before any calibration or analysis.** Operational analytic values left unspecified by the original registration are pinned, and several that existed only as code defaults are registered. No hypothesis, decision rule or threshold is changed. Three values are registered as selection procedures rather than numbers, because they depend on data not yet observed: the ENSC shrinkage parameter, the passim alignment parameters, and the grammatical feature list; each runs on benchmark or control data only and publishes its chosen value before the Book of Mormon is scored. The base model is fixed at 300M within the already registered 100-300M range, and the 125M pilot becomes a registered decision point reporting benchmark accuracy at both sizes. OSF revision 6ad3f82fc8f5176e336b2561, approved 2026-10-17; reasoning for each choice in `paper/amendment-002-draft.md`, registration text in `paper/amendment-002-osf-text.md`.

**Amendment 1, 2026-10-15, before any data work.** The project is conducted by one person
with AI assistance, so every step that assumed another person is replaced by a scripted or
AI-simulated equivalent, labeled as such:

- Section 8: the blind run's relabeling and decoy mixing is done by a sealing script with a
  committed hash of the key, not by a second person, and the analysis runs in a fresh session
  without the key.
- Paper review (BOM-36): the three simulated reviewer stances from the adversarial review are
  run against the full draft by an AI model, in place of advisors.
- Peer review (BOM-38): simulated by an AI model that sees only the released materials; no
  journal submission is planned. Reviews and responses are published verbatim.

No hypothesis, method, threshold, candidate, or data rule changes. The limit on review
independence is stated in section 10.

## 12. Reporting commitments

The paper reports every pre-registered hypothesis, every method's pass or fail, every
inconclusive result, every disagreement between methods, and every deviation from this
document.
