# data/dating

The linguistic dating classifier (BOM-29; pre-registration 5.3, 6.4; Amendments 2 and 17). Plan:
`docs/dating-plan.md`. Ids, positions, numbers and vocabulary only; no text.

| File | What | Rebuild |
| --- | --- | --- |
| `segments.parquet` | every sampled segment: work id, source, year, bin, split, author group, segment position, and the 61 grammar rates per 1,000 tokens | `python -m dating.classifier sample` |
| `sample.json` | bin edges, eligible and excluded counts, segments and volumes per split | same |
| `models.json` | the chosen penalties, cross-validation log losses, the grammar feature names, the 5,000-word lexical vocabulary | `python -m dating.classifier fit` |
| `grammar_coefficients.json` | the grammar model's coefficient per feature and bin | same |
| `validation.json` | held-out accuracy, keyed vs OCR, King James imitation, known-answer separation | `python -m dating.classifier validate` |

Inputs: the catalog and eligibility of `reuse.exact.eligible_any_year` (corrected years,
BOM-64); printed text (TCP keyed, BOM-14 cleaned OCR) and BOM-15 normalised text under
`data/corpus/`; KJV masks (BOM-16, BOM-61); `data/controls/pseudo_biblical_primary.jsonl`;
`data/known_answer/set.jsonl`; `data/kjv/kjv.jsonl`; `data/normalization/applied_map.tsv`.

Not in git: `data/corpus/dating/` holds the fitted models (`models.joblib`) and the lexical count
matrix; both rebuild with `fit`.
