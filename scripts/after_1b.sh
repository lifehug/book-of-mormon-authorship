#!/bin/bash
# BOM-27/28/31/66: when the 1B is home (driver state "done" and model.pt on the Mac), run its
# benchmark (primary, V1-V3) on a rented H100, publish it (owner-approved: etherfuse,
# CC BY-NC 4.0), then, every size running every test (owner, 2026-11-06), the 1B's candidate and
# control models (BOM-28) and its imitation model part (BOM-31: primary, V1, V3), each on its own
# H100 at the same time. Run a frozen copy under tmux.
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
echo "$(date '+%F %T') published; starting the 1B candidate models and imitation runs"
uv run python scripts/candidates_pod.py --issue 38 --size large --cap 40 &
cand=$!
sleep 300  # both drivers rewrite ~/.ssh/config when their pod comes up; keep them apart
uv run python -m eval.imitation files large > logs/imitation_large_files.txt
uv run python scripts/pod_jobs.py --name imitation_large --issue 41 \
  --files logs/imitation_large_files.txt \
  --jobs "python -m eval.imitation alm large --micro-batch 8" \
         "python -m eval.imitation alm large --variant v1 --micro-batch 8" \
         "python -m eval.imitation alm large --variant v3" \
  --fetch data/benchmark/imitation/alm_large.json data/benchmark/imitation/alm_large_v1.json \
          data/benchmark/imitation/alm_large_v3.json --cap 40 &
imit=$!
status=0
wait "$cand" || status=1
wait "$imit" || status=1
grep -q '"phase": "done"' logs/candidates_pod_large/state.json || { echo "candidate pod did not finish"; status=1; }
grep -q '"phase": "done"' logs/pod_jobs_imitation_large/state.json || { echo "imitation pod did not finish"; status=1; }
uv run python -m eval.imitation report || status=1
echo "$(date '+%F %T') done (status $status)"
exit $status
