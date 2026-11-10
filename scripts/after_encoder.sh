#!/bin/bash
# BOM-32/35/36, owner 2026-11-09 ("unlike last night, where everything stopped... things just
# kept going"; "do not hold the unblinding"): when the 590M style encoder's pod is finished, commit
# its results, unblind, then run the synthesis and the tables that read the unblinded results,
# committing and pushing after each step. A step that fails is logged and reported on the issue;
# the steps that do not depend on it still run. Run a frozen copy under tmux.
set -uo pipefail
cd /Users/ea/Workspace/book-of-mormon-authorship
LOG=logs/after_encoder.log
say() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
gate() { uv run ruff check . -q && uv run ruff format --check . -q && uv run pytest -q > /dev/null; }
commit() {  # message, paths...
  local msg="$1"; shift
  git add "$@" 2>/dev/null
  if git diff --cached --quiet; then say "nothing to commit for: $msg"; return 0; fi
  gate && git commit -qm "$msg

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_016PMpSssrj2TAWoVfcVKnJo" && git push -q && say "committed: $msg" \
    || { say "COMMIT FAILED: $msg"; return 1; }
}
issue() { gh issue comment "$1" -b "$2" > /dev/null || say "issue comment failed"; }
failed=()

phase() { python3 -c "import json;print(json.load(open('logs/style_pod_mid/state.json'))['phase'])"; }
until [[ "$(phase)" =~ ^(done|failed|capped)$ ]]; do sleep 300; done
eval_ok=$(python3 -c "import json;s=json.load(open('logs/style_pod_mid/state.json'));print(int(bool(s.get('eval_home')) and not s.get('eval_failed')))")
say "encoder pod finished (phase $(phase)); encoder tests home: $eval_ok"

# 1. The encoder's results and the blind manifest
uv run python -m eval.imitation report >> "$LOG" 2>&1 || failed+=(imitation_report)
commit "BOM-30/32: the 590M style encoder: benchmark, threshold, blind scoring of the sealed set (on its pod, no key), imitation" \
  data/benchmark/style_embed_mid.json data/benchmark/imitation/style_embed_mid.json \
  data/benchmark/imitation.json data/blind/ || failed+=(commit_encoder)

# 2. Unblind (needs seal.json and outputs.json committed)
if uv run python -m blind.unblind >> "$LOG" 2>&1; then
  commit "BOM-32: unblinded (simulated blinding): every method's records against the key, decoy accuracy, leave-one-candidate-out, false-match ladder" \
    data/blind/unblinded.json && issue 42 "Unblinded $(date '+%F %T') by scripts/after_encoder.sh: \`data/blind/unblinded.json\` committed. Next: synthesis (BOM-35), tables, paper slots."
else
  failed+=(unblind); say "UNBLIND FAILED; see $LOG"
  issue 42 "Unblinding failed at $(date '+%F %T'); the error is in logs/after_encoder.log on the Mac. Nothing was revealed beyond what the log shows."
fi

# 3. Synthesis per size, then the tables that read the unblinded results
if [ -f data/blind/unblinded.json ]; then
  { uv run python -m synth.model rates pilot base mid && \
    uv run python -m synth.model run --sizes pilot,base,mid; } >> "$LOG" 2>&1 || failed+=(synthesis)
  commit "BOM-35: synthesis per size (125M, 297M, 590M) from the unblinded results" data/synthesis/ || true
  uv run python -m eval.scribes run >> "$LOG" 2>&1 || failed+=(scribes)
  uv run python -m eval.claims table >> "$LOG" 2>&1 || failed+=(claims)
  commit "BOM-34/42: scribe comparison (6.3) and claims table from the unblinded results" data/ || true
fi
uv run python -m eval.open_set rescore >> "$LOG" 2>&1 || failed+=(open_set)
uv run python -m eval.prior_work table >> "$LOG" 2>&1 || failed+=(prior_work)
commit "BOM-68/69: open-set and prior-work tables with the 590M style encoder" data/benchmark/ || true

if [ ${#failed[@]} -eq 0 ]; then
  say "ALL DONE: unblinded, synthesis and tables committed"
  issue 45 "Overnight chain finished $(date '+%F %T'): synthesis per size in \`data/synthesis/\`, tables refreshed. Next: fill the paper's result slots (BOM-36)."
else
  say "DONE WITH FAILURES: ${failed[*]}"
  issue 45 "Overnight chain finished with failures: ${failed[*]} (details in logs/after_encoder.log on the Mac). Next: fix those, then the paper's result slots."
fi
