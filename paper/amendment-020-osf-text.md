# Amendment 20: the semantic retelling control applies the recorded missed own copy (post hoc)

*Filed 2026-11-04. Evidence: `data/semantic/corpus_known_answer.json`, `docs/semantic-plan.md`
("Whole-corpus results"), `semantic/corpus.py`, `reuse/exact.py` (`MISSED_OWN_COPIES`).*

---

**Amendment 20, filed 2026-11-04, after the whole-corpus semantic search had run and its results
had been seen. Post hoc: decided by the owner after seeing the control's result and the Book of
Mormon's source table.** It changes one thing: which volumes count as the *Testaments of the
Twelve Patriarchs*' own copies in the semantic positive control (Amendment 14, "Positive
controls"). Every other rule, threshold, null and score is unchanged.

**Why.** The plan leaves a target's own copies and editions out of its searches. The automatic
rule finds them by author and by the first six words of the title. It misses `tcp:A09151`, the
1576 printing of the same English translation as the 1791 text being tested, whose title is in
old spelling. That volume was recorded as a missed own copy in BOM-23 on 2026-10-31
(`MISSED_OWN_COPIES`), before any semantic search existed, and BOM-23 and BOM-24 already report
their known-answer scores with and without it. The semantic control code did not apply that list.

**What happened.** The control passes if the King James Bible is the strongest source in every
one of the text's three matched draws. In draws 0 and 1 it is (53.8 per 10,000 words against
47.2 for the next source). In draw 2 the strongest source is `tcp:A09151` itself (69.9 against
the King James Bible's 53.8): the text matching an earlier edition of its own words. As computed,
the control fails, and with it the gate that the test is shown to find paraphrase.

**The amended rule.** The *Twelve Patriarchs* control is decided with the recorded missed own copy
left out of its draws, as the plan's own-copies rule intends. With it out, the King James Bible is
the strongest source in all three draws, and the control passes. Josephus passes either way
(51.9, 51.0, 51.8 against 43.8, 44.2, 35.8). The test is therefore taken as shown to find known
paraphrase. The computation without the exclusion is kept and reported beside it.

**What this does not change.** The known-answer separation (Amendment 9) fails with and without
the exclusion (U = 14/27, p = 0.50; own copies out 15/27, p = 0.43), so the semantic table is
still reported as uninformative on the translation question. The Book of Mormon's source table,
the 500-volume null and the "stands out" rule are unchanged; the table is described, not used to
decide the translation question.
