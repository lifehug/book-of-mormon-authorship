#!/bin/zsh
# One-shot (BOM-25 second split): wait for the Mac's running index build to finish its current
# shard, then stop it; the rented GPU embeds the volumes after it. Counts only the Mac's own
# shards (shard_0*), not GPU shards arriving home: the first split counted both and restarted
# mid-shard on a GPU arrival, redoing about 3 hours of Mac work.
set -u
cd /Users/ea/Workspace/book-of-mormon-authorship
n0=$(ls data/corpus/semantic/index/shard_0*.done | wc -l)
while [ "$(ls data/corpus/semantic/index/shard_0*.done | wc -l)" -le "$n0" ]; do sleep 30; done
tmux kill-session -t '=semantic_index'
echo "--- stopped after its shard; the GPU takes the rest from ${1:-?} ($(date))" >> logs/semantic_index.log
echo "stopped $(date)"
