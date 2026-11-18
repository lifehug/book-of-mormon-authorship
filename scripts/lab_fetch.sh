#!/usr/bin/env bash
# The lab: copy corpus folders from the private B2 bucket to this machine with a read-only key.
# Usage: scripts/lab_fetch.sh minimum | <path under data/corpus> ...
#   minimum  what the lab's door needs: normalized/ (162 GB, every text), semantic/index/ (119 GB,
#            the meaning-search vectors) and lab/ (8 GB, the fast index): about 290 GB
#   <path>   any other folder listed in docs/holdings.md, e.g. sweep  or  style_embed/runs/style_v2
# Key: ~/.config/backblaze/credentials (B2_KEY_ID, B2_APP_KEY, B2_BUCKET), mode 600, never in git;
# docs/lab/access.md says how to get one. Copies only; resumes; never deletes anything.
set -euo pipefail
cd "$(dirname "$0")/.."
creds=~/.config/backblaze/credentials
[ -r "$creds" ] || { echo "missing $creds (see docs/lab/access.md)" >&2; exit 2; }
# shellcheck disable=SC1090
set -a; . "$creds"; set +a
export RCLONE_B2_ACCOUNT="$B2_KEY_ID" RCLONE_B2_KEY="$B2_APP_KEY"
[ $# -ge 1 ] || { echo "usage: $0 minimum | <path under data/corpus> ..." >&2; exit 2; }
paths=("$@"); [ "$1" = "minimum" ] && paths=(normalized semantic/index lab)
mkdir -p logs
for rel in "${paths[@]}"; do
  echo "$(date -u +%FT%TZ) fetch $rel"
  rclone copy ":b2:$B2_BUCKET/$rel" "data/corpus/$rel" --checksum --transfers 8 --fast-list \
    --stats 5m --stats-one-line --log-file logs/lab_fetch.log --log-level INFO
done
echo "done; verify with: uv run python -m metadata.manifest verify <dir> data/manifests/<name>.jsonl"
