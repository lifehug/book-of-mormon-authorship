#!/bin/bash
# BOM-27/28/31/66: when the mid is home (driver state "done" and model.pt on the Mac), run its
# benchmark (primary, V1-V3) on a rented H100 (not published: see below), then, every size running every test (owner, 2026-11-06), the mid's candidate and
# control models (BOM-28) and its imitation model part (BOM-31: primary, V1, V3), each on its own
# H100 at the same time. Run a frozen copy under tmux.
set -euo pipefail
cd /Users/ea/Workspace/book-of-mormon-authorship
M=data/corpus/timelocked_lm/runs/mid/model.pt
until [ -f "$M" ] && grep -q '"phase": "done"' logs/mid_pod/state.json; do sleep 120; done
echo "$(date '+%F %T') mid home; starting its benchmark"
uv run python scripts/alm_pod.py --issue 38 --files logs/alm_pod_files.txt --size mid --cap 40
grep -q '"phase": "done"' logs/alm_pod_mid/state.json || { echo "benchmark pod did not finish"; exit 1; }
for f in alm_mid alm_mid_v1 alm_mid_v2 alm_mid_v3; do
  test -f "data/benchmark/$f.json" || { echo "missing $f.json"; exit 1; }
done
# Not published here: the GPT-2 export (timelocked_lm.release) cannot carry QK-norm; the mid
# model needs its own export before release (BOM-66), and publishing is the owner's call.
echo "$(date '+%F %T') mid benchmark home"
echo "$(date '+%F %T') starting the mid candidate models and imitation runs"
uv run python scripts/candidates_pod.py --issue 38 --size mid --cap 40 &
cand=$!
sleep 300  # both drivers rewrite ~/.ssh/config when their pod comes up; keep them apart
uv run python -m eval.imitation files mid > logs/imitation_mid_files.txt
uv run python scripts/pod_jobs.py --name imitation_mid --issue 41 \
  --files logs/imitation_mid_files.txt \
  --jobs "python -m eval.imitation alm mid --micro-batch 8" \
         "python -m eval.imitation alm mid --variant v1 --micro-batch 8" \
         "python -m eval.imitation alm mid --variant v3" \
  --fetch data/benchmark/imitation/alm_mid.json data/benchmark/imitation/alm_mid_v1.json \
          data/benchmark/imitation/alm_mid_v3.json --cap 40 &
imit=$!
status=0
wait "$cand" || status=1
wait "$imit" || status=1
grep -q '"phase": "done"' logs/candidates_pod_mid/state.json || { echo "candidate pod did not finish"; status=1; }
grep -q '"phase": "done"' logs/pod_jobs_imitation_mid/state.json || { echo "imitation pod did not finish"; status=1; }
uv run python -m eval.imitation report || status=1
# Owner, 2026-11-07: the full milestone snapshots go once the model is trained and tested, but
# only after the owner says yes at that moment. The pod stays stopped (storage only) until then.
if [ "$status" = 0 ]; then
  echo "tests passed: ASK THE OWNER before deleting the mid pod and its full snapshots"
else
  echo "a test failed: the mid pod and its full snapshots are kept for the owner"
fi
echo "$(date '+%F %T') done (status $status)"
exit $status
