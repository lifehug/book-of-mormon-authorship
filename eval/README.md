# eval/: how to run the evaluations

Validation benchmark, replications of earlier studies, fidelity checks, repair, and the
improvements to the earlier methods; later, imitation robustness, the blind run, and the
Bayesian synthesis.

Issues: BOM-21, BOM-22, BOM-23, BOM-31, BOM-32, BOM-35, BOM-43, BOM-46, BOM-48, BOM-57, BOM-58, BOM-60, BOM-61, BOM-62.

**Keep this file current.** Every command a module lists in its "Usage" block must appear below;
`tests/test_run_guide.py` fails the build if one is missing. Add a row when you add a command.

## Before you start

| You need | For | How |
| --- | --- | --- |
| Python environment | everything | `uv sync --extra align` (a plain `uv sync` removes passim) |
| The corpus, cleaned and masked | everything that reads period texts | `docs/replication.md`; checksums in `data/manifests/` |
| Private data (Joseph Smith Papers transcripts, licensed texts, papers) | Holmes and Larsen controls, fidelity sources, PAN 2014 | `scripts/data_clone.sh` (owner's private repo); otherwise obtain each item from the links in the `SOURCES.md` files |
| Java 17 | MorphAdorner (`replicate holmes`), passim | `brew install openjdk@17` |
| R with `pamr` | `replicate jockers-pamr` only | `brew install r`, then `install.packages("pamr")` into `~/.R/library` |
| Claude Code CLI (`claude -p`) | `speakers label` only (model-assisted, simulated) | its outputs are committed, so you can skip relabelling |

Every analytic setting and seed comes from `config/preregistered.yaml`, so reruns draw the same
samples. Each command writes a stamped JSON (config hash, git commit) beside the others in
`data/benchmark/` or `data/classic/`. Run from the repository root with `uv run`.

## Kinds of code

- **Published method**: reproduces what the original authors did, as faithfully as the sources allow.
- **Check**: compares our code with the authors' published numbers.
- **Registered**: this project's own method, as pre-registered.
- **Improvement** (BOM-60): a tested change; its default never alters the published method.

`paper/methods-report.md` maps each method to all four.

## 1. Benchmark and calibration (BOM-21, BOM-43, BOM-46, BOM-48)

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.federalist` | data | the Federalist Papers, headings and signatures stripped | `data/benchmark/federalist/papers.jsonl` | seconds |
| `python -m eval.power` | registered | minimum sample sizes (section 7) | `power.json`, `power_candidates.csv` | ~1 h |
| `python -m eval.timesplit` | registered | can later writing stand in for earlier? | `timesplit.json` | ~30 min |
| `python -m eval.part2_benchmark [--queue N]` | Amendment 48 | BOM-75: draws the enlarged benchmark's 16 corpus authors (4 genres) by seed, applies the translation and repeated-text rules and the recorded screen (`data/benchmark/part2/screen.json`); `--queue N` lists the first N per genre for screening | `part2/authors.json` | seconds; `--queue` a few minutes |
| `python -m eval.benchmark --part2` | Amendment 48 | BOM-75: the classical methods on all seven tasks (the original three plus four corpus-author tasks) | `part2/benchmark.json`, `part2/thresholds.json` | ~1-2 h on the Mac |
| `python -m alm.benchmark <size> --part2` | Amendment 48 | BOM-75: the language-model method on all seven tasks (one fine-tune per author; run on a rented GPU) | `alm_<size>_p2.json` | ~0.5-2 h per size on one H100 |
| `python -m eval.open_set rescore --part2` | Amendments 25, 47 | BOM-75: the corrected open-set check on the seven-task results (classical and `alm_*_p2`), every rate with its 95% Wilson interval | `part2/open_set.json` | seconds |
| `python -m eval.part2_decoys plan` | Amendment 49 | BOM-76: leave-one-work-out folds for each candidate with two or more works, and the placebo writers' token inputs (Mac) | `part2/decoys_plan.json`; inputs under `data/corpus/alm/part2/` | seconds |
| `python -m eval.part2_decoys lowo <size>` | Amendment 49 | BOM-76: fine-tunes each fold's model and scores every fold's windows with it, the base model and every Amendment 43 candidate model (GPU) | `data/blind/part2/lowo_<size>.json` | ~0.5-1.5 h per size on one H100 |
| `python -m eval.part2_decoys placebo <size>` | Amendment 49 | BOM-76: each placebo writer fine-tuned on two 3,039-token slices (as Amendment 45), scored on the sealed set (GPU) | `data/blind/part2/placebo_<size>.json` | ~10-30 min per size on one H100 |
| `python -m eval.part2_decoys placebo-slices <size>` | Amendment 51 (post hoc) | each placebo writer fine-tuned on up to 12 non-overlapping 3,039-token slices spread through its text, scored on the sealed set; `report` ranks each slice in BOM-76's pool against the revelation model (GPU) | `data/blind/part2/placebo_slices_<size>.json` | ~20-60 min per size on one H100 |
| `python -m eval.part2_decoys report` | Amendment 49 | BOM-76: cross-work recognition per candidate with intervals; placebo writers' median ranks against the revelation model on the Book of Mormon chunks | `part2/decoys_report.json` | seconds |
| `python -m eval.part2_seeds run <size>` | Amendment 50 | BOM-77: every Amendment 43 unit fine-tuned with five more seeds and scored on the sealed set; weights not kept (GPU) | `data/blind/part2/seeds_<size>.json` | ~1-4 h per size on one H100 |
| `python -m eval.part2_seeds report` | Amendment 50 | BOM-77: each unit's mean rank and rank-first share on the Book of Mormon chunks per seed and in the original run, and their range | `part2/seeds_report.json` | seconds |
| `python -m eval.dual_register` | registered | authors with both imitation scripture and other prose | `dual_register.json` | minutes |
| `python -m eval.benchmark` | registered | the validation benchmark: pass or fail per method | `benchmark.json`, `thresholds.json` | ~10 min |
| `python -m eval.open_set rescore` | registered (Amendment 25, post hoc) | the corrected open-set check (threshold from the positives: the score 95% of true authors reach) for every method with a verification score, the original beside it | `data/benchmark/open_set.json` | seconds |
| `uv run bom multiverse` | registered | the benchmark and corpus demo under 54 alternative settings | `results/multiverse/`, copied to `data/classic/` | ~8 h |
| `python -m classic.corpus_run` | registered | the classical methods on 30 corpus authors (BOM-20 demo) | `data/classic/corpus_run.json` | ~10 min |

## 2. Replications of earlier studies (BOM-22)

Report: `paper/replication-report.md`. Run `chapters` first.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.replicate chapters` | data | finds the 239 modern chapters in the 1830 text | `replication/chapters_1830.jsonl` | minutes |
| `python -m eval.replicate jockers` | published method | Jockers et al. 2008 on our candidate texts | `replication_jockers.json` | ~5 min |
| `python -m eval.replicate jockers-data` | published method + check | the same on their deposited counts; swaps in our texts one candidate at a time | `replication_jockers_data.json` | ~10 min |
| `python -m eval.replicate jockers-pamr` | check | their NSC in their own tool, R's pamr | `replication_jockers_pamr.json` | ~2 min |
| `python -m reuse.rare scan` | published method | the rare 4-gram scan of every period volume (`--target bom` for the Book of Mormon) | `data/reuse/<target>/` | ~1 h |
| `python -m eval.replicate johnson` | published method + improvement | Johnson and Johnson 2013; also the registered rarity rule, by copy and by text | `replication_johnson.json` | ~20 min |
| `python -m eval.replicate johnson-examples` | published method | the rare phrases *The Late War* shares with the Book of Mormon, in context, and the other books that use them | `replication/latewar_shared_phrases.json` | ~10 min |
| `python -m eval.speakers label` | data (simulated) | model labels who speaks each part of every chapter, for Larsen | `replication/larsen_speakers.jsonl` | ~30 min |
| `python -m eval.speakers check` | check | speaker word counts against Larsen's Appendix B | printed; `replication/larsen_speakers_check.txt` | seconds |
| `python -m eval.replicate larsen` | published method | Larsen et al. 1980, by narrator and by speaker | `replication_larsen.json` | minutes |
| `python -m eval.replicate holmes` | published method | Holmes 1992, all five variables (needs MorphAdorner) | `replication_holmes.json` | ~5 min |
| `python -m eval.replicate ensc` | published method | Schaalje et al. 2011, ENSC in their design (needs `thresholds.json`) | `replication_ensc.json` | ~5 min |

## 3. Are our versions faithful? (BOM-57)

Report: `data/benchmark/fidelity/REPORT.md`; sources and links: `data/benchmark/fidelity/SOURCES.md`.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.fidelity ensc` | check | published ENSC on the Federalist Papers against Funai 2010; sample-length sweep | `fidelity/ensc.json` | ~10 min |
| `python -m eval.fidelity gi` | check | our General Imposters on PAN 2014 against Kestemont et al. Table 1 (needs PAN data, private) | `fidelity/gi.json` | ~20 min |

## 4. Repair or retire (BOM-58)

Plan, written before the run, and results: `docs/repair-plan.md`.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.repair` | check | candidate repairs, calibrated on the benchmark, tested on 30 fresh authors | `repair.json` | ~2 h |

## 5. Improvements (BOM-60)

Plan, written before any test: `docs/improvement-plan.md`. Report: `paper/methods-report.md`.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.improve delta` | improvement | a "none of these" score for Delta | `improve_delta.json` | ~30 min |
| `python -m eval.improve ensc-size` | improvement | ENSC's text-size model refitted on many authors | `improve_ensc_size.json` | ~10 min |
| `python -m eval.improve gi-rounds` | improvement | General Imposters with 1,000 rounds | `improve_gi_rounds.json` | ~2 h |
| `python -m eval.improve evaluate` | check | the one-time evaluation of every change on a second fresh set of 30 authors, settings read from the development results | `improve_evaluation.json` | ~12 h |

## 6. Known-answer controls (BOM-61)

Plan, written before any test runs on the set: `docs/known-answer-plan.md`.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.known_answer build` | data | the known-answer set: genuine translations of ancient texts and texts presented as ancient, with provenance | `data/known_answer/set.jsonl` | seconds |

## 7. Exact text reuse (BOM-23)

Plan, registered before any run (Amendment 10): `docs/reuse-plan.md`.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m reuse.exact scan` | registered | the lossless prefilter: which of each target's 5-grams every volume in any search contains | `data/reuse/exact/hits.parquet`, `searches.json` | ~80 min |
| `python -m reuse.exact align <search>` | registered | passim on the candidates of one search: `bom:full`, `late_war:full`, `sermon:full`, or `<text>:draw<0-2>` for the known-answer score | `data/reuse/exact/alignments/<search>.json` | minutes to hours |
| `python -m reuse.exact separation` | registered | Amendment 9's rule on the 45 matched-window draws: exact Mann-Whitney, Rowley check, spelling-era check; scores with and without own copies the title rule missed | `data/reuse/exact/known_answer.json` | seconds |
| `python -m reuse.exact sources <search>` | descriptive (post hoc labels) | each source volume of a full table: the years its own text mentions against its catalog year, the seal check, King James share; sorts the Book of Mormon's sources into later quotation, missed Bible text, shared period phrase | `data/reuse/exact/sources/<search>.json` | seconds |
| `python -m reuse.exact redate` | descriptive (BOM-64) | the full tables under the corrected dates: covered share without volumes now dated past each window, and those volumes listed (`separation` adds the known-answer score `score_redated`) | `data/reuse/exact/redated.json` | seconds |

## 8. The King James italics test (BOM-62)

Plan, registered before any count (Amendment 11): `docs/italics-plan.md`.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.italics ranges` | registered | the translation-only ranges of the independent translations, from their layout, before any count | `data/italics/translation_ranges.json` | seconds |
| `python -m eval.italics check` | registered (simulated, model-assisted) | the 100 seeded italic words looked up in page images of the 1828 Phinney Bible; resumes, retries outages | `data/italics/phinney_check.jsonl`, page images in `data/italics/phinney/pages/` | about 1.5 hours |
| `python -m eval.italics measure` | registered | kept / changed / dropped for italic and roman KJV words in every masked span; R_i, R_r, D with bootstrap intervals for the Book of Mormon, 1820s sermons, independent translations and Amendment 9's texts; Amendment 11's check | `data/italics/measure.json` | about 3 minutes |

## 9. The catalog date audit (BOM-64)

Plan, registered before the scan (Amendment 12): `docs/date-audit-plan.md`.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m metadata.dates check` | registered (BOM-56) | title-page check of every volume catalogued with the 1800 placeholder | `data/catalog/date_check.parquet` | seconds |
| `python -m metadata.dates body` | registered | counts year mentions in the full text of every volume dated 1830 or earlier; flags and corrects volumes that name later years | `data/catalog/date_body.parquet` (counts only) | ~5 min, 8 workers |
| `python -m metadata.dates sample` | registered (simulated, model-assisted) | the precision check: 100 flagged and 100 unflagged volumes, printing year read by a model from the opening and closing pages; resumes, retries outages | `data/catalog/date_sample.jsonl` | ~2 hours |

## 10. Semantic parallels (BOM-25)

Plan, registered before any search (Amendment 14): `docs/semantic-plan.md`; story skeletons, Amendment 15: `docs/skeleton-plan.md`. Needs the extra:
`uv sync --extra semantic`.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m semantic.choose` | registered (model choice) | five embedding models on the 1807 Psalms against the King James Psalms: recall at 1 and 10, passages per second | `data/semantic/model_choice.json` | ~20 min |
| `python -m semantic.choose distractors <model>` | registered (model choice) | the Psalms test with a million corpus passages as distractors; `--rescore <model>` measures re-scoring the top k | `data/semantic/distractors_<model>.json` | ~1 h (MiniLM) to ~3 h (bge-small with re-scoring) |
| `python -m semantic.index build [--before <work_id>]` | registered | the passage index of the whole corpus (278,796 volumes, 128-word passages, bge-small); resumes at the first unfinished shard and adds only volumes not yet indexed | `data/corpus/semantic/index/` (vectors and ids, no text; not in git) | ~12 days on the M4 (measured 183 passages/s alone) |
| `python -m semantic.index pack --from <work_id> [--before <work_id>] [--first N]` | registered (same passages) | the remaining volumes' passages from that work id on (up to `--before`; files numbered from `N` so a second batch never collides), with their text, for a rented GPU, plus 20,000 passages of `shard_00000` for the machine comparison | `data/corpus/semantic/pack/` (licensed text: never in git, deleted from the pod after) | ~1-2 h |
| `python -m semantic.index embed-pack --pack <dir> --out <dir>` | registered (same model and settings) | on the GPU: packed passages into `shard_pNNNNN` files of the index format (no text) | `<out>/shard_p*.npy`, `.parquet`, `.done`; `check.npy` | hours on one GPU |
| `python -m semantic.index compare --check <dir>` | - | cosine of the GPU's vectors against the Mac's for the same passages | `data/corpus/semantic/index/gpu_check.json` | seconds |
| `python -m semantic.index status` | - | shards, volumes and passages indexed so far | - | seconds |
| `python -m semantic.search named` | registered | the named proposed sources and their control groups against the Book of Mormon, every passage pair; ranks within group (the null check waits for the index) | `data/semantic/named.json` | ~10 min |
| `python -m semantic.search null` | registered (Amendment 21) | each named source's null: 500 same-window, same-genre, same-length volumes embedded fresh and scored directly like the source; re-scores the source as a check against `named.json`; resumes per volume | `data/semantic/named_null.json`; partials in `data/corpus/semantic/search/named_null_*.json` | ~1 h per source on the M4 |
| `python -m semantic.triage first\|second\|report [--workers 2 --per-hour 500]` | registered (Amendment 27); hosted model (owner's Claude subscription) | BOM-26: sorts 1,069 registered hit pairs into biblical / common / specific (first pass), a blind simulated second review of every SPECIFIC and 10% of the rest, kappa and the pairs both call SPECIFIC | pairs and replies in `data/corpus/semantic/triage/`; `data/semantic/triage.json` (ids, labels, counts) | ~2 h first pass, ~30 min second, at 500 calls/h |
| `python -m eval.grunder_ranks` | `data/access/grunder_sources.csv`; the BOM-23/24/25 outputs | exploratory, not pre-registered: where Grunder's catalog-matched proposed sources rank in the paraphrase, rare-phrase, exact-reuse and story-skeleton searches; proposed vs unproposed volumes by percentile (rank-sum) and stand-out rate (Fisher), overall and by genre; top 20 | `data/semantic/grunder_ranks.json` | seconds |
| `python -m semantic.corpus queries` | registered (Amendment 14) | query passages of the Book of Mormon, the known-answer texts and the masked retellings, their vectors and per-query bars (best of 10,000 window passages) | `data/corpus/semantic/search/q_*.npz`, `null_*.npy` | ~30-60 min |
| `python -m semantic.corpus scan` | registered | one exact pass over the passage index: the 100 nearest passages per query in the Book of Mormon's window and in each matched draw, rescored in full precision; resumable | `data/corpus/semantic/search/scan_state.npz` | ~1 h on the M4 GPU |
| `python -m semantic.corpus score` | registered | source scores, 500-volume genre/length null, bootstrap intervals and the top sources for the skeleton test; Amendment 9's known-answer score and separation; the King James retelling controls | `data/semantic/corpus_bom.json`, `parallels_bom.parquet`, `corpus_known_answer.json` | ~15 min |
| `python -m semantic.skeleton check` | registered (extractor check) | 20 King James chapters, events extracted twice by the hosted model and judged against the chapter; sets the event-match threshold | `data/semantic/skeleton/check.json` | ~2 min, 60 model calls |
| `python -m semantic.skeleton controls` | registered | the retelling positive controls (Josephus, Twelve Patriarchs, Jasher against their King James ranges and 20 unrelated books each); stops on a usage limit and resumes | `data/semantic/skeleton/controls.json`; events in `data/corpus/semantic/skeleton/events/` | hours, ~3,500 model calls |
| `python -m semantic.skeleton bom` | registered | the Book of Mormon's event sequence against the named sources and their control groups, aligned with an order test | `data/semantic/skeleton/bom.json` | hours, ~3,500 model calls |
| `scripts/skeleton_loop.sh controls\|bom [args]` | - | reruns a skeleton step every 15 minutes until it finishes (run under tmux) | as above | until done |
| `scripts/skeleton_overnight.sh` | registered | paced run: the extractor check repeated with the lean call (`check --out check_lean.json`), then controls, then bom, at most `PER_HOUR` (500) model calls an hour; every step accepts `--per-hour` | as above, plus `data/semantic/skeleton/check_lean.json` | ~13 h at 500/h |
| `python -m semantic.skeleton top [--workers 2 --per-hour 500]` | registered (Amendment 15) | the Book of Mormon against the top 20 sources of the whole-corpus passage search (`corpus_bom.json`): events of every block (hosted model, paced), alignment score and order p-value per source, no group rank | `data/semantic/skeleton/top.json`; events in `data/corpus/semantic/skeleton/events/` | ~4,200 calls, ~8.5 h at 500/h |

## Other

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m reuse.rare size` | registered | how large the borrowing null must be (BOM-45) | `data/reuse/null_sizing/sizing.json` | minutes |
| `python -m reuse.rare score` | registered score; points 2-5 of the plan post hoc (BOM-24, `docs/rare-plan.md`) | the Book of Mormon's ranked source list from the BOM-22 scan under corrected dates: rare shared 4-grams per 10,000 words (df <= 5 by text, by volume beside it), p against the whole period population, genre percentile, block-bootstrap intervals, named sources, imitation scripture as a group, volumes BOM-64 moved | `data/reuse/bom/rare.json` | minutes |
| `python -m reuse.rare known` | registered (Amendment 9 score) | scans the known-answer texts' 4-grams in BOM-23's matched draws, scores the strongest source per draw, applies the separation rule | `data/reuse/rare_known/hits.parquet`, `known_answer.json` | ~40 min |

## 11. The time-locked base model (BOM-27)

Plan, registered before any training (Amendment 16): `docs/timelocked-plan.md`.

| Command | Registered? | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m timelocked_lm.data select` | registered | the training set: 1780-1830 volumes by corrected year, Book of Mormon copies and contamination hits out, benchmark, candidate and known-answer texts out, 0.5% held out | `data/timelocked_lm/training_set.parquet`, `selection.json` | ~1 min (seal check cached) |
| `python -m timelocked_lm.tokenize train` | registered | byte-level BPE, 32,000 entries, on a seeded 1 GB sample | `data/timelocked_lm/tokenizer.json`, `tokenizer_sample.json` | ~1 min |
| `python -m timelocked_lm.tokenize encode` | registered | every training volume encoded, resumable per file | `data/corpus/timelocked_lm/tokens/` (~50 GB, not in git) | ~2 h on the M4 |
| `python -m timelocked_lm.tokenize status` | - | token files and counts so far | - | seconds |
| `python -m timelocked_lm.train pilot\|base\|large --out <dir>` (several GPUs: `torchrun --nproc_per_node=N -m ...`) | registered | trains the model on a GPU; checkpoints every 20 min and resumes; `tiny --max-steps 20` is a local smoke test | `<dir>/checkpoint.pt`, `model.pt`, `log.jsonl`, `run.json` | pilot ~10-13 H100-h, base ~25-30 |
| `python scripts/large_pod.py --issue 75 [--cap 650 --floor 25 --resume-at 100]` | `~/.config/runpod/token`, `~/.config/backblaze/credentials`; owner's approval (spend) | BOM-27 / Amendment 26: rents a Secure 8 x H100 pod, pulls the tokens from B2 (key on the pod for the download only, then deleted and checked), checks them against the manifest, trains the 1B under torchrun with restarts, pauses below the balance floor, brings the model home checked, deletes the tokens, terminates | `data/corpus/timelocked_lm/runs/large/`; `logs/large_pod/` | ~17 h |
| `python -m timelocked_lm.release convert pilot\|base` | - | BOM-66: maps a trained model onto Hugging Face's GPT-2 class (zero biases, exact GELU), checks its logits against the native model on held-out tokens, saves weights and tokenizer | `data/corpus/timelocked_lm/release/<size>/` | ~1 min |
| `python -m timelocked_lm.release card pilot\|base --repo <owner/name>` | - | the model card (`timelocked_lm/model_card.md` filled from `run.json` and `selection.json`) and `loss_curves.csv` (numbers only) | `README.md`, `loss_curves.csv` in the release folder | seconds |
| `python -m timelocked_lm.release upload pilot\|base --repo <owner/name>` | `~/.config/huggingface/token` (the owner's `etherfuse` account); owner's approval (publishing) | creates the public Hugging Face model repo and uploads the release folder; no training text | `huggingface.co/<owner/name>` | minutes |
| `python -m alm.benchmark pilot\|base [--variant v1]` | registered (Amendments 22, 23) | BOM-28: fine-tunes one copy of the time-locked model per benchmark author (18), scores the benchmark's held-out samples by log-perplexity ratio against the base, closed-set accuracy and open-set FPR as General Imposters'; resumes per author | `data/benchmark/alm_<size>.json`; per-author scores in `data/corpus/alm/benchmark/<size>/` | ~1 h at 125M, a few h at 300M on the M4 |
| `python -m alm.variants v2\|v3 pilot\|base` | registered (Amendment 23) | secondary uses of the time-locked model on the benchmark: v2 a classifier head over each task's authors; v3 the base model's hidden states as features in BOM-21's own trials (cosine nearest centroid, General Imposters); judged by Amendment 22's rule | `data/benchmark/alm_<size>_<variant>.json` | v2 ~1 h at 125M, ~2.5 h at 300M; v3 under an hour |
| `python -m alm.lr_select pilot\|base\|mid [--micro-batch 8]`, then the same with `--rerun` (V1 and V2 at the chosen rates, `--save-weights`) | Amendment 41 (post hoc) | each size's V1 and V2 learning rate chosen from `alm.lr_select_grid` on the benchmark authors' held-out *training* text (never the tests); the reruns at those rates sit beside the registered V1/V2, every fine-tuned copy kept | `data/benchmark/lr_select_<size>.json`, `alm_<size>_v1_lrsel.json`, `alm_<size>_v2_lrsel.json`; weights to B2 | ~1-2 h a size on an H100 |
| `python -m alm.variants v2 pilot\|base\|mid --seed-runs --save-weights` | Amendment 42 (post hoc) | V2 rerun at its registered settings with seeds 1..`alm.v2_seed_runs`, to measure its run-to-run spread (at 125M a rerun moved it from 0.900 to 0.764) | `data/benchmark/alm_<size>_v2_seed<k>.json`; weights to B2 | ~15 min a run at 590M on an H100 |
| `scripts/alm_queue.sh` | - | every benchmark run of the time-locked model, one GPU job at a time: V3 at 125M; when the base model is home, its release (BOM-66) and the 297M primary run; then V1, V2 at 125M and V1-V3 at 297M; then clears the uv cache | `logs/alm_queue.log`, `logs/alm_<run>.log` | superseded 2026-11-05 23:22 by `alm_queue_mac.sh`: the 297M fine-tunes swap on the Mac's 16 GB |
| `scripts/alm_queue_mac.sh` | - | the 125M benchmark variants (V3, V1, V2) on the Mac, one at a time, then clears the uv cache; the 297M runs go to a rented H100 | `logs/alm_queue.log` | ~2-3 h |
| `python scripts/alm_pod.py --issue 38 --files <list> [--size base\|large --cap 15]` | `~/.config/runpod/token`; owner's approval (spend) | the 297M benchmark jobs (primary, V1-V3) on a rented Secure H100: uploads only the files the jobs read (a dry-run list), checks them, runs, brings results home checked, deletes the corpus files, terminates | `data/benchmark/alm_base*.json`; `logs/alm_pod/` | ~1 h |
| `python -m style_embed.data build [--workers 6]` | registered (Amendment 24) | BOM-30: samples 128-token passages (benchmark word form) from the qualifying authors' works; holds out 10% of authors | `data/style_embed/authors.parquet`, `works.parquet`; passages (licensed text) in `data/corpus/style_embed/` | ~20 min on 6 cores |
| `python -m style_embed.train --out <dir> [--tiny --max-steps N]` | registered (Amendment 24) | trains the style encoder (the 297M base model, InfoNCE over two episodes per author); resumes from its checkpoint | `<dir>/style.pt`, `log.jsonl` | ~5 h on an H100 |
| `python scripts/style_pod.py --issue 40 [--cap 50]` | `~/.config/runpod/token`; owner's approval (spend) | rents a Secure H100, uploads and checks the passages and base model, trains, brings `style.pt` home checked, deletes the text, terminates; stops at the cap | `data/corpus/style_embed/runs/style/`; `logs/style_pod/` | ~6 h |
| `python scripts/style_pod.py --issue 100 --cap 55 --size v2` | `style_embed.v2 build`; `sweep.index tokens`; `~/.config/runpod/token`; owner's approval (spend) | BOM-89 steps 2 and 3 on one rented H100 (`scripts/style_v2_job.sh`): per-episode sweep vectors with the BOM-30 encoder, the second encoder's training, the same vectors with the second encoder; uploads throttled to 2 MB/s and SHA-256 checked; brings the encoder and vectors home checked, deletes the text, terminates | `data/corpus/style_embed/runs/style_v2/`, `data/corpus/sweep/episodes_gpu/`, `episodes_v2/`; `logs/style_pod_v2/` | ~8 h |
| `python -m style_embed.benchmark [--model <style.pt>]` | registered (Amendment 24) | the style fingerprints in BOM-21's own trials; Amendment 22's pass rule | `data/benchmark/style_embed.json` | under an hour |
| `python -m style_embed.v2 build [--workers 6]` | `style_embed.data build` (its author split); the genre table | BOM-89 step 3 (exploratory): 256 fresh passages per work for BOM-30's authors, each work's genre, a validation split carved from the training authors (BOM-30's held-out authors stay held out) | `data/style_embed/v2_works.parquet`, `v2_build.json`; passages (licensed text) in `data/corpus/style_embed/v2/` | ~30 min on 6 cores |
| `python -m style_embed.v2 train --out <dir> [--tiny --max-steps N]` | `style_embed.v2 build`; the 297M base model; owner's approval (GPU spend) | a second style encoder for cross-genre retrieval: half the steps draw one genre per batch with each author's positive from another genre, the rest random pairs; validation accuracy every 500 steps picks the kept weights; resumes | `<dir>/style.pt`, `log.jsonl` | ~5 h on an H100 |
| `python -m sweep.units build` | registered (Amendment 28) | BOM-39: the swept authors (named, non-corporate, 10,000+ words in the training set's volumes), up to 20 seeded 1,000-word profile blocks each round-robin over works, the 200 calibration books (style-held-out authors) with their rebuilt profiles and 5,000-word query chunks; ids and offsets only | `data/sweep/authors.parquet`, `blocks.parquet` | seconds |
| `python -m kjv_mask.run sweep` | `sweep.units build`; passim | KJV masking of every sweep block and calibration chunk, BOM-16's frozen settings | `data/kjv_mask/sweep/` | about 20 h (about 470 million words in 659 batches) |
| `python -m ingest.js_time [--limit N] [--delay 1.0]` | - | BOM-73: fetches the comparison writers (`data/js_time/controls.json`, 158 Internet Archive items 1831-44: unexposed periodicals and books, Campbell's *Millennial Harbinger*), resumes from disk | `data/corpus/js_time/text/` | ~1 h |
| `python -m kjv_mask.run js_time` | `eval.js_time assemble`, `ingest.js_time`; passim | KJV masking of Joseph Smith's 1833-44 documents and the BOM-73 comparison texts at BOM-16's frozen settings | `data/kjv_mask/js_time/` | ~1 h |
| `python -m eval.js_time assemble` | `ingest.candidates --manifest data/js_time/sources.json`, `ingest.js_time` | BOM-73 (Amendment 46): Joseph Smith's own-hand and dictated words per 1833-44 document (private), and the units table of every group with year and period | `data/js_time/units.csv`; `data/private/js_time/units/` | seconds |
| `python -m eval.js_time measure [--encoders base,mid]` | `kjv_mask.run js_time`; the style encoders | BOM-73: quotations dropped, comparison blocks on Mormonism dropped, 2,000-word blocks, distance to the masked Book of Mormon by Burrows' and Cosine Delta and the 297M and 590M encoders, bootstrap intervals, slopes against the unexposed group by permutation | `data/js_time/results.json` | ~1 h |
| `python -m eval.bom_quotes check` | `eval.bom_overlap` | Amendment 43's quotation rule as an importable function, checked against `eval.bom_overlap` on *Voice of Warning* | - | seconds |
| `python -m sweep.index tokens [--workers 8]` | `kjv_mask.run sweep` | each unit's words (author profile, calibration profile, query chunk) with KJV spans removed, benchmark word form | `data/corpus/sweep/tokens/`, `units.parquet` (private) | ~25 min |
| `python -m sweep.index mfw` | `sweep.index tokens` | the 300 most frequent words of the author profiles and every unit's relative frequencies over them | `data/corpus/sweep/mfw.npz`, `data/sweep/vocabulary.json` | ~30 min |
| `python -m sweep.index embed [--model <style.pt> --tag _v2]` | `sweep.index tokens`; the BOM-30 encoder | every unit's style vector (Mac GPU; resumes) | `data/corpus/sweep/style.npz` | several hours |
| `python -m sweep.index episodes [--model <style.pt> --tag _v2]` | `sweep.index tokens`; a style encoder (default BOM-30's) | BOM-89 (exploratory): several style vectors per unit, one per consecutive episode of 8 passages of 128 tokens (the length the encoder was trained on), and the whole-unit vector beside them; calibration units first; resumes from its parts | `data/corpus/sweep/episodes<tag>/part_*.npz` (private) | about 23 h on the Mac GPU, under an hour on an H100 |
| `python -m sweep.calibrate` | `sweep.index mfw` and `embed` | BOM-39/47: the 200 calibration books against every swept author under both signals; top-1 rates and the usable verdict, lead thresholds, expected false leads (leave-one-out), signal correlations, the 100 authors for the blind gate | `data/sweep/calibration.json` | minutes |
| `scripts/sweep_chain.sh` | - | waits for `kjv_mask.run sweep` to exit cleanly (its `EXIT` line in `logs/sweep_mask.log`), then runs `sweep.index tokens`, `mfw`, `embed` and `sweep.calibrate`; run a frozen copy under tmux | as those | about a day |
| `python -m ingest.jsp_images original [--pause 15]` | network | BOM-34: the original manuscript's 231 page photographs from the Joseph Smith Papers, one at a time with a pause, for checking the corrections catalog by eye; copyrighted, kept outside git | `data/corpus/jsp_images/original/` | ~1.5-2 h, ~5.8 GB |
| `python -m eval.claims table` | - | BOM-42: the claims register (`data/claims/register.yaml`) filled from the results that exist: each claim's evidence files present or pending, key numbers, untestable claims with their reason; verdicts only from the register | `data/claims/claims.json` | seconds |
| `python -m review.simulate run --draft paper/draft [--model ...]` | the finished draft; the `claude` CLI | BOM-38: three independent SIMULATED reviews (statistician, historian, stylometrist) of the draft and pre-registration only, verbatim, plus a response-plan template | `paper/review/` | minutes (three paced calls) |
| `python scripts/release_check.py [--max-string 400 --max-file-mb 50]` | - | BOM-37: the pre-release checklist (results hold no text, explorer panels load, nothing private tracked, licences, SOURCES.md, manifests, committed and pushed); exits 1 on a failure | stdout | seconds |
| `python -m alm.candidates plan` | registered (Amendment 30) | candidate units (admitted tiers, masked) and four control samples; held-out tails (BOM-32's decoy source); encoded inputs | `data/benchmark/alm_candidates_plan.json`, `data/corpus/alm/candidates/inputs/` | ~10 min |
| `python -m alm.candidates train base\|large [--micro-batch 8]` | `plan`; the working model | fine-tunes and keeps one model per unit; every model scores every held-out window; resumes | `data/corpus/alm/candidates/<size>/` | <1 h (297M), ~2-3 h (1B) on an H100 |
| `python -m alm.candidates validate base\|large` | `train` | closed set among all units and among candidates; 6.1's margin, best control minus candidate | `data/benchmark/alm_candidates_<size>.json` | minutes |
| `python scripts/candidates_pod.py --issue 38 --size base\|large [--cap 25]` | RunPod token; spend approval | the above on a Secure H100, SHA-256 checked both ways, private text deleted and checked | as above | ~1 h (297M), ~3-4 h (1B) |
| `python scripts/pod_jobs.py --name <name> --issue <n> --files <list> [--extra ...] --jobs "<cmd>" ... --fetch <path> ... [--cap 25 --disk 100]` | RunPod token; spend approval; the code pushed | any resumable jobs on a Secure H100: uploads SHA-256 checked, jobs in tmux (restarted only when the pod answers and the job is confirmed gone; an unreachable pod is left alone), results fetched and SHA-256 checked, text and models deleted from the pod and checked, pod terminated; state in `logs/pod_jobs_<name>/` | the `--fetch` paths | as the jobs |
| `python -m blind.seal [--key ~/.bom-blind/key.json]` | Amendment 32 | seals the narrator chunks with decoys; key outside the repo | `data/blind/seal.json`, `withheld.json`; `data/corpus/blind/sealed.jsonl` | minutes |
| `python -m blind.thresholds [pilot base large]` | `alm.candidates validate` at each size; the committed benchmark files | 6.1's match / non-match thresholds per method from benchmark data only: GI (`thresholds.json`), style (`style_embed.json`), ALM margins (`alm_candidates_<size>.json`); commit before the blind run | `data/blind/thresholds.json` | seconds |
| `python -m blind.run [--sizes pilot,base,large] [--only ...] [--sealed <path>]` | every scorer built; a fresh session | scores every sealed id with every method, hashes outputs | `data/blind/outputs/`, `outputs.json` | ~3-4 h |
| `python -m blind.unblind [--key ...]` | outputs committed | checks hashes, applies the key, decoy accuracy, sweep leads, leave-one-candidate-out | `data/blind/unblinded.json` | minutes |
| `python -m synth.model rates [pilot base large]` | `data/blind/thresholds.json`; benchmark results (and `alm_candidates_<size>.json` for the authorial family) | BOM-35: each method family's closed-set accuracy and the shares of benchmark positives and negatives in each 6.1 band, from benchmark data only | `data/synthesis/rates_<size>.json` | seconds |
| `python -m synth.model run [--unblinded data/blind/unblinded.json] [--sizes pilot,base,large]` | `rates`; the unblinded run; `data/benchmark/imitation.json` | 6.7's posterior over the reliable candidates and "not in set" per half and both, with the prior grid, drop-one, equal weights, independent chunks and the secondary candidates; dating, sweep and access beside | `data/synthesis/posterior_<size>.json`, `posterior_sizes.json` | seconds |
| `scripts/mac_gpu_chain.sh`, `scripts/mac_gpu_rerun.sh` | the Mac GPU free | the 125M runs of BOM-28 (candidate models) and BOM-31 (style and model parts); the rerun repeats the fine-tunes at micro-batch 2 after an out-of-memory at 8; frozen copies under tmux | `data/corpus/alm/candidates/pilot/`, `data/benchmark/imitation/` | overnight |
| `scripts/after_mid.sh` | the mid run (`large_pod.py --size mid`) | as `after_1b.sh` for the ~590M mid model (Amendment 39), without publishing (QK-norm needs its own export) | as `after_1b.sh` with `mid` | ~4 h after the mid model |
| `scripts/after_1b.sh` | the 1B driver; `~/.config/runpod/token`, `~/.config/huggingface/token` | waits for the 1B to be home (driver state done, `model.pt` on the Mac), runs `alm_pod.py --size large` (primary, V1-V3 on a rented H100, cap $40), converts, cards and uploads the 1B to `etherfuse/timelocked-1830-1b` (owner-approved), then, every size running every test (owner, 2026-11-06), the 1B candidate and control models (`candidates_pod.py --size large`, cap $40) and the 1B imitation model part (`pod_jobs.py`: primary, V1, V3; cap $40), each on its own H100 at once, and `eval.imitation report`; run a frozen copy under tmux | `data/benchmark/alm_large*.json`, `alm_candidates_large.json`, `imitation/alm_large*.json`; the Hugging Face repo | ~3-4 h after the 1B, then ~4-5 h |
| `python scripts/jobwatch.py [--interval 60 --stall 20]` | - | prints a line whenever a tmux job starts or ends, the 1B driver logs an event, or a Mac job log shows an error, an EXIT line or goes silent; run under a monitor so a crash is seen at once | stdout | runs until stopped |
| `scripts/pod_upload.sh` | - | copies the token files to the rented pod in 8 parallel rsync streams (no ownership: the pod's network disk refuses chown); rerunnable | the pod's `/workspace/corpus/timelocked_lm/tokens/` | ~1-1.5 h at 124 Mbps up |
| `scripts/pod_upload_pack.sh` | - | copies the index pack (BOM-25) to the pod the same way | the pod's `/workspace/semantic/pack/` | ~1 h for 32 GB |
| `scripts/b2_backup.sh upload\|check [path]`, `restore <file> <dir>`, `weekly` | key in `~/.config/backblaze/credentials`, `rclone` | BOM-65: copies `data/corpus/[path]` (default the passage index, `.` for all) to the private B2 bucket (never deletes there), checks it by size and SHA-1, or restores one file; `weekly` (launchd, Sundays 03:00) uploads then checks; see `docs/backup.md` | the bucket `bom-authorship-index`, paths mirroring `data/corpus/`; `logs/b2_backup.log` | ~20 h for the first 914 GB at ~13 MiB/s; minutes afterwards |
| `uv run python scripts/b2_prune_published.py [--delete]` | Hugging Face token, B2 key, `rclone` | owner 2026-11-11: lists every model weight whose SHA-256 on Hugging Face equals the local file's, and with `--delete` removes those from the B2 bucket (corpus text and `inputs/` never qualify); `b2_backup.sh upload` then skips them | `data/manifests/b2_published_on_hf.txt`; `logs/b2_backup.log` | ~5 min to hash ~350 GB of weights; minutes to delete |
| `python scripts/pod_watch.py --pod <id> --issue <n>` | - | the run's watcher, under tmux on the Mac: verifies the upload by SHA-256 against `data/manifests/timelocked_lm_tokens.jsonl`, starts the pilot then the base, restarts a dead or stalled run, backs up the checkpoint every 4 h, copies each model home checksum-verified, deletes the token files from the pod and terminates it; stops the pod past a spend cap; keeps the GitHub status issue's body current and comments on events | `logs/pod_watch/`; `data/corpus/timelocked_lm/runs/<size>/` | the length of the run |

## 11b. Robustness to deliberate imitation (BOM-31)

Plan: `docs/imitation-plan.md` (to be registered as Amendment 31).

| Command | Status | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.imitation build` | Amendment 31 | the forward and reverse tasks: dual-register authors' ordinary and imitation works, 10 seeded distractors; ids and word counts only | `data/benchmark/imitation_tasks.json` | ~1 min |
| `python -m eval.imitation classic` | `build` | Burrows' and Cosine Delta, General Imposters and ENSC (benchmark calibration) on both directions | `data/benchmark/imitation/{burrows_delta,cosine_delta,general_imposters,ensc}.json` | ~10-20 min (CPU) |
| `python -m eval.imitation style` | `build`; the BOM-30 encoder | the style embeddings on both directions | `data/benchmark/imitation/style_embed.json` | ~10 min (GPU) |
| `python -m eval.imitation alm <size> [--variant v1\|v3] [--micro-batch 8]` | `build`; each model size (all three run, owner 2026-11-06) | the authorial language models (one fine-tune per candidate per direction) or V3's hidden states | `data/benchmark/imitation/alm_<size>[_v].json` | 3-5 h on an H100 at 1B |
| `python -m eval.imitation report` | the method parts | per method: forward accuracy with exact 95% interval and n, per author, section 9's weight; reverse accuracy | `data/benchmark/imitation.json` | seconds |
| `python -m eval.imitation files <size>` | `build` | lists the files the model part reads beyond the repository (the tasks' normalised texts and the size's base model): the upload list for `scripts/pod_jobs.py` | stdout | seconds |

## 11c. The gain over prior work (BOM-68)

Plan: `docs/prior-work-plan.md`; Amendment 36 (draft) pins the GPT-2 ablation and the config.

| Command | Status | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.prior_work table` | reporting of registered runs (needs the `prior_work:` config) | every method, prior and ours, in one table on the benchmark's tests: closed set with a bootstrap interval, Amendment 25's false-match rate, pass; McNemar's exact test for every pair measured on the same tests; published Book of Mormon attributions beside our replications | `data/benchmark/prior_work.json` | seconds |
| `python -m eval.prior_work classic-tails` | `alm.benchmark`'s plan inputs; the imposter pools | BOM-68: Burrows and Cosine Delta, General Imposters and ENSC (the benchmark's calibrated settings) on Amendment 22's held-out tails, the language models' own tests, in their order, so `table` pairs them test by test | `data/benchmark/prior_work_classic_tails.json` | see the log; CPU |
| `python -m eval.prior_work classic-tails --part2` | `alm.benchmark`'s plan inputs with `--part2`; BOM-75's ENSC settings; the imposter pools | Amendment 52: the same four classical methods on BOM-75's 430 held-out tails, the `alm_*_p2` models' own tests in their order; then `table` adds the Holm-corrected head-to-head (`head_to_head_p2`) | `data/benchmark/prior_work_classic_tails_p2.json` | about an hour; CPU |
| `python -m eval.prior_work files` | - | prints every repository file the GPT-2 ablation reads (benchmark texts, masks), for `scripts/pod_jobs.py --files` | stdout | seconds |
| `python -m eval.prior_work ablation gpt2\|gpt2-medium [--micro-batch 8]` | Amendment 36 (draft) | Amendment 22's ALM pipeline with an off-the-shelf GPT-2 as the base, benchmark only (GPT-2 may have read the Book of Mormon, so it is never applied to it); then `eval.open_set rescore` and `table` | `data/benchmark/alm_gpt2*.json` | 124M: hours on the Mac; 355M: ~1 h on an H100 |

## 12. Linguistic dating (BOM-29)

Plan, registered before any fit (Amendment 17): `docs/dating-plan.md`; feature list `dating/features.py`.

| Command | Registered? | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m dating.classifier sample` | registered | seeded, author-split sample of 1473-1830 volumes in 31 bins; two 2,000-token prose segments each; the 61 grammar rates from the printed text | `data/dating/segments.parquet`, `sample.json` | ~1-2 h on the M4 |
| `python -m dating.classifier fit` | registered | lexical vocabulary from the training segments, then the grammar and lexical models with the penalty by author-grouped CV | `data/dating/models.json`, `grammar_coefficients.json`; `data/corpus/dating/` (models, lexical counts) | ~1 h |
| `python -m dating.classifier validate` | registered | held-out authors, keyed against OCR, King James imitation, Amendment 9's separation; no Book of Mormon text | `data/dating/validation.json` | ~15 min |
| `python -m dating.classifier h3c` | registered (6.4) | after unblinding: H3c, a permutation test on the Book of Mormon chunks' predicted years against the pseudo-biblical control volumes (grammar decides, lexical beside); accepted if p > 0.05 | `data/dating/h3c.json` | ~5 min |
| `python -m eval.bom_overlap` | read-only analysis (2026-11-10) | every run of 8+ words each candidate sample shares with the Book of Mormon's narrative, classed biblical, stock, predates the passage, same weeks, quotation (20+ words, after) or short ambiguous; for Amendment 43's review (`docs/bom-overlap-analysis.md`) | `data/candidates/bom_overlap.json` (numbers only) | ~2 min |
| `python -m eval.js_register classic`, `python -m eval.js_register style base\|mid`, `python -m eval.js_register alm pilot\|base\|mid` (GPU), `python -m eval.js_register report`, `python -m eval.js_register dose pilot\|base\|mid` (GPU), `python -m eval.js_register dose-report` | Amendment 44 (post hoc) | Joseph Smith's non-revelatory writing of 1831-33 pooled into one candidate unit and scored on the sealed set beside his revelatory sample, by the classical methods and candidate models at every size (Amendment 43 setting); `report` gives each Joseph Smith sample's mean rank among the candidates on the Book of Mormon chunks | `data/blind/a44/` | classic ~5 min; alm ~5 min a size on an H100 |
| `python -m eval.js_register people` | Amendment 44's scores (`data/blind/a44/`), the Amendment 43 outputs and the unblinding key | Amendment 53 (post hoc): the whole people-only ranking on the Book of Mormon chunks for every method and size, with Joseph Smith's revelation sample in the list and taken out (mean rank, times first, every unit) | `data/blind/a44/people.json` | seconds |
| `python -m eval.js_later sections` | Revelation Book 1 (`data/private/candidates/raw/js-1828-1829-revelations/`) | Amendment 54 (post hoc): every section set aside by rule 9 whose title begins "Revelation", one private text file each | `data/private/candidates/later/`, `data/blind/a54/sections.json` | seconds |
| `python -m kjv_mask.run js_later` | `eval.js_later sections`; passim | KJV masking of those sections at BOM-16's frozen settings | `data/kjv_mask/js_later/` | ~10-30 min |
| `python -m eval.js_later plan` | the masking; the 1830 edition, KJV and control inputs | drops Book of Mormon quotations (Amendment 43's rule) and encodes the unit | `data/corpus/alm/a54/`, `data/blind/a54/plan.json` | minutes |
| `python -m eval.js_later classic` | `plan`; Amendment 43's thresholds | Burrows' and Cosine Delta and General Imposters with the later revelations (and his pooled prose) among the references | `data/blind/a54/classic.json` | ~30 min |
| `python -m eval.js_later style base\|mid` | `plan`; the style encoders | the same for the 297M and 590M style encoders | `data/blind/a54/style_<size>.json` | ~15 min each |
| `python -m eval.js_later alm pilot\|base\|mid` | `plan`, the sealed set, a base model; an H100 | one model on the whole unit plus up to 12 equal-dose slices, each scored on the sealed set; no weights kept | `data/blind/a54/alm_<size>.json` | ~15-40 min per size |
| `python -m eval.js_later report` | the above, Amendments 44, 45 and BOM-76's placebo scores, the unblinding key | people-only ranking with the later revelations added (with and without the 1828-29 sample); each slice's median rank against the 1828-29 revelation model | `data/blind/a54/report.json` | seconds |
| `python -m eval.clustered head-to-head` | `data/benchmark/alm_*_p2.json`, `prior_work_classic_tails_p2.json` | Amendment 55 (post hoc): Amendment 52's 12 comparisons counted by author (sign test, Holm, author-resampled gap) | `data/benchmark/clustered.json` | seconds |
| `python -m eval.clustered head-to-head --ext` | the above plus `alm_*_p3.json`, `prior_work_classic_tails_p3.json` | Amendment 56's decision: the 12 comparisons by author on all 55 authors (Holm), with the 32 new and 23 old alone beside | `data/benchmark/clustered.json` | seconds |
| `python -m sweep.older` | the sweep index (`data/corpus/sweep/`), `data/sweep/` | Amendment 57 step 0: Burrows' Delta, ENSC and General Imposters as library-wide sweeps on the 200 calibration books (top-1, top-10, median rank, the 70% bar) | `data/sweep/older_methods.json` | a few hours (GI) |
| `python -m sweep.coverage` | `data/sweep/calibration.json`, `older_methods.json`; the catalog and genre tables | BOM-89/91 (exploratory): shortlist coverage, the share of the 200 known books whose true author is among the K closest of all swept authors, per signal; each book tagged by identity (life dates agree between book and profile), by genre (profile in the book's genre: same, mixed, cross) and by the number of works in the profile | `data/sweep/coverage.json` | seconds |
| `python -m sweep.episodes [--tag _gpu\|_v2] [--profile-episodes N]` | `sweep.index episodes` with that tag; `data/sweep/coverage.json`; `people.parquet` if built | BOM-89 step 2 (exploratory): the 200 known books ranked by whole-unit vectors and by each author's closest 1 or 3 episodes, over every swept author and over those not known to be dead or under age in 1829; coverage at K by identity and genre group | `data/sweep/coverage_episodes<tag>.json` | about 10 min |
| `python -m sweep.people lookup` | `data/sweep/authors.parquet`; the catalog; outside requests (owner's approval, 2026-11-13) | BOM-91 (exploratory): for swept authors the catalog leaves without life dates, and a seeded 500 it does date (the known-answer check), asks the Library of Congress name authority file; every reply cached, failures asked again on a rerun | `data/sweep/loc_cache.jsonl` | about 2-3 h (one request every half second) |
| `python -m sweep.people build` | `sweep.people lookup` (optional: without it, catalog dates only) | each swept author's life dates (catalog, else a single plausible Library of Congress match), status in 1829 (alive, dead, too young, unknown), and the lookup rule's agreement with the catalog on the 500 | `data/sweep/people.parquet`, `people.json` | seconds |
| `python -m eval.list_size prepare` | the benchmark texts (`data/corpus/`), `data/benchmark/part2/` | Amendment 58: the 55 tested authors' training blocks, 1,070 tests and imposter pools | `data/corpus/list_size/pool.pkl` (corpus text, not in git) | ~2 min |
| `python -m eval.list_size classic [--workers 8]` | `pool.pkl` | Amendment 58: the four older methods refitted on random and similar lists of 2-55 authors; resumes per author | `data/corpus/list_size/classic/` | ~2.5 h (8 workers) |
| `python -m alm.benchmark bundle --pool`; `scripts/a58_pool.sh` | the benchmark texts; pod, base models | Amendment 58: the 55 tested authors' models retrained as registered, each scoring all 1,070 tests (one pod per size) | `data/benchmark/alm_<size>_pool.json` | ~1 h (125M), ~2 h (297M), ~4 h (590M) on an H100 |
| `python -m eval.list_size report` | the above, `data/benchmark/alm_*_pool.json` when present | Amendment 58: accuracy against list length by author, longest list at 90% / 70%, the 12-author decision test | `data/benchmark/list_size.json` | ~1 min |
| `python -m eval.list_size tournament` | `pool.pkl`, `data/benchmark/alm_*_pool.json` | BOM-93 (exploratory): on the 55-author list, straight ranking against heats with a final on the same passage or a fresh one, and several passages averaged | `data/benchmark/list_size_tournament.json` | ~1 min |
| `python -m eval.list_size normalised` | `pool.pkl`, `data/benchmark/alm_*_pool.json` | BOM-90 follow-up (exploratory, post hoc): each model's score put on its own scale (its mean and spread on other authors' passages), the scale set on one group of authors (BOM-75's 23 or Amendment 56's 32) and tested on the other, both directions; one passage, 1-8 passages averaged, all passages; raw against scaled by author | `data/benchmark/list_size_normalised.json` | ~1 min |
| `python -m eval.library_pool prepare` | the sweep's tokens (`data/corpus/sweep/`), `data/sweep/authors.parquet`, `blocks.parquet` | BOM-94 (exploratory): packs the shared pool, the 200 known-book authors (profiles rebuilt without the book) and 800 seeded other swept authors, with the books' first two query chunks as tests | `data/corpus/library_pool/plan.json.gz` (licensed text, not in git) | ~1 min |
| `python -m eval.library_pool run pilot\|base\|mid [--limit N]` | `prepare`; the base model; GPU (owner's approval) | every pool author's equal-dose models (three slices of the 1828-29 revelation sample's 3,039 tokens; one of 11,264 tokens) trained as Amendment 45 and scored on every test; one file per model, resumes; `--limit` stops after N and prints seconds per model | `data/sweep/pool_<size>.npz` (names and numbers) | to be measured (estimate 4-5 h on an H100 at 125M) |
| `python -m eval.library_pool report pilot\|base\|mid` | `data/sweep/pool_<size>.npz`, `data/sweep/coverage.json` | BOM-94 (exploratory): per dose, how often the true author is first and in the top 5, 10 and 20 of a random list of 2 to 1,000 pool authors (exact, by author), by passage and by book, raw and per-model-scaled scores (scale from the other half of the books), all books and by genre group | `data/sweep/pool_report_<size>.json` | seconds |
| `python -m eval.clustered curve` | `data/benchmark/alm_*_p2.json` | Amendment 55: verification curve, raw / z-norm / z-margin, leave one author out; held-out false matches and true authors confirmed at 1/2/5/10% and at the registered 95% point | `data/benchmark/clustered.json` | ~1 min |
| `python -m eval.clustered by-length` | Amendment 53/54 scores, the unblinding key | Amendment 55: people-only firsts counted separately on the 2,000- and 5,000-word sealed chunks | `data/blind/a55_by_length.json` | seconds |
| `python -m eval.part2_benchmark --ext --queue` | the catalog, genre labels, Amendment 48's draw | Amendment 56: the next authors in each genre's seeded order, with titles, for the AI screen | stdout | ~1 min |
| `python -m eval.part2_benchmark --ext` | the screen (`data/benchmark/part2/screen.json`) | Amendment 56's draw: 8 more authors per genre by Amendment 48's rules | `data/benchmark/part2/authors_ext.json` | ~1 min |
| `python -m alm.benchmark bundle --ext` | the draw; the corpus | the eight new tasks' plan packed for a rented GPU (licensed text; local only, wiped from the pod) | `data/corpus/alm/benchmark/p3_plan.json.gz` | ~30 s |
| `python -m alm.benchmark <size> --ext` | the bundle or the corpus; a base model; an H100 | Amendment 56: every size on the eight new tasks (640 tests) | `data/benchmark/alm_<size>_p3.json` | ~15-60 min per size |
| `python -m eval.prior_work classic-tails --ext` | the draw; the corpus; imposter pools | Amendment 56: Burrows, Cosine, General Imposters and ENSC on the same 640 tests | `data/benchmark/prior_work_classic_tails_p3.json` | ~1.5 h |
| `python -m eval.per_candidate report [--run registered\|a43]` | descriptive | each candidate sample on the 168 chunks, per method and model size: mean rank among the candidate samples, chunks ranking it first (the method's own pick), match and inconclusive calls; samples with one score on every chunk listed as not scorable (Cowdery's 1829 sample after Amendment 43: 844 tokens, no training step) | `data/blind/per_candidate.json`, `data/blind/a43/per_candidate.json` | seconds |
| `python -m dating.transformer embed` | registered (Amendment 29); the 297M base model | the transformer cross-check's features: every dating segment's mean final hidden state (Mac GPU; resumes) | `data/corpus/dating/transformer_segments.npy` | ~10 h |
| `python -m dating.transformer fit` | `embed` | the same regularised multinomial logistic regression on those features | `data/dating/transformer.json` | minutes |
| `python -m dating.transformer validate` | `fit` | held-out authors by era, 6.4 as amended, King James imitation, known-answer separation, and the leakage check | `data/dating/transformer_validation.json` | ~30 min |

## 13. Derived tables for replication (BOM-44)

Amendment 18; terms per source `docs/derived-data-terms.md`.

| Command | Registered? | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.derived export` | - | the benchmark as 1,000-token blocks of counts over each task's 1,000 most frequent words; the rare-phrase hit tables (open-source targets only) and target hash lists; runs the check | `data/corpus/derived/` (release staging), `data/derived/export.json` | ~5 min |
| `python -m eval.derived check` | - | the non-reconstructability check on every staged table: ids and labels only as strings, no positions, integer counts, vocabularies at most 1,000 | - | seconds |

## BOM-34. Manuscript and dictation evidence

Plan and results: `docs/manuscript-evidence.md`.

| Command | Needs | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m manuscript.corrections build` | the private JSP transcripts (`data/private/bom/`) | every correction marked in the original and printer's manuscripts, typed and credited to its scribe; dictated against copied (homophone share, Fisher), all pages, same passages, same scribe | `data/manuscript/corrections.csv`, `summary.json`; word pairs privately in `data/private/manuscript/` | seconds |
| `python -m eval.scribes run [--size 2000 --permutations 1000 --min-chunks 3]` | BOM-32 unblinded (`data/blind/unblinded.json`) | 6.3: leave-one-out Cosine Delta accuracy sorting chunks by narrator, scribe and dictation order, permutation nulls, the separability verdict | `data/benchmark/scribes.json` | ~1 h at 1,000 permutations |
