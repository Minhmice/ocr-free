#!/usr/bin/env python3
"""
Validate a captured orchestrator response (markdown/text) against repo policy.

Use case:
- We can score/predict routing deterministically, but this harness checks a *real* orchestrator output
  (copied from chat) for policy compliance.

Validations (deterministic, heuristic but conservative):
- Contains an "Execution Plan" section.
- Contains at least one specialist handoff first-line in the required format:
    Act as [specialist] per .cursor/agents/specialists/[specialist]/SKILL.md
- For implementation/mixed tasks: mentions Phase 2 code-reviewer + qa-tester.
- Does not include direct implementation patches/diffs from the orchestrator (common signatures).

Constraints:
- stdlib-only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


_EXEC_PLAN_RE = re.compile(r"(?im)^\s*##\s*Execution Plan\s*$|^\s*Execution Plan\s*$")
_HANDOFF_FIRST_LINE_RE = re.compile(
    r"(?m)^Act as ([a-z0-9-]+) per \.cursor/agents/specialists/([a-z0-9-]+)/SKILL\.md\s*$"
)


def _looks_like_implementation_or_mixed(text: str) -> bool:
    t = (text or "").lower()
    # If the orchestrator is discussing or planning actual code changes, treat as implementation/mixed.
    # Keep this conservative: require at least one strong change verb and no explicit docs-only constraint.
    strong_change = any(w in t for w in [" implement ", " refactor ", " add ", " fix ", " wire ", " integrate ", " patch "])
    explicit_docs_only = any(w in t for w in ["docs only", "documentation only", "no code changes"])
    return bool(strong_change) and not explicit_docs_only


def _has_phase2_gate_mention(text: str) -> bool:
    t = (text or "").lower()
    # Require both gate agents; allow flexible wording but prefer explicit "phase 2".
    has_reviewers = ("code-reviewer" in t) and ("qa-tester" in t)
    has_phase2 = ("phase 2" in t) or ("review & qa" in t) or ("review and qa" in t) or ("post-implementation gate" in t)
    return has_reviewers and has_phase2


def _detect_direct_implementation_signatures(text: str) -> List[str]:
    """
    Catch obvious violations: orchestrator directly outputting a patch/diff/code-edit directive.
    We intentionally keep this heuristic tight to reduce false positives.
    """
    t = text or ""
    hits: List[str] = []
    signatures = [
        ("applypatch", re.compile(r"(?i)\bApplyPatch\b")),
        ("begin_patch_block", re.compile(r"(?m)^\*\*\* Begin Patch\s*$")),
        ("diff_fence", re.compile(r"(?i)```diff\b")),
        ("git_commit_cmd", re.compile(r"(?m)^\s*git\s+commit\b")),
        ("unified_diff_hunk", re.compile(r"(?m)^\@\@ .*\@\@")),
    ]
    for name, rx in signatures:
        if rx.search(t):
            hits.append(name)
    return hits


def validate_trace(text: str) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    if _EXEC_PLAN_RE.search(text or "") is None:
        errors.append("missing Execution Plan section")

    handoff_matches = list(_HANDOFF_FIRST_LINE_RE.finditer(text or ""))
    if not handoff_matches:
        errors.append("missing specialist handoff first line (Act as … per …/SKILL.md)")
    else:
        # Ensure specialist ids match in both capture groups.
        for m in handoff_matches:
            a = m.group(1)
            b = m.group(2)
            if a != b:
                errors.append(f"handoff first line mismatch specialist ids: {a!r} vs {b!r}")
                break

    if _looks_like_implementation_or_mixed(text or ""):
        if not _has_phase2_gate_mention(text or ""):
            errors.append("implementation/mixed task missing Phase 2 gate mention (code-reviewer + qa-tester)")

    impl_hits = _detect_direct_implementation_signatures(text or "")
    if impl_hits:
        errors.append(f"orchestrator appears to include direct implementation patch/diff signatures: {impl_hits}")

    return (len(errors) == 0), errors


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="validate_orchestrator_trace.py",
        description="Validate captured orchestrator output against policy.",
    )
    ap.add_argument("--input", required=True, help="Path to a markdown/text file containing orchestrator output.")
    ap.add_argument(
        "--fixtures-dir",
        default=str(Path(__file__).resolve().parents[1] / "fixtures" / "orchestrator-trace"),
        help="Optional: directory containing fixture traces (for --check-fixtures).",
    )
    ap.add_argument(
        "--check-fixtures",
        action="store_true",
        help="Run validator over all fixtures and enforce expected PASS/FAIL naming convention.",
    )
    args = ap.parse_args(argv)

    if args.check_fixtures:
        fixtures_dir = Path(args.fixtures_dir).resolve()
        if not fixtures_dir.exists():
            print(f"FAIL: fixtures dir not found: {fixtures_dir}", file=sys.stderr)
            return 2
        md_files = sorted(fixtures_dir.glob("*.md"))
        if not md_files:
            print(f"FAIL: no .md fixtures found under: {fixtures_dir}", file=sys.stderr)
            return 2

        any_fail = False
        for p in md_files:
            text = p.read_text(encoding="utf-8")
            ok, errs = validate_trace(text)
            expected_ok = ("pass_" in p.name) and ("fail_" not in p.name)
            status = "PASS" if ok else "FAIL"
            exp = "PASS" if expected_ok else "FAIL"
            print(f"{status}: {p.name} (expected {exp})")
            if ok != expected_ok:
                any_fail = True
                for e in errs:
                    print(f"  - {e}", file=sys.stderr)
        if any_fail:
            print("FAIL: fixture expectations not met", file=sys.stderr)
            return 1
        print("PASS: all fixtures matched expected outcomes")
        return 0

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"FAIL: input not found: {in_path}", file=sys.stderr)
        return 2

    text = in_path.read_text(encoding="utf-8")
    ok, errs = validate_trace(text)
    if ok:
        print("PASS: orchestrator trace validated")
        return 0
    print("FAIL: orchestrator trace policy violations", file=sys.stderr)
    for e in errs:
        print(f"- {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

