#!/usr/bin/env bash
# BOM-27/28/66: what runs on the Mac once the base model is home (owner, 2026-11-05: start the tests
# without waiting). Waits for the watcher to pass the base phase (model.pt home, SHA-256 checked),
# publishes the base model (owner's approval: public, etherfuse, CC BY-NC 4.0), runs the ALM
# benchmark at 297M after the pilot's run finishes (one job on the GPU at a time), then clears the
# uv cache once the watcher has exited. Run under tmux; logs to logs/after_base.log.
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/after_base.log
say() { echo "$(date '+%F %T') $*" | tee -a "$log"; }
phase() { python3 -c "import json; print(json.load(open('logs/pod_watch/state.json'))['phase'])"; }

say "waiting for the base model to be home"
until [[ "$(phase)" == cleanup || "$(phase)" == finished ]]; do sleep 120; done
say "base model home: $(ls -l data/corpus/timelocked_lm/runs/base/model.pt)"

repo=etherfuse/timelocked-1830-300m
uv run python -m timelocked_lm.release convert base >>"$log" 2>&1 \
  && uv run python -m timelocked_lm.release card base --repo "$repo" >>"$log" 2>&1 \
  && uv run python -m timelocked_lm.release upload base --repo "$repo" >>"$log" 2>&1 \
  && say "published https://huggingface.co/$repo" || say "base release FAILED (see above)"

say "waiting for the pilot ALM run to finish"
while tmux has-session -t '=almpilot' 2>/dev/null; do sleep 60; done
say "starting the ALM benchmark at 297M"
uv run python -m alm.benchmark base 2>&1 | grep -v -i warn | tee logs/alm_base.log
say "ALM base exit ${PIPESTATUS[0]}"

while tmux has-session -t '=podwatch' 2>/dev/null; do sleep 120; done
uv cache clean >>"$log" 2>&1 && say "uv cache cleared" || say "uv cache clean failed"
say "done"
