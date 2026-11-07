# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Running

| Job | Where | Done (est.) | When it ends |
| --- | --- | --- | --- |
| BOM-27 1B training (`scripts/large_pod.py`, tmux `largepod`) | 4 x H100 pod `qmon0qov69hb7r` (started 2026-11-06 13:25; the pod stops itself if the finished model sits uncollected 3 h) | 2026-11-07 ~20:00 | `after_1b.sh` takes over |
| After the 1B (`scripts/after_1b.sh`, tmux `after1b`) | waits; then H100s | Sat night | 1B benchmark (primary, V1-V3) -> publish to `etherfuse/timelocked-1830-1b` -> 1B candidate models and 1B imitation in parallel -> `eval.imitation report` |
| BOM-39 KJV masking of sweep blocks (tmux `sweepmask`) | Mac CPU | 2026-11-07 ~13:30 (2.5 min a batch) | `scripts/sweep_chain.sh` (tmux `sweepchain`): `sweep.index` tokens, mfw, embed, then `sweep.calibrate` -> write up BOM-39/47 |
| BOM-29 transformer cross-check (tmux `bom29`) | Mac GPU | 2026-11-06 ~22:00 | write up beside the grammar model; close BOM-29; `mac_gpu_chain.sh` starts |
| 125M tests | style imitation and V3 on the Mac (`macgpu`, done/ending); candidate models (tmux `candpodpilot`) and imitation primary + V1 (tmux `imitpilot`) moved to H100s after the Mac ran short of memory (owner, ~$5) | ~22:30 | `eval.imitation report`; 125M candidate validation |

## Decided

- **Every model size runs every model-based test** (owner; Amendment 37): 125M, 297M, 1B side by side, none the headline.
- **6.1/6.2 after the 1B benchmark** (owner): if the 1B reaches 6.1's 5% rate, keep the rule; otherwise Amendment 33 option (b), post hoc: each method returns *match* at its best achievable threshold, its real false-match rate beside every call; 6.2's two families unchanged. Then file Amendment 33 and seal.

## Next, in order (start the first whose inputs exist)

1. **After the 1B benchmark:** apply the 6.1/6.2 decision, file Amendment 33, `blind.thresholds`, `blind.seal`.
2. **BOM-32 blind run** (a fresh AI session without the key; simulated blinding) once the sweep index and all sizes' candidate models exist; then `blind.unblind`.
3. **BOM-35 synthesis** (`synth.model`, per size), **BOM-34 6.3 comparison** (`eval.scribes`), **BOM-42 claims table** (`eval.claims`), **BOM-68** table with the 1B rows.
4. **BOM-36 paper:** fill the 14 result slots in `paper/draft/`; then **BOM-38** simulated review (`review.simulate`); then **BOM-37** release (`scripts/release_check.py`; publishing is the owner's call).

Done today: BOM-26 closed; prep and first results for 28 (297M), 29, 31 (classical, 297M), 32, 33
(access table final), 34 (dictation evidence, photo hand-check), 35, 37, 38, 42, 68 (GPT-2 ablation).
Waiting on the owner only: BOM-71 (Google-digitized volumes, if provided).

## Timeline to the paper

Only the 1B (Sat ~20:00) and the sweep (Sat afternoon) are physical waits. Blind run Sunday;
synthesis and claims Monday; paper slots filled and the first full draft ~Tuesday Nov 10.
