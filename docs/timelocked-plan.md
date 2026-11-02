# The time-locked base model: the plan, written before any training run (BOM-27)

Written 2026-11-01. Registered as Amendment 16 (OSF revision 6ae7e7682a1c00cdd1bde281) before any
model is trained. Settings:
`timelocked_lm.*` in `config/preregistered.yaml`; code in `timelocked_lm/`.

## What is already registered

Section 5.2 and Amendment 2: a GPT-style model trained from scratch on 1780-1830 text with the
Book of Mormon and all post-1830 text excluded; a 125M pilot, then the 300M base model, with the
validation benchmark run at both sizes (a registered decision point); byte-level BPE tokenizer of
32,000 entries trained on the same corpus only; context 1,024; one pass over the deduplicated
corpus; AdamW, cosine schedule, peak learning rate 3e-4, 2% warmup. 4.2: the 12-token
contamination check on every training volume.

## What this plan fixes

**The training set** (`python -m timelocked_lm.data select`, `data/timelocked_lm/selection.json`):

- every volume the corpus searches use (text, a date, deduplication keepers, OCR exclusions
  applied) whose corrected year (BOM-64) is 1780-1830: 204,557 volumes;
- **newspapers are left out**, as in every other corpus analysis here: Chronicling America's OCR
  is the noisiest in the corpus (BOM-50), and its pages are not works;
- removed: the Book of Mormon's 7 catalogued copies and 1 more volume holding 20 or more of its
  original 12-token strings (4.2's check, run on every volume: the training set is clean, and the
  most any kept volume shares is 12);
- removed, so that the base model has not read any text a perplexity ratio will later be computed
  on: every volume by an author in the validation benchmark (1,489: Scott and the comparison
  novelists, the Federalist authors, the known imitation-scripture authors), every volume by a
  named candidate (19), and the known-answer texts with their own copies (225). Matching is by
  catalog author, so a few namesakes go too (an Oxford Joseph Smith); over-exclusion costs
  nothing here, under-exclusion would bias the benchmark;
- kept: 202,816 volumes; 0.5% of them (989, by a seeded hash) held out for validation loss.

**The tokenizer:** fit on a seeded sample of 1 GB of training-split text (2,456 whole volumes);
validation volumes are never in the sample. `data/timelocked_lm/tokenizer.json`.

**The models** (counts include the tied 32,000-entry embedding):

| | Layers | Width | Heads | Parameters |
| --- | --- | --- | --- | --- |
| Pilot | 14 | 768 | 12 | 124.5M |
| Base | 24 | 960 | 15 | 297.2M |

Pre-norm decoder blocks, learned positions, GELU, no biases, GPT-2 initialisation.

**Training:** 524,288 tokens per optimizer step (512 sequences of 1,024); the training split cut
into 1,025-token windows taken once each in a seeded random order (the registered one pass);
AdamW betas 0.9/0.95, weight decay 0.1 on matrices only, gradient clipping at 1.0; cosine decay to
10% of the peak; bf16. Validation loss on 20M held-out tokens every 1,000 steps. Seeds derive
from `bom27-train`. Checkpoints every 20 minutes, so a rented machine that stops costs at most
that.

**Where:** a rented H100 (BOM-04, `docs/budget.md`). The encoded training set (token ids, which
are the licensed text in another form) is copied to the rented machine for the run and deleted
after it; nothing is published but the model, its card and loss curves.

## The pilot decision point

After the pilot, the BOM-28 benchmark runs at 125M; after the base model, at 300M. Both
accuracies are published. If accuracy is still rising steeply, a further amendment may raise the
size before the base model is trained (Amendment 2).

## Known weaknesses, stated now

- OCR noise: the corpus is machine-read; the model learns its errors as well as its English.
- Excluding the benchmark's novelists removes some of the period's best-known fiction from the
  base model.
- One pass at this size is past the compute-optimal token count for the pilot; that is the
  registered design (one pass), kept for both sizes so they differ only in size.
