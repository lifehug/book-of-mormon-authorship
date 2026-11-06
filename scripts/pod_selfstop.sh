#!/bin/bash
# Runs on the 1B pod (BOM-27). If the model is finished but the Mac has not collected it within
# GRACE seconds (the Mac is off or offline), stop the pod: a stopped pod keeps its disk, model
# included, and bills only storage. The Mac driver restarts it and fetches when it is back.
OUT=/workspace/repo/data/corpus/timelocked_lm/runs/large/model.pt
GRACE=${GRACE:-10800}
eval "$(tr '\0' '\n' < /proc/1/environ | grep -E '^RUNPOD_(API_KEY|POD_ID)=' | sed 's/^/export /')"
while true; do
  if [ -f "$OUT" ] && [ $(( $(date +%s) - $(stat -c %Y "$OUT") )) -gt "$GRACE" ]; then
    echo "$(date '+%F %T') model uncollected for ${GRACE}s; stopping pod $RUNPOD_POD_ID"
    curl -s -X POST -H "Authorization: Bearer $RUNPOD_API_KEY" \
      "https://rest.runpod.io/v1/pods/$RUNPOD_POD_ID/stop"
    exit 0
  fi
  sleep 600
done
