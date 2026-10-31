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

## 8. The King James italics test (BOM-62)

Plan, registered before any count (Amendment 11): `docs/italics-plan.md`.

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m eval.italics ranges` | registered | the translation-only ranges of the independent translations, from their layout, before any count | `data/italics/translation_ranges.json` | seconds |

## Other

| Command | Kind | What it does | Writes | Time |
| --- | --- | --- | --- | --- |
| `python -m reuse.rare size` | registered | how large the borrowing null must be (BOM-45) | `data/reuse/null_sizing/sizing.json` | minutes |
