#!/usr/bin/env bash
# BOM-89 steps 2 and 3 on the rented H100 (exploratory); started by scripts/style_pod.py --size v2.
# Each part resumes itself, so a restart of this script carries on where it stopped.
#   1. step 2: per-episode sweep vectors with the BOM-30 encoder
#   2. step 3: train the second encoder (style_embed.v2)
#   3. the same vectors with the second encoder (each part also holds the whole-unit vector)
# Usage: bash scripts/style_v2_job.sh <output folder of the run>
set -euo pipefail
out="$1"
pip install -q scipy scikit-learn joblib rapidfuzz > /dev/null 2>&1 || true
python -m sweep.index episodes --tag _gpu
python -m style_embed.v2 train --out "$out"
python -m sweep.index episodes --model "$out/style.pt" --tag _v2
touch /workspace/JOB_DONE
