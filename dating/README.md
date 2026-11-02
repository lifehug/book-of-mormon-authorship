# dating/

Linguistic dating classifier trained on dated corpora (pre-registration 5.3, 6.4; Amendments 2
and 17). Plan: `docs/dating-plan.md`.

- `features.py`: the registered grammatical feature list (61 rates), read from the printed text
  through one letter-only fold.
- `classifier.py`: sample, fit (grammar and lexical models) and validate.

Issues: BOM-29.
