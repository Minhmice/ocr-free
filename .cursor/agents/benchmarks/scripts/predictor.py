#!/usr/bin/env python3
"""
Deterministic predictor for benchmark Layers A–C (Phase 3B.1).

Hard constraints:
- stdlib-only
- deterministic keyword/phrase checks (explicit contains), no fuzzy matching
- signals derived from:
  - .planning/codebase/AGENT_RUNTIME_PROTOCOL.md (taxonomy + recommended routing precedence)
  - .cursor/agents/routing/rules.yaml (agent keyword signals + quality gate rules)

This module is used by `.cursor/agents/benchmarks/scripts/run_benchmark.py` to avoid
false-confidence "echo expected" behavior in real mode.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


# ---- Shared helpers --------------------------------------------------------------


def _norm_prompt(prompt: str) -> str:
    return " ".join((prompt or "").strip().lower().split())


def _contains_any(haystack: str, phrases: List[str]) -> List[str]:
    h = _norm_prompt(haystack)
    raw_tokens = h.split()
    # Light, deterministic token normalization for short keyword matching.
    tokens = [t.strip(".,;:!?()[]{}\"'`") for t in raw_tokens]
    hits: List[str] = []
    for p in phrases:
        pn = _norm_prompt(p)
        if not pn:
            continue
        # Avoid false positives for very short keywords like "ui" matching inside other words
        # (e.g. "suite"). For single-token keywords <= 3 chars, require token-level match.
        if " " not in pn and len(pn) <= 3:
            if pn in tokens:
                hits.append(p)
            continue
        if pn in h:
            hits.append(p)
    return hits


def _iter_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: expected object, got {type(obj).__name__}")
            yield line_no, obj


# ---- Case loading ----------------------------------------------------------------


def load_cases(cases_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all cases from cases_dir/*.jsonl.
    Returns a flat list of dict objects in file order.
    """
    cases: List[Dict[str, Any]] = []
    cases_dir = Path(cases_dir)
    for p in sorted(cases_dir.glob("*.jsonl")):
        for _, obj in _iter_jsonl(p):
            cases.append(obj)
    return cases


# ---- Deterministic maps (explicit phrase/keyword checks) -------------------------
# NOTE: stdlib-only: we intentionally do not parse YAML at runtime. These keyword
# lists are copied directly from `.cursor/agents/routing/rules.yaml` signals.*.keywords.


SIGNAL_KEYWORDS: Dict[str, List[str]] = {
    "product-manager": ["requirements", "scope", "priority", "acceptance", "mvp", "non-goal"],
    "planner": ["plan", "roadmap", "decompose", "sequence", "milestone", "documentation plan"],
    "research-analyst": ["compare", "evaluate", "unknown", "best practice", "tradeoff", "analyze docs", "review docs"],
    "frontend-developer": [
        "ui",
        "component",
        "page",
        "layout",
        "a11y",
        "render",
        "translation",
        "i18n",
        "locale",
        "localized",
        "shadcn",
        "components.json",
        "radix",
        "add button",
        "add dialog",
    ],
    "backend-developer": ["api", "route", "auth", "service", "server", "endpoint"],
    "typescript-specialist": ["type error", "generic", "zod", "inference", "type-safe"],
    "database-specialist": ["schema", "migration", "rls", "query", "index", "sql"],
    "debugger": ["bug", "repro", "regression", "flaky", "trace", "root cause"],
    "code-reviewer": ["review", "risk", "security", "maintainability", "correctness"],
    "security-specialist": [
        "security",
        "vulnerability",
        "audit",
        "risk",
        "xss",
        "sql injection",
        "auth",
        "access control",
        "secret",
        "csp",
    ],
    "qa-tester": ["test plan", "verify", "pass/fail", "edge case", "coverage"],
    "documentation-writer": ["readme", "update readme", "write docs", "update docs", "add runbook", "write how-to", "changelog"],
    "devops-engineer": ["deploy", "pipeline", "rollback", "slo", "monitoring", "ci/cd"],
    "google-cli-specialist": [
        "gws",
        "google workspace",
        "google-cli",
        "gws auth",
        "google workspace auth",
        "gws discovery",
        "google workspace discovery",
        "drive cli",
        "gmail cli",
        "calendar cli",
        "gws validate",
    ],
}


