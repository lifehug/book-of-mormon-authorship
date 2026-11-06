---
license: cc-by-nc-4.0
language: en
library_name: transformers
pipeline_tag: text-generation
tags: [gpt2, historical, 1780-1830, time-locked, book-of-mormon-authorship]
---

# Time-locked English 1780-1830 ({name})

A GPT-style language model trained from scratch **only on English printed 1780-1830**, with the
Book of Mormon and everything after 1830 left out. It is the {size} model of an open,
pre-registered study of the authorship, borrowing and dating of the earliest Book of Mormon text
(https://github.com/lifehug/book-of-mormon-authorship; pre-registration https://osf.io/6ugxc/).
The project does not argue for or against divine inspiration; the model exists to measure how
ordinary a passage was for its time.

## Use

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

tok = AutoTokenizer.from_pretrained("{repo}")
model = AutoModelForCausalLM.from_pretrained("{repo}")
ids = tok("And it came to pass that", return_tensors="pt").input_ids
print(tok.decode(model.generate(ids, max_new_tokens=40, do_sample=True, top_p=0.9)[0]))
```

## Model

| | |
| --- | --- |
| Architecture | pre-norm decoder (GPT-2 class): {sh[layers]} layers, width {sh[width]}, {sh[heads]} heads, learned positions, tied embeddings, exact GELU, no biases (zero in this export) |
| Parameters | {run[params]:,} |
| Context | {run[seq]:,} tokens |
| Tokenizer | byte-level BPE, {run[vocab]:,} entries, fit on a 1 GB seeded sample of the training split only |
| Training | one pass over {tokens_b}B tokens ({run[steps]:,} steps of 524,288 tokens); AdamW (0.9, 0.95), weight decay 0.1, peak learning rate 3e-4, 2% warmup, cosine to 10%; bf16 on one H100 |
| Validation loss | {final[val_loss]} at step {final[step]:,} (20M tokens from 989 held-out volumes) |

Loss curves: `loss_curves.csv`. The exported weights were checked against the native model:
`conversion_check.json` (largest logit difference on held-out tokens).

## Data

{kept:,} volumes printed 1780-1830 (corrected dates), newspapers excluded:

| Source | Volumes | Terms |
| --- | --- | --- |
| Internet Archive | {by[internet_archive]:,} | public-domain scans |
| Harvard Institutional Books 1.0 | {by[institutional_books]:,} | Institutional Data Initiative terms (noncommercial; derivatives only if significantly transformed, with attribution) |
| HathiTrust (public-domain, open access) | {by[hathitrust]:,} | HathiTrust researcher agreement |
| Text Creation Partnership (EEBO, ECCO, Evans) | {by[tcp]:,} | CC0 |

Removed before training: every catalogued copy of the Book of Mormon and every volume holding 20
or more of its original 12-token strings (the most any kept volume shares is 12); every volume by
an author in the study's validation benchmark ({ex[benchmark author]:,}), by a named
candidate author ({ex[candidate author]}), and the known-answer texts with their
copies ({ex[known-answer text]}). 0.5% of volumes (989) held out for validation.

**Attribution.** Contains derivatives of Harvard Institutional Books 1.0, Institutional Data
Initiative, Harvard Law School Library. Released under CC BY-NC 4.0 to respect that source's
noncommercial terms. No training text or token files are distributed.

## Limits

- 1780-1830 English as digitised: OCR errors, long s, and the period's spelling and typography
  are in the training data, and the model reproduces them.
- Small by current standards and trained once; not instruction-tuned; it will produce confident
  period prose on any topic, including false and offensive content typical of its sources.
- The training set is weighted to what libraries kept and digitised (religion, law, history,
  sermons), not to how people spoke.
