# Book of Mormon Authorship

An open, pre-registered, reproducible computational study of the authorship and textual
relationships of the earliest Book of Mormon text (original manuscript, printer's manuscript,
1830 edition), compared against English print from roughly 1780-1830.

The project combines classical stylometry with methods that only recently became possible:
a time-locked language model trained solely on period text with the Book of Mormon held out,
one fine-tuned authorial model per candidate, semantic text-reuse search at corpus scale,
and a linguistic dating classifier.

## Research questions

1. **Attribution (open-set).** Which candidate authors, if any, does the text resemble?
   "None of the above" is always a possible answer.
2. **Borrowing.** Which earlier texts share wording or ideas with it, and is each overlap
   more than chance?
3. **Dating.** When do its grammar and vocabulary come from: early modern English, or
   18th-19th century pseudo-biblical English?

## Ground rules

- The analysis plan is **pre-registered on OSF** before any analysis (BOM-02). Any change after
  registration needs a dated, public amendment.
- **Adversarial collaboration**: a believing and a critical scholar approve the protocol before
  results exist (BOM-03).
- The Book of Mormon text is **sealed** from all model training and tuning until the blind run
  (BOM-32). The only exception is BOM-22, which replicates published studies with their original
  methods.
- Every method must pass a validation benchmark (BOM-21) and an imitation test (BOM-31) or be
  down-weighted or dropped.
- The design must be able to return any answer. Nulls and conflicts are reported.
- Publish as you go: code here, data manifests and models on Hugging Face or Zenodo with a DOI.

## Plan

The work is 38 issues in 8 phases, in `docs/backlog.md` and mirrored as GitHub issues
`BOM-01` to `BOM-38`. The project is done when all 38 are closed, in order.

| Phase | Scope | Issues |
| --- | --- | --- |
| 0 Foundations | Repo, pre-registration, advisors, budget | BOM-01 to BOM-04 |
| 1 Corpus | Base texts, KJV, Harvard, HathiTrust, Internet Archive, newspapers, EEBO-TCP, candidates | BOM-05 to BOM-13 |
| 2 Preparation | OCR cleanup, normalization, KJV masking, segmentation, controls, frozen corpus v1.0 | BOM-14 to BOM-19 |
| 3 Classical stylometry | Method library, validation benchmark, replication of prior studies | BOM-20 to BOM-22 |
| 4 Borrowing | Exact reuse, rare phrases with a null model, semantic parallels, review | BOM-23 to BOM-26 |
| 5 AI-era methods | Time-locked LM, authorial LMs, dating classifier, style embeddings | BOM-27 to BOM-30 |
| 6 Verification | Imitation robustness, blind run, access and manuscript evidence, Bayesian synthesis | BOM-31 to BOM-35 |
| 7 Publish | Preprint, release and explorer, peer review | BOM-36 to BOM-38 |

Background on prior studies, what is new, and known limits: `docs/background.md`.

## Layout

Each top-level package owns one stage of the pipeline and says in its README which issues
it serves: `ingest/`, `metadata/`, `ocr_fix/`, `kjv_mask/`, `segment/`, `classic/`,
`reuse/`, `semantic/`, `timelocked_lm/`, `alm/`, `dating/`, `style_embed/`, `eval/`, `paper/`.

- `data/` holds raw and derived data (gitignored). Only checksum manifests under
  `data/manifests/` are tracked. See `docs/data-versioning.md`.
- `docs/` holds the backlog, background, and design notes.
- `scripts/` holds one-off tooling such as the backlog importer.
- `tests/` holds the test suite.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

CI runs the same three commands on every push and pull request.

## License

Code: MIT (`LICENSE`). Derived data: CC BY 4.0 (`LICENSE-DATA`). Source texts keep their
original licenses.

## History

This repository began in 2016 as a Java frequency-analysis experiment on the 1830 text and
Joseph Smith's journals (David Taylor and John McConnell). That code is in the git history
before the October 2026 reset and is not used by the current project.