TASK_PHRASES: Dict[str, List[str]] = {
    # NOTE: This map is for *explicit phrase hits* we expose as matched_signals.task_phrases.
    # Classification precedence is implemented in classify_task_type() below.
    "docs_only": ["readme", "docs", "runbook", "markdown", "documentation", "docs only", "documentation only"],
    # Intentionally excludes generic "update/change/edit/fix" per Phase 3B.1-fix rules.
    "implementation": ["implement", "refactor", "add endpoint", "add api", "add route", "create migration", "schema", "function", "config file"],
    "debugging": [
        "bug",
        "repro",
        "reproduce",
        "root cause",
        "regression",
        "flaky",
        "wrong route",
        "500",
        "stack trace",
        "crash",
        "fails",
        "failing",
        "error",
    ],
    "architecture": ["architecture", "design", "implementation plan", "plan", "roadmap", "sequence", "milestone", "decompose"],
    "research": ["compare", "evaluate", "tradeoff", "tradeoffs", "best practice", "recommendation"],
    "rule_ingestion": [
        "ingest",
        ".mdc",
        "rule-map",
        "registry",
        "routing ingestion",
        "routing rules",
        "rules.yaml",
        "skill-finder",
        "specialist scaffold",
        "specialist scaffolding",
    ],
    "validation_only": [
        "run the agent-system validators",
        "run the agent system validators",
        "run the agent system validation scripts",
        "run validators",
        "validate_agent_system.py",
        "test_search_smoke.py",
        "summarize results",
        "just report pass/fail",
        "do not change any files",
        "no file changes",
        "no code changes",
        "no code change",
    ],
    "conflict": ["but do not", "but don't", "do not change", "don't change", "without changing", "however do not", "no backend code"],
}


