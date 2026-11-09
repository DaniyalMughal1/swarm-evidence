#!/bin/sh
# Held-out run order for the primary model (frozen protocol). Each stage has its own credit cap;
# the runner also enforces the cumulative SWARM_MAX_CREDITS ceiling from .env.
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python
for st in stage1 stage2 controls calibration stage3 stage4; do
  echo "=== $st $(date -u +%FT%TZ) ==="
  $PY -m swarm_evidence run --stage "$st" --stage-budget 15 --concurrency 4 --rpm 24 || echo "stage $st exited nonzero"
done
echo "=== chain done $(date -u +%FT%TZ) ==="
