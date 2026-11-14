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

- **BOM-89 steps 2 and 3: done 2026-11-14 ($25.10).** Stopping rule applied: second encoder, closest-episode score, possible gallery; the top 1,000 holds the true author for 90.0% of known books, 82.3% of cross-genre books (first encoder 90.0 and 79.0). Sweep work has stopped. Details on issue #100.
- **BOM-95 second opinion (rented H100, pod `bom-bom95-second`; Mac driver tmux `bom95`, log `logs/bom95_second.out`, state `logs/pod_jobs_bom95_second/`; started 2026-11-14 about 04:45; cap $10, estimate about $5, about 1 h):** `python scripts/pod_jobs.py --name bom95_second --issue 105 --files logs/bom95_files.txt --extra data/corpus/timelocked_lm/runs/pilot/model.pt --jobs 'python -m eval.library_pool run pilot --name _bom' --fetch data/sweep/pool_bom_pilot.npz --cap 10` (rerun to resume). **Then:** `python -m eval.library_bom second pilot`, commit, post to issue #105, and step 5 (the write-up: blog log, outline section 14, results tables for the Phase 2 blog).
- **BOM-94 step 3: done 2026-11-14 ($16.98).** On the same 1,000-author pool the style encoder finds the true author first for 66% of known books, equal-dose author models for 42-44% (`data/sweep/pool_report_pilot.json`, `pool_fusion_pilot.json`). Step 4 was changed for that reason (owner approved): the encoder ranks, the author models are a second opinion.
- **BOM-95 step 4a: done 2026-11-14 (free).** `data/sweep/bom_ranking.json` (procedure frozen in 9ed5940): Joseph Smith's revelations first or second of 23,872 authors at every profile size; library top is the prophet John Wroe and Quaker ministers' journals; 6-9 of each top 20 are dead authors. Details on issue #106.
- **BOM-91 life dates: done 2026-11-13 night.** 6,016 alive in 1829, 5,584 dead or too young, 12,275 unknown (`data/sweep/people.parquet`); the lookup rule agrees with the catalog on 212 of 219 known answers. Possible gallery: 18,288.

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
| 1 | Better sweep (new encoder, per-episode vectors) and the alive list (life dates) | BOM-89, BOM-91 | $25.10 | **done 2026-11-14**: 90% coverage at 1,000 (82% cross genre); 6,016 alive, 18,288 possible |
| 2 | Freeze the whole procedure in the config in one commit before the Book of Mormon is touched: gallery (alive, real people), shortlist size, model size, equal dose, passages, raw and scaled scores, decoys, what is reported | BOM-93 | free | to do |
| 3 | Validate on known books: one shared pool of about 1,000 equal-dose models; accuracy and top-N at list sizes up to 1,000; with the sweep's coverage this gives X | BOM-94 | about $17 | running (see Running) |
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
