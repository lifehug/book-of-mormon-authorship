#!/bin/zsh
# One-shot (BOM-25 split): wait for the Mac's running index build to finish its current shard, then
# restart it limited to the volumes before the GPU's share. Restarting at a shard boundary loses nothing.
set -u
cd /Users/ea/Workspace/book-of-mormon-authorship
n0=$(ls data/corpus/semantic/index/shard_*.done | wc -l)
while [ "$(ls data/corpus/semantic/index/shard_*.done | wc -l)" -le "$n0" ]; do sleep 30; done
tmux kill-session -t '=semantic_index'
echo "--- restarted with --before internet_archive: $(date)" >> logs/semantic_index.log
tmux new-session -d -s semantic_index "cd $PWD && caffeinate -i uv run --extra semantic python -u -m semantic.index build --workers 6 --before internet_archive: >> logs/semantic_index.log 2>&1; echo EXIT \$? >> logs/semantic_index.log"
echo "restarted $(date)"
