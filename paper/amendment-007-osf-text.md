# Amendment 7: sample-size floors and what they mean for the candidates, ENSC's open-set rule, the borrowing null, the imitation weights, and the benchmark's construction

*Filed 2026-10-30. Evidence: `data/benchmark/power.json`, `data/benchmark/power_candidates.csv`,
`data/benchmark/timesplit.json`, `data/benchmark/dual_register.json`,
`data/benchmark/benchmark.json`, `data/benchmark/run1/`, `data/benchmark/SOURCES.md`,
`data/classic/corpus_run.json`, `data/reuse/null_sizing/`.*

---

**Amendment 7, filed 2026-10-30, before any Book of Mormon scoring** other than the registered
replications of published studies (BOM-22). No hypothesis, decision rule or threshold of section
6 changes.

**Timing, stated plainly.** Changes 1 to 6 were written on 2026-10-28 and 2026-10-30, before the
validation benchmark ran. Change 7 was written after the dual-register count and before the
benchmark. Change 8 records how the benchmark was built and one correction made to it; it is
written after the benchmark's results were seen, and is labelled post hoc for that reason.
Under section 7 two methods failed (General Imposters and ENSC; Change 8), and they are reported
and excluded from the synthesis as registered.

**What prompted this.** Section 7 defines a method's minimum sample as the smallest size at
which closed-set accuracy stays at or above 80%, and section 10 expects Joseph Smith to fall
under it. That has now been measured on known authors, so the expectation can be stated with
numbers before any result exists, rather than discovered after.

