#!/usr/bin/env bash
# Rerun a story-skeleton step until it finishes (BOM-25). A run stops with exit 1 when model
# calls keep failing (usage limit, outage) or blocks remain unanswered; the next run resumes from
# the event files, so waiting and retrying is all recovery needs. Extra arguments go to the step,
# e.g. --per-hour 500 to pace the model calls.
# Usage: scripts/skeleton_loop.sh controls|bom [args...]
set -u
step=$1
shift
until uv run python -m semantic.skeleton "$step" "$@"; do
  echo "$(date '+%F %T') $step incomplete; retrying in 900s"
  sleep 900
done
echo "$(date '+%F %T') $step done"
