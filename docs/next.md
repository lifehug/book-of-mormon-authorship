# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Running

| Job | Where | Done (est.) | When it ends |
| --- | --- | --- | --- |
| BOM-27 **590M mid model** (`large_pod.py --size mid`, tmux `midpod`; Amendment 39) | 2 x H100 pod `j4rz95isd68egw`, cap $345 | ~Mon 00:30 (step 38,368 of 48,931 at 16:15 Sun; val loss 2.232 at 37k) | `after_mid.sh` (tmux `aftermid`): benchmark, candidates, imitation; then blind ALM scoring at mid; then **ask the owner** before deleting the pod's full snapshots |

## Done today (2026-11-07)

- QK-norm stability test passed (`data/stability/`); 590M launched.
- Sweep: masking (0.93% of 464M words), index (style step on an H100 after two Mac GPU hangs), calibration: true author first 27-35%, **not usable** by 6.6; expected false leads 0.035 per query, so any lead is surprising (BOM-47).
- Blind run: sealed (211 ids: 168 chunks, 43 decoys); Amendment 33 filed (both 6.1 readings + false-match ladder); scored blind in a fresh session: classic, dating, style, ALM 125M and 297M, sweep. Only the 590M's ALM remains before unblinding.
- Fixed: the data/corpus link (an rsync fetch had replaced it; nothing lost), pod cleanup, stall detection.

## Waiting on the owner

- **Delete the mid pod's full snapshots** once its tests pass: ask the owner at that moment.

## Decided

- **Every model size runs every model-based test** (owner; Amendment 37): 125M, 297M, 1B side by side, none the headline.
- **6.1 both ways** (owner, Amendment 33): registered and achievable rules plus the false-match ladder, all reported.
- **1B replaced by the 590M mid with QK-norm** (owner, Amendment 39); a 1B restart stays possible later.
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
