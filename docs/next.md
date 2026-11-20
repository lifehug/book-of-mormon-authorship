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

- **B2 backup gap (BOM-98, #109): closed 2026-11-18.** `scripts/b2_backup.sh upload` had failed on every run from 2026-11-11 (empty-array error under macOS bash), the weekly job of 2026-11-15 included. Script fixed; the catch-up ran 2026-11-18 12:03-14:14 UTC (9.27 GiB new) and its check found 0 differences over 2,449,012 files. A failed weekly run now writes `weekly FAILED` to the log and shows a desktop notice; `scripts/b2_backup.sh status` reports it.
- **The lab, 2026-11-18 (BOM-97):** registry (`data/lab/`), rule sets (`lab.views`), the door (`lab/door.py`), five skills (`.claude/skills/lab-*`), docs (`docs/lab/`). Study tagged `study-v1`; `master` protected (pull request + 1 approval for collaborators; admins may push; no force-push). **HathiTrust approved adding researchers on 2026-11-18** (each signs the researcher agreement and is added to the owner's; then the read-only B2 key; `docs/lab/adding-a-researcher.md`). No researcher added yet. Not built: a keyword index over all texts (the `phrase` command reads files, so it is slow beyond a few thousand works); meaning search over newspapers (not in the passage index).
- **Release prep, 2026-11-16 (owner posting the blog at lifehug.com/book-of-mormon):** README rewritten for the finished study; the seven Hugging Face cards updated; the second style encoder published at `etherfuse/bom-authorship-style-encoder` `v2/`; repo website field set. A site bundle (page, parts, link list, context file) was handed over as a zip.
- **BOM-89 further known books: done 2026-11-14.** 727 known books: true author first 34%, top 10 59%, top 100 76.5%; cross genre (212) 17 / 38 / 56. In the paper, blog and outline. Details on issue #100.
- **BOM-96 "the problem of nobody": done 2026-11-14.** `data/sweep/nobody.json`: at 95% of true authors confirmed, false pairs accepted: second encoder 33%, LambdaG 56%, author models 78-88%, two modern style models 83-88% (bar 5%). In paper 5.4, the blog page (section 4) and the blog log. Left: read the cited papers in the originals; LUAR not run. Issue #107.
- **Issues, 2026-11-18 (owner: the study is done; issues stay open only for research into better or bigger models).** Everything else closed, each with its state at closing. Open: **better** = BOM-99 (a known-answer test for the scripture voice), BOM-100 (subtract the voice), BOM-101 (train the encoder against the voice); **bigger** = BOM-78 to BOM-86 (Part 2: 1.3B and up, newspapers, all English before 1830). None started; Part 2 stage 1 needs the owner's go.
- **New tests, written up 2026-11-18 (owner: an issue for each, with how to do it; none started):** BOM-102 translation marks, BOM-103 dating the debates (replaces BOM-63), BOM-104 Joseph Smith's other dictated texts and the Lectures on Faith, BOM-105 prophets in two voices (shares its set with BOM-99), BOM-106 spoken or written, BOM-107 chiasmus against the library, BOM-108 the names. All lab work; suggested order 102, 103, then 105. **Sources fetched 2026-11-18** (`python -m lab.sources fetch`; 78 of 79, about 1.2 GB; record in `data/lab/sources.json`; Moses and Abraham manuscripts included, on the owner's word that the 25 October decision holds). **Catalogue records for the translation labels pulled 2026-11-18** (`python -m lab.sources marc`, 72 minutes): all 62,163 HathiTrust records; 2,642 marked as translations (MARC 041 first indicator 1), 2,007 name the original language; `data/corpus/lab/sources/translation_labels/hathitrust_marc.jsonl`; checksums for all open lab sources in `data/manifests/lab_sources.jsonl` (6,878 files). Left to save by hand in a browser: about ten papers on sites that refuse programs (list in the research file). **Name lists for BOM-108 researched 2026-11-19** (`docs/research/2026-11-19-name-lists-for-bom-108.md`; none fetched yet): Hebrew inscription names found (DAHPN, 874 names, CC BY-SA; Golub, 524 names); Egyptian open lists stop before the Late Period, which sits in Trismegistos (owner to decide: email Leuven for an export, or not); about twenty period and control lists located. Next action: add these to `lab/sources.py` and fetch on the owner's word. **Sources researched 2026-11-18** (`docs/research/2026-11-18-sources-for-new-tests.md`, and a comment on each issue): BOM-103 and BOM-107 need nothing from outside; BOM-106 needs one download (Old Bailey corpus); BOM-104's Moses and Abraham texts wait on the owner's call about the Joseph Smith Papers terms.
- **The book's setting, 2026-11-20 (owner: Native American names were missing; what could be tested about the setting; an issue for each).** Nine tests written up, none started: BOM-109 where three worlds disagree, BOM-110 the place-name map against chance, BOM-111 the inventory of things, BOM-112 the Dale and Dale checklist made fair, BOM-113 Roper's anachronism tally with a control, BOM-114 numbers and Alma 11, BOM-115 warfare, BOM-116 geography against placebo regions, BOM-117 the Uto-Aztecan claim. Research: `docs/research/2026-11-20-the-books-setting.md`. Suggested order: 110 and 114 (a day each), then 111, 109.
- **Running the tests (owner, 2026-11-20: "let's run all these tests").** One at a time, each with a test card first. **BOM-118 pilot stopped at its known-answer check, 2026-11-20** (paced judging on the subscription, `lab.judge`, haiku: the judge read the claimed archaic sense in 7 of 10 of Skousen's cited verses, bar 8; 1 of 30 ordinary uses misjudged; no library passage judged; code `lab/archaic.py` and `pilot.json` not yet committed, waiting for BOM-110's unfinished file to pass the lab write test; a second attempt with whole paragraphs and sonnet is running; the design also lacks power for rare senses of common words and is being narrowed to the cited verse's frame). **Done: BOM-108** (names: among English-spelled lists 55% closest to King James against 19% for other authors' invented names; 58% one edit or splice from a King James name; the cross-spelling comparison with ancient and native lists is a test of spelling and bears no conclusion; `data/lab/names/result.json`; left: a sound-based version, a real Assyrian list (`pnao.zip` holds no names), Walker's Key re-OCR). **Part done: BOM-114** (no base-twenty lean: 40% of round numbers against 91% in native Mesoamerican texts; the wider number profile failed its known-answer check and was not scored; Alma 11 fits English measures and Roman coins 6 of 8, verdict depends on the random baseline; `data/lab/setting/numbers/result.json`; left: source the catalogue of weight systems, add Christenson's Popol Vuh when fetched). **Done: BOM-126** (claimed sources ranked: Warren and Ramsay in the crowd; Bunyan's book fairly close in meaning but the Faithful trial scene not near Abinadi; Josephus and Foxe closer; `data/lab/reruns/claimed_sources/result.json`; left: story order, the authors' own parallel lists). **Done: BOM-120** (therefore and wherefore: one break in dictation order, inside Ether; order explains it better than narrator; 0 of 264 library works switch as sharply; `data/lab/reruns/mosiah_priority/result.json`; left: the dated revelations). Next, in order: BOM-126 (claimed sources ranked), BOM-110 (place names against chance), BOM-114 (numbers), BOM-108 (names), then BOM-119, BOM-111, BOM-105 with BOM-99, BOM-103. Tests needing a purchase (BOM-118, BOM-122) or an API or GPU cost wait for the owner.
- **Second write-up (owner, 2026-11-20: a separate blog and paper; "a cohesive reasoning, setup, understanding, and comparison for all of these").** `paper/blog-tests.md` is the living draft: why, the four steps every test follows, a side-by-side table of all the tests in five groups (claim, who, compared against before, compared against here, status), results as they land. Update it with every result; the Log in `paper/blog.md` continues as the diary.
- **Stopped 2026-11-20 15:15 PST on the account's usage limit (resets 16:40).** Owner: these tests become a separate blog and paper; run every test needing no purchase, paid model or GPU. Four test agents were started (BOM-126, BOM-110, BOM-114, BOM-108) under the brief in the session scratchpad (`lab_test_brief.md`); the BOM-108 one stopped on the limit after writing only its card folder (`data/private/lab/owner/2026-11-20-names/`), the others likely the same. Nothing of theirs is committed. Next action: check `git status` for their partial files, restart each test from its issue, then BOM-119, 111, 105+99, 103. Pending the owner: approval of about $200 for AI-judged tests (pilots first); 12 papers to save by hand (list given in chat; addresses in the research files).
- **Earlier studies to rerun, 2026-11-20 (owner: rerun as much as is impactful with the data in one place).** Ten written up, none started: BOM-118 archaic vocabulary item by item, BOM-119 early modern syntax against every book, BOM-120 therefore and wherefore in dictation order, BOM-121 voice diversity, BOM-122 Isaiah variants against all commentaries, BOM-123 "secret combinations" by year, BOM-124 New Testament wording before Christ, BOM-125 complexity against other dictated texts, BOM-126 claimed sources ranked, BOM-127 manuscript errors. Research: `docs/research/2026-11-20-studies-to-rerun.md`. Three item lists would need buying (Skousen's *Nature of the Original Language*, Townsend 2025, Eccel 2018). Suggested first: 120 and 126 (a day each, nothing to buy), then 119.
- **Fetched 2026-11-20:** setting texts, place lists, wordlists and Native American names (68 sources; all arrived; 1,326 treaty pages, Aztec name glyph pages, GeoNames, ASJP, the gazetteers); the BOM-108 name lists (49); 13 papers saved by hand by the owner (`data/lab/sources_by_hand.json`). `data/corpus/lab/sources` is 3.4 GB; record `data/lab/sources.json` (195 sources). Clinton's 1818 memoir came back short (4,323 words; a pamphlet). B2 backup of `lab/sources` last run 2026-11-20 14:43, before the last 35 sources: the weekly run picks them up.
- **Running since 2026-11-20: Trismegistos People** (tmux `tm_people`; `python -m lab.sources tm`; log `logs/lab/sources_tm.log`). The site's open per-person service at one request every 3.2 s, about 18 days; resumes itself (rerun the same command). Gives name, date, region; not the language of a name or an Egyptian transliteration, which sit on pages behind a browser check (not touched). Owner asked for the crawl 2026-11-20.
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
