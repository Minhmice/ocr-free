## Agent Benchmarks Report (Template)

### Run metadata

- **run_id**: `<run_id>`
- **timestamp**: `<timestamp>`
- **suite**: `<suite_name>`
- **system_under_test**: `cursor-agent-vip-pro`
- **runner_version**: `<version>`
- **os**: `<os>`
- **python**: `<python_version>`

### Summary

- **cases_total**: `<int>`
- **score_total**: `<0-100>`
- **pass_rate**: `<passes>/<total>`

### Scores by layer

- **Layer A (routing)**: `<score>`
- **Layer B (handoff contract)**: `<score>`
- **Layer C (workflow trace)**: `<score>`
- **Layer D (failure mutation)**: `<score>`

### Evidence: validator outputs

> Per `.planning/codebase/AGENT_BENCHMARK_PLAN.md` safety rules, do not claim a validation passed without embedding stdout/stderr evidence.

#### `.cursor/agents/scripts/validate_agent_system.py`

```text
<paste stdout/stderr here>
```

#### `.cursor/agents/scripts/test_search_smoke.py`

```text
<paste stdout/stderr here>
```

### Failures (if any)

For each failure, include:

- **case_id**: `<case_id>`
- **expected**: `<expected json summary>`
- **actual**: `<actual json summary>`
- **reason**: `<why scored as fail>`
- **recommendation**: `<next action>`

### Recommendations

- `<recommendation 1>`
- `<recommendation 2>`

# Benchmarks (Phase 3B.1) — Latest Run

This folder is intentionally minimal in Phase 3B.1.

## Quickstart

Validate seed cases:

```bash
python .cursor/agents/benchmarks/scripts/validate_cases.py
```

Dry-run the benchmark runner (**scaffold validation only**; no benchmark execution):

```bash
python .cursor/agents/benchmarks/scripts/run_benchmark.py --dry-run
```

Run the benchmark runner in real mode (Phase 3B.1: **deterministic predictor** for Layers **A–C**; **no LLM**):

```bash
python .cursor/agents/benchmarks/scripts/run_benchmark.py
```

Score a run:

```bash
python .cursor/agents/benchmarks/scripts/score_benchmark.py --actual .cursor/agents/benchmarks/runs/latest/actual_results.jsonl
```

## Phase 3C: adversarial suite + golden regression checks

Phase 3C adds an adversarial routing suite designed to probe confusing keywords, negations, and near-collisions while keeping the existing 50 verified expected outputs stable.

### Adversarial suite

- **New cases file**: `.cursor/agents/benchmarks/cases/adversarial.jsonl`
- **Case count**: 20
- **Total suite size**: 70 cases (50 baseline + 20 adversarial)

Run schema validation (should report `total_cases=70`):

```bash
python .cursor/agents/benchmarks/scripts/validate_cases.py
```

Run the benchmark runner (real mode; deterministic predictor for Layers A–C):

```bash
python .cursor/agents/benchmarks/scripts/run_benchmark.py
```

Score the latest run:

```bash
python .cursor/agents/benchmarks/scripts/score_benchmark.py --actual .cursor/agents/benchmarks/runs/latest/actual_results.jsonl
```

### Golden regression checks

The committed golden baseline summary is stored at:

- `.cursor/agents/benchmarks/expected/golden_summary.json`

Regression expectations:

- **score_total** remains **100**
- **failures** remains empty
- Any deviations from the baseline summary must be treated as a regression unless there is an objectively correct reason (and the change is documented)

### `run_all.sh` usage

If your environment provides a wrapper script named `run_all.sh`, it should be used as the single entrypoint to:

- validate case schema
- run the benchmark runner
- score the latest run

If `run_all.sh` is not present in this repository checkout, use the three commands above as the canonical Phase 3C procedure.

## Phase 4: Local + CI quality gate wrappers

### POSIX wrapper

```sh
sh .cursor/agents/benchmarks/scripts/run_all.sh
```

### Windows PowerShell wrapper

```powershell
powershell -ExecutionPolicy Bypass -File .cursor/agents/benchmarks/scripts/run_all.ps1
```

Both wrappers fail fast and print:

- `summary_scored.json: <path>`

### CI

GitHub Actions workflow:

- `.github/workflows/agent-benchmark.yml`

### Pre-commit manual full run

```bash
pre-commit run agent-benchmark-run-all --hook-stage manual
```

## Result fields guidance (Phase 3B.1)

Each case result row should include:

- **mode**: `"dry_run"` or `"real"`
- **benchmark_valid**: boolean indicating whether the runner produced a **benchmarkable** `actual` for that case
- **reason**: short string explaining why the case is **not** benchmark-valid (e.g., `"dry_run_scaffold_validation"`, `"unsupported_layer"`, `"missing_input"`)

### Dry-run vs real mode (Phase 3B.1)

- **dry-run (`--dry-run`)**: **scaffold validation only**. It is allowed (and expected) that outputs are **not benchmarkable**. In reports, treat dry-run as “the harness validates and can execute,” not “the system passed the benchmark.”
- **real mode**: attempts to produce **benchmarkable** results. In Phase 3B.1, real mode is only expected to be meaningful for **Layers A–C** (deterministic predictor); other layers may intentionally remain scaffold-only.

### `benchmark_valid` meaning (Phase 3B.1)

- **`benchmark_valid=true`**: this case produced an `actual` that should be included in scoring/metrics for the layer(s) supported in this phase.
- **`benchmark_valid=false`**: this case should be treated as **non-benchmarkable** and **excluded** from scoring. `reason` must be present to make the exclusion auditable.

### Layer D/E status in Phase 3B.2

- **Layer D (failure mutation)**: mutations are applied **only inside a temp copy** of `.cursor/**` (never mutate the real working tree). The runner records mutation artifacts and validation outputs so failures are auditable.
- **Layer E (architecture ablation)**: still **scaffold-only** for ablation execution, but cases must include a top-level `ablation_axis` object so the harness can record axis metadata. Scoring treats Layer E like routing while scaffolded (axis ignored for now).

### Evidence requirement: paste validator outputs

- This report must embed the exact stdout/stderr from:
  - `.cursor/agents/scripts/validate_agent_system.py`
  - `.cursor/agents/scripts/test_search_smoke.py`
  - `.cursor/agents/benchmarks/scripts/validate_cases.py` (if you claim case schema validation passed)
  The goal is that reviewers can audit claims without re-running locally.

Interpretation:

- **dry-run**: Expect `mode="dry_run"` and `benchmark_valid=false` with `reason="dry_run_scaffold_validation"`. Treat dry-run outputs (if any are written) as **non-benchmarkable**; the dry-run contract is scaffold validation only.
- **real mode**: Expect `mode="real"`. In Phase 3B.1, Layers **A–C** use a deterministic predictor and should normally be `benchmark_valid=true`. Other layers may be `benchmark_valid=false` with an appropriate `reason` (for example, `"unsupported_layer"`).

Guidance:

- When `benchmark_valid=false`, `reason` should be non-empty and stable (prefer a small fixed set of reason strings over ad-hoc prose).

