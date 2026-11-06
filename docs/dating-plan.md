# Linguistic dating: the plan, written before any model is fitted (BOM-29)

Written 2026-11-01. Registered as Amendment 17 before the classifier is fitted or any validation
text is scored. Settings: `dating.*` in `config/preregistered.yaml`; code in `dating/`.

## What is already registered

5.3: a classifier trained on dated text from EEBO-TCP (1473-1700), 18th-century texts and the
1780-1830 corpus, with grammatical features (verb inflection, pronoun forms, auxiliary patterns,
relative clauses) and lexical features as separate models; output a predicted-year distribution
per segment. 6.4: the text is dated to a window if at least 80% of segments' 90% intervals fall
inside it; H3c is accepted if a permutation test on the predicted-year distributions of the Book
of Mormon and the pseudo-biblical control set gives p above 0.05. Amendment 2: regularised
multinomial logistic regression; the grammatical feature list fixed and published before the
benchmark, drawn from the early modern English literature and not selected on performance;
10,000 permutations; a transformer variant reported alongside as a cross-check. 4.4: dating runs
on the Book of Mormon's original (non-King James) spans only.

## A problem found while planning, and the fix

MorphAdorner's standard spellings, registered for pre-1700 text (4.3), replace grammatical forms
as well as spellings. From `data/normalization/applied_map.tsv`: `doth` -> `does` 1,270,334
times, `ye` -> `you` 882,357, `saith` -> `says` 592,880, `maketh` -> `makes`, `'tis` -> `it's`.
Text from 1700 on keeps those forms as printed (Amendment 6). A grammar model reading the
normalised text would see Tudor and Stuart prose as more modern than it is, and the bias would run
in the direction that matters most for the Book of Mormon.

