# Results that are final before the blind run (draft, BOM-36)

These results do not depend on the blind run. The borrowing results (section 1) are the
registered answers to Q2. Sections 2 to 4 are validation; sections 5 and 6 are production and
access evidence reported beside the synthesis. Numbers are read from the files named.

## 1. Borrowing (Q2)

### 1.1 Exact reuse (BOM-23; `docs/reuse-plan.md`)

With KJV spans masked, 58 passages in 47 earlier-catalogued volumes align with the Book of Mormon,
covering 0.52% of it. Seventeen of the 47 are later texts quoting it under catalog dates decades
too early (Congressional serial-set volumes catalogued 1817, *The Millennial Harbinger*
catalogued 1830); without them the share is 0.16%. The other 30 volumes share short, loose
religious stock phrases (9-46 tokens, identity 0.27-0.67). For comparison, *The Late War* (1816)
shares 8.92% with earlier books and an 1821 sermon collection 2.47%.

### 1.2 Rare phrases (BOM-24; `data/reuse/bom/rare.json`)

| Source | Rare shared 4-grams | Per 10,000 words | Rank of 204,520 | p (95% interval) |
| --- | --- | --- | --- | --- |
| *The First Book of Napoleon* (1809) | 12 | 5.45 | 63 | 0.0003 (0.0002-0.0031) |
| *The Late War* (1816, 9 printings) | 22 | 3.86 | 131 | 0.0006 (0.0004-0.0017) |
| *View of the Hebrews* (1825) | 2 | 0.37 | 9,496 | 0.046 (0.017-1.0) |
| Spalding, *Manuscript Story* | 1 | 0.24 | - | 0.068 |
| Luke (KJV), against the masked text | 0 | 0 | - | 1.0 |

*The Late War* and *Napoleon* are significant by the registered rule. Within the curated
pseudo-biblical group (post hoc), the 1829 reprint of Ilive's *Book of Jasher* shares more (7.99
per 10,000 words, 31 phrases); the shared phrases are battle and chronicle formulas. The rule
calls 2,044 volumes significant, mostly short pieces sharing one phrase.

### 1.3 Paraphrase (BOM-25; `data/semantic/named.json`, `named_null.json`)

| Source | Rank in group | Score (95% interval) | Null median | Null 99th pct. | Percentile | Stands out |
| --- | --- | --- | --- | --- | --- | --- |
| *View of the Hebrews* (1825) | 1 of 49 | 29.6 (28.0-31.3) | 14.6 | 45.0 | 84.6 | no |
| *View of the Hebrews* (1823) | 2 of 49 | 29.5 (27.9-31.1) | 9.2 | 38.4 | 94.0 | no |
| *The First Book of Napoleon* | 3 of 18 | 7.9 (6.9-9.0) | 0.1 | 8.8 | 98.4 | no |
| *The Late War* (1816) | 6 of 18 | 1.9 (1.4-2.4) | 0.4 | 14.6 | 79.8 | no |
| Spalding, *Manuscript Story* | 12 of 49 | 5.5 | - | - | - | no (rank) |

*View of the Hebrews* leads the origins-of-the-American-Indians group, but 77 of 500
genre-and-length-matched religious volumes score higher. In the whole-corpus search (163,121,310
passages, 221,373 volumes in the window; `data/semantic/corpus_bom.json`) editions of Josephus take
14 of the top 20 places; the registered rule flags 622 sources, which mostly measures biblical
register.

### 1.4 Story order (BOM-25; `data/semantic/skeleton/`)

No source shares the Book of Mormon's order of events at the registered level (order p at most
0.01). Among the 20 leading search sources the longest shared run is 9 of its 1,421 events
(Josephus, order p 0.24); the positive control, Josephus against Genesis-Judges, shares 108 events
in order (p 0.001). Named sources: *View of the Hebrews* 1823, 3 events, order p 0.97, rank 17 of
49; 1825, 2 events, p 1.0, rank 43 of 49; Spalding, 4 events, p 0.67; *The Late War*, 2 events,
p 1.0; *Napoleon*, 3 events, p 1.0.

### 1.5 Known-answer controls (Amendment 9)

Exact reuse (U 4 of 27, p 0.964), rare phrases (U 6/27, p 0.927) and paraphrase (U 14/27, p 0.50)
do not separate genuine translations of ancient texts from compositions presented as ancient, and
the King James italics test is not shown to work (`docs/italics-plan.md`). None of the borrowing
tests therefore bears on the translation question; each describes which period books share the
Book of Mormon's wording, ideas or plot.

### 1.6 Triage (BOM-26; `data/semantic/triage.json`, `docs/triage-plan.md`)

| Search | Biblical | Common | Specific (first pass) |
| --- | ---: | ---: | ---: |
| Paraphrase, named sources | 104 | 144 | 1 |
| Paraphrase, 20 leading sources | 149 | 350 | 1 |
| Paraphrase, random sample | 104 | 146 | 0 |
| Rare phrases, named sources | 10 | 23 | 0 |
| Rare phrases, 20 densest volumes | 15 | 22 | 0 |
| **All** | **382** | **685** | **2** |

The simulated second review re-labelled both first-pass SPECIFIC pairs COMMON (Spalding's
elephant-like "Mammoons"; survival in a just war in a collected *Works* of 1820): **0 pairs
specific under both passes.** Agreement on the 104 doubly labelled pairs 0.740, Cohen's kappa
0.505.

