# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"). Checked every
hour by a scheduled check-in, and whenever a job reports. Rules: never two GPU jobs on the Mac at
once; rented GPUs only within approvals already given; every new analysis gets its plan and
amendment first; the issue comment carries the next action.

## Running

| Job | Where | Started | Done (est.) | When it ends, start |
| --- | --- | --- | --- | --- |
| BOM-27 1B training (`scripts/large_pod.py`, tmux `largepod`) | 4 x H100 pod `89wpgyfino58g1` | 2026-11-06 09:51 (relaunch; first launch failed, see BOM-27) | 2026-11-07 ~17:00 | 1B benchmark (primary, V1-V3) on an H100 via `alm_pod.py` with `large`; publish (BOM-66); pick the working model by the benchmark |
| BOM-39 KJV masking of sweep blocks (`kjv_mask.run sweep`, tmux `sweepmask`) | Mac CPU (passim) | 2026-11-06 09:56 | 2026-11-06 late | `sweep.index`: MFW counts and style vectors (Mac GPU), then `sweep.calibrate` |

## Next, in order (start the first whose inputs exist; several may run at once if they use different machines)

1. **BOM-39 + BOM-47 sweep** - plan and Amendment 28 filed (`docs/sweep-plan.md`). Build: units and block sample -> KJV masking of the blocks (passim, about a day) -> MFW counts and style vectors (Mac GPU, about half a day) -> calibration and the expected false-lead count. Mac.
2. **BOM-29 dating cross-check** - the remaining "transformer cross-check" with the time-locked models. Mac.
3. **BOM-68** - one table of all methods on equal terms; GPT-2 ablation amendment and runs (125M on the Mac, 355M on a short GPU run).
4. **BOM-33 / BOM-34 evidence** - access and dictation evidence tables; research, no compute.
5. **BOM-28 candidate models** - after the 1B benchmark picks the working model: one fine-tuned copy per candidate author (GPU, a few hours).
6. **BOM-31** robustness to deliberate imitation.
7. **BOM-32** the blind run, when 26-31 and 39 are done.
8. Then 35, 42, 36, 38, 37.

Side issues as capacity allows: BOM-49, 51, 61, 63; BOM-50 and 53 deferred.
