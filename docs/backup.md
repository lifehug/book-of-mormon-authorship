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
scripts/b2_backup.sh weekly                 # upload . then check .; skips if the drive is absent
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
commit it. A weekly launchd job does the upload and check automatically (below).

## Weekly job

`scripts/launchd/com.bom.b2backup.plist` runs `scripts/b2_backup.sh weekly` on Sundays at 03:00
(Mac mini time), logging to `logs/b2_backup.log` and `logs/b2_weekly.out`. If the corpus drive
is not mounted it logs a skip and exits. Install or reinstall:

```
cp scripts/launchd/com.bom.b2backup.plist ~/Library/LaunchAgents/
launchctl bootout gui/$(id -u)/com.bom.b2backup 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.bom.b2backup.plist
```

Don't edit `scripts/b2_backup.sh` while a run from it is going: bash reads a script as it runs,
so an edit can make it execute stray lines. Stop the run, edit, restart (or run a copy).

## First backup (2026-11-04/05)

- Upload: 914 GB in three runs (index first; then the whole corpus, restarted once to raise
  parallel transfers from 8 to 32 for the ~2 million small text files, with one 48 MB chunk per
  file so memory stays near 1.5 GB). 13 MiB/s for large files; small files are limited per file.
  One transient DNS failure on the first run, re-sent by the next.
- Restore test: `semantic/index/shard_p00137.npy` (70.6 MB) downloaded from the bucket; SHA-256
  `dd575da7...c268609` matches `data/manifests/semantic_index.jsonl`.
