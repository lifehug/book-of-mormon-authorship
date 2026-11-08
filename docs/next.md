# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Running

| Job | Where | Done (est.) | When it ends |
| --- | --- | --- | --- |
| BOM-27 **590M mid model** (`large_pod.py --size mid`, tmux `midpod`; Amendment 39) | 2 x H100 pod `j4rz95isd68egw`, cap $345 | ~Mon 01:00 | `after_mid.sh` (tmux `aftermid`): benchmark, candidates, imitation; then blind ALM scoring at mid; then **ask the owner** before deleting the pod's full snapshots |
| BOM-47 plausibility gate on the 100 gate-sample authors (research agent, blind to scores) | agent | tonight | chance survival rate beside the expected false-lead count |

## Done today (2026-11-07)

- QK-norm stability test passed (`data/stability/`); 590M launched.
- Sweep: masking (0.93% of 464M words), index (style step on an H100 after two Mac GPU hangs), calibration: true author first 27-35%, **not usable** by 6.6; expected false leads 0.035 per query, so any lead is surprising (BOM-47).
- Blind run: sealed (211 ids: 168 chunks, 43 decoys); Amendment 33 filed (both 6.1 readings + false-match ladder); scored blind in a fresh session: classic, dating, style, ALM 125M and 297M, sweep. Only the 590M's ALM remains before unblinding.
- Fixed: the data/corpus link (an rsync fetch had replaced it; nothing lost), pod cleanup, stall detection.

## Waiting on the owner

- **Delete the mid pod's full snapshots** once its tests pass: ask the owner at that moment.

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
