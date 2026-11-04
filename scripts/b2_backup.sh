#!/usr/bin/env bash
# BOM-65: off-site private backup of the passage index to Backblaze B2.
# Usage: scripts/b2_backup.sh upload|check|restore <file> <dir>
#   upload   copy new or changed index files to the bucket (never deletes remote files)
#   check    compare local index and bucket by size and SHA-1; nonzero exit on any difference
#   restore  download one file from the bucket into <dir>
# Key: ~/.config/backblaze/credentials (B2_KEY_ID, B2_APP_KEY, B2_BUCKET), mode 600, never in git.
set -euo pipefail
cd "$(dirname "$0")/.."
creds=~/.config/backblaze/credentials
[ -r "$creds" ] || { echo "missing $creds (see docs/backup.md)" >&2; exit 2; }
# shellcheck disable=SC1090
set -a; . "$creds"; set +a
export RCLONE_B2_ACCOUNT="$B2_KEY_ID" RCLONE_B2_KEY="$B2_APP_KEY"
src=data/corpus/semantic/index
dst=":b2:$B2_BUCKET/semantic/index"
mkdir -p logs
log=logs/b2_backup.log
case "${1:-}" in
  upload)
    echo "$(date -u +%FT%TZ) upload start" >>"$log"
    rclone copy "$src" "$dst" --checksum --transfers 8 --b2-chunk-size 96M \
      --stats 10m --stats-one-line --log-file "$log" --log-level INFO
    echo "$(date -u +%FT%TZ) upload done" >>"$log" ;;
  check)
    rclone check "$src" "$dst" --one-way --log-file "$log" --log-level NOTICE
    echo "$(date -u +%FT%TZ) check: 0 differences" | tee -a "$log" ;;
  restore)
    [ $# -eq 3 ] || { echo "usage: $0 restore <file> <dir>" >&2; exit 2; }
    rclone copy "$dst/$2" "$3" --log-level NOTICE ;;
  *) sed -n '3,6p' "$0"; exit 2 ;;
esac