def classify_task_type(prompt: str) -> str:
    """
    Deterministic task-type classifier (Layer A).

    Returns one of:
      docs_only | implementation | debugging | architecture | research | rule_ingestion | validation_only | mixed_task

    Precedence rules (Phase 3B.1-fix):
    - DOCS_ONLY wins when prompt is clearly docs-only AND does not include code/config/runtime terms.
    - Words update/change/edit/fix alone do NOT imply implementation.
    - IMPLEMENTATION wins only when prompt mentions code/API/component/schema/migration/script/function/config file
      or explicit repo file edits beyond docs.
    - RULE_INGESTION wins for .mdc/rule-map/skill-finder/registry/routing ingestion/specialist scaffold.
    - DEBUGGING wins for reproduce/root cause/failing/wrong route unless user asks patch immediately.
    - MIXED_TASK when docs + implementation/rule_ingestion.
    """
    p_raw = prompt or ""
    p = _norm_prompt(p_raw)

    # Deterministic lexical signals.
    docs_terms = [
        "readme",
        "docs",
        "documentation",
        "runbook",
        "markdown",
        ".md",
    ]
    docs_analysis_terms = [
        "analyze",
        "analysis",
        "review",
        "summarize",
        "summary",
        "audit",
        "evaluate",
        "compare",
    ]

    # Separate "mentions code" vs "requests code change".
    #
    # IMPORTANT:
    # - Mentions like "config-driven", "validation scripts", or "commands" do NOT imply implementation.
    # - Implementation requires either:
    #   (change verb + code artifact term) OR (change verb + UI/FE domain term).
    change_verbs = [
        "add",
        "implement",
        "refactor",
        "resolve",
        "create",
        "modify",
        "rename",
        "remove",
        "delete",
        "migrate",
        "convert",
        "wire",
        "hook up",
        "integrate",
        "build",
        "generate",
        # allow "fix" but only when paired with an artifact/UI term
        "fix",
        "adjust",
        "tweak",
        "update",
        "change",
        "edit",
    ]

    code_artifact_terms = [
        "auth",
        "authentication",
        "api",
        "endpoint",
        "route",
        "router",
        "handler",
        "service",
        "cli",
        "command",
        "commands",
        "subcommand",
        "flag",
        "schema",
        "migration",
        "sql",
        "script",
        "function",
        "class",
        "module",
        "config file",
        "configuration file",
        "yaml file",
        "json file",
        "toml file",
        "env file",
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".sql",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
    ]

    ui_terms = [
        # NOTE: do not include bare "ui" here; substring matches cause false positives
        # (e.g. "suite"). Frontend routing still uses token-aware SIGNAL_KEYWORDS.
        "component",
        "page",
        "layout",
        "button",
        "dashboard",
    ]

    # Mentions that are *not* themselves implementation.
    # (Used only to avoid accidental "has_code" style flips.)
    code_mention_terms = [
        "code",
        "repo",
        "file",
        "config",
        "configuration",
        "config-driven",
        "command",
        "commands",
        "validation script",
        "validation scripts",
    ]

    rule_ingestion_terms = [
        ".mdc",
        "rule-map",
        "registry",
        "routing ingestion",
        "routing rules",
        "skill-finder",
        "specialist scaffold",
        "specialist scaffolding",
        "agent mapping",
        "agent-system mapping",
        "agent system mapping",
        "ingest rules",
        "ingestion",
    ]

    debugging_terms = [
        "repro",
        "reproduce",
        "root cause",
        "failing",
        "fails",
        "wrong route",
        "regression",
        "flaky",
        "trace",
        "stack trace",
        "crash",
    ]

    # "Patch immediately" ask: debugging should NOT override implementation when user explicitly requests a patch now.
    patch_now_terms = [
        "send a patch",
        "provide a patch",
        "apply a patch",
        "make the change",
        "implement the fix",
        "fix it now",
    ]

    docs_only_constraints = [
        "docs only",
        "documentation only",
        "no code changes",
        "no code change",
        "do not change any code",
        "don't change any code",
    ]

    def has_any(terms: List[str]) -> bool:
        return any(t in p for t in terms)

    has_docs = has_any(docs_terms)
    has_docs_analysis = has_docs and has_any(docs_analysis_terms)
    has_rule_ingestion = has_any(rule_ingestion_terms)
    has_debugging = has_any(debugging_terms)
    asks_patch_now = has_any(patch_now_terms)
    has_validation_only = bool(_contains_any(p_raw, TASK_PHRASES["validation_only"]))
    has_docs_only_constraint = has_any(docs_only_constraints)
    has_conflict = bool(_contains_any(p_raw, TASK_PHRASES["conflict"]))

    # Docs-only hard override (Layer A stability):
    # If the user *explicitly* constrains to docs-only and mentions docs artifacts,
    # force docs_only even if prompt mentions code-ish words like "validation scripts".
    if has_docs_only_constraint and has_docs and not has_rule_ingestion:
        return "docs_only"

    # Implementation request detection (strict).
    # Avoid counting negated change verbs (e.g. "do not change any files") as implementation intent.
    def has_nonnegated_change_verb() -> bool:
        for v in change_verbs:
            if v not in p:
                continue
            # Very simple deterministic negation guard.
            if f"do not {v}" in p or f"don't {v}" in p:
                continue
            return True
        return False

    has_change_verb = has_nonnegated_change_verb()
    mentions_code_artifact = has_any(code_artifact_terms)
    mentions_ui_domain = has_any(ui_terms)
    requests_implementation = bool(has_change_verb and (mentions_code_artifact or mentions_ui_domain))

    # "Mentions code" only: can inform mixed_task, but must not flip research/architecture into implementation.
    mentions_code_only = bool(has_any(code_mention_terms) or mentions_code_artifact)

    # Conflicts ("but do not", "without changing", etc.) indicate mixed intent: implement something while
    # preserving constraints. Keep this as mixed_task even when implementation is requested.
    if has_conflict and requests_implementation and not has_docs and not has_rule_ingestion:
        return "mixed_task"

    # Mixed if docs mentioned + (implementation-ish OR rule ingestion).
    if has_docs and (has_rule_ingestion or requests_implementation):
        return "mixed_task"

    # Rule ingestion wins next (explicit routing/registry/rules scaffolding work).
    if has_rule_ingestion:
        return "rule_ingestion"

    # Validation-only when explicitly requested and not accompanied by implementation signals.
    if has_validation_only and not requests_implementation and not has_rule_ingestion:
        return "validation_only"

    # Debugging wins unless the user is explicitly asking for a patch immediately.
    # (Do not let generic change verbs like "fix" flip root-cause investigations into implementation.)
    if has_debugging and not asks_patch_now and not has_rule_ingestion:
        return "debugging"

    # Docs analysis without explicit doc-writing intent routes to research.
    # (e.g. "analyze our docs", "summarize the runbook") should not be treated as docs_only.
    if has_docs_analysis and not requests_implementation and not has_rule_ingestion and not has_debugging:
        return "research"

    # Docs-only is strict: must be docs terms with no code/config/runtime terms.
    if has_docs and not mentions_code_only and not has_rule_ingestion and not has_debugging:
        return "docs_only"

    # Implementation only when prompt mentions concrete code/config/runtime terms.
    if requests_implementation:
        return "implementation"

    # Otherwise fall back to other taxonomy based on explicit phrases (conservative).
    hits: Dict[str, List[str]] = {}
    for k, phrases in TASK_PHRASES.items():
        m = _contains_any(p_raw, phrases)
        if m:
            hits[k] = m

    if "architecture" in hits and "research" in hits:
        return "mixed_task"
    if "architecture" in hits:
        return "architecture"
    if "research" in hits:
        return "research"

    # Ambiguity defaults to mixed_task (conservative).
    return "mixed_task"


