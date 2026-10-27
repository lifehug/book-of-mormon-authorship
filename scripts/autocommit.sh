#!/usr/bin/env sh
# Commit and push given paths on a timer while a long job runs (CLAUDE.md: long jobs commit
# their output as they go). Usage: scripts/autocommit.sh <seconds> "<message>" <path>...
# Stops when the tmux session named in $WATCH (if set) has ended, after a final commit.
set -u
interval=$1; msg=$2; shift 2
commit() {
  git add -- "$@" 2>/dev/null
  if ! git diff --cached --quiet -- "$@"; then
    git commit -q -m "$msg ($(date '+%Y-%m-%d %H:%M'))

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- "$@" && git push -q origin master
  fi
}
while :; do
  sleep "$interval"
  commit "$@"
  if [ -n "${WATCH:-}" ] && ! tmux has-session -t "$WATCH" 2>/dev/null; then
    commit "$@"; exit 0
  fi
done
