# KJV masking (BOM-16)

| File | Built by | What it is |
| --- | --- | --- |
| `eval_docs.jsonl` | `python -m kjv_mask.evaluate build` | 40 passages of non-religious TCP Evans prose (screened: no verbatim scripture of their own) with 240 KJV verses planted at known places: verbatim, 0.75-identity paraphrase, 0.40 decoy |
| `eval_grid.jsonl` | `python -m kjv_mask.evaluate grid` | masking precision, recall and F1 on those for `min_match` 1-4 with Amendment 2's registered settings; identical at every value (P 0.947, R 0.781, F1 0.856), so the registered tie-break gives 4 |
| `validation_200.jsonl` | `python -m kjv_mask.validate run --model opus` | Amendment 2's check: 100 verbatim and 100 paraphrase spans from 120 Evans sermon passages, each read beside its KJV chapter by an AI reviewer, **a simulated hand check** (Amendment 1). 191/200 judged KJV-derived (95.5%; criterion 90%, fixed beforehand) |
| `bom/spans.jsonl`, `bom/report.json` | `python -m kjv_mask.run bom` | spans in each 1830 paragraph (`bom:<seq>`): offsets, KJV chapter, class, identity. 18,336 of 268,811 words masked (6.82%) |
| `candidates/spans.jsonl`, `candidates/report.json` | `python -m kjv_mask.run candidates` | the same for every candidate text: the Joseph Smith Papers samples and the printed units cleaned by `ocr_fix.candidates`. 23,055 of 621,005 words (3.71%). Offsets only, so public although some texts are private |

Spans carry no text. Masked text is derived by removing them (`segment.build.original_words`).

**Known limitation, from the validation.** Edges: verbatim spans were judged too short in 38 of
100 (too long in 8), so some quoted words at a span's edges remain in the "original" text, and
the masked share is somewhat understated. Of 100 paraphrase spans, 47 were judged verbatim by
the reviewer and 9 not KJV-derived.

Control texts are masked when the control sets exist (BOM-18), batch by batch at the
validation's scale, since passim's `max_df` counts documents within a run.