def _match_routing_signals(prompt: str) -> Dict[str, List[str]]:
    matched: Dict[str, List[str]] = {}
    for agent_id, keywords in SIGNAL_KEYWORDS.items():
        hits = _contains_any(prompt, keywords)
        if hits:
            matched[agent_id] = hits
    return matched


def _routing_precedence() -> List[str]:
    # Recommended protocol precedence from AGENT_RUNTIME_PROTOCOL §3 (deterministic, limited set).
    return [
        "rule-skill-ingestor",
        "documentation-writer",
        "debugger",
        "database-specialist",
        "typescript-specialist",
        "backend-developer",
        "frontend-developer",
        "devops-engineer",
        "qa-tester",
        "research-analyst",
        "planner",
        "product-manager",
        "code-reviewer",
        "google-cli-specialist",
    ]


def predict_quality_gates(task_type: str, prompt: str) -> List[str]:
    """
    Deterministic gate prediction.

    Requirements:
    - IMPLEMENTATION or MIXED_TASK => include code-reviewer + qa-tester.
    - DOCS_ONLY => no mandatory quality gate.
    """
    tt = (task_type or "").lower()
    if tt in {"implementation", "mixed_task"}:
        return ["code-reviewer", "qa-tester"]
    return []


def predict_validation_commands(task_type: str, prompt: str) -> List[str]:
    """
    Deterministic validation-command intent prediction (no execution).

    Requirements (Phase 3B.1-fix):
    - RULE_INGESTION => both scripts
    - routing/search/skill-finder changes => test_search_smoke.py
    - registry/rule-map/.mdc/specialist scaffold changes => validate_agent_system.py
    - if task touches agent-system mappings/rules and ambiguous => both
    - DOCS_ONLY => no validation unless docs about agent-system validation docs, then validate_agent_system.py
    """
    p = _norm_prompt(prompt)

    validate_cmd = "python .cursor/agents/scripts/validate_agent_system.py"
    smoke_cmd = "python .cursor/agents/scripts/test_search_smoke.py"
    benchmark_validate_cases_cmd = "python .cursor/agents/benchmarks/scripts/validate_cases.py"
    benchmark_run_dry_cmd = "python .cursor/agents/benchmarks/scripts/run_benchmark.py --dry-run"

    def touches_search_or_skill_finder() -> bool:
        # Avoid false positives like "research" containing "search".
        tokens = p.split()
        if "search" in tokens:
            return True
        return any(
            x in p
            for x in [
                "route selection",
                "skill-finder",
                "skill finder",
                "test_search_smoke.py",
            ]
        )

    def touches_registry_or_rulemap_or_mdc() -> bool:
        return any(
            x in p
            for x in [
                "registry",
                "rule-map",
                ".mdc",
                "specialist scaffold",
                "specialist scaffolding",
                "validate_agent_system.py",
            ]
        )

    def touches_agent_system_rules_or_mappings_ambiguous() -> bool:
        # Ambiguous by design: mentions "agent system" + rules/mapping without specifying which validator.
        if "agent system" not in p and "agent-system" not in p:
            return False
        return any(x in p for x in ["rule", "rules", "mapping", "mappings", "routing rules", "signals"])

    def is_docs_about_validation_docs() -> bool:
        # Docs-only tasks generally don't require validation; exception: docs specifically about agent-system validators.
        if "docs" not in p and "documentation" not in p and "readme" not in p and "runbook" not in p:
            return False
        return any(x in p for x in ["validate_agent_system.py", "agent system validators", "validator", "validation scripts"])

    tt = (task_type or "").lower()
    if tt == "rule_ingestion":
        return [validate_cmd, smoke_cmd]

    if tt == "validation_only":
        out: List[str] = []
        # Benchmark suite validation commands (explicit request only).
        if "python .cursor/agents/benchmarks/scripts/validate_cases.py" in p or "validate_cases.py" in p:
            out.append(benchmark_validate_cases_cmd)
        if "python .cursor/agents/benchmarks/scripts/run_benchmark.py --dry-run" in p or "run_benchmark.py --dry-run" in p:
            out.append(benchmark_run_dry_cmd)
        if touches_search_or_skill_finder():
            out.append(smoke_cmd)
        if touches_registry_or_rulemap_or_mdc() or touches_agent_system_rules_or_mappings_ambiguous():
            out.append(validate_cmd)
        # If explicitly "run validators" but doesn't specify, default to both for safety.
        if not out:
            out = [validate_cmd, smoke_cmd]
        # stable de-dupe
        dedup: List[str] = []
        for c in out:
            if c not in dedup:
                dedup.append(c)
        return dedup

    # DOCS_ONLY: only validate when docs are about agent-system validation.
    if tt == "docs_only":
        if not is_docs_about_validation_docs():
            return []
        # If the docs explicitly mention "validation scripts"/"validators" (plural), default to both.
        if any(x in p for x in ["validation scripts", "agent system validators", "agent-system validators", "run validators", "run the validators"]):
            return [validate_cmd, smoke_cmd]
        return [validate_cmd]

    # Other task types: infer based on what is being changed.
    out: List[str] = []
    if touches_search_or_skill_finder():
        out.append(smoke_cmd)
    if touches_registry_or_rulemap_or_mdc():
        out.append(validate_cmd)
    if touches_agent_system_rules_or_mappings_ambiguous():
        out = [validate_cmd, smoke_cmd]

    dedup2: List[str] = []
    for c in out:
        if c not in dedup2:
            dedup2.append(c)
    return dedup2


