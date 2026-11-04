# Off-site backup of the passage index (BOM-65)

The passage index (`data/corpus/semantic/index/`, 842 files, 119 GB) lives on the external drive
`/Volumes/bomdata`. Rebuilding it costs about a day and $100-150 of rented GPU, so a private
copy is kept on Backblaze B2 (about $0.75 a month). Nothing else from `data/corpus/` is backed up
there (owner's decision, 2026-11-04).

The index holds no text: `shard_*.npy` are passage vectors and `shard_*.parquet` hold only
`work_id`, passage number, character offsets and word count. It is still kept private, like the
licensed books it was made from, and is never published.

## Where

| | |
| --- | --- |
| Bucket | `bom-authorship-index` (private, SSE-B2 encryption, keep only the last version) |
| Path | `semantic/index/` |
| Key | `~/.config/backblaze/credentials` on the Mac mini, mode 600: `B2_KEY_ID`, `B2_APP_KEY`, `B2_BUCKET`, `B2_BUCKET_ID`. The key `bom-mac-mini` reaches this bucket only (list, read, write, delete files). Never in git or chat. |
| Account | the owner's Backblaze account; console at https://secure.backblaze.com/b2_buckets.htm |
| Checksums | `data/manifests/semantic_index.jsonl` (SHA-256 per file) |

## Commands

```
scripts/b2_backup.sh upload                 # copy new or changed files; never deletes in the bucket
scripts/b2_backup.sh check                  # size + SHA-1 comparison; exits nonzero on any difference
scripts/b2_backup.sh restore <file> <dir>   # download one file
```

All three log to `logs/b2_backup.log`. They need `rclone` (`brew install rclone`); the key is
passed through environment variables, so there is no rclone config file holding a secret.

## Restoring the whole index

1. Get the key: on a new machine, create a key for the bucket at
   https://secure.backblaze.com/app_keys.htm and save it as above.
2. `rclone copy ":b2:bom-authorship-index/semantic/index" data/corpus/semantic/index --checksum --transfers 8`
   with `RCLONE_B2_ACCOUNT` and `RCLONE_B2_KEY` set from the credentials file (as
   `scripts/b2_backup.sh` does).
3. Verify every file against the manifest:
   `uv run python -m metadata.manifest verify data/corpus/semantic/index data/manifests/semantic_index.jsonl`.

## Adding to the index

The index is built shard by shard, so new volumes become new shards (BOM-25, `semantic.index`).
Run `scripts/b2_backup.sh upload` then `check` after any new shard, rebuild the manifest, and
commit it. A weekly launchd job does the upload and check automatically (see below).
