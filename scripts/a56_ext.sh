#!/usr/bin/env bash
# Amendment 56: 32 more benchmark authors (eight tasks), one pod per size (the H100 type that scored
# BOM-75). Uploads the packed plan (licensed text, wiped after) (capped at 2 MB/s by pod_jobs.py);
# the base model comes from B2. Results only come home; no weights. Each pod starts only when the
# RunPod balance covers its cap plus $5. Afterwards: python -m eval.clustered head-to-head.
# Usage: scripts/a56_ext.sh            log: logs/a56_chain.log
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/a56_chain.log
say() { echo "$(date -u +%FT%TZ) [A56] $*" | tee -a "$log"; }
balance() {
  curl -s -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(cat ~/.config/runpod/token)" \
    https://api.runpod.io/graphql -d '{"query":"query { myself { clientBalance } }"}' |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["myself"]["clientBalance"])' \
    2>/dev/null || echo 0
}
files=logs/a56_files.txt
printf '%s\n' data/corpus/alm/benchmark/p3_plan.json.gz >"$files"
for spec in "pilot 3" "base 5" "mid 8"; do
  read -r size cap <<<"$spec"
  until python3 -c "import sys; sys.exit(0 if float('$(balance)') >= $cap + 5 else 1)"; do
    say "$size: balance \$$(balance) below cap \$$cap + \$5; waiting for a top-up"
    sleep 600
  done
  say "$size: start (balance \$$(balance), cap \$$cap)"
  uv run python scripts/pod_jobs.py --name "a56_$size" --issue 86 --files "$files" \
    --extra "data/corpus/timelocked_lm/runs/$size/model.pt" \
    --jobs "python -m alm.benchmark $size --ext --micro-batch 8" \
    --fetch "data/benchmark/alm_${size}_p3.json" --cap "$cap" \
    >>"logs/a56_$size.out" 2>&1
  st=$(python3 -c "import json; print(json.load(open('logs/pod_jobs_a56_$size/state.json'))['phase'])" 2>/dev/null)
  say "$size: driver exited; state $st"
done
say "Amendment 56 GPU runs done"
