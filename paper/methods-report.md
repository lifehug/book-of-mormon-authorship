# What the earlier methods get wrong, and what fixes them (BOM-60)

*2026-10-30. Numbers marked "development" were measured on data already seen (the BOM-21 tasks
and BOM-58's 30 authors); the one-time evaluation on a second fresh set is the last section.
Registered as a methods contribution, not used on the Book of Mormon: Amendment 8, Change 4.*

This report collects what the benchmark (BOM-21), the replications (BOM-22), the fidelity checks
(BOM-57) and the repair step (BOM-58) found about the classical methods used on the Book of Mormon
question, and tests changes that might fix them. It is a contribution to the methods, not a way
to rescue a method for this study: methods retired in BOM-58 stay retired here, and any change
used later in this study must first be registered by amendment. The plan was committed before
any test: `docs/improvement-plan.md`.

## The code: which is the published method, which is ours

A replicator can run every published method as published, our check of it, and our change to it,
on the same data. Where a change is an option on shared code, its default reproduces the original.

| Method | As published | Our check against the published result | Our change (BOM-60) | Command |
| --- | --- | --- | --- | --- |
| Larsen et al. 1980, MANOVA on function words | `eval/replicate.py` `larsen`, `larsen_speakers` | speaker counts against their Appendix B (`eval/speakers.py check`) | - | `python -m eval.replicate larsen` |
| Holmes 1992, vocabulary richness | `eval/replicate.py` `holmes`; `classic/sichel.py` | Sichel fit on his own Table 3 (`tests/test_sichel.py`) | - | `python -m eval.replicate holmes` |
| Jockers et al. 2008, Delta and NSC | `eval/replicate.py` `jockers`, `jockers-data`; `eval/jockers_pamr.R` (their own tool) | their deposited data: same 110 words, CV error 8.76% (8.8%) | Delta options `delta_words`, `delta_scale_known` (off by default) | `python -m eval.replicate jockers-data` / `jockers-pamr` |
| Schaalje et al. 2011, ENSC | `classic/ensc_published.py` (port of the authors' R code) | Federalist checks (`eval/fidelity.py ensc`) | refit size model (`size_model=`); improvement 3 | `python -m eval.fidelity ensc`; `python -m eval.improve ensc-size` |
| Johnson and Johnson 2013, rare 4-grams | `eval/replicate.py` `johnson` (their rule) | - | rarity by text (`reuse.rare.copy_clusters`); improvement 1 | `python -m eval.replicate johnson` |
| General Imposters (Kestemont et al. 2016) | `classic/imposters.py` | PAN 2014 against their Table 1 (`eval/fidelity.py gi`) | more rounds; improvement 4 | `python -m eval.fidelity gi`; `python -m eval.improve gi-rounds` |
| Burrows' and Cosine Delta | `classic/delta.py` | benchmark (`eval/benchmark.py`) | verification score; improvement 2 | `python -m eval.improve delta` |
| Our first ENSC (BOM-20) | `classic/ensc.py` (**not** the published method; kept so the BOM-21 result reproduces) | found unfaithful in BOM-57 | - | `python -m eval.benchmark` |

## 1. Rarity counted by text, not by printed copy (development: works)

**Problem.** Under the registered rule a 4-gram is rare in at most 5 documents. Hunt's *The Late
War* survives in nine printings in the corpus, so every phrase it shares with the Book of Mormon
sits in at least eight documents and none is rare: 1 rare shared 4-gram, p = 0.05.

**Change.** Count document frequency by text, copies found by content: two volumes are copies
when the sets of target 4-grams they share overlap by 80% or more (`reuse.rare.copy_clusters`).
Grouping by title was tried first and rejected: it merged a multi-volume work's different volumes
(240 volumes of *The Decline and Fall*) and a periodical's issues (4,813 volumes of the
Congressional Serial Set). By content, 221,344 volumes form 217,386 texts, and the largest groups
are genuine reprints (13 Bibles, 11 copies of Barclay's *Apology*).

**Result.** Hunt's nine printings fall into four groups; *The Late War* shares 15 rare 4-grams,
rank 177 of 221,344, p = 0.0008. *The First Book of Napoleon*, printed once, barely moves (10 to
11). The whole-corpus null's 99th percentile rises 16%, the cost of seeing reprinted sources.

## 2. A "none of these" score for Delta (development: does not work)

**Change.** "None" when even the nearest author's profile is farther than a threshold set at a 5%
false-"none" rate on in-set tests.

**Result.** On the very tasks it was calibrated on, the open-set false-positive rate is 24%
(Burrows) and 29% (Cosine); on BOM-58's 30 authors, 68% and 97%. A raw Delta distance depends on
the vocabulary and on how many authors are compared, so a threshold does not carry from one task
to another.

## 3. ENSC's text-size model refitted (development: does not work, and explains something)

**Change.** Schaalje et al.'s variance model, `s^2 = a c^p / w^q`, fitted on many authors instead
of two, at their block sizes and Funai's 108 words.

**Result.** On 30 period authors (25,824 points, R^2 0.94): a = 1.09, p = 1.164, q = 0.747, against
the published 0.259, 1.1147, 0.661. The published model puts word-frequency variance about four
times lower than these authors show. With the refit, the swing in ENSC's answer across candidate
sample lengths halves (25.5 to 13.7 points), but it wrongly names a candidate for Hamilton's papers
59-73% of the time. The published model's success on Hamilton seems to rest partly on understating
natural variation, which makes every candidate look far away and so favours "none of these".

## 4. General Imposters: more rounds (development: does not work)

**Change.** 1,000 rounds instead of the registered 100, so that the score cannot pin at its
maximum. (Imposters matched to the test's register are already the BOM-21 design: imitation
scripture, history and fiction pools per task.)

**Result.** On the BOM-21 tasks, closed-set accuracy rises from 83.9% to 88.3% and the held-out
open-set false-positive rate is 4.4%, but the match threshold is still at the maximum score: some
wrong authors win all 1,000 rounds, so more rounds cannot lift the ceiling, and the closed-set bar
of 90% is still missed.

## 5. Closed-set traps, measured (from BOM-22)

A method that must name someone from a list names whoever's samples sit nearest. Two measurements:

- **Which texts stand for a candidate decides the answer.** On Jockers et al.'s own data, replacing
  one candidate's samples with other genuine writing by the same man moves his count of chapters
  (first or second choice) from 169 to 92 (Rigdon), 42 to 137 (Pratt) and 36 to 81 (Cowdery);
  Spalding, the one candidate whose text is the same in both, moves from 89 to 80. Their Rigdon is
  mostly his 1864 revelations.
- **Unscreened quotation of the target.** Five of our 35 Pratt samples and one of 25 Cowdery samples
  quote the Book of Mormon; with them in, Pratt's count was 186 instead of 137.

**Rules that follow:** an open-set method that passes validation before any attribution; candidate
texts screened for quotation of the target; results reported as they move with the choice of
candidate samples.

## Evaluation (once, on 30 authors no earlier step used)

`python -m eval.improve evaluate`, `data/benchmark/improve_evaluation.json`. Thirty corpus authors
drawn with seed "bom60-eval", excluding every author used before (Joel Barlow, Frances Brooke,
Jonathan Edwards, James Madison, Tobias Smollett, Anna Seward and 24 others; chance on the closed
set 3.3%), 20 tests of 5,000 words each from a held-out work. Every setting and threshold was
fixed from the development data before the set was drawn, and the design was registered
(Amendment 8, Change 4) while the run was still going, before its result was known.

| Method | Closed set | Open-set false positives | False "none" | Section 7 |
| --- | --- | --- | --- | --- |
| General Imposters, 100 rounds (registered) | 56.5% | 0% | - | fails |
| General Imposters, 1,000 rounds (improvement 4) | 56.7% | 0% | - | fails |
| Burrows' Delta + distance threshold (improvement 2) | 57.0% | 73.2% | 14.2% | fails |
| Cosine Delta + distance threshold (improvement 2) | 60.3% | 98.8% | 0% | fails |
| ENSC as published, published size model | 53.8% | 90.2% | 2.5% | fails |
| ENSC as published, refitted size model (improvement 3) | 54.8% | 92.5% | 0.5% | fails |

Section 7's bars are at least 90% closed set and at most 5% open-set false positives.

**What it shows.**

- **No change works, and no method meets the bar.** Each improvement moves its method by about a
  point, inside the noise of 600 tests. The development verdicts (2, 3 and 4 do not work) hold on
  data none of them had seen.
- **General Imposters' 0% false positives is not a success.** Its match threshold, set on the
  BOM-21 tasks, is the maximum possible score (1.0 at both 100 and 1,000 rounds), so no score
  can exceed it and it never says "match" at all. The open-set rate is zero by construction;
  the method's only working answer is the closed-set one, right 57% of the time.
- **Delta's threshold does not travel.** Set on BOM-21 at a 5% false-"none" rate, it gives 14%
  (Burrows) and 0% (Cosine) on these authors, and the open set fails badly, as in development.
- **The closed-set ceiling is about 55-60% among 30 period authors**, for every method, the same
  as on BOM-58's authors (47-63%). With a long candidate list of ordinary period prose, the
  classical methods name the right author a little over half the time.

**Deviations, before any scoring.** "jersey, new" (the New Jersey legislature) passed the filter
for collective attributions and is one of the 30; Josephus is read in translation, as three of
BOM-58's authors were. The result's stamp names commit 751d65d, the commit current when the file
was written; the code that ran is that of 3041f08, and no Python or config file differs between
them.

**Improvement 1 (rarity by text)** is not part of this evaluation: it is a borrowing rule, not an
attribution method, and its test was the Johnson replication above. It is the one change this
study uses (Amendment 8, Change 3), with the registered by-volume count reported beside it.