def predict_route(prompt: str) -> Dict[str, Any]:
    """
    Predict Layer A routing output.

    Must include `matched_signals` for auditability.
    """
    task_type = classify_task_type(prompt)
    routing_signals = _match_routing_signals(prompt)

    # Synthesize rule-skill-ingestor routing signal deterministically from phrases.
    if _contains_any(prompt, TASK_PHRASES["rule_ingestion"]):
        routing_signals.setdefault("rule-skill-ingestor", ["<rule_ingestion_phrase>"])

    precedence = _routing_precedence()
    ordered_candidates = [a for a in precedence if a in routing_signals]

    primary_agent = "orchestrator"
    secondary_agents: List[str] = []

    # Precedence-driven explicit overrides per AGENT_RUNTIME_PROTOCOL.
    if task_type == "rule_ingestion":
        primary_agent = "rule-skill-ingestor"
    elif task_type == "docs_only":
        primary_agent = "documentation-writer"
    elif task_type == "validation_only":
        primary_agent = "qa-tester"
    elif task_type == "debugging":
        primary_agent = "debugger"
    elif task_type == "architecture":
        primary_agent = "planner"
    elif task_type == "research":
        primary_agent = "research-analyst"
    elif task_type == "implementation":
        # Cross-layer work: both backend+frontend signals => planner primary.
        if "backend-developer" in routing_signals and "frontend-developer" in routing_signals:
            primary_agent = "planner"
            secondary_agents = ["backend-developer", "frontend-developer"]
        else:
            # If a Google Workspace CLI signal is present, it should win over generic backend signals
            # like "auth" for implementation work.
            if "google-cli-specialist" in routing_signals:
                primary_agent = "google-cli-specialist"
            else:
                # Most-specific-wins for implementation.
                for candidate in [
                    "typescript-specialist",
                    "database-specialist",
                    "google-cli-specialist",
                    "backend-developer",
                    "frontend-developer",
                    "devops-engineer",
                ]:
                    if candidate in routing_signals:
                        primary_agent = candidate
                        break
            # Deterministic secondary for "API + typescript" or "API + database"
            p = _norm_prompt(prompt)
            if primary_agent in {"typescript-specialist", "database-specialist"} and ("api" in p or "endpoint" in p or "route" in p):
                if "backend-developer" not in secondary_agents:
                    secondary_agents.append("backend-developer")
    else:
        # mixed_task: orchestrator owns slicing/conflict resolution; include likely secondaries in stable order.
        primary_agent = "orchestrator"
        order = [
            "planner",
            "security-specialist",
            "code-reviewer",
            "google-cli-specialist",
            "backend-developer",
            "frontend-developer",
            "database-specialist",
            "typescript-specialist",
            "devops-engineer",
            "documentation-writer",
            "debugger",
            "qa-tester",
            "research-analyst",
        ]
        # Suppress false-positive database-specialist suggestions when the only DB signal is the token
        # "sql" coming from the phrase "sql injection" (security-specialist concern).
        suppress_db_sql_injection_only = False
        p_norm = _norm_prompt(prompt)
        if "sql injection" in p_norm:
            db_hits = routing_signals.get("database-specialist") or []
            if db_hits == ["sql"]:
                suppress_db_sql_injection_only = True

        for a in order:
            if suppress_db_sql_injection_only and a == "database-specialist":
                continue
            if a in routing_signals and a != primary_agent and a not in secondary_agents:
                secondary_agents.append(a)
        if "planner" not in secondary_agents:
            secondary_agents.insert(0, "planner")

    quality_gates = predict_quality_gates(task_type, prompt)
    validation_commands = predict_validation_commands(task_type, prompt)

    task_phrase_hits: Dict[str, List[str]] = {}
    for k, phrases in TASK_PHRASES.items():
        h = _contains_any(prompt, phrases)
        if h:
            task_phrase_hits[k] = h

    return {
        "task_type": task_type,
        "primary_agent": primary_agent,
        "secondary_agents": secondary_agents,
        "quality_gates": quality_gates,
        "validation_commands": validation_commands,
        "matched_signals": {
            "task_phrases": task_phrase_hits,
            "routing_signals": routing_signals,
            "routing_precedence_ordered": ordered_candidates,
        },
    }


