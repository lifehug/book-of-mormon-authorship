#!/usr/bin/env bash
# BOM-27/28/66: every benchmark run of the time-locked model, one GPU job at a time (owner,
# 2026-11-05: run every test, start without waiting). After the 125M primary run (tmux almpilot):
# V3 at 125M while the base model finishes; when the base is home (the watcher is past its base
# phase: model.pt copied and SHA-256 checked), publish it (public, etherfuse, CC BY-NC 4.0) and run
# the 297M primary benchmark; then V1 and V2 at 125M, V1-V3 at 297M; then clear the uv cache once
# the watcher has exited. Each step resumes from its own saved scores. Logs: logs/alm_queue.log.
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/alm_queue.log
say() { echo "$(date '+%F %T') $*" | tee -a "$log"; }
phase() { python3 -c "import json; print(json.load(open('logs/pod_watch/state.json'))['phase'])"; }
step() {  # name, command...
  local name=$1; shift
  say "start $name"
  "$@" 2>&1 | grep --line-buffered -v -i warn >>"logs/alm_${name}.log"
  say "end $name: exit ${PIPESTATUS[0]}"
}

while tmux has-session -t '=almpilot' 2>/dev/null; do sleep 60; done
say "125M primary run finished: $(tail -2 logs/alm_pilot.log | head -1)"
step pilot_v3 uv run python -m alm.variants v3 pilot

say "waiting for the base model to be home"
until [[ "$(phase)" == cleanup || "$(phase)" == finished ]]; do sleep 120; done
repo=etherfuse/timelocked-1830-300m
uv run python -m timelocked_lm.release convert base >>"$log" 2>&1 \
  && uv run python -m timelocked_lm.release card base --repo "$repo" >>"$log" 2>&1 \
  && uv run python -m timelocked_lm.release upload base --repo "$repo" >>"$log" 2>&1 \
  && say "published https://huggingface.co/$repo" || say "base release FAILED (see above)"

step base uv run python -m alm.benchmark base
step pilot_v1 uv run python -m alm.benchmark pilot --variant v1
step pilot_v2 uv run python -m alm.variants v2 pilot
step base_v1 uv run python -m alm.benchmark base --variant v1
step base_v2 uv run python -m alm.variants v2 base
step base_v3 uv run python -m alm.variants v3 base

while tmux has-session -t '=podwatch' 2>/dev/null; do sleep 120; done
uv cache clean >>"$log" 2>&1 && say "uv cache cleared" || say "uv cache clean failed"
say "queue done"
