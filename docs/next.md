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

- **BOM-89 step 2 (Mac, tmux `episodes`, log `logs/sweep_episodes.log`, started 2026-11-13 17:35, about 23 h):** `python -m sweep.index episodes` (one style vector per 8-passage episode for every sweep unit; resumes from `data/corpus/sweep/episodes/part_*.npz`; rerun the same command if the session is gone). Then score by an author's closest episodes and report coverage at K by genre group, as `python -m sweep.coverage` does.
- **Nothing on GPU; all pods terminated.** BOM-90's list-size runs finished 2026-11-13 (three sizes, about $31.60); its write-up into the blog log, outline and method record is still owed.

## Sweep plan (BOM-89, issue #100; priced 2026-11-13)

1. Coverage by genre (done, `data/sweep/coverage.json`): top 100 of 23,872 holds the true author 83% of the time when the profile is in the book's genre, 56.5% when it is not (the Book of Mormon's case).
2. Per-episode fingerprints, existing encoder (running, Mac, free).
3. Retrain the encoder: more data (the BOM-30 log shows it memorised its 7,673 authors; held-out accuracy flat from step 1,000), different-genre positives, same-genre decoys, confirmed-identity authors held out. Data prep on the Mac (free); training about 4.5 H100-hours, about $35-50. **Needs the owner's go.**
4. Re-ranker on the top 100-500, only if still short: about $45-60. **Needs the owner's go.**

## Waiting on the owner

- Go-ahead for step 3's GPU spend (about $35-50). The Phase 1 blog draft (`paper/blog-phase1.html`, on the Desktop) waits for a read-through.

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
