#!/usr/bin/env bash
# Pause an upload while the Mac's network is losing packets, resume it when clean (owner,
# 2026-11-11: uploads dropped remote control twice). Usage: scripts/net_guard.sh <pgrep pattern>
# Every 60 s: 20 pings to 1.1.1.1. Two readings in a row over 10% loss -> SIGSTOP the matching
# processes; two clean readings (<=2%) -> SIGCONT. Logs to logs/net_guard.log.
set -u
pat="$1"; log=logs/net_guard.log; bad=0; good=0; paused=0
while pgrep -f "$pat" >/dev/null; do
  loss=$(ping -q -c 20 -i 0.5 1.1.1.1 2>/dev/null | grep -oE '[0-9.]+% packet loss' | cut -d% -f1)
  loss=${loss:-100}; l=${loss%.*}
  if [ "$l" -gt 10 ]; then bad=$((bad+1)); good=0; elif [ "$l" -le 2 ]; then good=$((good+1)); bad=0; fi
  echo "$(date -u +%FT%TZ) loss=${loss}% paused=$paused" >>"$log"
  if [ $paused -eq 0 ] && [ $bad -ge 2 ]; then pkill -STOP -f "$pat"; paused=1; echo "$(date -u +%FT%TZ) PAUSED" >>"$log"; fi
  if [ $paused -eq 1 ] && [ $good -ge 2 ]; then pkill -CONT -f "$pat"; paused=0; echo "$(date -u +%FT%TZ) RESUMED" >>"$log"; fi
  sleep 30
done
