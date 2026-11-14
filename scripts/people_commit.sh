#!/usr/bin/env bash
# Commit and push the Library of Congress lookup's cache every 30 minutes while the lookup runs
# (tmux session `people`), so a disk failure or restart cannot cost the replies (BOM-91).
# Usage: scripts/people_commit.sh   (under tmux)
cd "$(dirname "$0")/.." || exit 1
while :; do
  sleep 1800
  git add data/sweep/loc_cache.jsonl
  if ! git diff --cached --quiet; then
    n=$(wc -l < data/sweep/loc_cache.jsonl | tr -d ' ')
    git commit -q -m "BOM-91: Library of Congress lookup cache, $n replies (timed commit)

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01RcNmwqL3jKNd4o1FwRf41B" -- data/sweep/loc_cache.jsonl && git push -q
  fi
  tmux has-session -t '=people' 2>/dev/null || break
done
