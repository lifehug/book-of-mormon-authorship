#!/bin/bash
# Owner, 2026-11-06: every model size runs every test. The 125M runs on the Mac GPU, after the
# BOM-29 cross-check frees it: BOM-28 candidate models, then BOM-31's style and model parts
# (primary, V1, V3). Run a frozen copy under tmux.
set -uo pipefail
cd /Users/ea/Workspace/book-of-mormon-authorship
until grep -q "^EXIT" logs/bom29.log; do sleep 60; done
run() { echo "$(date '+%F %T') $*"; uv run python "$@" || echo "FAILED: $*"; }
run -m alm.candidates train pilot --micro-batch 8
run -m alm.candidates validate pilot
run -m eval.imitation style
run -m eval.imitation alm pilot
run -m eval.imitation alm pilot --variant v1
run -m eval.imitation alm pilot --variant v3
run -m eval.imitation report
echo "$(date '+%F %T') done"
