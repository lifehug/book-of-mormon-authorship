#!/bin/zsh
# BOM-23: every reuse search in order (known-answer draws, then the full tables), skipping any
# whose result already exists. Resumable: passim runs are cached under data/corpus/reuse_runs.
cd "$(dirname "$0")/.."
searches=($(uv run python -c "
import json
s=json.load(open('data/reuse/exact/searches.json'))['searches']
print(' '.join(sorted(k for k in s if ':draw' in k) + ['late_war:full','sermon:full','bom:full']))"))
for s in $searches; do
  f="data/reuse/exact/alignments/${s/:/_}.json"
  [[ -f $f ]] && { echo "done: $s"; continue; }
  uv run python -m reuse.exact align $s --workers 6 || echo "FAILED: $s"
done
