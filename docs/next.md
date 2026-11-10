# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Done overnight (2026-11-10)

- 590M style encoder trained, tested and scored blind on its pod; **unblinded 04:15** (after a
  fix to how the sweep's output is read); synthesis per size, scribe comparison (6.3), claims,
  open-set and prior-work tables committed. First read: `docs/results-first-read.md`.

## Next

1. **BOM-36:** fill the paper's result slots from `docs/results-first-read.md`; BOM-29's formal H3 report.
2. **Publish the models** (below).
3. **BOM-38** simulated review, **BOM-37** release.

## Tomorrow (2026-11-10)

- **Publish every model to Hugging Face** (owner, 2026-11-09; deferred a day for B2's daily
  download cap; blocks nothing). Dating models are live. Rerun: `python -m timelocked_lm.publish
  stage`, then the `pod_jobs.py --name publish ... --b2-pull ... --hf-token` command in
  `logs/publish.log`'s last launch (~222 GB from B2; check the owner's B2 cap first). Then commit
  the README "The models" table and `docs/replication.md`'s download section (both written, not
  yet committed) with the `data/manifests/hf_*.jsonl` lists. Add the 590M style encoder.

## Waiting on the owner


- **Delete the mid pod's full snapshots** once its tests pass: ask the owner at that moment.

## Decided

- **Every model size runs every model-based test** (owner; Amendment 37): 125M, 297M, 1B side by side, none the headline.
- **6.1 both ways** (owner, Amendment 33): registered and achievable rules plus the false-match ladder, all reported.
- **1B replaced by the 590M mid with QK-norm** (owner, Amendment 39); a 1B restart stays possible later.
- **No 1B before unblinding** (owner, 2026-11-09): unblind as soon as the 590M encoder is scored; a 1B, if ever run, is reported as scored after unblinding.
- **Publish every model** (owner, 2026-11-09), fine-tunes included (BOM-72 rebuilds the discarded ones after the analysis); private corpus text never.
- **No pre-declared "best" model** (owner, 2026-11-08): run everything, report everything side by side; plans unchanged.

## Next, in order (start the first whose inputs exist)

1. **After `aftermid` prints BLIND RUN COMPLETE:** commit `data/blind/`, then `blind.unblind` (simulated blinding).
2. **BOM-35 synthesis** (`synth.model`, per size), **BOM-34 6.3 comparison** (`eval.scribes`), **BOM-42 claims table** (`eval.claims`), **BOM-68** table with the mid rows.
3. **BOM-36 paper:** fill the 14 result slots in `paper/draft/`; then **BOM-38** simulated review (`review.simulate`); then **BOM-37** release (`scripts/release_check.py`; publishing is the owner's call).

Done today: BOM-26 closed; prep and first results for 28 (297M), 29, 31 (classical, 297M), 32, 33
(access table final), 34 (dictation evidence, photo hand-check), 35, 37, 38, 42, 68 (GPT-2 ablation).
Waiting on the owner only: BOM-71 (Google-digitized volumes, if provided).

## Timeline to the paper

The only physical wait is the 590M (~00:30 Mon) and its pod tests (Mon morning). Unblinding,
synthesis and claims Monday; first full draft ~Tuesday Nov 10.
