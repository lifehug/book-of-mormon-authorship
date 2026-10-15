# data/

Raw and derived data live here but are **not committed**. Only `data/manifests/` is tracked.

Every dataset an issue produces gets a manifest (JSON Lines, one record per file with
`path`, `bytes`, `sha256`) built with:

```
uv run python -m metadata.manifest build data/<dataset> -o data/manifests/<dataset>.jsonl
uv run python -m metadata.manifest verify data/<dataset> data/manifests/<dataset>.jsonl
```

See `docs/data-versioning.md` for the rules.
