#!/bin/zsh
# Upload BOM-27 token files to the pod in 8 parallel rsync streams; rerunnable (rsync skips done files).
set -u
pids=()
SRC=/Users/ea/Workspace/book-of-mormon-authorship/data/corpus/timelocked_lm/tokens
ssh bompod 'mkdir -p /workspace/corpus/timelocked_lm/tokens'
cd $SRC
ls | sort | awk '{print > ("/tmp/bomup." NR%8)}'
for i in 0 1 2 3 4 5 6 7; do
  rsync -rt --partial --no-o --no-g --files-from=/tmp/bomup.$i ./ bompod:/workspace/corpus/timelocked_lm/tokens/ &
  pids+=($!)
done
fail=0
for p in $pids; do wait $p || fail=$((fail+1)); done
echo "UPLOAD DONE failed_streams=$fail $(date)"
