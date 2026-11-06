# data/semantic/

Semantic parallels (BOM-25; plan `docs/semantic-plan.md`, Amendment 13). Ids, numbers and scores
only; no text.

| File | What | Rebuild |
| --- | --- | --- |
| `model_choice.json` | the model test: 443 passages of the 1807 *New Translation of the Book of Psalms* (`institutional_books:AH5KIN`) against the King James Bible's 7,970 passages (`data/kjv/kjv.jsonl`); recall at 1 and 10 and passages per second for five models on the M4 (MPS) | `python -m semantic.choose` (~20 min) |
| `distractors_<model>.json` | the same test with 1,000,000 corpus passages added to the gallery (seeded; Bibles, psalters, hymnals, prayer books left out): recall at 1-1,000, and for bge-small the effect of re-scoring its top k with e5-base | `python -m semantic.choose distractors <model> [--rescore <model>]` (~1 h for MiniLM; bge-small's file came from the command's scratch predecessor, same procedure) |
| `named.json` | the named proposed sources and their control groups against the Book of Mormon, every passage pair: per member its passages, parallels, score with bootstrap interval, rank, and its 50 strongest pairs as passage numbers and scores (no text) | `python -m semantic.search named` (~10 min on the M4) |
| `corpus_bom.json` | the whole-corpus search (Amendment 14): every source volume of the Book of Mormon's 1780-1830 window with a parallel, its score, bootstrap interval, 500-volume genre/length null and percentile, the `stands_out` flag, whether BOM-64 moved it past 1830, and the top 20 sources for the skeleton test; Bible volumes listed apart; titles and ids only | `python -m semantic.corpus queries && ... scan && ... score` (~1 h on the M4) |
| `parallels_bom.parquet` | every parallel behind it: query passage number, source volume, passage number and character span, cosine, the query's bar and King James share (no text) | same |
| `corpus_known_answer.json` | Amendment 9's semantic score for each known-answer text (strongest source in each of BOM-23's matched draws, mean over draws), the separation test, and the King James retelling controls (Josephus, *Twelve Patriarchs*, *Jasher*), each with and without the missed own copy | same |

The index itself is under `data/corpus/semantic/index/` (on the data drive, not in git): float16
vectors and passage ids per shard, `settings.json` with the model and settings, checksummed in
`data/manifests/semantic_index.jsonl`. Rebuild with `python -m semantic.index build` (about a week
on an M4); the models are downloaded from Hugging Face by name
(https://huggingface.co/BAAI/bge-small-en-v1.5, https://huggingface.co/intfloat/e5-base-v2).

- `named_null.json`: Amendment 21's null for each named source (500 volumes each, scored directly), with per-volume scores by id, the source's re-score, 99th percentile, percentile and verdict; no text. Rebuild with `python -m semantic.search null` (~1 h per source on the M4; resumes from `data/corpus/semantic/search/named_null_*.json`).

## skeleton/ (BOM-25 story skeletons, Amendment 15; `docs/skeleton-plan.md`)

- `skeleton/check.json`: the extractor check. `python -m semantic.skeleton check`: 20 King James
  chapters (seed `bom25-skeleton-check`) from `data/kjv/kjv.jsonl`, events extracted twice by
  claude-sonnet-5-5 and judged against the chapter (model-assisted, simulated); holds the King
  James event lists (public domain), agreement, support and the event-match threshold.
- `skeleton/controls.json`, `skeleton/bom.json`: alignment scores, spans (block numbers), order
  p-values and ranks; no text. Rebuild with `python -m semantic.skeleton controls|bom`. The event
  lists they are computed from paraphrase licensed volumes and stay in
  `data/corpus/semantic/skeleton/events/` (not in git; checksums in
  `data/manifests/semantic_skeleton_events.jsonl`).
- `skeleton/top.json`: the Book of Mormon against the 20 leading whole-corpus search sources
  (`skeleton.top_search_sources`, from `corpus_bom.json`): search rank, id, title, score, events
  matched, spans, order p; no text. Rebuild with `python -m semantic.skeleton top`.

`triage.json`: BOM-26 (Amendment 27): biblical / common / specific counts per search, the confusion table and kappa between the two passes, and the pairs specific under both (ids only). Rebuild with `python -m semantic.triage first`, `second`, `report`; the replies, which hold corpus text, stay in `data/corpus/semantic/triage/`.
