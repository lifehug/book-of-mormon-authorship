#!/usr/bin/env bash
# Amendment 54: Joseph Smith's later revelations, one pod per size (the H100 type that scored
# Amendments 43-51). Uploads the encoded unit and the sealed set (capped at 2 MB/s by pod_jobs.py);
# the base model comes from B2. Results only come home; no weights. Each pod starts only when the
# RunPod balance covers its cap plus $5. Afterwards: python -m eval.js_later report.
# Usage: scripts/a54_later.sh            log: logs/a54_chain.log
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/a54_chain.log
say() { echo "$(date -u +%FT%TZ) [A54] $*" | tee -a "$log"; }
balance() {
  curl -s -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(cat ~/.config/runpod/token)" \
    https://api.runpod.io/graphql -d '{"query":"query { myself { clientBalance } }"}' |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["myself"]["clientBalance"])' \
    2>/dev/null || echo 0
}
files=logs/a54_files.txt
printf '%s\n' data/corpus/alm/a54/cand__joseph-smith__revelations__post1830.npz \
  data/corpus/blind/sealed.jsonl >"$files"
for spec in "pilot 2" "base 3" "mid 4"; do
  read -r size cap <<<"$spec"
  until python3 -c "import sys; sys.exit(0 if float('$(balance)') >= $cap + 5 else 1)"; do
    say "$size: balance \$$(balance) below cap \$$cap + \$5; waiting for a top-up"
    sleep 600
  done
  say "$size: start (balance \$$(balance), cap \$$cap)"
  uv run python scripts/pod_jobs.py --name "a54_$size" --issue 84 --files "$files" \
    --extra "data/corpus/timelocked_lm/runs/$size/model.pt" \
    --jobs "python -m eval.js_later alm $size --micro-batch 8" \
    --fetch "data/blind/a54/alm_$size.json" --cap "$cap" \
    >>"logs/a54_$size.out" 2>&1
  st=$(python3 -c "import json; print(json.load(open('logs/pod_jobs_a54_$size/state.json'))['phase'])" 2>/dev/null)
  say "$size: driver exited; state $st"
done
say "Amendment 54 GPU runs done"