So **the grammar model reads the printed text** (keyed, or BOM-14's cleaned OCR) through one fold
applied identically to every date: lower case, long s and ligatures, `v`/`u` and `j`/`i` merged,
`vv` -> `w`. It changes letters, never words. **The lexical model reads the registered normalised
text** (spelling variation is not vocabulary), with every word the grammar model reads removed, and
every standard spelling MorphAdorner substituted for a grammatical form (`makes` for `maketh`), so
the normalisation cannot carry grammar into it.

## The grammatical feature list (`dating/features.py`)

61 rates per 1,000 tokens. No part-of-speech tagger: none applies uniformly to 1473-1830 print and
to OCR, so every feature is a closed word list or a two- or three-word pattern.

| Group | Features | Named in |
| --- | --- | --- |
| Verb inflection | hath, has, doth, does, saith, says; other -eth forms; thou + -st verb; second-person verb forms (art, hast, shalt, wilt, didst, ...) | Nevalainen & Raumolin-Brunberg 2003 (ch. 4: -th to -s, has/hath, does/doth); Lass 1999; Barber 1997 |
| Pronoun forms | thou, thee, thy, thine, ye, you, your; mine/thine vs my/thy before a vowel; its; thereof and the there-, here- adverbs | N&R-B 2003 (ye to you, mine to my, its); Busse 2002 (thou/you); Österman 1997 (pronominal adverbs) |
| Auxiliary patterns | do, did; do + not vs lexical verb + not (I know not); n't contractions; 'tis/'twas; be- vs have-perfect with come, gone, become, ...; be + -ing; shall, will, should, would, may, might, must, can, could; lest; subjunctive be after if/though/lest/unless | Ellegård 1953 (do); Kytö 1997 (be/have perfect); Kytö 1991 (shall/will); Rissanen 1999; Arnaud 1998 (progressive) |
| Relative clauses | which, who, whom, whose, that, the which; where- adverbs, wherefore | N&R-B 2003 (which to who); Rissanen 1999 |
| Function-word forms | unto, upon, among(st), while/whilst, betwixt/between, ere, nor; an before h- | Barber 1997; Görlach 1991 |

The list was written from these sources before any model was fitted; no feature was added,
dropped or tuned after seeing a result.

## Data

Every eligible dated volume (text, a date, deduplication keepers, OCR exclusions; no newspapers;
corrected year, Amendment 12) from 1473 to 1830: 256,655 volumes after leaving out Bibles (948),
the Book of Mormon's copies and contamination hits (8), every pseudo-biblical control (2,574: the
King James imitation test's texts), and every text a later test scores: benchmark authors
(1,493), candidates (19), known-answer texts (230). 1473-1779 is all TCP (hand-keyed); 1780-1830 is
mostly OCR, with 2,833 keyed TCP volumes.

**Bins:** 1473-1529 as one bin (383 volumes), then decades to 1820-1830: 31 bins.

**Split:** 20% of authors (a volume without an author is its own group), by seeded hash, are
validation; no author is on both sides. **Sample:** per bin, a seeded draw of up to 1,500
training and 375 validation volumes; from each, up to 2 segments of 2,000 tokens at seeded
positions, skipping the first and last segment where there are four or more. A segment is used
only if it is running prose: at least 20% of its tokens are function words (a seeded check of
355 segments: median 53%, 0.8% below 20%; it drops tables and OCR debris).

## Models

Each model: standardised log(1 + rate) features, L2-regularised multinomial logistic regression,
the penalty chosen from {0.01, 0.1, 1, 10} by 5-fold author-grouped cross-validation (mean log
loss) on the training segments, then refit on all of them. Lexical vocabulary: the 5,000 words
with the highest document frequency in the training segments, after the exclusions above.

A segment's output is its probability over the 31 bins; its median year and 90% interval read off
that distribution, uniform within each bin. **The grammar model decides 6.4 and H3**, as Amendment 2
registers; the lexical model is reported beside it. The transformer cross-check (Amendment 2)
is fixed by Amendment 29 (`dating/transformer.py`): the time-locked 297M base model's mean final
hidden states as features for the same classifier, run on the Mac, reported beside both.

## Validation (no Book of Mormon text)

1. **Held-out authors:** mean absolute error of the median year, 90% interval coverage, bin
   accuracy, overall, by era and by bin; and 6.4's window rule on held-out 1780-1830 segments
   (how often a genuine 1780-1830 text is "dated to the window") and on earlier ones (how often an
   earlier text is wrongly placed in it).
2. **Keyed against OCR:** held-out TCP and OCR volumes of 1780-1809, the decades with both. If
   the model had learned OCR noise as a date, the two would differ.
3. **King James imitation (the issue's fourth task):** the pseudo-biblical primary controls,
   with King James spans removed as the Book of Mormon's are, against held-out ordinary
   1780-1830 volumes: the shift in mean predicted year, volume-level, two-sided permutation test
   (10,000). And the King James text itself.
4. **Known-answer (Amendment 9):** each text's score is its median predicted year minus the year
   its English was printed (higher: its own time); the registered one-sided exact separation.

## Known weaknesses, stated now

- No tagger: `which` as a relative and as a determiner count alike; `that` is every `that`. The
  features are rates, so the noise is the same at every date, but it is noise.
- The 1780-1830 bins are mostly OCR while earlier ones are keyed; check 2 measures this.
- The pre-1700 bins are drawn from EEBO-TCP's selection, which favours religious and political
  print; the 1780-1830 corpus is broader.
- Dating grammar is not dating authorship: a writer imitating older English is placed earlier,
  which is exactly what H3c and check 3 are there to measure.

## After validation: 6.4's decision rule (Amendment 19, post hoc)

Validation showed the registered interval rule cannot work with this model. The grammar model's
90% intervals are honest (coverage 0.91) but about 85 years wide for 1780-1830 text, wider than
the 51-year window, so only 14% of genuine 1780-1830 segments meet it. The owner chose
(2026-11-02) to amend before any Book of Mormon scoring: H3a and H3b are decided on segment
median years, as section 2 words them (more than half in 1780-1830: H3a; more than half in
1473-1700: H3b; else neither), with the interval rule reported beside it. `dating.classifier.h3_call`
is the rule; `validate` now reports it per segment and per held-out volume.

| Held-out volumes (grammar) | H3a | H3b | neither |
| --- | ---: | ---: | ---: |
| 1780-1830 | 1,464 | 80 | 331 |
| 1700-1779 | 217 | 212 | 568 |
| 1473-1699 | 48 | 3,729 | 367 |
| pseudo-biblical controls, 1780-1830 | 10 | 7 | 8 |

The King James text is called H3b. Keyed 1780-1809 segments reach the window less often than OCR
ones of the same years (55% against 83%, 71 keyed segments): a limitation for a keyed text such
as the Book of Mormon's, reported beside the result.
