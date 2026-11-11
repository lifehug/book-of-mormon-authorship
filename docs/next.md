# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Running

- **Hugging Face upload** of the candidate weights (tmux `hfpush`, log `logs/hf_candidates_push.log`),
  one stream (~6 MB/s), with `scripts/net_guard.sh` (tmux `netguard`) pausing it on packet loss.
  If it dies, rerun the same tmux command; the Hub skips what it holds. No B2 prune (BOM-88).
- **Stage 0 chain 1** (tmux `stage0`, `scripts/stage0_chain.sh`, log `logs/stage0_chain.log`):
  waits for the upload to end and a clean network, then BOM-75's language-model runs, pilot, base,
  mid (`alm_pod.py --part2`, caps $10/$15/$30). Then `python -m eval.open_set rescore --part2`.
- **Stage 0 chain 2** (tmux `stage0b`, `scripts/stage0_chain2.sh`): after chain 1, one pod per size
  for BOM-76 (`eval.part2_decoys lowo`, `placebo`) and BOM-77's seeds (`eval.part2_seeds run`), caps
  $15/$25/$45. Then `python -m eval.part2_decoys report` and `python -m eval.part2_seeds report`.
  Each pod waits for the RunPod balance to cover its cap + $5 (owner is topping up).
- **Done without GPU:** BOM-74 (Amendment 47); BOM-75's draw (Amendment 48, 16 authors, 430 tests)
  and classical scores (General Imposters false matches 0.794 [0.756, 0.827]).
- **Not started:** BOM-77's larger samples (needs source text and attribution decisions; ask).
- **Then:** commit the HF manifest and `data/kjv_mask/js_time/`.

## Next, in order (owner, 2026-11-10: the paper first, written in full, before any Part 2 stage)

1. **BOM-36: rewrite the paper on outline version 2** (`paper/outline.md`, sections 1-13): per-model
   "best at" tables; ranking vs matching; post-1830 samples; the Joseph Smith deep dive; the CES
   Letter books one by one (confirm the Letter's book list first); model size (4.x); Part 2 (13).
   Then the explainers and results docs to match, and the 46 pending review-response rows.
2. **BOM-73 done** (closed): influence not supported; result in paper 10.1. Owner decisions pending:
   D3 (run the registered feature sets post hoc?), claim c09's re-grade, `docs/index.md` (asked).
3. **BOM-37** release prep: **owner's go-ahead to publish**. No Zenodo deposit (owner, 2026-11-11).
4. Blog post with the results (after the owner reads the paper).
5. **Amendment 44/45 weights** (B2 `alm/a44`, 86.9 GiB, pushed from the pod, not on the Mac): check
   whether they are on Hugging Face; if not, stage and publish them like the others (keep and
   publish every weight).
6. **Part 2 Stage 0** (BOM-74 to BOM-77; milestone "Part 2 · Stage 0"): after the paper is written.
   **Stage 1 needs the owner's go** after reviewing Stage 0's results.

Before done: **BOM-88** (#99), final storage pattern (corpus + index in B2; models on Hugging Face
only; PRO decision). Then, last: **BOM-87** (#98), clean up published Hugging Face
repos to the base-and-candidate guideline (benchmark-finetunes weights, 146 GB; owner confirms first).

## Decided

- **Hugging Face: base and candidate models only** (owner, 2026-11-11). Enough to replicate;
  other fine-tunes (Stage 0 included) publish scores, not weights.

- **No more OSF filing** (owner, 2026-11-11). Amendments are recorded in the repo only
  (preregistration.md section 11 + config, committed before the results they govern).

- **Main outputs are the paper and the blog** (owner, 2026-11-11); no Zenodo deposit. Everything
  else stays public for replication; a tagged GitHub release still gets a DOI automatically.

- **BOM-72 dropped** (owner, 2026-11-11): the discarded benchmark fine-tunes (main, V1, V2,
  imitation) are not rebuilt; no result depends on them and the transfers drop the owner's remote
  connection. Rebuildable from the published base models, code and config.

- **Every model size runs every model-based test**, reported side by side; no averaging across
  methods and no headline model; "best at X" judged on known answers only (owner, 2026-11-08/10).
- **Mask only Book of Mormon quotations** in candidate samples (Amendment 43).
- ~~Publish every model~~ superseded 2026-11-11: base and candidate models only; private corpus text never.
- **Register placebo** (BOM-76): primary group died before September 1827; secondary group born
  after 1830 with no exposure, reported separately (owner, 2026-11-10).
- **Part 2 order**: paper first; Stage 0 committed; Stage 1 only on the owner's go (2026-11-10).
