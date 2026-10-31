# Amendment 8: the Deltas as closed-set evidence only, repair or retirement of the failed methods, rarity counted by text, and the improvement study

*Filed 2026-10-30. Evidence: `data/benchmark/benchmark.json`, `data/benchmark/repair.json`,
`docs/repair-plan.md`, `docs/improvement-plan.md`, `data/benchmark/replication_johnson.json`,
`data/benchmark/improve_*.json`, `paper/deviations.md` (D1), `paper/methods-report.md`.*

---

**Amendment 8, filed 2026-10-30, before any Book of Mormon scoring** other than the registered
replications of published studies (BOM-22). No hypothesis, decision rule or threshold of section
6 changes.

**Timing, stated plainly.** Change 1 was decided after the benchmark's results were seen
(post hoc). Change 2's plan was committed before its tests ran; its results are recorded here.
Change 3 was devised after the Johnson and Johnson replication (BOM-22) had been run on the Book
of Mormon and had shown the registered rule blind to *The Late War*; it is therefore post hoc,
and is registered before the borrowing analysis (6.5, BOM-24) runs. Change 4's plan was committed
before any of its tests, and is filed while its one-time evaluation is still running, before its
result is known.

**Change 1 (post hoc): Burrows' and Cosine Delta are closed-set evidence only.** Section 7 passes a
method on closed-set accuracy of at least 90% and an open-set false-positive rate of at most 5%.
The Deltas reach 100% and 97% closed-set on the benchmark, but 6.1 gives them no verification
score, so the open-set half cannot be applied. Decided by the owner after the results were seen:
they enter the synthesis (6.7) only as which listed candidate is closest, never as evidence that a
candidate did or did not write a text and never toward "none of these". **The paper states beside
every Delta result that they did not pass the registered bar**, and that on 30 fresh period
authors their closed-set accuracy is 63% (Burrows) and 62% (Cosine): the bar is met at the scale
of a short candidate list, not of a corpus-wide search.

**Change 2: repair or retirement of General Imposters and ENSC.** Both failed section 7
(Amendment 7, Change 8). A check of our implementations against published results found General
Imposters faithful (PAN 2014, Kestemont et al. 2016) and our first ENSC not the published method;
ENSC is replaced by a port of Schaalje et al.'s published method (latent author, 2011 text-size
adjustment), as a correction. Plan, committed before the tests: General Imposters with 30% of
features per round (the only setting that passed in the multiverse); ENSC as published with
shrinkage by cross-validation over the registered grid and lambda the smallest value on
{1.5, 2, 3, 4, 5, 6, 8} with at most 5% false "none" on in-set tests; all settings calibrated on
the benchmark and applied unchanged to 30 fresh corpus authors drawn with seed "bom58-fresh"
(personal authors not used by any earlier step; collective attributions excluded). A method is
repaired only if it meets both section 7 bars on both sets. Result: General Imposters 93.9%
closed-set and 3.3% open-set false positives on the benchmark, but 51.3% closed-set on the fresh
authors; ENSC as published 44% and 88% open-set false positives. **Neither is repaired; both are
retired from this study** and reported as failed. The classical family that enters the synthesis
is therefore the two Deltas under Change 1.

**Change 3 (post hoc): in the borrowing analysis, document frequency counts texts, not printed
copies.** Under the registered rule a 4-gram is rare if it occurs in at most 5 documents. A
source that survives in several printings makes every phrase it shares with the target appear in
that many documents, so a reprinted source cannot be detected: Hunt's *The Late War*, in nine
printings in the corpus, shares 1 rare 4-gram with the Book of Mormon (p = 0.05). 6.5 now counts a
4-gram's document frequency by text: two volumes are copies of one text when, among volumes
sharing at least 10 of the target's 4-grams, the Jaccard overlap of their shared-gram sets is at
least 0.8 (candidate pairs found through 4-grams occurring in at most 20 volumes, sharing at least
5 of them). Copies are found by content, because grouping by title merged distinct volumes of
multi-volume works and the issues of periodicals. On the replication this gives 221,344 volumes
as 217,386 texts; *The Late War* shares 15 rare 4-grams (p = 0.0008), and the whole-corpus null's
99th percentile rises 16%. Amendment 7, Change 6 (target copies excluded, the whole corpus as
null, empirical p at most 0.01) is unchanged. **Because this rule was devised after a Book of
Mormon result was seen, 6.5 reports the registered by-volume count beside it for every source**,
and any source significant under one rule but not the other is reported as such.

**Change 4: the improvement study, a contribution to the methods only.** Improvements to the
earlier methods were developed on data already seen (the benchmark and the 30 authors of Change
2) and are evaluated once on a second set of 30 fresh corpus authors drawn with seed "bom60-eval",
excluding every author used before: a "none of these" threshold for Delta (at 5% false "none");
ENSC's text-size model refitted on many authors; General Imposters at 1,000 rounds. On the
development data, Delta's threshold, the refitted ENSC and 1,000-round General Imposters all fail
section 7. **None of these is used on the Book of Mormon**, whatever the evaluation shows; a
method retired in Change 2 stays retired. Only Change 3 (rarity by text) enters this study.
