#!/usr/bin/env bash
# Amendment 51 (BOM-76): the register placebo on a grid of slices, one pod per size.
# Uploads are the token inputs and the sealed set (~25 MB, capped at 2 MB/s by pod_jobs.py); the
# base model comes from B2. Results only come home; no weights. Each pod starts only when the RunPod
# balance covers its cap plus $5. Afterwards: python -m eval.part2_decoys report.
# Usage: scripts/stage0_slices.sh            log: logs/stage0_chain.log
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/stage0_chain.log
say() { echo "$(date -u +%FT%TZ) [A51] $*" | tee -a "$log"; }
balance() {
  curl -s -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(cat ~/.config/runpod/token)" \
    https://api.runpod.io/graphql -d '{"query":"query { myself { clientBalance } }"}' |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["myself"]["clientBalance"])' \
    2>/dev/null || echo 0
}
files=logs/stage0_76_77_files.txt
for spec in "pilot 8" "base 12" "mid 20"; do
  read -r size cap <<<"$spec"
  until python3 -c "import sys; sys.exit(0 if float('$(balance)') >= $cap + 5 else 1)"; do
    say "$size: balance \$$(balance) below cap \$$cap + \$5; waiting for a top-up"
    sleep 600
  done
  say "$size: start (balance \$$(balance), cap \$$cap)"
  uv run python scripts/pod_jobs.py --name "slices_$size" --issue 87 --files "$files" \
    --extra "data/corpus/timelocked_lm/runs/$size/model.pt" \
    --jobs "python -m eval.part2_decoys placebo-slices $size --micro-batch 8" \
    --fetch "data/blind/part2/placebo_slices_$size.json" --cap "$cap" \
    >>"logs/slices_$size.out" 2>&1
  st=$(python3 -c "import json; print(json.load(open('logs/pod_jobs_slices_$size/state.json'))['phase'])" 2>/dev/null)
  say "$size: driver exited; state $st"
done
say "Amendment 51 slices done"
