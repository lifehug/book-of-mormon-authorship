# Off-site backup of the corpus (BOM-65)

The passage index (`data/corpus/semantic/index/`, 842 files, 119 GB) lives on the external drive
`/Volumes/bomdata`. Rebuilding it costs about a day and $100-150 of rented GPU, so a private
copy is kept on Backblaze B2. On 2026-11-04 the owner widened the backup from the index alone to
all of `data/corpus/` (914 GB, about $6-7 a month): the raw sources, the costly outputs (index,
models, runs) and the rebuildable middle steps. Bucket paths mirror `data/corpus/`, so the index
is at `semantic/index/`.

The corpus includes licensed text (Harvard Institutional Books, HathiTrust). A private, encrypted
bucket under the owner's own account is a backup, not redistribution; the bucket is never made
public and nothing in it is published.

## Where

| | |
| --- | --- |
| Bucket | `bom-authorship-index` (private, SSE-B2 encryption, keep only the last version) |
| Path | mirrors `data/corpus/` (index at `semantic/index/`) |
| Key | `~/.config/backblaze/credentials` on the Mac mini, mode 600: `B2_KEY_ID`, `B2_APP_KEY`, `B2_BUCKET`, `B2_BUCKET_ID`. The key `bom-mac-mini` reaches this bucket only (list, read, write, delete files). Never in git or chat. |
| Account | the owner's Backblaze account; console at https://secure.backblaze.com/b2_buckets.htm |
| Checksums | `data/manifests/*.jsonl` (SHA-256 per file; the index's is `semantic_index.jsonl`) |

## Commands

```
scripts/b2_backup.sh upload [path]          # copy new or changed files; never deletes in the bucket
scripts/b2_backup.sh check [path]           # size + SHA-1 comparison; exits nonzero on any difference
scripts/b2_backup.sh restore <file> <dir>   # download one file
```

`path` is relative to `data/corpus/`; it defaults to `semantic/index`, and `.` means everything.
All three log to `logs/b2_backup.log`. They need `rclone` (`brew install rclone`); the key is
passed through environment variables, so there is no rclone config file holding a secret.

## Restoring

1. Get the key: on a new machine, create a key for the bucket at
   https://secure.backblaze.com/app_keys.htm and save it as above.
2. `rclone copy ":b2:bom-authorship-index" data/corpus --checksum --transfers 8` (or a subfolder of both)
   with `RCLONE_B2_ACCOUNT` and `RCLONE_B2_KEY` set from the credentials file (as
   `scripts/b2_backup.sh` does).
3. Verify against the manifests, e.g. for the index:
   `uv run python -m metadata.manifest verify data/corpus/semantic/index data/manifests/semantic_index.jsonl`.

## Adding to the index

The index is built shard by shard, so new volumes become new shards (BOM-25, `semantic.index`).
Run `scripts/b2_backup.sh upload` then `check` after any new shard, rebuild the manifest, and
commit it. A weekly launchd job does the upload and check automatically (see below).
