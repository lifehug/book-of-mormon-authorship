# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Done 2026-11-10

- Unblinded 04:15; synthesis, scribes, claims (verdicts owner-approved), H3c (rejected).
- Every model published on Hugging Face (README "The models"; checksums in `data/manifests/hf_*`).
- Book of Mormon quotations found in candidate samples (Cowdery's 1829 Articles, Pratt): Amendment
  43 (quotations only), rerun filed beside the registered run (`data/*/a43/`).
- Joseph Smith revelatory vs non-revelatory (Amendment 44): closeness runs through the revelatory
  register. BOM-73 (his prose over time) researched and tabled.
- Explainers drafted (`paper/explainers/`).

## Next

1. **BOM-36:** assemble the full paper (`paper/paper.md`) from the drafts and results.
2. **BOM-38:** simulated review (`python -m review.simulate run --draft paper/draft`), responses.
3. **BOM-37:** release prep; **owner's go-ahead to publish**, Zenodo connection (owner's login).
4. Blog post with the results (after the owner reads the explainers).
5. Back up the Amendment 43 candidate weights to B2 when the 590M fetch finishes.
6. Later: BOM-72 (rebuild discarded benchmark copies), BOM-73 (tabled).

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
