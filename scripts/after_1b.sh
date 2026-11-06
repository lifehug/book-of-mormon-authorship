#!/bin/bash
# BOM-27/28/66: when the 1B is home (driver state "done" and model.pt on the Mac), run its
# benchmark (primary, V1-V3) on a rented H100, then publish it (owner-approved: etherfuse,
# CC BY-NC 4.0). Run a frozen copy under tmux.
set -euo pipefail
cd /Users/ea/Workspace/book-of-mormon-authorship
M=data/corpus/timelocked_lm/runs/large/model.pt
until [ -f "$M" ] && grep -q '"phase": "done"' logs/large_pod/state.json; do sleep 120; done
echo "$(date '+%F %T') 1B home; starting its benchmark"
uv run python scripts/alm_pod.py --issue 38 --files logs/alm_pod_files.txt --size large --cap 40
grep -q '"phase": "done"' logs/alm_pod_large/state.json || { echo "benchmark pod did not finish"; exit 1; }
for f in alm_large alm_large_v1 alm_large_v2 alm_large_v3; do
  test -f "data/benchmark/$f.json" || { echo "missing $f.json"; exit 1; }
done
echo "$(date '+%F %T') 1B benchmark home; publishing"
uv run python -m timelocked_lm.release convert large
uv run python -m timelocked_lm.release card large --repo etherfuse/timelocked-1830-1b
uv run python -m timelocked_lm.release upload large --repo etherfuse/timelocked-1830-1b
echo "$(date '+%F %T') done"
