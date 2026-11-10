# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Running

- tmux `b2a43`: B2 backup of the Amendment 43 candidate weights (mid), the registered originals
  and the Amendment 44 weights. Writes `logs/b2_a43.done`.
- tmux `jsmask`: King James masking of the BOM-73 texts (`logs/js_time_mask.log`); then
  `python -m eval.js_time measure`.

## Next, in order (owner, 2026-11-10: the paper first, written in full, before any Part 2 stage)

1. **BOM-36: rewrite the paper on outline version 2** (`paper/outline.md`, sections 1-13): per-model
   "best at" tables; ranking vs matching; post-1830 samples; the Joseph Smith deep dive; the CES
   Letter books one by one (confirm the Letter's book list first); model size (4.x); Part 2 (13).
   Then the explainers and results docs to match, and the 46 pending review-response rows.
2. **BOM-73** (Amendment 46 filed): everything fetched and assembled; masking running; then
   measure and write the result into paper 10.1. Owner decisions pending: D3 (run the registered
   feature sets post hoc?), claim c09's re-grade, `docs/index.md` (asked).
3. **BOM-37** release prep: **owner's go-ahead to publish**; Zenodo needs the owner's login.
4. Blog post with the results (after the owner reads the paper).
5. **Part 2 Stage 0** (BOM-74 to BOM-77; milestone "Part 2 · Stage 0"): after the paper is written.
   **Stage 1 needs the owner's go** after reviewing Stage 0's results. Later: BOM-72.

## Decided

- **Every model size runs every model-based test**, reported side by side; no averaging across
  methods and no headline model; "best at X" judged on known answers only (owner, 2026-11-08/10).
- **Mask only Book of Mormon quotations** in candidate samples (Amendment 43).
- **Publish every model**, fine-tunes included; private corpus text never (owner, 2026-11-09).
- **Register placebo** (BOM-76): primary group died before September 1827; secondary group born
  after 1830 with no exposure, reported separately (owner, 2026-11-10).
- **Part 2 order**: paper first; Stage 0 committed; Stage 1 only on the owner's go (2026-11-10).
