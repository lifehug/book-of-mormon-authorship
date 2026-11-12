# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Running

- **Nothing on GPU.** Stage 0's GPU work is done (2026-11-11, about $17.50 in all): BOM-75 closed
  (590M false matches 0.635 [0.588, 0.679]; no method passes), BOM-76 closed (only Ethan Smith
  recognized across works; register rule triggered at 590M by Jacob Ilive), BOM-77 seeds done.
  The Hugging Face upload finished (BOM-72/73, 8e64552).
- **Owner decisions:** BOM-77's larger samples (build or skip); borrowing tests on Ilive's *Book of
  Jasher* (the plan's trigger for a high-ranking placebo writer); Stage 1 go/no-go (bar: 0.585).
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
