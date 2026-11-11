#!/usr/bin/env bash
# BOM-75..77 (Part 2, Stage 0) GPU chain (owner, 2026-11-11: "start 75 and once the upload finishes
# and network is free do 76 and 77 given the resources and compute are available").
# 1. wait until the Hugging Face upload (tmux hfpush) has ended;
# 2. wait until the network is clean: three 20-ping readings in a row at <=2% loss;
# 3. for each size, check the RunPod balance covers the job's cap plus $5, then run its pod
#    (scripts/alm_pod.py --part2: texts up at <=2 MB/s, base model from B2, results home, pod wiped).
# A step that cannot start (balance) waits and rechecks every 10 minutes; it never skips.
# Usage: scripts/stage0_chain.sh            log: logs/stage0_chain.log
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/stage0_chain.log
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$log"; }
balance() {
  curl -s -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(cat ~/.config/runpod/token)" \
    https://api.runpod.io/graphql -d '{"query":"query { myself { clientBalance } }"}' |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["myself"]["clientBalance"])' \
    2>/dev/null || echo 0
}
clean() {
  local l
  l=$(ping -q -c 20 -i 0.5 1.1.1.1 2>/dev/null | grep -oE '[0-9.]+% packet loss' | cut -d% -f1)
  [ -n "$l" ] && [ "${l%.*}" -le 2 ]
}
say "chain start"
while tmux has-session -t '=hfpush' 2>/dev/null &&
  ! tail -3 logs/hf_candidates_push.log | grep -qE '^(DONE|EXIT)'; do
  sleep 300
done
say "Hugging Face upload ended: $(tail -1 logs/hf_candidates_push.log)"
n=0
while [ "$n" -lt 3 ]; do
  if clean; then n=$((n + 1)); else n=0; fi
  sleep 30
done
say "network clean (3 readings)"
for spec in "pilot 10" "base 15" "mid 30"; do
  read -r size cap <<<"$spec"
  until python3 -c "import sys; sys.exit(0 if float('$(balance)') >= $cap + 5 else 1)"; do
    say "$size: balance \$$(balance) below cap \$$cap + \$5; waiting for a top-up"
    sleep 600
  done
  say "$size: start (balance \$$(balance), cap \$$cap)"
  uv run python scripts/alm_pod.py --issue 86 --files logs/alm_pod_p2_files_all.txt \
    --size "$size" --part2 --cap "$cap" >>"logs/alm_pod_p2_$size.out" 2>&1
  st=$(python3 -c "import json; print(json.load(open('logs/alm_pod_p2_$size/state.json'))['phase'])" 2>/dev/null)
  say "$size: driver exited; state $st"
done
say "BOM-75 GPU chain done"
