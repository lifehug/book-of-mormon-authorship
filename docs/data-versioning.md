# Data versioning

The project versions data with **checksum manifests**, not DVC. Reasons: no extra
service to run, manifests are plain text that reviewers can read in a browser, and the
frozen corpus (BOM-19) will be published on Zenodo with a DOI anyway, so the repo only
needs to prove which bytes were used.

## Rules

1. Raw and derived files go under `data/` and are gitignored. Only `data/manifests/` is tracked.
2. Every dataset an issue produces gets one manifest: `data/manifests/<dataset>.jsonl`.
   Build it with `python -m metadata.manifest build`, verify with `verify`.
3. A manifest record is `{"path", "bytes", "sha256"}`. Ingest manifests (BOM-05 to BOM-11)
   add source metadata (identifier, title, author, date, source URL) in sibling catalog files.
4. Change the data, rebuild the manifest, commit both in the same change. CI will later verify
   manifests for any dataset that is present on the runner.
5. Large files (models, full corpora) are published to Hugging Face or Zenodo; the repo keeps
   the manifest and the DOI or model card link.
