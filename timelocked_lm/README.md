# timelocked_lm/

Train the 1780-1830 time-locked language model with the Book of Mormon held out.

Issues: BOM-27.

Plan: `docs/timelocked-plan.md` (Amendment 16). Steps, in order:

1. `python -m timelocked_lm.data select` -- the training set (ids and reasons, no text).
2. `python -m timelocked_lm.tokenize train`, then `encode` -- tokenizer and token files.
3. `python -m timelocked_lm.train pilot|base --out <dir>` -- on the rented GPU; resumable.
