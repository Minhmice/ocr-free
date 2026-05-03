#!/usr/bin/env python3
"""
Parity check: ensure predictor routing keywords match rules.yaml.

Policy:
- Compare `.cursor/agents/benchmarks/scripts/predictor.py` SIGNAL_KEYWORDS
  against `.cursor/agents/routing/rules.yaml` signals.*.keywords
- Fail (exit non-zero) if any agent has missing/extra keywords.

Constraints:
- stdlib-only
- YAML-lite parsing tailored to the repo's rules.yaml structure
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


_QUOTED_RE = re.compile(r'"([^"]*)"')
_ALWAYS_APPLY_RE = re.compile(r"(?m)^alwaysApply:\s*true\s*$")


def _validate_always_orchestrator_rule(path: Path) -> Tuple[bool, str]:
    """
    Smoke-check `.cursor/rules/always-orchestrator-skill.mdc`.
    Requirements:
    - frontmatter contains `alwaysApply: true`
    - body references `.cursor/agents/orchestrator/SKILL.md`
    """
    if not path.exists():
        return False, f"missing rule file: {path}"
    text = path.read_text(encoding="utf-8")

    # frontmatter: must contain alwaysApply: true somewhere between the first two --- lines
    if not text.lstrip().startswith("---"):
        return False, "missing frontmatter start '---'"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False, "missing frontmatter closing '---'"
    frontmatter = parts[1]
    body = parts[2]

    if _ALWAYS_APPLY_RE.search(frontmatter) is None:
        return False, "frontmatter missing `alwaysApply: true`"
    if ".cursor/agents/orchestrator/SKILL.md" not in body:
        return False, "body missing reference to `.cursor/agents/orchestrator/SKILL.md`"
    return True, "ok"


def _extract_signals_keywords_from_rules_yaml(text: str) -> Dict[str, List[str]]:
    """
    YAML-lite extractor for:
      signals:
        <agent_id>:
          keywords: ["a", "b"]
        <agent_id>:
          keywords:
            ["a", "b", ...]
    including bracketed lists that span multiple lines.
    """
    lines = text.splitlines()

    # Find 'signals:' line.
    start = None
    for i, raw in enumerate(lines):
        if raw.rstrip() == "signals:":
            start = i + 1
            break
    if start is None:
        raise ValueError("rules.yaml: missing top-level 'signals:'")

    out: Dict[str, List[str]] = {}
    i = start

    def indent_of(s: str) -> int:
        return len(s) - len(s.lstrip(" "))

    # signals block ends when indent returns to 0 (new top-level key)
    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue
        if indent_of(raw) == 0:
            break

        # agent id line: two-space indent, ends with colon
        if indent_of(raw) == 2 and raw.strip().endswith(":"):
            agent_id = raw.strip()[:-1].strip()
            i += 1

            # scan this agent block until next agent or end
            keywords_buf = ""
            while i < len(lines):
                r2 = lines[i]
                if not r2.strip():
                    i += 1
                    continue
                if indent_of(r2) <= 2:
                    break

                s2 = r2.strip()
                if s2.startswith("keywords:"):
                    # inline list or start of multi-line list
                    after = s2[len("keywords:") :].strip()
                    if after:
                        keywords_buf = after
                        i += 1
                    else:
                        i += 1
                        # collect subsequent indented lines until we close the bracket list
                        chunk_lines = []
                        while i < len(lines):
                            r3 = lines[i]
                            if not r3.strip():
                                i += 1
                                continue
                            if indent_of(r3) <= 4 and chunk_lines:
                                break
                            chunk_lines.append(r3.strip())
                            if "]" in r3:
                                i += 1
                                break
                            i += 1
                        keywords_buf = " ".join(chunk_lines).strip()
                    break

                i += 1

            if not keywords_buf:
                raise ValueError(f"rules.yaml: missing keywords for signal {agent_id!r}")

            # Extract quoted string items.
            items = [m.group(1) for m in _QUOTED_RE.finditer(keywords_buf)]
            if not items:
                raise ValueError(f"rules.yaml: failed to parse quoted keywords for {agent_id!r}: {keywords_buf!r}")
            out[agent_id] = items
            continue

        i += 1

    return out


def _diff_sets(a: List[str], b: List[str]) -> Tuple[List[str], List[str]]:
    a_set = set(a)
    b_set = set(b)
    missing = sorted(b_set - a_set)  # in predictor? no, missing from predictor relative to rules
    extra = sorted(a_set - b_set)
    return missing, extra


def _run_self_tests() -> Tuple[bool, List[str]]:
    failures: List[str] = []

    # Fixture 1: inline keyword list.
    fx1 = """
