#!/bin/sh
# Runs after the primary chain: pre-registered secondary model (stages 1-2 first), then two labelled
# exploratory runs (reasoning-enabled monitor; temperature-0 repeat), then the remaining secondary stages.
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python
while ! grep -q "chain done" results/logs/primary_chain.log 2>/dev/null; do sleep 20; done
run() { echo "=== $* $(date -u +%FT%TZ) ==="; $PY -m swarm_evidence run "$@" || echo "exited nonzero: $*"; }
run --stage stage1 --model gemma-4-31b-it --tag _gemma --stage-budget 10 --concurrency 4 --rpm 24
run --stage stage2 --model gemma-4-31b-it --tag _gemma --stage-budget 10 --concurrency 4 --rpm 24
run --stage stage1 --model "qwen3.5-397b+reasoning" --tag _reasoning_exploratory --max-output-tokens 4096 --stage-budget 5 --concurrency 4 --rpm 24
run --stage stage1 --tag _repeat_exploratory --replicates 2 --stage-budget 2 --concurrency 4 --rpm 24
echo "=== live slice $(date -u +%FT%TZ) ==="; $PY -m swarm_evidence live --seeds 12 --arms dependency,lexical,chronological --caps 2000 --stage-budget 5 --rpm 22 || echo "live exited nonzero"
run --stage calibration --model gemma-4-31b-it --tag _gemma --stage-budget 10 --concurrency 4 --rpm 24
run --stage stage3 --model gemma-4-31b-it --tag _gemma --stage-budget 10 --concurrency 4 --rpm 24
echo "=== followup done $(date -u +%FT%TZ) ==="
