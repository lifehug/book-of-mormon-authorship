#!/usr/bin/env bash
# Rerun a story-skeleton step until it finishes (BOM-25). A run stops with exit 1 when model
# calls keep failing (usage limit, outage) or blocks remain unanswered; the next run resumes from
# the event files, so waiting and retrying is all recovery needs.
# Usage: scripts/skeleton_loop.sh controls|bom [wait_seconds]
set -u
step=$1
wait=${2:-900}
until uv run python -m semantic.skeleton "$step"; do
  echo "$(date '+%F %T') $step incomplete; retrying in ${wait}s"
  sleep "$wait"
done
echo "$(date '+%F %T') $step done"
