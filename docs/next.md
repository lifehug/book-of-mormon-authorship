# What runs now and what starts next

The standing queue (owner, 2026-11-06: "when things finish, start something else"; prepare
everything ahead, never sit waiting). A job monitor (`scripts/jobwatch.py`) reports any crash,
stall or finish at once; an hourly check-in walks this file. Rules: never two heavy GPU jobs on the
Mac at once; rented GPUs within approvals given; the issue comment carries the next action.

## Phase 2 goal (owner, 2026-11-13; tracker BOM-92)

Be able to say, with a measured number, "if the author left other writing in this corpus, this
procedure finds him X% of the time", then run it on the Book of Mormon. **Author algorithm** = the
Phase 1 per-candidate models (built); **sweep algorithm** = the library search (to build). Order:
BOM-90 (accuracy by list size, running) -> BOM-93 part 1 (tournament simulation, minutes) -> BOM-91 (clean
labels, free) -> BOM-89 (sweep algorithm) -> BOM-93 part 2 (the real tournament) -> BOM-94 (end-to-end test on known books: X) -> BOM-95
(the Book of Mormon). Experimenting: no amendment before each run.

## Running

- **BOM-89 steps 2 and 3 (rented H100, pod `bom89-style-v2`; Mac driver in tmux `stylev2`, log `logs/style_pod_v2.log`, state `logs/style_pod_v2/state.json`; started 2026-11-13 evening; owner approved, cap $55, expected $25-35, about 8 h):** `python scripts/style_pod.py --issue 100 --cap 55 --size v2`. Uploads (about 5 GB, throttled to 2 MB/s), then on the pod `scripts/style_v2_job.sh`: per-episode sweep vectors with the BOM-30 encoder, `style_embed.v2 train` (20,000 steps), the same vectors with the new encoder; everything comes home checked and the pod is terminated. **If the driver is gone, rerun the same command** (it resumes from its state). Events are posted on issue #100.
- **Then (Mac, minutes):** score coverage at K by genre group for (a) the old encoder per episode, (b) the new encoder whole-profile, (c) the new encoder per episode, beside `data/sweep/coverage.json`. The scoring module (`sweep/episodes.py`) is not written yet.
- The Mac's own step 2 run was stopped at 1,000 units when the owner chose the GPU; its parts in `data/corpus/sweep/episodes/` are kept and unused.

- **BOM-94 step 3 (rented H100, pod `bom-bom94-pilot`; Mac driver tmux `bom94`, log `logs/bom94_pilot.out`, state `logs/pod_jobs_bom94_pilot/`; started 2026-11-13 night; cap $30, estimate about $18):** `python scripts/pod_jobs.py --name bom94_pilot --issue 104 --files logs/bom94_files.txt --extra data/corpus/timelocked_lm/runs/pilot/model.pt --jobs 'python -m eval.library_pool run pilot' --fetch data/sweep/pool_pilot.npz --cap 30` (rerun to resume). About 4,000 equal-dose 125M models (1,000 authors: three small slices and one large) scored on the 200 known books' 373 test chunks. **Price check:** the pod prints seconds per model every 100 models (`ssh podjobsbom94pilot tail /workspace/jobs.out`); the estimate assumes about 4 s; above about 8 s, stop and tell the owner. **Then:** write `eval.library_pool report` (accuracy and top-N by list size to 1,000, raw and scaled, small against large dose, by genre group; sweep-chosen lists inside the pool).
- **BOM-91 life dates (Mac, tmux `people`, log `logs/people_lookup.log`; started 2026-11-13 evening, about 9 h; owner approved the outside lookup):** `python -m sweep.people lookup` (Library of Congress name file for 13,077 undated authors and a 500-author known-answer check; resumes; cache committed every 30 min by tmux `peoplecommit`). Then `python -m sweep.people build`. Catalog dates alone: 5,230 alive in 1829, 4,672 dead or too young, 13,973 unknown. Details on issue #102.

## Fixed path to the conclusion (owner approved, 2026-11-13 night; replaces the open-ended order of work)

**The conclusion to reach:** "We searched every author alive in 1829 in the library. These rate highest. On known books this procedure puts the true author in its top N about X% of the time." Beside it: where the Phase 1 candidates (Joseph Smith's revelations and the others) rank against the library's top. It will not say "one of these wrote it".

Audit findings behind this (2026-11-13):
- The sweep had no stopping rule. A wide shortlist (500-1,000) covers for an imperfect sweep; 1,000 author models cost about $33 at 125M.
- The Phase 1 candidates are manuscripts and are not in the library; they must be added to the final ranking.
- Sample size biases the ranking (Phase 1, Amendment 45): every author model is trained on the same amount (equal dose).
- The top may be a genre, not a person: dead authors stay in as decoys.
- The author algorithm is measured only up to lists of 55; the plan relies on 500-1,000.
- Validation needs one shared pool of about 1,000 author models scored against every test book (about $35-70), not a shortlist per book ($300+). Random lists are easier than sweep-chosen ones, so this is an upper bound; say so.

| # | Step | Issue | Cost | State |
| --- | --- | --- | --- | --- |
| 1 | Better sweep (new encoder, per-episode vectors) and the alive list (life dates) | BOM-89, BOM-91 | about $30 | running 2026-11-13 night |
| 2 | Freeze the whole procedure in the config in one commit before the Book of Mormon is touched: gallery (alive, real people), shortlist size, model size, equal dose, passages, raw and scaled scores, decoys, what is reported | BOM-93 | free | to do |
| 3 | Validate on known books: one shared pool of about 1,000 equal-dose models; accuracy and top-N at list sizes up to 1,000; with the sweep's coverage this gives X | BOM-94 | about $35-70 | to do |
| 4 | The Book of Mormon: shortlist of 1,000 + Phase 1 candidates + dead-author decoys | BOM-95 | about $35-70 | to do |
| 5 | Write up: the top 20, X, the caveats | BOM-95 | free | to do |

**Sweep stopping rule:** after tonight's run, measure coverage at 1,000 on the alive-only gallery for the cross-genre known books (now 76% on the full gallery with the old encoder). The best of the three variants (old encoder per episode, new encoder, new encoder per episode) is taken and sweep work stops, whatever the number; it is reported as part of X. Only if it is below the old encoder's own figure does anything more get tried.

**Dropped from this path:** the re-ranker, a model for every author in the library, the 590M size, heats (they equal a straight ranking). Place of publication (American / Northeast) is a free tag if the source records give it easily, not a gate.

Total about $100-170 and a few days. Exploratory throughout; step 2's commit timestamp is the record of what was fixed before the result.

## Waiting on the owner

- The Phase 1 blog draft (`paper/blog-phase1.html`, on the Desktop) waits for a read-through.

## Done 2026-11-12 (details in the blog's Log and the issues)

- Amendments 52-56: head-to-head settled by author on 55 authors (ours better than all four older
  methods at every size); "none of these" normalisation tried and failed; later revelations;
  chunks by length. Outline v3 (`paper/outline.md`), method record (`docs/method-improvements.md`),
  holdings index (`docs/holdings.md`), research check (`docs/research/2026-11-12-easy-wins-and-sota.md`).

## Next, in order (owner, 2026-11-10: the paper first, written in full, before any Part 2 stage)

1. **BOM-36: rewrite the paper on outline version 3** (`paper/outline.md`; after BOM-90 is decided): per-model
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