**Change 1: how the floors are measured.** On known-author sets only: the Federalist Papers
(the 70 papers with an undisputed single author) and known-author pseudo-biblical works (Hunt,
Snowden, Linning, Hughes; one copy per text), on KJV-masked text. Text is cut into 1,000-word
blocks; each curve uses the authors able to supply every size; 20 seeded trials per author per
size, at 1,000, 2,000, 5,000, 10,000 and 20,000 words. Two curves: *test size* (a held-out
passage of N words against each author's remaining text) and *reference size* (a 5,000-word test
with each author's known text capped at N words). A floor is the smallest size from which every
larger size also reaches 80%. Where the two sets disagree, the larger floor governs.

**Change 2: the floors, as measured.** Reference: 10,000 masked words for Burrows' Delta, Cosine
Delta, General Imposters and ENSC (the Federalist set; the pseudo-biblical set gives 1,000-2,000
but shares subject matter between test and reference). Test: 2,000- and 5,000-word passages reach
85-100% for every method in both sets, so the 2,000- and 5,000-word chunks of 4.5 are analysed as
registered. These floors are re-measured, with the same design, as the language-model (BOM-28)
and embedding (BOM-30) families are built.

**Change 3: what is expected before any result.** On pre-1830 text, the confirmatory sample of
section 3:

- Ethan Smith (277,352 masked words), Gilbert Hunt (56,956) and Solomon Spalding (41,833) clear
  every classical floor and are testable.
- Joseph Smith (3,082) and Oliver Cowdery (2,691) fall below the 10,000-word floor. **No
  classical method is expected to be able to support or reject either on pre-1830 text**, and any
  classical score for them is reported as below the floor, not as evidence.
- Sidney Rigdon, Parley P. Pratt and W. W. Phelps have no pre-1830 text; on the confirmatory
  sample they are untestable by any method.

Section 6.2 calls a candidate supported only when two method families agree, so a candidate must
clear two families' floors to be concludable at all. That is stated here so that a confident
score from one family, for a candidate below another family's floor, cannot later be read as a
result.

**Change 4: ENSC's open-set rule.** ENSC assigns "none of the above" when every author's
likelihood falls below alpha; the registration names ENSC but not alpha or its class priors. At
0.05 the rule said "none" for 11 of 30 works whose author was present (BOM-20), so alpha is not a
p-value. It is calibrated on the Phase 3 benchmark like every threshold in 6.1: the largest alpha
giving at most a 5% false-"none" rate on in-set works, published before any Book of Mormon
scoring. Class priors are proportional to training documents.

**Change 5: what the time-split test is expected to allow.** Amendment 5 admits a candidate's
later writing only if a profile from one side of 1830 recognises their writing on the other at the
section 7 floor. Measured on 30 corpus authors with 10,000+ words on both sides of a gap of seven
or more years, the classical methods recognise the author 37-60% of the time (chance 3%). Of the
candidates, only Joseph Smith and Oliver Cowdery have text on both sides, one test each, both
below the 10,000-word floor. **No candidate is therefore expected to qualify for an expanded corpus
under the classical methods**, and Amendment 5's secondary analysis is expected to report that,
rather than results, unless a later method family shows much smaller drift.

**Change 6: the borrowing null is the whole period corpus.** 6.5 builds the null from "at least
500 randomly chosen period volumes" and calls a source significant above its 99th percentile.
Measured against a stand-in target (Gilbert Hunt's *The Late War*, so the Book of Mormon is not
touched), the 99th percentile estimated from 500 volumes has a 95% interval of roughly six-fold
width (0.056 to 0.366 rare shared 4-grams per 10,000 words, +/-119%), and even 20,000 volumes leave
+/-16%. Since one pass over the corpus scores every volume, the null is the entire eligible
period population (about 200,000 volumes; "at least 500" is met and genre strata are complete), so
the threshold has no sampling error. Two rules make the test well defined: the target's own
copies (for the Book of Mormon, the sealed copies of 4.2) are excluded from every document
frequency, because seven missed copies of *The Late War* made its distinctive phrases look common
and collapsed the null to zero; and because most volumes score exactly zero, a source is a
significant parallel when its empirical p-value (the share of null volumes scoring at least as
high, ties counted against it) is at most 0.01.

**Change 7: the imitation weights rest on very few authors, so an equal-weight run is added.**
Section 9 weights each method in the synthesis (6.7) by its accuracy at identifying authors from
their imitation-biblical writing, in bands at 80% and 60%. That accuracy can be measured only on
authors who wrote both an imitation-biblical work and other prose of adequate length. Counted on
the curated pseudo-biblical list of Amendment 6 (18 works by 10 catalogued authors), with 10,000
masked words of other writing required (the Change 2 floor) and copies of the curated works not
counted: **three authors qualify** (Snowden, Dodsley, Kenrick), and the true number may be lower,
since the catalog credits Dodsley with anthologies he edited and Kenrick's other work is itself an
imitation (of Shakespeare). At three authors a method that is right every time has a 95% interval
of about 29-100%, so the 60% and 80% bands cannot be told apart. Section 9's weights are kept, and
each method's imitation accuracy is reported with an exact (Clopper-Pearson) 95% interval and its
n. **6.7 is also run with equal method weights, and both results are published side by side.** If
the two disagree on any headline conclusion, the paper says so and does not choose between them.
Evidence: `data/benchmark/dual_register.json`.

**Change 8 (post hoc): how the benchmark is built, and the imposter pool.** Section 7 names the
benchmark's parts and pass criteria but not its construction. As run: the tasks in
`data/benchmark/tasks.json` (the Federalist Papers; four known authors of imitation scripture,
Hunt, Snowden, Linning and Hughes, one copy per text; Walter Scott's two novels dictated in 1819
tested against his hand-written novels and ten novelists of 1810-1830); 20 seeded 5,000-word
tests per author from text held out of the reference; Burrows' and Cosine Delta judged closed-set
only, since 6.1 gives them no verification score; General Imposters' open-set false-positive rate
measured on held-out trials (two folds); ENSC's alpha searched over 1e-6 to 0.5 under Change 4.
General Imposters draws its imposters from the genre-matched controls (5.1; Amendment 2: 100 per
trial from a pool of 200). Amendment 6's curated pseudo-biblical list has 18 works, of which 10
were usable once the task authors' works were removed, and the first run used that pool of 10;
it also admitted another copy of one test author's book. The registered pool size is kept:
**every eligible curated work is used and the rest is drawn, seeded, from Amendment 3's list, one
copy per work; the task authors' works are excluded as works, not only by file; sealed copies
are excluded.** The first run is published alongside (`data/benchmark/run1/`). Result of the
corrected run: Burrows' Delta 100% and Cosine Delta 97% closed-set accuracy; General Imposters
83% closed-set, with a match threshold at the maximum score, and ENSC 66% open-set false
positives at alpha 0.5: both fail section 7.