def predict_workflow_trace(
    prompt: str,
    task_type: str,
    primary_agent: str,
    quality_gates: List[str],
) -> List[Dict[str, Any]]:
    """
    Predict a normalized workflow trace (Layer C).

    Deterministic event policy (Phase 3B.1-fix):
    - Ordered events:
      classify, route, handoff, process, optional quality_gate (repeat per gate), optional validation, final
    - Each event object:
      {"event": <str>, "agent": <str>, "required": true, "notes": <str>}
    - Deterministic: stable ordering, no random/derived timestamps.
    """
    tt = (task_type or "").lower()
    trace: List[Dict[str, Any]] = []

    def ev(event: str, agent: str, notes: str, required: bool = True) -> Dict[str, Any]:
        return {"event": event, "agent": agent, "required": bool(required), "notes": str(notes)}

    # Required core steps.
    trace.append(ev("classify", "orchestrator", f"task_type={tt}"))
    trace.append(ev("route", "orchestrator", f"primary_agent={primary_agent}"))
    trace.append(ev("handoff", "orchestrator", f"to_agent={primary_agent}"))
    trace.append(ev("process", primary_agent or "orchestrator", "execute primary work"))

    # Quality gates after processing (when applicable).
    for gate_agent in (quality_gates or []):
        trace.append(ev("quality_gate", gate_agent, "run required gate"))

    # Validation intent (when applicable).
    cmds = predict_validation_commands(tt, prompt)
    if cmds:
        trace.append(ev("validation", "qa-tester", "predict validation command intents"))

    trace.append(ev("final", "orchestrator", "complete workflow"))
    return trace


