## Benchmark Rubric (Phase 3A)

This rubric defines deterministic-only scoring for the seed benchmark cases under `.cursor/agents/benchmarks/**`.

### Scope and limitations (Phase 3A)

- **Seed cases only**: This directory contains a small, representative seed set (not the full 50-case distribution described in planning).
- **Deterministic-only**: Scoring and validation MUST be script/rule-based and MUST NOT call external LLMs.
- **Routing + protocol focus**: Seed cases primarily validate routing correctness, contract-complete handoffs, workflow sequencing, and validator-driven failure detection.

### Required case fields

Each JSONL line in `cases/*.jsonl` MUST match the case schema defined in `.planning/codebase/AGENT_BENCHMARK_PLAN.md` §3:

- `id` (string)
- `layer` (string; A/B/C/D)
- `prompt` (string)
- `expected` object:
  - `task_type` (string)
  - `primary_agent` (string; must be a known agent id from `.cursor/agents/registry.yaml`)
  - `secondary_agents` (string[])
  - `quality_gates` (string[])
  - `validation_commands` (string[])
- `tags` (string[]) containing:
  - one **category tag** (e.g. `docs_only`, `implementation`, `debugging`, `architecture`, `research`, `rule_ingestion`, `validation_only`, `mixed_conflict`)
  - one **difficulty tag** (e.g. `easy`, `medium`, `hard`)
- `notes` (string) explaining why `expected` is correct, with evidence paths when relevant.

### Quality gate evidence rule

Expected quality gates MUST be consistent with `.cursor/agents/routing/rules.yaml`:

- `quality_gates.mandatory_before_done`: `code-reviewer`, `qa-tester`

### Validation commands evidence rule

When a case expects validations, the command strings MUST reference the canonical scripts:

- `python .cursor/agents/scripts/validate_agent_system.py`
- `python .cursor/agents/scripts/test_search_smoke.py`

### Deterministic scoring (100 points)

Total score is **100 points**, using the weights specified in `.planning/codebase/AGENT_BENCHMARK_PLAN.md` §5:

- **task classification**: 15
- **primary agent**: 20
- **secondary agents**: 10
- **quality gate discipline**: 20
- **validation correctness**: 15
- **handoff schema completeness**: 10
- **minimal-agent selection**: 5
- **failure recovery**: 5

### Deterministic-only scoring rules (high level)

- **Exact-match where possible**: Compare predicted vs expected `task_type`, `primary_agent`, `secondary_agents` (order-insensitive), `quality_gates` (order-insensitive), and `validation_commands` (order-insensitive).
- **Minimal-agent selection**: Penalize unnecessary delegation when the prompt clearly routes to a single specialist (evidence: `.cursor/agents/validation/benchmark-suite.md` Scenario 1).
- **Handoff schema completeness**: When a case is a handoff/contract test (Layer B), require the response structure defined in `.cursor/agents/shared/agent-contract.md`.
- **Failure recovery**: For Layer D mutation cases, require use of a temp copy and validator-driven detection (safety rules in `.planning/codebase/AGENT_BENCHMARK_PLAN.md` §9).

### Non-scored (report-only) metrics

These may be reported for analysis but MUST NOT affect the 100-point score:

- Reliability (repeatability under deterministic settings)
- Efficiency (runtime, number of steps/tool calls)
- Alignment/Discipline (protocol compliance beyond minimum)
- Latency (time-to-first-correct decision)
- Maintainability (clarity/structure of produced artifacts)

