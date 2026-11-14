## 9. Corrections and robustness

The registered run is the main record (git tag `blind-registered-2026-11-10`). Everything in this
section was found or decided after some result existed. Each step is labelled, dated in section
11 of the pre-registration, and reported beside the registered result, not in place of it.
Amendments up to 46 were filed on OSF; from 47 on they are recorded in the repository only,
committed before the results they govern, so the commit time is the record.

### 9.1 Every post hoc step

"Post hoc" here means decided after a relevant result had been seen. Several of the later steps
had their rule written down before their own run (noted in the third column), but all of them
came after unblinding and were prompted by what the unblinded results showed.

**After unblinding (2026-11-10 onward).**

| Step | Amendment | Decided after | What changed | Effect |
| --- | --- | --- | --- | --- |
| The quotation leak | 43 | unblinding, and after seeing which samples were affected | Book of Mormon quotations (passages of 20+ shared words written after the matching passage was dictated) dropped from candidate samples; candidate models retrained, sealed set rescored | Cowdery's first-place ranking (119 of 168 chunks at 590M) removed; the 1828-29 revelations first for the language models on 159, 168, 131 chunks; match calls 10 / 5 / 3 become 2 / 2 / 0 (9.2) |
| Joseph Smith's ordinary prose scored | 44 | unblinding, on the owner's question | his non-revelatory writing of 1831-33 pooled and scored beside the 1828-29 revelations | ordinary prose mid-list for the language models and encoders, first for Burrows' Delta (6.1) |
| Equal dose | 45 | the simulated reviews | every candidate sample refitted on slices of exactly the revelations' 3,039 tokens | revelations first on 168 of 168 chunks at 125M and 297M; 62 at 590M, a *Late War* slice ahead on 63% (6.2) |
| His prose over time | 46 | unblinding, on the owner's question; method filed before scoring | distance of his 1833-44 prose, readers' and unexposed writers' to the book, by period | no movement toward the book's style; the registered permutation test unreadable and not used (6.6) |
| The synthesis placebo | none | the simulated reviews | the registered synthesis run on the candidates' own held-out passages | it leans to "not in set" on true authors' text; its 0.744 carries little information (9.3) |
| Registered feature sets not run | none (deviation D3) | the simulated reviews | found: character n-grams, part-of-speech n-grams and the content-word set were registered for the classical methods and never run on the benchmark or the sealed set; only most-frequent words were | not known; whether to run them post hoc is undecided (`paper/deviations.md`) |
| A larger benchmark and its pass rule | 47, 48 | unblinding; rule and draw fixed before scoring | 430 held-out tests on 23 authors in place of 110; pass rule and stopping rule for larger models | no method passes; the best false-match rate is 63% (590M) where the 110 tests had given 22% |
| Cross-work decoys and register placebo | 49 | unblinding; rule fixed before any model was trained | each candidate tested on a work left out of training; six writers who died before September 1827 ranked at equal dose | only Ethan Smith recognised across works (7); the register rule triggered at 590M only (6.3) |
| Seeds | 50 | unblinding; rule fixed before the run | every candidate and control model retrained with five further seeds | ranking stable; two misses at 590M in opposite directions; one-batch models cannot vary (6.5) |
| Slices | 51 | the first placebo results | up to 12 slices per placebo writer in place of one pair | 0 of 67 slices reach the revelations at 125M and 297M; Ilive 8 of 12 and Dowling 9 of 12 at 590M (6.3) |
| The 430-test head-to-head | 52 | Part 1's paired results and the 430-test totals | the four older methods run on exactly the 430 tests the language models took; McNemar test per pair, Holm-corrected | all 12 comparisons "ours better" by test (for example 297M against Burrows' Delta 59 to 9); corrected by Amendment 55 |
| The whole ranking with and without the revelations | 53 | the language-model rankings had been computed from saved scores | reporting only: every candidate sample's rank for every method, with the 1828-29 revelations in and out | section 6.1's two tables |
| The later revelations | 54 | Amendments 44, 45, 51, 53; rule fixed before any text was prepared | his 1830-34 revelations as a whole sample and as 12 equal-dose slices | every slice 2nd or 3rd behind the 1828-29 revelations at 125M and 297M; 10 of 12 at or above them at 590M (6.4) |
| Counting by author | 55(a) | Amendment 52, and a simulated research review by an AI agent that had already shown the by-author counts | the unit of the head-to-head becomes the author (sign test, Holm-corrected, intervals from resampling authors) | on 23 authors: ours better than General Imposters and ENSC; ahead of Burrows' and Cosine Delta on 10-11 authors to 2-3, not significant (Holm p 0.13-0.15) |
| The normalised curve | 55(b) | the same review, whose exploratory split by test had suggested a large gain | the whole trade-off curve reported; score normalisation (z-norm, z-margin) tested with each author held out | normalisation fails on new authors (17-26% false matches at a 5% target); the raw score holds its target (about 6%) and confirms 38-61% of true authors; the registered bar is unchanged and still failed (51-57% false matches) |
| Chunks by length | 55(c) | the same review | every count over the 168 chunks also given for the 121 and the 47 | the two lengths agree (6.4a) |
| 32 more benchmark authors | 56 | Amendment 55's by-author result; draw rule and stopping rule fixed first | 32 authors added by the original rules; the by-author test on all 55 | all 12 comparisons "ours better" (Holm p at most 0.0014); the 32 new authors alone repeat it (5.1) |
| The imitation-test correction | none (2026-11-12) | a by-author recount | the imitation test's passages come from three authors; counted by author, Burrows' Delta gets 1 of 3 and the 297M models 2 of 3, where by passage it was 13 of 18 against 7 of 17 | "the models are weaker under imitation" withdrawn; the test is too small to judge either way (5.3) |

