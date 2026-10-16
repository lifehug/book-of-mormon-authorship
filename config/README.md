# config/

Every analytic choice the pipeline makes, in one versioned file. Issues: BOM-40.

```sh
uv run python -m metadata.config validate   # check against the pre-registration
uv run python -m metadata.config show       # the whole config as JSON
uv run python -m metadata.config hash       # SHA-256, for stamping outputs
uv run python -m metadata.config pending    # choices still needing an amendment
```

In code:

```python
from metadata.config import load, sha256_of_config

cfg = load()  # raises if a registered value has been edited
cutoff = cfg["corpus"]["ocr_max_cer"]
stamp = sha256_of_config()  # write this next to whatever the stage produces
```

## Rules

- **No module hard-codes an analytic value.** Thresholds, cutoffs, chunk sizes, seeds and
  model choices are read from here. A result is only traceable if the config that produced
  it is identified, which is what the hash is for.
- **Only pre-registered choices appear as values.** `load()` rejects a config whose registered
  values disagree with `paper/preregistration.md`, so editing a pinned number fails loudly.
  Changing one takes a dated amendment to the OSF registration, not an edit here.
- **Unregistered choices are listed, not guessed.** They live in `pending_amendment` with the
  issue that needs them. If a value is neither in the config nor in that list, you are about
  to invent one: add it to the list instead.

## Scope today

`preregistered.yaml` covers the Phase 2 stages: BOM-12, BOM-14, BOM-15, BOM-16, BOM-17. It was
written ahead of BOM-40 because those stages consume corpus-layer thresholds and would
otherwise hard-code them, leaving BOM-40 a retro-fix.

BOM-40 extends it to the classical methods, language models, dating, embeddings and the
decision rules once BOM-20 closes, and adds `multiverse.yaml` plus the specification-curve
runner. The seven entries in `pending_amendment` must all be pinned by dated amendment before
BOM-21 calibration starts.