# ---- Layer B: contract validation ------------------------------------------------


REQUIRED_CONTRACT_HEADERS = [
    "Task",
    "InputsUsed",
    "Assumptions",
    "Constraints",
    "Actions",
    "Output",
    "Risks",
    "NextAction",
    "Handoff",
]

_HANDOFF_FIRST_LINE_RE = re.compile(r"^Act as ([a-z0-9-]+) per \.cursor/agents/specialists/([a-z0-9-]+)/SKILL\.md")


def _has_header(text: str, header: str) -> bool:
    # Deterministic: header must appear as its own line (exact match).
    target = "\n" + header + "\n"
    t = "\n" + (text or "") + "\n"
    return target in t


def _extract_handoff_block(text: str) -> str:
    # Simple slice from "Handoff" header to end.
    t = text or ""
    idx = t.find("\nHandoff\n")
    if idx == -1:
        idx = t.find("Handoff\n")
        if idx == -1:
            return ""
    return t[idx:].strip()


def validate_handoff_candidate(candidate_response: str) -> Dict[str, Any]:
    """
    Validate candidate_response against `.cursor/agents/shared/agent-contract.md` requirements.
    Returns a deterministic report suitable for scoring.
    """
    text = candidate_response or ""
    first_line = ""
    extracted_specialist_id = ""
    handoff_prompt_first_line_ok = False
    lines = text.splitlines()
    if lines:
        first_line = lines[0].strip()
        m = _HANDOFF_FIRST_LINE_RE.match(first_line)
        if m:
            a = m.group(1)
            b = m.group(2)
            extracted_specialist_id = a if a == b else ""
            handoff_prompt_first_line_ok = bool(extracted_specialist_id)

    present = [h for h in REQUIRED_CONTRACT_HEADERS if _has_header(text, h)]
    missing = [h for h in REQUIRED_CONTRACT_HEADERS if h not in present]

    handoff_block = _extract_handoff_block(text)
    handoff_has_to_agent = "to_agent" in handoff_block
    handoff_has_reason = "reason" in handoff_block
    handoff_has_payload = "payload" in handoff_block

    return {
        "required_headers": list(REQUIRED_CONTRACT_HEADERS),
        "present_headers": present,
        "missing_headers": missing,
        "handoff_prompt_first_line_ok": bool(handoff_prompt_first_line_ok),
        "extracted_specialist_id": extracted_specialist_id,
        "candidate_first_line": first_line,
        "handoff": {
            "present": _has_header(text, "Handoff"),
            "has_to_agent": bool(handoff_has_to_agent),
            "has_reason": bool(handoff_has_reason),
            "has_payload": bool(handoff_has_payload),
        },
        "matched_signals": {
            "headers_present": present,
            "handoff_block_present": bool(handoff_block),
            "handoff_keys_present": [
                k
                for k, ok in [
                    ("to_agent", handoff_has_to_agent),
                    ("reason", handoff_has_reason),
                    ("payload", handoff_has_payload),
                ]
                if ok
            ],
            "handoff_prompt_first_line_ok": bool(handoff_prompt_first_line_ok),
        },
    }