**Before unblinding.**

| Step | Amendment | Decided after | What changed | Effect |
| --- | --- | --- | --- | --- |
| Delta as closed-set evidence; rarity by text | 8 | the benchmark | Burrows' and Cosine Delta kept only for "which listed candidate is closest"; rare phrases counted by distinct text, not by printed copy | *The Late War* becomes visible to the rare-phrase rule |
| Dating by segment medians | 19 | dating validation, before any Book of Mormon scoring | H3a and H3b decided on median years, since the registered interval rule passed only 14% of genuine period text | none on the Book of Mormon result |
| Semantic controls | 20, 21 | the semantic positive control | a known own-copy excluded; named sources tested against matched nulls | one control passes; *View of the Hebrews* placed at the 85th percentile |
| The open-set threshold | 25 | the benchmark | match threshold set at the 5th percentile of true authors | the false-match rates of section 5 (General Imposters 0% becomes 62%) |
| A disclosed leak | 31 | a smoke test | one Cosine Delta imitation figure was seen before the imitation rule was registered | none |
| Both match rules reported | 33 | the benchmark | both readings of the match rule and a false-match ladder reported | none (both shown) |
| The 1B model replaced | 38, 39 | an unrecoverable loss spike in training | a 590M model with QK-norm takes the 1B's place | one model size |
| The sweep's plausibility gate | 40 | the gate, read literally, passed 94% of random authors; before any lead was seen | gate read as period and (place or access) | none (no lead) |
| Variant learning rates | 41 | the 590M benchmark | variants V1 and V2 rerun at a rate chosen on held-out training text | V1 at that rate equals the primary method |
| The V2 seed fluke | 42 | V2 moved when rerun on another machine | V2, a variant of the language-model method, rerun with five further seeds per size | its registered 297M run had the lowest false-match rate of any method (14%) and was first reported as the best; across seeds it ranges 53-98% at 297M and 9-93% at 125M. V2 carries no weight |

### 9.2 The quotation leak in detail

After unblinding, the 590M candidate models ranked Oliver Cowdery's 1829 sample closest on 119 of
168 chunks. That sample, his "Articles of the Church of Christ", is 40% word-for-word Book of
Mormon text. Parley P. Pratt's books quote it at length too. The seal had been enforced on
training data and not on candidate samples.

Every run of words a candidate sample shares with the text was classed by a rule fixed before the
matches were read: biblical; period stock phrasing; written before the matching passage was
dictated; written in the same weeks; or written after it (`docs/bom-overlap-analysis.md`). Only
quotations were dropped. Masking every shared run was considered and rejected, because it would
also remove shared idiom that may be genuine evidence, above all from Joseph Smith's 1828-29
revelations. Those contain no quotation (one shared phrase predates the passage it matches; the
rest were dictated in the same weeks) and are unchanged. This decision was made after seeing
which samples it would affect, and it leaves the revelations' shared phrasing in; both facts
should be weighed by the reader.

