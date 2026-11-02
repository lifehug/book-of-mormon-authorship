# Amendment 16: the time-locked base model's training set and settings

*Filed 2026-11-01. Evidence: `docs/timelocked-plan.md`, `data/timelocked_lm/selection.json`.*

---

**Amendment 16, filed 2026-11-01, before any language model is trained.** It fixes the details of
5.2's base model that Amendment 2 left open. No hypothesis, decision rule or threshold of
section 6 changes, and Amendment 2's sizes, tokenizer, context, schedule and learning rate stand.

**Training set.** Every volume of the comparison corpus (text, a date, deduplication keepers, OCR
exclusions applied; newspapers left out, as in every other corpus analysis) whose corrected year
(Amendment 12) is 1780-1830: 204,557 volumes. Removed: the Book of Mormon's catalogued copies and
every volume sharing 20 or more of its original 12-token strings (4.2's check, run on every
volume; 8 volumes); and, so that the base model has not read any text a perplexity ratio will be
computed on, every volume by an author of the validation benchmark (1,489), by a named candidate
(19), and the known-answer texts with their own copies (225). Kept: 202,816 volumes, of which
0.5% (989, by a seeded hash) are held out for validation loss. About 25 billion tokens.

**Tokenizer.** Byte-level BPE, 32,000 entries, fit on a seeded 1 GB sample of training-split
volumes.

**Models.** Decoder-only transformers, pre-norm, learned positions, tied embeddings, no biases:
the pilot 14 layers of width 768 (124.5 million parameters), the base 24 layers of width 960
(297 million). Both trained for one pass over the training split in 1,024-token windows in a
seeded random order, 524,288 tokens per step, AdamW (betas 0.9 and 0.95, weight decay 0.1),
gradient clipping 1.0, cosine decay to 10% of the peak, bf16, on a rented GPU.
