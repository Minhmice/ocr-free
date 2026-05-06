# Benchmark History

## Purpose

Record human-auditable benchmark runs over time, so regressions and improvements can be traced without re-running old commits.

This file is **manual**. CI may surface summary data, but it must not silently rewrite history.

## Manual entry format

Append newest entry at top under **Latest**. Keep entries small and factual.

Template:

```text
- date: YYYY-MM-DD
  cases_total: <int>
  score: <0-100>
  failures: <int>
  adversarial: <int>
  mutation_cases: <int>
  ci_status: <pending|pass|fail> (<notes>)
  local_windows_wrapper: <pass|fail> (<command>)
  notes: <short>
```

## Latest

- date: 2026-04-28
  cases_total: 70
  score: 100
  failures: 0
  adversarial: 20
  mutation_cases: 6
  ci_status: pending (waiting for first GitHub Actions run)
  local_windows_wrapper: pass (`powershell -ExecutionPolicy Bypass -File .cursor/agents/benchmarks/scripts/run_all.ps1`)
  notes: Phase 4 wrappers + CI workflow added; golden regression gates PASS locally.

