#!/usr/bin/env bash
set -eu # errexit+nounset
set -o pipefail # pipefail
PY=python # prefer python (CI)
command -v "$PY" >/dev/null 2>&1 || PY=python3 # fallback
command -v "$PY" >/dev/null 2>&1 || { echo "ERROR: python/python3 not found"; exit 127; } # guard
$PY .cursor/agents/benchmarks/scripts/check_routing_parity.py --self-test # 1
$PY .cursor/agents/benchmarks/scripts/check_secrets_hygiene.py # 2
$PY .cursor/agents/benchmarks/scripts/check_routing_parity.py # 3
$PY .cursor/agents/benchmarks/scripts/validate_orchestrator_trace.py --input .cursor/agents/benchmarks/fixtures/orchestrator-trace/pass_frontend_low_risk.md --check-fixtures # 4
$PY .cursor/agents/benchmarks/scripts/validate_cases.py # 5
$PY .cursor/agents/benchmarks/scripts/run_benchmark.py # 6
$PY .cursor/agents/benchmarks/scripts/score_benchmark.py --actual .cursor/agents/benchmarks/runs/latest/actual_results.jsonl --golden .cursor/agents/benchmarks/expected/golden_summary.json # 7
echo "OK: full gate passed" # done
exit 0 # end

