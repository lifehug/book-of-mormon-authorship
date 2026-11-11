#!/usr/bin/env bash
# BOM-76 and BOM-77 (seeds) GPU chain, after BOM-75's (scripts/stage0_chain.sh) logs "done".
# One pod per size runs: cross-work folds (eval.part2_decoys lowo), the register placebo
# (eval.part2_decoys placebo) and the five extra seeds (eval.part2_seeds run). Uploads from the Mac
# are the token inputs and the sealed set (~25 MB, capped at 2 MB/s by pod_jobs.py); the base model
# and Amendment 43's weights come onto the pod from B2. Results only come home; no weights.
# Each pod starts only when the RunPod balance covers its cap plus $5 (rechecked every 10 min).
# Usage: scripts/stage0_chain2.sh            log: logs/stage0_chain.log
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/stage0_chain.log
say() { echo "$(date -u +%FT%TZ) [76/77] $*" | tee -a "$log"; }
balance() {
  curl -s -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(cat ~/.config/runpod/token)" \
    https://api.runpod.io/graphql -d '{"query":"query { myself { clientBalance } }"}' |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["myself"]["clientBalance"])' \
    2>/dev/null || echo 0
}
say "waiting for BOM-75's chain"
until grep -q "BOM-75 GPU chain done" "$log" 2>/dev/null; do sleep 300; done
files=logs/stage0_76_77_files.txt
cat logs/bom76_files.txt >"$files"
ls data/corpus/alm/candidates/inputs/*.npz >>"$files"
for spec in "pilot 15" "base 25" "mid 45"; do
  read -r size cap <<<"$spec"
  until python3 -c "import sys; sys.exit(0 if float('$(balance)') >= $cap + 5 else 1)"; do
    say "$size: balance \$$(balance) below cap \$$cap + \$5; waiting for a top-up"
    sleep 600
  done
  say "$size: start (balance \$$(balance), cap \$$cap)"
  uv run python scripts/pod_jobs.py --name "stage0_$size" --issue 87 --files "$files" \
    --extra "data/corpus/timelocked_lm/runs/$size/model.pt" \
    --jobs "python -m eval.part2_decoys lowo $size --micro-batch 8" \
    "python -m eval.part2_decoys placebo $size --micro-batch 8" \
    "python -m eval.part2_seeds run $size --micro-batch 8" \
    --fetch "data/blind/part2/lowo_$size.json" "data/blind/part2/placebo_$size.json" \
    "data/blind/part2/seeds_$size.json" \
    --b2-pull "data/corpus/alm/candidates/$size" --cap "$cap" >>"logs/stage0_$size.out" 2>&1
  st=$(python3 -c "import json; print(json.load(open('logs/pod_jobs_stage0_$size/state.json'))['phase'])" 2>/dev/null)
  say "$size: driver exited; state $st"
done
say "BOM-76/77 GPU chain done"
