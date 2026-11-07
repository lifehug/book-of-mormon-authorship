#!/bin/bash
# The 125M fine-tunes ran out of GPU memory on the Mac at 8 sequences a micro-batch while the sweep
# masking also ran (2026-11-06). Rerun them at 2 (the same 8-sequence update, accumulated), after
# mac_gpu_chain.sh ends. Each step resumes from what is on disk. Run a frozen copy under tmux.
set -uo pipefail
cd /Users/ea/Workspace/book-of-mormon-authorship
while tmux has-session -t '=macgpu' 2>/dev/null; do sleep 60; done
run() { echo "$(date '+%F %T') $*"; uv run python "$@" || echo "FAILED: $*"; }
run -m alm.candidates train pilot --micro-batch 2
run -m alm.candidates validate pilot
run -m eval.imitation alm pilot --micro-batch 2
run -m eval.imitation alm pilot --variant v1 --micro-batch 2
run -m eval.imitation report
echo "$(date '+%F %T') rerun done"
