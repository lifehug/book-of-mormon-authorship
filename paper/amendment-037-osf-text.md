# Amendment 37: every model size runs every model-based test, side by side (BOM-27 to BOM-35)

*Filed 2026-11-06. Evidence: `docs/blind-run-plan.md`, `docs/synthesis-plan.md`, `scripts/pod_jobs.py`.*

---

**Amendment 37, filed 2026-11-06, before any Book of Mormon text is scored and before the 1B
model's benchmark exists.** Amendment 2 registered the time-locked model at 125M and 300M with a
decision point between them, and Amendment 26 added a 1B; Amendments 30, 31 and 32 then spoke of
"the working model chosen by the benchmark". The owner's decision replaces that choice: **every
model size (125M, 297M and 1B) runs every model-based test, and the results are reported side by
side; no size is singled out as the working or headline model.**

**What runs at every size.** The benchmark and its variants (Amendments 22, 23); the candidate and
control authorial models (Amendment 30); the imitation test's model part (Amendment 31: primary, V1,
V3); the blind run's authorial scores (Amendment 32), each size with its own 6.1 thresholds
calibrated on its own candidates' held-out windows; and the synthesis (6.7, Amendment 34), run once
per size with that size's authorial evidence beside the shared classical and embedding families,
plus one table of the sizes' posteriors with each size's most probable hypothesis and whether the
sizes agree. The style embeddings (BOM-30's encoder), dating's transformer cross-check (Amendment
29's 297M) and the author sweep each keep the one model they were registered with.

**Reading.** Agreement across sizes is reported as such; where the sizes disagree, the disagreement
is the result, and no size's answer is preferred to another's. Nothing else changes: decision
rules, thresholds' derivation, and every other method stay as registered.
