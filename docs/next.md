# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Running (2026-11-09 10:15)

| Job | Where | Done (est.) | Then |
| --- | --- | --- | --- |
| 590M benchmark: main 98.2% / 21.8% false matches; V1 62.7% / 81.8% and V2 76.4% / 39.1% (worse than 297M, cause unknown, evidence in `logs/alm_pod_mid/pod_evidence/`); V3 running | H100 pod (tmux `aftermid`) | ~10:45 | candidates + blind scoring and imitation pods start on their own (models pulled from B2) |
| 590M style encoder (`style_pod.py --size mid`; trains, then benchmark, threshold, blind scoring, imitation on the pod) | tmux `encmid`, waits for RunPod balance >= $90 | ~11 h after start | merge results; unblind |
| Training pod cleanup (tokens off the stopped pod) | tmux `midclean`, retries start every 5 min (RunPod HTTP 500) | when the host frees | pod stopped, snapshots kept for the owner |
| Weekly corpus B2 backup | paused (`kill -STOP 60610`) to free upload bandwidth | | **resume with `kill -CONT 60610`** after the pod uploads |

## Waiting on the owner

- **RunPod top-up** (owner added it 2026-11-09 ~09:00; API still shows ~$53).
- **590M V1/V2**: investigate now or after the analysis.

- **Delete the mid pod's full snapshots** once its tests pass: ask the owner at that moment.

## Decided

- **Every model size runs every model-based test** (owner; Amendment 37): 125M, 297M, 1B side by side, none the headline.
- **6.1 both ways** (owner, Amendment 33): registered and achievable rules plus the false-match ladder, all reported.
- **1B replaced by the 590M mid with QK-norm** (owner, Amendment 39); a 1B restart stays possible later.
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
