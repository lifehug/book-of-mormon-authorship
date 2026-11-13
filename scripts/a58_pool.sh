#!/usr/bin/env bash
# Amendment 58 (BOM-90): the 55 tested authors' models, each scoring all 1,070 tests, one pod per
# size (the H100 type that scored
# BOM-75). Uploads the packed plan (licensed text, wiped after) (capped at 2 MB/s by pod_jobs.py);
# the base model comes from B2. Results only come home; no weights. Each pod starts only when the
# RunPod balance covers its cap plus $5. Afterwards: python -m eval.list_size report.
# Usage: scripts/a58_pool.sh            log: logs/a58_chain.log
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/a58_chain.log
say() { echo "$(date -u +%FT%TZ) [A58] $*" | tee -a "$log"; }
balance() {
  curl -s -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(cat ~/.config/runpod/token)" \
    https://api.runpod.io/graphql -d '{"query":"query { myself { clientBalance } }"}' |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["myself"]["clientBalance"])' \
    2>/dev/null || echo 0
}
files=logs/a58_files.txt
printf '%s\n' data/corpus/alm/benchmark/pool_plan.json.gz >"$files"
for spec in "pilot 6" "base 10" "mid 20"; do
  read -r size cap <<<"$spec"
  until python3 -c "import sys; sys.exit(0 if float('$(balance)') >= $cap + 5 else 1)"; do
    say "$size: balance \$$(balance) below cap \$$cap + \$5; waiting for a top-up"
    sleep 600
  done
  say "$size: start (balance \$$(balance), cap \$$cap)"
  uv run python scripts/pod_jobs.py --name "a58_$size" --issue 101 --files "$files" \
    --extra "data/corpus/timelocked_lm/runs/$size/model.pt" \
    --jobs "python -m alm.benchmark $size --pool --micro-batch 8" \
    --fetch "data/benchmark/alm_${size}_pool.json" --cap "$cap" \
    >>"logs/a58_$size.out" 2>&1
  st=$(python3 -c "import json; print(json.load(open('logs/pod_jobs_a58_$size/state.json'))['phase'])" 2>/dev/null)
  say "$size: driver exited; state $st"
done
say "Amendment 58 GPU runs done"
