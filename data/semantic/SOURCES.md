# data/semantic/

Semantic parallels (BOM-25; plan `docs/semantic-plan.md`, Amendment 13). Ids, numbers and scores
only; no text.

| File | What | Rebuild |
| --- | --- | --- |
| `model_choice.json` | the model test: 443 passages of the 1807 *New Translation of the Book of Psalms* (`institutional_books:AH5KIN`) against the King James Bible's 7,970 passages (`data/kjv/kjv.jsonl`); recall at 1 and 10 and passages per second for five models on the M4 (MPS) | `python -m semantic.choose` (~20 min) |
| `distractors_<model>.json` | the same test with 1,000,000 corpus passages added to the gallery (seeded; Bibles, psalters, hymnals, prayer books left out): recall at 1-1,000, and for bge-small the effect of re-scoring its top k with e5-base | `python -m semantic.choose distractors <model> [--rescore <model>]` (~1 h for MiniLM; bge-small's file came from the command's scratch predecessor, same procedure) |
| `named.json` | the named proposed sources and their control groups against the Book of Mormon, every passage pair: per member its passages, parallels, score with bootstrap interval, rank, and its 50 strongest pairs as passage numbers and scores (no text) | `python -m semantic.search named` (~10 min on the M4) |

The index itself is under `data/corpus/semantic/index/` (on the data drive, not in git): float16
vectors and passage ids per shard, `settings.json` with the model and settings, checksummed in
`data/manifests/semantic_index.jsonl`. Rebuild with `python -m semantic.index build` (about a week
on an M4); the models are downloaded from Hugging Face by name
(https://huggingface.co/BAAI/bge-small-en-v1.5, https://huggingface.co/intfloat/e5-base-v2).
