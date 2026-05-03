# Skill location policy

This repo separates **Cursor rules**, **job skills**, and **specialist agents**. This document explains **where each belongs**, and what is considered the **source of truth**.

## 1) Cursor rules (`.cursor/rules/**`)

**What**: Context-injection rules (`*.mdc`) that Cursor auto-applies based on file globs or `alwaysApply: true`.

**Use for**:
- Always-on orchestration policy (example: `.cursor/rules/always-orchestrator-skill.mdc`)
- Lightweight, file-context guidance (example: frontend/back-end rules)

**Do not use for**:
- Long how-to guides or large “knowledge bases”
- Duplicating specialist procedures (keep those in skills/specialists)

**Required invariants**:
- If `alwaysApply: true`, the rule must point to the canonical orchestrator skill path:
  - `.cursor/agents/orchestrator/SKILL.md`

## 2) Field job skills (`.cursor/agents/skills/**`)

**What**: One “job spec” per field (frontend, backend, database, devops, docs, etc.). These describe **what to do** and **how to operate** in that field.

**Use for**:
- High-level workflow + guardrails for a domain
- The place orchestrator handoffs can reference as “the job”

**Source of truth**:
- `.cursor/agents/skills/README.md` is the index mapping fields → skill files → specialist agents.

## 3) Specialist agents (`.cursor/agents/specialists/<id>/SKILL.md`)

**What**: The specialist role prompt. This is **who executes** the job.

**Use for**:
- Execution instructions for that agent’s operating behavior and boundaries
- The first line of any specialist handoff must reference this path (see below)

**Required handoff first line**:

`Act as <specialist-id> per .cursor/agents/specialists/<specialist-id>/SKILL.md`

## 4) Orchestrator (`.cursor/agents/orchestrator/**`)

**What**: The dispatcher that decomposes work and delegates to registered specialists.

**Source of truth**:
- `.cursor/agents/orchestrator/SKILL.md`
- `.cursor/agents/orchestrator/SKILL-DETAILS.md`
- `.cursor/agents/orchestrator/task-to-agent-mapping-rules.md`
- `.cursor/agents/orchestrator/PERFORMANCE.md`

## 5) External / project-level skill packs (`.agents/skills/**`)

Some skills (notably **Expo/React Native**) live under project-level `.agents/skills/**` and are referenced from Cursor via:
- `.cursor/agents/skills/expo-react-native.md`

Policy:
- Keep the detailed procedures in `.agents/skills/**`.
- Keep the Cursor routing bridge in `.cursor/agents/skills/*.md`.

## 6) Benchmarks (`.cursor/agents/benchmarks/**`)

Benchmarks are the repo’s deterministic quality gate for the agent system:
- `scripts/` stdlib-only harnesses
- `cases/` case corpus
- `expected/` golden baselines
- `fixtures/` non-JSONL fixtures (e.g. orchestrator trace samples)

Generated artifacts must not be committed:
- `.cursor/agents/benchmarks/runs/**` (ignored via `.gitignore`)

