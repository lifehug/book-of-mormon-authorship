#!/usr/bin/env bash
# BOM-28: the 125M benchmark runs that fit the Mac mini's memory (the 297M fine-tunes swap on 16 GB
# and go to a rented H100 instead). One GPU job at a time; each resumes from its saved scores.
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/alm_queue.log
say() { echo "$(date '+%F %T') $*" | tee -a "$log"; }
step() {
  local name=$1; shift
  say "start $name"
  "$@" 2>&1 | grep --line-buffered -v -i warn >>"logs/alm_${name}.log"
  say "end $name: exit ${PIPESTATUS[0]}"
}
step pilot_v3 uv run python -m alm.variants v3 pilot
step pilot_v1 uv run python -m alm.benchmark pilot --variant v1
step pilot_v2 uv run python -m alm.variants v2 pilot
uv cache clean >>"$log" 2>&1 && say "uv cache cleared" || say "uv cache clean failed"
say "Mac queue done"
