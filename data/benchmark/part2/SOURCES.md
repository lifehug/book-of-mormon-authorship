# Enlarged benchmark (BOM-75, Amendment 48)

| File | Built by | What it is |
| --- | --- | --- |
| `screen.json` | by an AI model (Claude), 2026-11-11, from catalogue titles and years | each screened author's decision against Amendment 48's four criteria (one person; English; own words; distinct texts), with the reason for every rejection and every dropped work |
| `authors.json` | `python -m eval.part2_benchmark` (seconds) | the draw: eligible authors per genre, why the rest were left out, who was skipped and why, and the 16 drawn authors with their work ids and word counts (no text) |

Rebuild: `uv run python -m eval.part2_benchmark`; the screening list is `--queue N`. The texts
come from the corpus catalogue (`data/catalog/catalog.parquet`); Institutional Books and
HathiTrust texts are obtained as in `docs/replication.md`.
