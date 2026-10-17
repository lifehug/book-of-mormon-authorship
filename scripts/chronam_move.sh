#!/usr/bin/env sh
# Move finished Chronicling America batch tarballs off the internal disk as they land (BOM-10).
#
# The batches are downloaded by hand into ~/Downloads (76 of them, about 59 GB), which does not
# fit on a 256 GB internal disk alongside everything else. This moves each one to the external
# SSD once it is complete, so Downloads never accumulates.
#
# "Complete" means the size has not changed between two passes. A browser writes the final
# .tar.bz2 name only after the download finishes (Safari uses a .download directory until then,
# Chrome .crdownload), but the stability check costs nothing and covers a slow flush.
#
# Run under nohup; it loops until stopped.
#
#     nohup sh scripts/chronam_move.sh > logs/chronam_move.log 2>&1 &

set -e
SRC="${1:-$HOME/Downloads}"
DST="${2:-/Volumes/bomdata/incoming/chronam}"
INTERVAL="${3:-30}"

mkdir -p "$DST"
echo "watching $SRC -> $DST every ${INTERVAL}s"

while true; do
    for f in "$SRC"/*.tar.bz2; do
        [ -e "$f" ] || continue
        name=$(basename "$f")
        size1=$(wc -c < "$f" 2>/dev/null || echo 0)
        sleep 3
        size2=$(wc -c < "$f" 2>/dev/null || echo 0)
        if [ "$size1" != "$size2" ] || [ "$size1" = "0" ]; then
            echo "$(date '+%H:%M:%S') still growing, leaving: $name"
            continue
        fi
        # A browser re-downloading a file it already has names the copy "batch (1).tar.bz2".
        # Treat it as a duplicate of "batch.tar.bz2" and drop it, but only when the sizes agree:
        # a differing size means the original is damaged, and the copy is the good one.
        base=$(echo "$name" | sed -E 's/ \([0-9]+\)\.tar\.bz2$/.tar.bz2/')
        if [ "$base" != "$name" ]; then
            orig=""
            [ -e "$DST/$base" ] && orig="$DST/$base"
            [ -z "$orig" ] && [ -e "$SRC/$base" ] && orig="$SRC/$base"
            if [ -n "$orig" ] && [ "$(wc -c < "$orig")" = "$size1" ]; then
                echo "$(date '+%H:%M:%S') duplicate of $base, removing: $name"
                rm -f "$f"
                continue
            fi
            if [ -n "$orig" ]; then
                echo "$(date '+%H:%M:%S') WARNING $name differs from $base; keeping both"
            else
                name="$base"
            fi
        fi
        if [ -e "$DST/$name" ]; then
            echo "$(date '+%H:%M:%S') already at destination, removing duplicate: $name"
            rm -f "$f"
            continue
        fi
        mv "$f" "$DST/$name"
        echo "$(date '+%H:%M:%S') moved $name ($(echo "$size1" | awk '{printf "%.2f GB", $1/1e9}'))"
    done
    sleep "$INTERVAL"
done
