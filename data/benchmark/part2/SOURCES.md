# Enlarged benchmark (BOM-75, Amendment 48)

| File | Built by | What it is |
| --- | --- | --- |
| `screen.json` | by an AI model (Claude), 2026-11-11, from catalogue titles and years | each screened author's decision against Amendment 48's four criteria (one person; English; own words; distinct texts), with the reason for every rejection and every dropped work |
| `authors.json` | `python -m eval.part2_benchmark` (seconds) | the draw: eligible authors per genre, why the rest were left out, who was skipped and why, and the 16 drawn authors with their work ids and word counts (no text) |
| `benchmark.json`, `thresholds.json` | `python -m eval.benchmark --part2` (~4 min on the Mac) | the classical methods on all seven tasks: 500 trials (20 seeded 5,000-word windows per testable author) |
| `open_set.json` | `python -m eval.open_set rescore --part2` (seconds) | Amendment 25's corrected false-match rate and Amendment 47's 95% Wilson intervals for every method; the language-model rows appear once `alm_*_p2.json` exist |
| `placebo.json` | by an AI model (Claude), 2026-11-11 | BOM-76's register-placebo writers: death dates (AI knowledge, open to correction), the texts used and why, and who was left out and why |
| `texts/aquarian_gospel_1911.txt` | fetched 2026-11-11 from https://archive.org/download/aquariangospelof00levirich/aquariangospelof00levirich_djvu.txt (public domain, 1911 printing; SHA-256 a0eae215f6663ea6748ad5dca2d8512cc893dfaf8015b649fae10143a972b134) | Levi H. Dowling, *The Aquarian Gospel of Jesus the Christ*: the secondary placebo text |
| `decoys_plan.json` | `python -m eval.part2_decoys plan` (seconds) | BOM-76's leave-one-work-out folds (unit, held-out work, windows, training tokens) and placebo inputs (tokens); names and numbers only |

Rebuild: `uv run python -m eval.part2_benchmark`; the screening list is `--queue N`. The texts
come from the corpus catalogue (`data/catalog/catalog.parquet`); Institutional Books and
HathiTrust texts are obtained as in `docs/replication.md`.
