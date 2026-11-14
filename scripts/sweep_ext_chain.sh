#!/usr/bin/env bash
# BOM-89: the further known books, after their KJV masking (tmux `maskext`,
# `python -m kjv_mask.run sweep_ext`) has ended: tokens, per-episode vectors with the second
# encoder (Mac GPU, resumes), then coverage at the full profile and the two equal sizes.
# Usage: scripts/sweep_ext_chain.sh   (under tmux; log logs/sweep_ext_chain.log)
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/sweep_ext_chain.log
say() { echo "$(date -u +%FT%TZ) [EXT] $*" | tee -a "$log"; }
while tmux has-session -t '=maskext' 2>/dev/null; do sleep 60; done
[ -s data/kjv_mask/sweep_ext/spans.jsonl ] || { say "no spans: masking did not finish"; exit 1; }
say "masking done; tokens"
uv run python -m sweep.index tokens --ext >>"$log" 2>&1 || { say "tokens failed"; exit 1; }
say "episodes"
uv run python -m sweep.index episodes --ext --tag _v2 \
  --model data/corpus/style_embed/runs/style_v2/style.pt >>"$log" 2>&1 || { say "episodes failed"; exit 1; }
for n in "" 2 11; do
  say "coverage ${n:-full}"
  uv run python -m sweep.episodes --tag _v2 ${n:+--profile-episodes $n} >>"$log" 2>&1 || { say "coverage failed"; exit 1; }
done
say "done"
