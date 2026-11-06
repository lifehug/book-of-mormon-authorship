#!/bin/bash
# BOM-39: after the KJV masking of the sweep blocks exits cleanly, run the index and calibration.
set -euo pipefail
cd /Users/ea/Workspace/book-of-mormon-authorship
until grep -q "^EXIT" logs/sweep_mask.log; do sleep 60; done
grep -q "^EXIT 0" logs/sweep_mask.log || { echo "masking failed; chain not started"; exit 1; }
uv run python -m sweep.index tokens --workers 8
uv run python -m sweep.index mfw
uv run python -m sweep.index embed
uv run python -m sweep.calibrate
