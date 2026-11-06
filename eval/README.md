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
| `scripts/alm_queue.sh` | - | every benchmark run of the time-locked model, one GPU job at a time: V3 at 125M; when the base model is home, its release (BOM-66) and the 297M primary run; then V1, V2 at 125M and V1-V3 at 297M; then clears the uv cache | `logs/alm_queue.log`, `logs/alm_<run>.log` | superseded 2026-11-05 23:22 by `alm_queue_mac.sh`: the 297M fine-tunes swap on the Mac's 16 GB |
| `scripts/alm_queue_mac.sh` | - | the 125M benchmark variants (V3, V1, V2) on the Mac, one at a time, then clears the uv cache; the 297M runs go to a rented H100 | `logs/alm_queue.log` | ~2-3 h |
| `python scripts/alm_pod.py --issue 38 --files <list> [--size base\|large --cap 15]` | `~/.config/runpod/token`; owner's approval (spend) | the 297M benchmark jobs (primary, V1-V3) on a rented Secure H100: uploads only the files the jobs read (a dry-run list), checks them, runs, brings results home checked, deletes the corpus files, terminates | `data/benchmark/alm_base*.json`; `logs/alm_pod/` | ~1 h |
| `python -m style_embed.data build [--workers 6]` | registered (Amendment 24) | BOM-30: samples 128-token passages (benchmark word form) from the qualifying authors' works; holds out 10% of authors | `data/style_embed/authors.parquet`, `works.parquet`; passages (licensed text) in `data/corpus/style_embed/` | ~20 min on 6 cores |
| `python -m style_embed.train --out <dir> [--tiny --max-steps N]` | registered (Amendment 24) | trains the style encoder (the 297M base model, InfoNCE over two episodes per author); resumes from its checkpoint | `<dir>/style.pt`, `log.jsonl` | ~5 h on an H100 |
| `python scripts/style_pod.py --issue 40 [--cap 50]` | `~/.config/runpod/token`; owner's approval (spend) | rents a Secure H100, uploads and checks the passages and base model, trains, brings `style.pt` home checked, deletes the text, terminates; stops at the cap | `data/corpus/style_embed/runs/style/`; `logs/style_pod/` | ~6 h |
| `python -m style_embed.benchmark [--model <style.pt>]` | registered (Amendment 24) | the style fingerprints in BOM-21's own trials; Amendment 22's pass rule | `data/benchmark/style_embed.json` | under an hour |
| `python -m sweep.units build` | registered (Amendment 28) | BOM-39: the swept authors (named, non-corporate, 10,000+ words in the training set's volumes), up to 20 seeded 1,000-word profile blocks each round-robin over works, the 200 calibration books (style-held-out authors) with their rebuilt profiles and 5,000-word query chunks; ids and offsets only | `data/sweep/authors.parquet`, `blocks.parquet` | seconds |
| `python -m kjv_mask.run sweep` | `sweep.units build`; passim | KJV masking of every sweep block and calibration chunk, BOM-16's frozen settings | `data/kjv_mask/sweep/` | about 20 h (about 470 million words in 659 batches) |
| `python -m sweep.index tokens [--workers 8]` | `kjv_mask.run sweep` | each unit's words (author profile, calibration profile, query chunk) with KJV spans removed, benchmark word form | `data/corpus/sweep/tokens/`, `units.parquet` (private) | ~25 min |
| `python -m sweep.index mfw` | `sweep.index tokens` | the 300 most frequent words of the author profiles and every unit's relative frequencies over them | `data/corpus/sweep/mfw.npz`, `data/sweep/vocabulary.json` | ~30 min |
| `python -m sweep.index embed` | `sweep.index tokens`; the BOM-30 encoder | every unit's style vector (Mac GPU; resumes) | `data/corpus/sweep/style.npz` | several hours |
| `python -m sweep.calibrate` | `sweep.index mfw` and `embed` | BOM-39/47: the 200 calibration books against every swept author under both signals; top-1 rates and the usable verdict, lead thresholds, expected false leads (leave-one-out), signal correlations, the 100 authors for the blind gate | `data/sweep/calibration.json` | minutes |
| `scripts/sweep_chain.sh` | - | waits for `kjv_mask.run sweep` to exit cleanly (its `EXIT` line in `logs/sweep_mask.log`), then runs `sweep.index tokens`, `mfw`, `embed` and `sweep.calibrate`; run a frozen copy under tmux | as those | about a day |
| `python -m alm.candidates plan` | registered (Amendment 30) | candidate units (admitted tiers, masked) and four control samples; held-out tails (BOM-32's decoy source); encoded inputs | `data/benchmark/alm_candidates_plan.json`, `data/corpus/alm/candidates/inputs/` | ~10 min |
| `python -m alm.candidates train base\|large [--micro-batch 8]` | `plan`; the working model | fine-tunes and keeps one model per unit; every model scores every held-out window; resumes | `data/corpus/alm/candidates/<size>/` | <1 h (297M), ~2-3 h (1B) on an H100 |
| `python -m alm.candidates validate base\|large` | `train` | closed set among all units and among candidates; 6.1's margin, best control minus candidate | `data/benchmark/alm_candidates_<size>.json` | minutes |
| `python scripts/candidates_pod.py --issue 38 --size base\|large [--cap 25]` | RunPod token; spend approval | the above on a Secure H100, SHA-256 checked both ways, private text deleted and checked | as above | ~1 h (297M), ~3-4 h (1B) |
| `python -m blind.seal [--key ~/.bom-blind/key.json]` | Amendment 32 | seals the narrator chunks with decoys; key outside the repo | `data/blind/seal.json`, `withheld.json`; `data/corpus/blind/sealed.jsonl` | minutes |
| `python -m blind.run --size base\|large [--only ...] [--sealed <path>]` | every scorer built; a fresh session | scores every sealed id with every method, hashes outputs | `data/blind/outputs/`, `outputs.json` | ~3-4 h |
| `python -m blind.unblind [--key ...]` | outputs committed | checks hashes, applies the key, decoy accuracy, sweep leads, leave-one-candidate-out | `data/blind/unblinded.json` | minutes |
| `scripts/after_1b.sh` | the 1B driver; `~/.config/runpod/token`, `~/.config/huggingface/token` | waits for the 1B to be home (driver state done, `model.pt` on the Mac), runs `alm_pod.py --size large` (primary, V1-V3 on a rented H100, cap $40), then converts, cards and uploads the 1B to `etherfuse/timelocked-1830-1b` (owner-approved); run a frozen copy under tmux | `data/benchmark/alm_large*.json`; the Hugging Face repo | ~3-4 h after the 1B |
| `python scripts/jobwatch.py [--interval 60 --stall 20]` | - | prints a line whenever a tmux job starts or ends, the 1B driver logs an event, or a Mac job log shows an error, an EXIT line or goes silent; run under a monitor so a crash is seen at once | stdout | runs until stopped |
| `scripts/pod_upload.sh` | - | copies the token files to the rented pod in 8 parallel rsync streams (no ownership: the pod's network disk refuses chown); rerunnable | the pod's `/workspace/corpus/timelocked_lm/tokens/` | ~1-1.5 h at 124 Mbps up |
| `scripts/pod_upload_pack.sh` | - | copies the index pack (BOM-25) to the pod the same way | the pod's `/workspace/semantic/pack/` | ~1 h for 32 GB |
| `scripts/b2_backup.sh upload\|check [path]`, `restore <file> <dir>`, `weekly` | key in `~/.config/backblaze/credentials`, `rclone` | BOM-65: copies `data/corpus/[path]` (default the passage index, `.` for all) to the private B2 bucket (never deletes there), checks it by size and SHA-1, or restores one file; `weekly` (launchd, Sundays 03:00) uploads then checks; see `docs/backup.md` | the bucket `bom-authorship-index`, paths mirroring `data/corpus/`; `logs/b2_backup.log` | ~20 h for the first 914 GB at ~13 MiB/s; minutes afterwards |
| `python scripts/pod_watch.py --pod <id> --issue <n>` | - | the run's watcher, under tmux on the Mac: verifies the upload by SHA-256 against `data/manifests/timelocked_lm_tokens.jsonl`, starts the pilot then the base, restarts a dead or stalled run, backs up the checkpoint every 4 h, copies each model home checksum-verified, deletes the token files from the pod and terminates it; stops the pod past a spend cap; keeps the GitHub status issue's body current and comments on events | `logs/pod_watch/`; `data/corpus/timelocked_lm/runs/<size>/` | the length of the run |

## 11b. Robustness to deliberate imitation (BOM-31)

Plan: `docs/imitation-plan.md` (to be registered as Amendment 31).

| Command | Status | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.imitation build` | Amendment 31 | the forward and reverse tasks: dual-register authors' ordinary and imitation works, 10 seeded distractors; ids and word counts only | `data/benchmark/imitation_tasks.json` | ~1 min |
| `python -m eval.imitation classic` | `build` | Burrows' and Cosine Delta, General Imposters and ENSC (benchmark calibration) on both directions | `data/benchmark/imitation/{burrows_delta,cosine_delta,general_imposters,ensc}.json` | ~10-20 min (CPU) |
| `python -m eval.imitation style` | `build`; the BOM-30 encoder | the style embeddings on both directions | `data/benchmark/imitation/style_embed.json` | ~10 min (GPU) |
| `python -m eval.imitation alm <size> [--variant v1\|v3] [--micro-batch 8]` | `build`; the working model size | the authorial language models (one fine-tune per candidate per direction) or V3's hidden states | `data/benchmark/imitation/alm_<size>[_v].json` | 3-5 h on an H100 at 1B |
| `python -m eval.imitation report` | the method parts | per method: forward accuracy with exact 95% interval and n, per author, section 9's weight; reverse accuracy | `data/benchmark/imitation.json` | seconds |

## 12. Linguistic dating (BOM-29)

Plan, registered before any fit (Amendment 17): `docs/dating-plan.md`; feature list `dating/features.py`.

| Command | Registered? | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m dating.classifier sample` | registered | seeded, author-split sample of 1473-1830 volumes in 31 bins; two 2,000-token prose segments each; the 61 grammar rates from the printed text | `data/dating/segments.parquet`, `sample.json` | ~1-2 h on the M4 |
| `python -m dating.classifier fit` | registered | lexical vocabulary from the training segments, then the grammar and lexical models with the penalty by author-grouped CV | `data/dating/models.json`, `grammar_coefficients.json`; `data/corpus/dating/` (models, lexical counts) | ~1 h |
| `python -m dating.classifier validate` | registered | held-out authors, keyed against OCR, King James imitation, Amendment 9's separation; no Book of Mormon text | `data/dating/validation.json` | ~15 min |
| `python -m dating.transformer embed` | registered (Amendment 29); the 297M base model | the transformer cross-check's features: every dating segment's mean final hidden state (Mac GPU; resumes) | `data/corpus/dating/transformer_segments.npy` | ~10 h |
| `python -m dating.transformer fit` | `embed` | the same regularised multinomial logistic regression on those features | `data/dating/transformer.json` | minutes |
| `python -m dating.transformer validate` | `fit` | held-out authors by era, 6.4 as amended, King James imitation, known-answer separation, and the leakage check | `data/dating/transformer_validation.json` | ~30 min |

## 13. Derived tables for replication (BOM-44)

Amendment 18; terms per source `docs/derived-data-terms.md`.

| Command | Registered? | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.derived export` | - | the benchmark as 1,000-token blocks of counts over each task's 1,000 most frequent words; the rare-phrase hit tables (open-source targets only) and target hash lists; runs the check | `data/corpus/derived/` (release staging), `data/derived/export.json` | ~5 min |
| `python -m eval.derived check` | - | the non-reconstructability check on every staged table: ids and labels only as strings, no positions, integer counts, vocabularies at most 1,000 | - | seconds |
