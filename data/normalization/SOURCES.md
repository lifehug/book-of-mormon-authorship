# Spelling and orthography normalisation (BOM-15)

Pre-registration 4.3 and Amendment 2 register two regimes, chosen by date of printing
(`corpus.spelling_normalization`, `ocr_fix.normalize.regime`):

| Printed | Regime | What changes |
| --- | --- | --- |
| before 1700 | `morphadorner_emod_lexicon` | MorphAdorner 2.0.1's Early Modern English adorner, run as distributed (`ocr_fix.morphadorner`): parts of speech tagged, then each word's standard spelling (`vnto` -> `unto`, `ye` -> `the` or `you` by part of speech), plus the typographic artifacts below |
| 1780-1830 | `artifacts_only` | long s and printers' ligatures only (`ſ` -> `s`, `ﬁ` -> `fi`); `publick` and `shew` stay as printed |
| 1700-1779, undated | `artifacts_only` | the registration is silent; listed in `pending_amendment` (`spelling_normalization.1700_1779`) |

Input is BOM-14's cleaned text for OCR sources and the keyed text for TCP. Normalised text is
written to `data/corpus/normalized/<source>/` (local only, like all corpus text; checksums in
`data/manifests/corpus_normalized.jsonl`). Nothing is read and overwritten in place.

| File | Built by | In git | What it is |
| --- | --- | --- | --- |
| `normalization.parquet` | `python -m ocr_fix.normalize run` | yes | per text: regime, output path, artifacts replaced, words standardised, adorned tokens not found in the original (`unaligned`) |
| `applied_counts.jsonl` | the same run | no (0.7 GB) | per text, every (variant, standard, count) applied; rebuilt by the run |
| `applied_map.tsv` | `python -m ocr_fix.normalize map` | yes | what was actually applied across the corpus: variant, standard, tokens, texts |

MorphAdorner's adorned output (token, spelling, part of speech, standard spelling, lemma) is
kept whole in `data/corpus/morphadorner_adorned/`, local. The 2.0.1 distribution is
`data/corpus/morphadorner/morphadorner-2.0.1.zip` (manifest `data/manifests/morphadorner.jsonl`),
unpacked to `data/corpus/morphadorner/app/`; it runs under OpenJDK 17.

## Rebuild

```
python -m ocr_fix.clean run                 # BOM-14, OCR sources
python -m ocr_fix.morphadorner adorn        # pre-1700 TCP texts, about 8 hours, resumable
python -m ocr_fix.normalize run             # resumable
python -m ocr_fix.normalize map
```

## A wrong turn, kept

The first run (2026-10-26) applied MorphAdorner's merged spelling-pairs table token by token
without tagging. MorphAdorner never does that: the table's entries for ambiguous words are
fallbacks that its word-class table overrides. Without the tagger, `part` became `partly`
about a million times and determiner `ye` became `you`. Those outputs are kept in
`data/corpus/normalized_superseded_table/` with their rows in
`normalization_table_superseded.parquet`.

## A quirk, not patched

MorphAdorner's EME adorner maps the article `an` to `and` (486 of 497 uses in TCP A00005). It
is applied unchanged, because the registered method is MorphAdorner's, and its count is in
`applied_map.tsv`. Keeping `an` as printed is proposed in `pending_amendment`
(`spelling_normalization.morphadorner_an`). Only the pre-1700 reference texts are affected;
the raw text is kept, so either reading can be rebuilt.
