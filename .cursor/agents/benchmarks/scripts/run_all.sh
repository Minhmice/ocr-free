#!/bin/sh
set -eu

# Run from repo root (recommended). If run elsewhere, we still try to resolve paths relative to this script.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BENCH_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

CASES_DIR="$BENCH_ROOT/cases"
RUNS_LATEST="$BENCH_ROOT/runs/latest"
ACTUAL="$RUNS_LATEST/actual_results.jsonl"
GOLDEN="$BENCH_ROOT/expected/golden_summary.json"

python "$SCRIPT_DIR/validate_cases.py" --cases-dir "$CASES_DIR"
python "$SCRIPT_DIR/run_benchmark.py" --cases-dir "$CASES_DIR" --out-dir "$RUNS_LATEST"
python "$SCRIPT_DIR/score_benchmark.py" --actual "$ACTUAL" --golden "$GOLDEN"

echo "summary_scored.json: $RUNS_LATEST/summary_scored.json"