| Method | Registered: first (of 168) | Without quotations | Match calls |
| --- | --- | --- | --- |
| Cosine Delta | Joseph Smith 131, Hunt 31 | Joseph Smith 148, Hunt 20 | none in either |
| Burrows' Delta | Joseph Smith 77, Hunt 47, Pratt 37 | Joseph Smith 91, Hunt 49, Pratt 25 | none in either |
| General Imposters | Pratt 74, Joseph Smith 48 | Joseph Smith 66, Pratt 66 | none in either |
| Style encoders 297M / 590M | Joseph Smith 150 / Cowdery 102 | Joseph Smith 151 / 99 | none in either |
| Candidate models 125M / 297M / 590M | Joseph Smith 82 / 133 / 46; Cowdery 29 / 34 / 119 | Joseph Smith 159 / 168 / 131 | 10 / 5 / 3 become 2 / 2 / 0 |

"Joseph Smith" in this table adds his three samples together (the 1828-29 revelations and his
dictated and handwritten writing after 1830). For Burrows' Delta most of his count is the later
prose (41 and 21 chunks against 29 for the revelations); for the other methods nearly all of it is
the revelations (`data/blind/per_candidate.json`, `data/blind/a43/per_candidate.json`).

### 9.3 The synthesis and its placebo

The registered plan combined the method families into one posterior probability for each
candidate and for "not in the set", weighting each family by its benchmark accuracy and by its
result on the imitation test. The model-based families received zero weight from the imitation
test, so only General Imposters entered, and the posterior is the same at every model size. It
covers only the three candidates with samples of at least 10,000 words from before 1830: "not in
set" 0.744 (prior 0.5), Hunt 0.089, Spalding 0.085, Ethan Smith 0.082. Joseph Smith and Cowdery
are outside it, untested by it, not ruled out.

*The placebo (post hoc, raised by the simulated reviews).* Run on the candidates' own held-out
passages, the same synthesis still leans to "not in set": Ethan Smith's passages 0.59, Hunt's
0.56, Spalding's 0.51, control passages 0.63 (`data/synthesis/placebo/decoys.json`). It cannot
recognise an author's own text, because General Imposters cannot reach "match" at its registered
threshold. The 0.744 is therefore reported as registered and carries little information. It also
moves with modelling choices: 0.42 to 0.92 across priors of 0.2 to 0.8, about 0.99 with equal
family weights, and back to the prior if General Imposters is dropped. Two later corrections
bear on it as well: the imitation test that set the family weights is too small to judge
(section 5.3), and read strictly the registered rule admits no family at all, since every one
failed the benchmark bar. H1b ("none of these") cannot be supported by it.

### 9.4 Process failures

Reported because the study's guarantee is that everything can be checked.

- **Source data deleted.** The newspaper extractor deleted the archives it read, losing the
  per-word OCR confidence and word positions for all 158,960 pages. A build test now fails on any
  destructive call in the pipeline (BOM-50; recovery is open).
- **Licensed text nearly published.** A 117 MB results file holding corpus text was caught by the
  repository's size limit before it was pushed; results files now hold names and numbers only.
  Earlier, validation excerpts from Harvard's texts and a personal email and IP address were
  committed and removed by rewriting history.
- **Models discarded.** The benchmark's fine-tuned models were scored and then deleted to save
  disk, and the abandoned 1B model's checkpoints were deleted without asking. They have not been
  rebuilt (BOM-72 was dropped on 2026-11-11): no result depends on the weights, their scores are
  saved, and they can be rebuilt from the published base models, code and seeds.
- **Wrong results caught later.** A first genre-agreement figure (7.4%) counted 3,027 outage
  failures as answers. A paraphrase write-up said no named source ranked first when one did. A
  rare-phrase count came from the wrong book. A closed catalog issue had left out HathiTrust. The
  430 benchmark tests were first analysed as 430 independent tests when they come from 23 authors
  (Amendment 55). The imitation test was first read by passage when it has three authors. A first
  write-up called the 590M "the size that sees style best" when the three sizes pick the right
  author equally often. Each was corrected in the open.
- **A check that looked like a win.** An exploratory split of the benchmark by test made score
  normalisation look like a large gain for "none of these"; split by author, as it should have
  been, the gain vanished (Amendment 55(b)). The quick version is in the record, labelled.
