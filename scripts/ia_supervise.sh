#!/usr/bin/env sh
# Keep the Internet Archive pull running until the work is actually done (BOM-09).
#
# The pull stops itself when it thinks the Archive is rate-limiting us, which is correct
# behaviour. Twice that judgement was wrong -- once on a single unservable file, once on the
# third flaky item of a 16-hour run -- and each time the job sat dead for hours with nobody
# watching. Tuning the heuristic is not the fix; the heuristic will be wrong again. The fix is
# that being wrong should cost minutes, not a night.
#
# So: restart after any exit, as long as the work list is still shrinking. If a restart makes no
# progress at all, the stop was real and this gives up rather than hammering a service that is
# genuinely asking us to stop.
#
#     nohup sh scripts/ia_supervise.sh > logs/ia_supervise.log 2>&1 &

set -e
TARGET=251204
TEXT=data/corpus/internet_archive/text
LOG=logs/ia_pull.log
BACKOFF="${1:-300}"      # seconds to wait before each restart
MAX_IDLE="${2:-3}"       # consecutive restarts with no new files before giving up

count() { find "$TEXT" -type f 2>/dev/null | wc -l | tr -d ' '; }

idle=0
while true; do
    have=$(count)
    if [ "$have" -ge "$TARGET" ]; then
        echo "$(date '+%F %T') complete: $have/$TARGET"
        break
    fi
    echo "$(date '+%F %T') starting pull at $have/$TARGET"
    uv run python -u -m ingest.internet_archive pull --skip-harvard-overlap --workers 16 \
        >> "$LOG" 2>&1 || true
    now=$(count)
    gained=$((now - have))
    echo "$(date '+%F %T') pull exited, +$gained items (now $now/$TARGET)"

    if [ "$now" -ge "$TARGET" ]; then
        echo "$(date '+%F %T') complete: $now/$TARGET"
        break
    fi

    # A real rate limit produces no progress. Bad luck produces thousands of files.
    if [ "$gained" -le 0 ]; then
        idle=$((idle + 1))
        echo "$(date '+%F %T') no progress ($idle/$MAX_IDLE consecutive)"
        if [ "$idle" -ge "$MAX_IDLE" ]; then
            echo "$(date '+%F %T') giving up: $MAX_IDLE restarts with no progress. The Archive"
            echo "  is probably genuinely refusing us. Leave it for some hours before retrying."
            break
        fi
        # Back off harder when nothing is moving.
        sleep $((BACKOFF * idle * 4))
    else
        idle=0
        sleep "$BACKOFF"
    fi
done
