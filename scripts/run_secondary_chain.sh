#!/bin/sh
# Held-out run order for the secondary model family (frozen protocol), tagged "_gemma".
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python
STAGES=${STAGES:-"stage1 stage2 calibration stage3"}
for st in $STAGES; do
  echo "=== $st $(date -u +%FT%TZ) ==="
  $PY -m swarm_evidence run --stage "$st" --model gemma-4-31b-it --tag _gemma --stage-budget 10 --concurrency 3 --rpm ${RPM:-20} || echo "stage $st exited nonzero"
done
echo "=== chain done $(date -u +%FT%TZ) ==="
