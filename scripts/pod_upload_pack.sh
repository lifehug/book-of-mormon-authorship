#!/bin/zsh
# Upload the index pack (BOM-25) to the pod in 8 parallel rsync streams; rerunnable.
set -u
pids=()
SRC=/Users/ea/Workspace/book-of-mormon-authorship/data/corpus/semantic/pack
ssh bompod 'mkdir -p /workspace/semantic/pack'
cd $SRC
rsync -rt --partial --no-o --no-g check.parquet pack.json bompod:/workspace/semantic/pack/
ls pack_*.parquet | sort | awk '{print > ("/tmp/bompack." NR%8)}'
for i in 0 1 2 3 4 5 6 7; do
  rsync -rt --partial --no-o --no-g --files-from=/tmp/bompack.$i ./ bompod:/workspace/semantic/pack/ &
  pids+=($!)
done
fail=0
for p in $pids; do wait $p || fail=$((fail+1)); done
echo "PACK UPLOAD DONE failed_streams=$fail $(date)"