signals:
  backend-developer:
    keywords: ["api", "route", "auth"]
"""
    got1 = _extract_signals_keywords_from_rules_yaml(fx1)
    if got1.get("backend-developer") != ["api", "route", "auth"]:
        failures.append(f"fixture1 mismatch: {got1!r}")

    # Fixture 2: multiline bracket keyword list.
    fx2 = """
signals:
  planner:
    keywords:
      [
        "plan",
        "roadmap",
        "sequence"
      ]
"""
    got2 = _extract_signals_keywords_from_rules_yaml(fx2)
    if got2.get("planner") != ["plan", "roadmap", "sequence"]:
        failures.append(f"fixture2 mismatch: {got2!r}")

    # Fixture 3: comments + reordered agents.
    fx3 = """
signals:
  frontend-developer:
    # comment before keywords
    keywords: ["ui", "component"]
  backend-developer:
    keywords:
      [
        "api", # inline comment
        "endpoint"
      ]
"""
    got3 = _extract_signals_keywords_from_rules_yaml(fx3)
    if got3.get("frontend-developer") != ["ui", "component"]:
        failures.append(f"fixture3 frontend mismatch: {got3!r}")
    if got3.get("backend-developer") != ["api", "endpoint"]:
        failures.append(f"fixture3 backend mismatch: {got3!r}")

    return (len(failures) == 0), failures


def main(argv: List[str]) -> int:
    repo_root = Path(__file__).resolve().parents[4]

    parser = argparse.ArgumentParser(prog="check_routing_parity.py", description="Check predictor routing parity with rules.yaml.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic stdlib-only self-tests for YAML-lite keyword extraction.",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        ok, failures = _run_self_tests()
        if not ok:
            print("FAIL: routing parity self-tests failed", file=sys.stderr)
            for f in failures:
                print(f"- {f}", file=sys.stderr)
            return 1
        print("PASS: routing parity self-tests")
        return 0

    # Always-orchestrator rule smoke check (must run on normal parity runs).
    always_rule_path = repo_root / ".cursor" / "rules" / "always-orchestrator-skill.mdc"
    ok_rule, detail = _validate_always_orchestrator_rule(always_rule_path)
    if not ok_rule:
        print("FAIL: always-orchestrator rule smoke check failed", file=sys.stderr)
        print(f"- file: {always_rule_path}", file=sys.stderr)
        print(f"- detail: {detail}", file=sys.stderr)
        return 1

    rules_path = repo_root / ".cursor" / "agents" / "routing" / "rules.yaml"
    if not rules_path.exists():
        print(f"ERROR: rules.yaml not found: {rules_path}", file=sys.stderr)
        return 2

    # Import predictor in-process to read its SIGNAL_KEYWORDS.
    # (stdlib-only: no exec-eval parsing; importing is deterministic here.)
    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    try:
        import predictor  # type: ignore
    except Exception as e:
        print(f"ERROR: failed to import predictor.py: {e}", file=sys.stderr)
        return 2

    predictor_map = getattr(predictor, "SIGNAL_KEYWORDS", None)
    if not isinstance(predictor_map, dict):
        print("ERROR: predictor.SIGNAL_KEYWORDS missing or invalid", file=sys.stderr)
        return 2

    rules_text = rules_path.read_text(encoding="utf-8")
    rules_map = _extract_signals_keywords_from_rules_yaml(rules_text)

    failures: List[str] = []

    # Compare only agents present in rules.yaml signals.
    for agent_id, rules_keywords in sorted(rules_map.items()):
        pred_keywords = predictor_map.get(agent_id)
        if not isinstance(pred_keywords, list) or not all(isinstance(x, str) for x in pred_keywords):
            failures.append(f"{agent_id}: predictor missing/invalid keyword list")
            continue
        missing, extra = _diff_sets(pred_keywords, rules_keywords)
        if missing or extra:
            msg = [f"{agent_id}: keyword drift detected"]
            if missing:
                msg.append(f"  missing_in_predictor: {missing}")
            if extra:
                msg.append(f"  extra_in_predictor:   {extra}")
            failures.append("\n".join(msg))

    # Also catch predictor keys that don't exist in rules.yaml signals.
    extra_agents = sorted(set(predictor_map.keys()) - set(rules_map.keys()))
    if extra_agents:
        failures.append(f"predictor contains unknown signal agents: {extra_agents}")

    if failures:
        print("FAIL: predictor SIGNAL_KEYWORDS drifted from rules.yaml signals.keywords", file=sys.stderr)
        for f in failures:
            print(f"- {f}", file=sys.stderr)
        return 1

    print("PASS: predictor SIGNAL_KEYWORDS matches rules.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

