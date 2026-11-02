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
| `python -m semantic.index build` | registered | the passage index of the whole corpus (278,796 volumes, 128-word passages, bge-small); resumes at the first unfinished shard and adds only volumes not yet indexed | `data/corpus/semantic/index/` (vectors and ids, no text; not in git) | ~12 days on the M4 (measured 183 passages/s alone) |
| `python -m semantic.index status` | - | shards, volumes and passages indexed so far | - | seconds |
| `python -m semantic.search named` | registered | the named proposed sources and their control groups against the Book of Mormon, every passage pair; ranks within group (the null check waits for the index) | `data/semantic/named.json` | ~10 min |
| `python -m semantic.skeleton check` | registered (extractor check) | 20 King James chapters, events extracted twice by the hosted model and judged against the chapter; sets the event-match threshold | `data/semantic/skeleton/check.json` | ~2 min, 60 model calls |
| `python -m semantic.skeleton controls` | registered | the retelling positive controls (Josephus, Twelve Patriarchs, Jasher against their King James ranges and 20 unrelated books each); stops on a usage limit and resumes | `data/semantic/skeleton/controls.json`; events in `data/corpus/semantic/skeleton/events/` | hours, ~3,500 model calls |
| `python -m semantic.skeleton bom` | registered | the Book of Mormon's event sequence against the named sources and their control groups, aligned with an order test | `data/semantic/skeleton/bom.json` | hours, ~3,500 model calls |
| `scripts/skeleton_loop.sh controls\|bom` | - | reruns a skeleton step every 15 minutes until it finishes (run under tmux) | as above | until done |

## Other

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m reuse.rare size` | registered | how large the borrowing null must be (BOM-45) | `data/reuse/null_sizing/sizing.json` | minutes |
| `python -m reuse.rare score` | registered score; points 2-5 of the plan post hoc (BOM-24, `docs/rare-plan.md`) | the Book of Mormon's ranked source list from the BOM-22 scan under corrected dates: rare shared 4-grams per 10,000 words (df <= 5 by text, by volume beside it), p against the whole period population, genre percentile, block-bootstrap intervals, named sources, imitation scripture as a group, volumes BOM-64 moved | `data/reuse/bom/rare.json` | minutes |
| `python -m reuse.rare known` | registered (Amendment 9 score) | scans the known-answer texts' 4-grams in BOM-23's matched draws, scores the strongest source per draw, applies the separation rule | `data/reuse/rare_known/hits.parquet`, `known_answer.json` | ~40 min |
