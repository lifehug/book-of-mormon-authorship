# KJV masking (BOM-16)

| File | Built by | What it is |
| --- | --- | --- |
| `eval_docs.jsonl` | `python -m kjv_mask.evaluate build` | 40 passages of non-religious TCP Evans prose (screened: no verbatim scripture of their own) with 240 KJV verses planted at known places: verbatim, 0.75-identity paraphrase, 0.40 decoy |
| `eval_grid.jsonl` | `python -m kjv_mask.evaluate grid` | masking precision, recall and F1 on those for `min_match` 1-4 with Amendment 2's registered settings; identical at every value (P 0.947, R 0.781, F1 0.856), so the registered tie-break gives 4 |
| `validation_200.jsonl` | `python -m kjv_mask.validate run --model opus` | Amendment 2's check: 100 verbatim and 100 paraphrase spans from 120 Evans sermon passages, each read beside its KJV chapter by an AI reviewer, **a simulated hand check** (Amendment 1). 191/200 judged KJV-derived (95.5%; criterion 90%, fixed beforehand) |
| `bom/spans.jsonl`, `bom/report.json` | `python -m kjv_mask.run bom` | spans in each 1830 paragraph (`bom:<seq>`): offsets, KJV chapter, class, identity. 18,336 of 268,811 words masked (6.82%) |
| `candidates/spans.jsonl`, `candidates/report.json` | `python -m kjv_mask.run candidates` | the same for every candidate text: the Joseph Smith Papers samples and the printed units cleaned by `ocr_fix.candidates`. 23,055 of 621,005 words (3.71%). Offsets only, so public although some texts are private |
| `controls/spans.jsonl.gz`, `controls/report.json` | `python -m kjv_mask.run controls` (about 23 hours on the mini), then `gzip -n -9` | the same for every control volume, 17,456 texts and 1,548,751,290 words: 27,576,618 masked (1.78%). The uncompressed file is 107 MB, over GitHub's limit, so only the byte-reproducible gzip is committed. Restore with `gunzip -k data/kjv_mask/controls/spans.jsonl.gz`; the restored file's SHA-256 is `3087699692377d13ab085ca0069648e2a544891b7c1bb37286013267e26b4c0a`. The run masked the lists as they stood before BOM-55, a superset of the current ones; every current member has its spans |
| `known_answer/spans.jsonl`, `known_answer/report.json` | `python -m kjv_mask.run known_answer` (about 3 minutes) | the same for BOM-61's 22 known-answer volumes (`data/known_answer/set.jsonl`): 6,340 of 2,111,201 words (0.30%); *Jasher* 3.5%, the *Apocryphal New Testament* 1.3%, Hesiod 1.2%, the *Twelve Patriarchs* 0.9%, Ossian, Rowley, Homer and *Sacontala* 0%. Three volumes were already masked as controls and are masked again here in this group's own batches |
| `italics/spans.jsonl`, `italics/report.json` | `python -m kjv_mask.run italics` (about a minute) | the same for BOM-62's independent translations, translation text only (`data/italics/translation_ranges.json`), one document per range (`<work_id>#<start>`): 31,643 of 130,460 words (24.3%); these translators kept the King James wording where they agreed with it, and those passages are what the italics test compares |

Spans carry no text. Masked text is derived by removing them (`segment.build.original_words`).

**Known limitation, from the validation.** Edges: verbatim spans were judged too short in 38 of
100 (too long in 8), so some quoted words at a span's edges remain in the "original" text, and
the masked share is somewhat understated. Of 100 paraphrase spans, 47 were judged verbatim by
the reviewer and 9 not KJV-derived.

**Controls.** Masked batch by batch at the validation's scale (about 720,000 words), since
passim's `max_df` counts documents within a run. Under Amendment 6, texts over 150,000 words were
aligned as pieces overlapping by 500 words (control volumes reach 2.5 million words); 14 batches
of long, densely biblical pieces (Bible commentaries such as the 1826 *Recensio synoptica*)
exhausted the 6 GB heap and completed on the 12 GB retry, logged in `logs/passim_failures.jsonl`;
none needed the split-into-thirds fallback (`split_further` is empty).

| Control set | Volumes | Words masked | Median text | 95th percentile |
| --- | --- | --- | --- | --- |
| general prose | 4,998 | 0.14% | 0.00% | 0.8% |
| history | 2,986 | 0.41% | 0.00% | 1.2% |
| sermons 1820s | 6,143 | 2.46% | 0.68% | 7.9% |
| pseudo-biblical (either label) | 3,672 | 3.40% | 0.64% | 10.1% |
| pseudo-biblical (primary label) | 29 | 17.12% | 0.12% | 14.9% |

The Book of Mormon, for comparison: 6.82%. The primary-label figure is carried by one or two
texts that are Bibles themselves (*A new self-interpreting Testament*, 1827), which BOM-54's
curated list excludes.

**2026-10-28, BOM-56.** Eight volumes whose title pages dated them to the 1820s joined the 1820s sermons and were masked with `python -m kjv_mask.run controls --missing-only`, which masks only texts without spans and merges them in; no other text was re-run.
