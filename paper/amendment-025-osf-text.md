# Amendment 25: the open-set check, corrected (post hoc)

*Filed 2026-11-05. Evidence: `eval/open_set.py`, `data/benchmark/alm_pilot.json`, BOM-69.*

---

**Amendment 25, filed 2026-11-05, after the 125M authorial-language-model benchmark result had been
read. Post hoc.** Section 7's open-set criterion asks how often a method confidently names a
candidate when the true author is absent. As built (6.1, General Imposters; reused by Amendment 22),
the match threshold was the 95th percentile of the open-set negatives and the rate was the share
of held-out negatives above it. For any method with continuous scores that is about 5% by
construction, whatever the method can do; the 125M model's 0.0545 against the 0.05 bar is that
noise, and General Imposters' 0.0 reflects ties in its discrete scores. The check did not measure
what 7 intends.

**Corrected check.** The match threshold is the score that 95% of true authors reach (the 5th
percentile of the positives, `benchmark.open_set_accept` 0.95); an open-set negative at or above it
is a false match. The rate is measured on two held-out folds of the tests (threshold from one
fold's positives, rate on the other fold's negatives; seed `benchmark-open-set-fold`). A method
passes with closed-set accuracy at least 0.90 and this rate at most 0.05, as 7 states. It applies
to every method with a verification score, old and new alike: General Imposters, Amendment 22's
models, Amendment 23's variants and Amendment 24's style embeddings. ENSC's own "none" answer and
the Deltas (no verification score) are unchanged. The original computation is reported beside the
corrected one for every method, and no other rule, threshold or result changes.
