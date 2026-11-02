#!/usr/bin/env bash
# The paced overnight run of the story-skeleton test (BOM-25): repeat the extractor check with the
# lean call (stop if it no longer passes), then the controls, then the Book of Mormon, at most
# PER_HOUR model calls an hour (default 500). Run under tmux:
#   tmux new-session -d -s skeleton 'scripts/skeleton_overnight.sh 2>&1 | tee -a logs/skeleton.log'
set -euo pipefail
rate=${PER_HOUR:-500}
uv run python -m semantic.skeleton check --out check_lean.json --per-hour "$rate"
uv run python -c "import json,sys; sys.exit(0 if json.load(open('data/semantic/skeleton/check_lean.json'))['passes'] else 1)" \
  || { echo "lean check fails; stopping"; exit 1; }
scripts/skeleton_loop.sh controls --per-hour "$rate"
scripts/skeleton_loop.sh bom --per-hour "$rate"
