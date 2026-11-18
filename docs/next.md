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

- **The lab, 2026-11-18 (BOM-97):** registry (`data/lab/`), rule sets (`lab.views`), the door (`lab/door.py`), five skills (`.claude/skills/lab-*`), docs (`docs/lab/`). Study tagged `study-v1`; `master` protected (pull request + 1 approval for collaborators; admins may push; no force-push). **Waiting on the owner:** word that HathiTrust has approved adding researchers, before any read-only B2 key is made (`docs/lab/access.md`). Not built: a keyword index over all texts (the `phrase` command reads files, so it is slow beyond a few thousand works); meaning search over newspapers (not in the passage index).
- **Release prep, 2026-11-16 (owner posting the blog at lifehug.com/book-of-mormon):** README rewritten for the finished study; the seven Hugging Face cards updated; the second style encoder published at `etherfuse/bom-authorship-style-encoder` `v2/`; repo website field set. A site bundle (page, parts, link list, context file) was handed over as a zip.
- **BOM-89 further known books: done 2026-11-14.** 727 known books: true author first 34%, top 10 59%, top 100 76.5%; cross genre (212) 17 / 38 / 56. In the paper, blog and outline. Details on issue #100.
- **BOM-96 "the problem of nobody": done 2026-11-14.** `data/sweep/nobody.json`: at 95% of true authors confirmed, false pairs accepted: second encoder 33%, LambdaG 56%, author models 78-88%, two modern style models 83-88% (bar 5%). In paper 5.4, the blog page (section 4) and the blog log. Left: read the cited papers in the originals; LUAR not run. Issue #107.
- **Nothing is running.**
- No GPU pods exist (the stopped pod from the failed run was deleted 2026-11-14 with the owner's OK).

## Now (owner, 2026-11-14): strengthen the paper, then write it. One paper, Phase 1 leads.

1. **More known books:** done (727).
2. **A known-answer test in the Book of Mormon's own genre:** done (`data/sweep/bom_genre_check.json`).
3. **Clean the names in the top lists:** done 2026-11-14 (`top_people` in `data/sweep/bom_ranking.json`).
4. **Write the paper** (BOM-36): first full draft done 2026-11-14 (`paper/paper.md`, assembled from `paper/draft/v3/sec00-sec14.md` and `appendix.md` by `python scripts/assemble_paper.py`; AI-simulated fact-check in `paper/review/v3-factcheck.md`, its corrections applied). Left: the 727-book numbers, the 8 CHECK marks, the "could not verify" list at the end of the fact-check, the appendices (still the 2026-11-10 text), the owner's read.

## Phase 2 fixed path: done 2026-11-14 (about $50; tracker #106)

1. Sweep and alive list (BOM-89, BOM-91; $25.10): second style encoder, closest-episode score; the top 1,000 of the 18,288 possible authors holds the true author for 90% of known books (82% cross genre). 6,016 alive in 1829, 5,584 dead or too young, 12,275 unknown.
2. Procedure frozen before the Book of Mormon was touched: commit 9ed5940 (`eval/library_bom.py`, config `library_search`).
3. Shared pool (BOM-94; $16.98): on 1,000 library authors the style encoder finds the true author first for 66% of known books, equal-dose author models for 42-44%. The plan changed for that reason (owner approved): the encoder ranks, the models are a second opinion.
4. The Book of Mormon (BOM-95; free, plus $3.50 for the second opinion and $3.70 lost to a failed run): `data/sweep/bom_ranking.json`, `bom_second_opinion_pilot.json`. Joseph Smith's revelations first or second of 23,872 at every profile size; library top is the prophet John Wroe and Quaker ministers' journals; 6-9 of each top 20 are dead authors. X beside it: true author first 38%, top 10 66%, top 100 80.5% (cross genre 29 / 52 / 68).
5. Write-up material: `paper/blog.md` Log (2026-11-14, two entries), `paper/outline.md` section 14, `docs/method-improvements.md` #16-20.

## Waiting on the owner

- The Phase 1 blog draft (`paper/blog-phase1.html`, on the Desktop) waits for a read-through.
- Whether to write the Phase 2 blog as its own page or as a section of the Phase 1 page.

## Left over, not blocking

- BOM-90: explain the 297M reproduction gap (same pick on 1,065 of 1,070, largest score difference 0.0047), then close.
- BOM-91: non-person flag for pen-names and bare surnames; one author under two name forms (William Savery); place of publication.
- Not run: 297M or 590M author models on the library; the encoder at more known books.

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
