# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"). Checked every
hour by a scheduled check-in, and whenever a job reports. Rules: never two GPU jobs on the Mac at
once; rented GPUs only within approvals already given; every new analysis gets its plan and
amendment first; the issue comment carries the next action.

## Running

| Job | Where | Started | Done (est.) | When it ends, start |
| --- | --- | --- | --- | --- |
| BOM-27 1B training (`scripts/large_pod.py`, tmux `largepod`) | 4 x H100 pod | 2026-11-06 07:17 | 2026-11-07 ~14:30 | 1B benchmark (primary, V1-V3) on an H100 via `alm_pod.py` with `large`; publish (BOM-66); pick the working model by the benchmark |

## Next, in order (start the first whose inputs exist; several may run at once if they use different machines)

1. **BOM-26 triage** - count hits per search, pick the registered sample, cost the model calls, plan + amendment, then a paced run (500 calls/h, 2 workers) in the background. Mac CPU / hosted model.
2. **BOM-39 + BOM-47 sweep** - author profiles for every qualifying author (classical signal + style fingerprints), calibration on 200 held-out books from the 834 held-out authors, the expected false-lead count written down. Mac.
3. **BOM-29 dating cross-check** - the remaining "transformer cross-check" with the time-locked models. Mac.
4. **BOM-68** - one table of all methods on equal terms; GPT-2 ablation amendment and runs (125M on the Mac, 355M on a short GPU run).
5. **BOM-33 / BOM-34 evidence** - access and dictation evidence tables; research, no compute.
6. **BOM-28 candidate models** - after the 1B benchmark picks the working model: one fine-tuned copy per candidate author (GPU, a few hours).
7. **BOM-31** robustness to deliberate imitation.
8. **BOM-32** the blind run, when 26-31 and 39 are done.
9. Then 35, 42, 36, 38, 37.

Side issues as capacity allows: BOM-49, 51, 61, 63; BOM-50 and 53 deferred.