**Reading (Q2).** No named proposed source stands out under its registered null in any of the
four searches except rare phrases, where *The Late War* and *Napoleon* pass a rule that the whole
imitation-scripture genre also passes. No passage is copied and no plot is shared. Every surfaced
similarity is explained, on triage, by King James wording (36%) or period stock phrasing (64%).

## 2. Benchmark (section 7; `data/benchmark/open_set.json`, `prior_work.json`)

| Method | Size | Federalist | Imitation scripture | Dictated (Scott) | Overall | False matches | Passes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| General Imposters | - | | | | 0.833 | 0.617 | no |
| ENSC (its own "none") | - | | | | 1.000 | 0.661 | no |
| Style embeddings | - | | | | 0.839 | 0.500 | no |
| ALM primary | 125M | 0.769 | 0.958 | 1.000 | 0.936 | 0.473 | no |
| ALM primary | 297M | 1.000 | 0.958 | 1.000 | 0.991 | 0.382 | no |
| V1 (lr 1e-4) | 125M / 297M | | | | 0.936 / 0.936 | 0.455 / 0.473 | no |
| V2 (classifier head) | 125M / 297M | | | | 0.900 / 0.909 | 0.282 / 0.136 | no |
| V3 (hidden states) | 125M / 297M | | | | 0.839 / 0.844 | 0.689 / 0.717 | no |
| All of the above | 1B | [RESULT] | | | [RESULT] | [RESULT] | [RESULT] |

**No method passes** the registered bar (closed set at least 0.90 and false matches at most
0.05). Every method can rank candidates; none can yet say "none of these" reliably. Classical
methods, style embeddings and V3 are scored on BOM-21's 180 trials; the fine-tuned models on 110
held-out tests, so the two groups are compared within, not across (BOM-68; paired exact McNemar
tests in `data/benchmark/prior_work.json`).

**Candidate models at 297M** (`data/benchmark/alm_candidates_base.json`): held-out closed-set
accuracy among all units 1.0 for Ethan Smith (20 tests), Spalding (7), Cowdery printed (7) and
Phelps (3); Hunt 0.8 (10); Pratt 0.95 (19); Rigdon 0.5 (2). Samples under 10,000 words are
untested.

## 3. Dating validation (Q3; `data/dating/validation.json`)

| | Grammar (decides H3) | Lexical |
| --- | --- | --- |
| Held-out mean error | 23 years | 13 years |
| 90% interval coverage | 0.91 | 0.76 |
| Median 90% interval width, 1780-1830 text | 85 years | 19 years |
| Held-out 1780-1830 volumes called H3a (Amendment 19) | 1,464 of 1,875 | |
| Held-out pre-1700 volumes called H3b | 3,729 of 4,144 | |
| Pseudo-biblical controls vs ordinary 1780-1830 | -53 years (p 0.0001) | -5.5 years (p 0.26) |
| King James text | 1631 (H3b) | 1710 |
| Known-answer separation (Amendment 9) | p 0.57, none | p 0.81, none |

King James imitation alone moves the grammar model's date back by about half a century; this is
the comparison H3c registers. The transformer cross-check: [RESULT: `data/dating/transformer_validation.json`].

## 4. Imitation robustness, classical methods (BOM-31; `data/benchmark/imitation.json`)

| Method | Forward (imitation text to real author) | Weight | Reverse |
| --- | --- | --- | --- |
| Burrows' Delta | 13/18 = 0.72 (0.47-0.90) | 0.5 | 0.38 |
| Cosine Delta | 13/18 = 0.72 (0.47-0.90) | 0.5 | 0.29 |
| General Imposters | 11/18 = 0.61 (0.36-0.83) | 0.5 | 0.12 |
| ENSC | 7/18 = 0.39 (0.17-0.64) | 0 | 0.25 |

[RESULT: style embeddings and model-based methods at 125M, 297M and 1B.]

## 5. Production evidence (BOM-34; `data/manuscript/summary.json`, `docs/manuscript-evidence.md`)

The catalog types 1,597 corrections on the original manuscript's 231 surviving pages and 2,136
on the printer's manuscript's 468. Sound-alike word corrections (listed homophones such as
where/were, there/their) are far more common in the dictated original than in the copied
printer's manuscript:

| Comparison | Original | Printer's | Odds ratio | Fisher p |
| --- | ---: | ---: | ---: | ---: |
| All pages: homophone fixes / substitutions | 36 / 693 | 8 / 927 | 6.3 | 1e-7 |
| Same passages only | 36 / 693 | 2 / 457 | 12.5 | 2e-6 |
| Oliver Cowdery as scribe in both | 36 / 590 | 6 / 837 | 9.0 | 2e-9 |

This bears on how the words reached the page (by ear, then copied by eye); it cannot distinguish
whether a dictated text was composed, recited or read aloud.

## 6. Access evidence (BOM-33; `data/access/access_table.csv`, `docs/access-evidence.md`)

Of 33 texts scored: 15 at 3 (documented within Joseph Smith's reach; all but one are editions of
Josephus, in the Manchester library's accessions and in Palmyra bookstore advertisements including
January-May 1829), 2 at 2, 10 at 1, 6 at 0. Named sources: *View of the Hebrews* 1825 edition 2
(advertised in Utica, 1826), 1823 edition 1; *The Late War* 1 (Palmyra "Historical Reader"
advertisements of 1827-1830 do not name the author); *The First Book of Napoleon* 0; Spalding's
manuscript 0. Availability is not use.
