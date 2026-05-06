#!/usr/bin/env python3
"""
Phase 3B.1 deterministic benchmark scorer (stdlib-only).

Scores deterministic predictor outputs (not echoed expected).

Layers:
- A: compare task_type, primary_agent, secondary_agents, quality_gates, validation_commands
- B: score handoff_schema_completeness based on validate_handoff_candidate output
- C: score required trace event presence+order against expected.expected_trace
- D/E: scaffold-only (not performance-scored)

Applies rubric weights (100-pt) from AGENT_BENCHMARK_PLAN:
  - task classification: 15  -> task_type
  - primary agent: 20        -> primary_agent
  - secondary agents: 10     -> secondary_agents
  - quality gate discipline: 20 -> quality_gates
  - validation correctness: 15 -> validation_commands
  - handoff schema completeness: 10 -> layer B
  - minimal-agent selection: 5 -> not_scored in Phase 3B.1
  - failure recovery: 5 -> Layer D mutation validation (Phase 3B.2)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


RUBRIC_WEIGHTS = {
    "task_type": 15,
    "primary_agent": 20,
    "secondary_agents": 10,
    "quality_gates": 20,
    "validation_commands": 15,
    "handoff_schema_completeness": 10,
    "minimal_agent_selection": 5,
    "failure_recovery": 5,
}

SCORABLE_FIELDS = ["task_type", "primary_agent", "secondary_agents", "quality_gates", "validation_commands"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def load_expected_map(path: Path) -> Dict[str, Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("expected_results.json must be an object mapping case_id -> expected")
    out: Dict[str, Dict[str, Any]] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            continue
        out[k] = v
    return out


def _norm_list(x: Any) -> Optional[List[str]]:
    if x is None:
        return None
    if not isinstance(x, list) or not all(isinstance(i, str) for i in x):
        return None
    return x


def compare_field(field: str, expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, str]:
    if field not in expected:
        return True, "not_applicable (missing in expected)"

    ev = expected.get(field)
    av = actual.get(field)

    if field in ["secondary_agents", "quality_gates", "validation_commands"]:
        el = _norm_list(ev)
        al = _norm_list(av)
        if el is None:
            return False, "invalid expected type (need list[str])"
        if al is None:
            return False, "invalid actual type (need list[str])"
        # Order-insensitive compare: routing/scaffold does not guarantee stable ordering
        # across equivalent selections (especially secondary_agents).
        if sorted(el) == sorted(al):
            return True, "match (order-insensitive)"
        return False, f"mismatch (expected={el}, actual={al})"

    if not isinstance(ev, str):
        return False, "invalid expected type (need str)"
    if not isinstance(av, str):
        return False, "invalid actual type (need str)"
    if ev == av:
        return True, "exact_match"
    return False, f"mismatch (expected={ev!r}, actual={av!r})"


def _handoff_completeness_score(report: Any) -> Tuple[int, Dict[str, Any]]:
    """
    Score Layer B handoff completeness using predictor.validate_handoff_candidate output.
    Returns (earned_points, breakdown).

    Policy (deterministic):
    - 1 point per required header present, scaled to RUBRIC_WEIGHTS["handoff_schema_completeness"]
    - plus 1 bonus point if handoff has to_agent+reason+payload
    - capped to max weight
    """
    weight = RUBRIC_WEIGHTS["handoff_schema_completeness"]
    if not isinstance(report, dict):
        return 0, {"detail": "invalid report type (need object)"}

    required = report.get("required_headers")
    present = report.get("present_headers")
    handoff = report.get("handoff", {})
    if not isinstance(required, list) or not isinstance(present, list):
        return 0, {"detail": "missing required_headers/present_headers"}

    req_count = max(1, len([h for h in required if isinstance(h, str)]))
    present_count = len([h for h in present if isinstance(h, str)])

    base = int(round((present_count / req_count) * weight))

    bonus = 0
    first_line_ok = report.get("handoff_prompt_first_line_ok") is True
    if (
        isinstance(handoff, dict)
        and handoff.get("has_to_agent")
        and handoff.get("has_reason")
        and handoff.get("has_payload")
        and first_line_ok
    ):
        bonus = 1

    earned = min(weight, base + bonus)
    return earned, {
        "required_headers_count": req_count,
        "present_headers_count": present_count,
        "base_points": base,
        "bonus": bonus,
        "handoff_prompt_first_line_ok": bool(first_line_ok),
        "earned": earned,
        "max": weight,
    }


def _trace_order_check(expected_trace: Any, actual_trace: Any) -> Tuple[bool, str]:
    """
    Layer C check: required events must appear in order (extras allowed; subsequence ok).

    expected_trace: list[object] where each object is:
      {"event": <str>, "agent": <str>, "required": true, "notes": <str>}
    actual_trace: list[object] with at least {"event": <str>}
    """
    if not isinstance(expected_trace, list) or not all(isinstance(x, dict) for x in expected_trace):
        return False, "invalid expected.expected_trace (need list[object])"
    if not isinstance(actual_trace, list) or not all(isinstance(x, dict) for x in actual_trace):
        return False, "invalid actual predicted_trace (need list[object])"

    required_events: List[str] = []
    for e in expected_trace:
        ev = e.get("event")
        required = e.get("required")
        if required is False:
            continue
        if isinstance(ev, str) and ev:
            required_events.append(ev)

    actual_events = []
    for a in actual_trace:
        ev = a.get("event")
        if isinstance(ev, str) and ev:
            actual_events.append(ev)

    # subsequence check
    idx = 0
    for req in required_events:
        try:
            idx = actual_events.index(req, idx) + 1
        except ValueError:
            if req not in actual_events:
                return False, f"missing required event {req!r} (required={required_events}, actual={actual_events})"
            return False, f"out_of_order required event {req!r} (required={required_events}, actual={actual_events})"

    return True, "required events present in order"


def _layer_d_failure_recovery_score(expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Layer D scoring (deterministic, stdlib-only).

    Policy:
    - Uses RUBRIC_WEIGHTS["failure_recovery"] (5 points total).
    - Checks:
      - expected.expected_exit_code (optional) matches actual.exit_code
      - expected.expected_error_substrings (optional) -> any substring present in stdout or stderr
      - If expected.validation_commands is non-empty, require actual.validation_command_executed == True

    Note: We intentionally keep Layer D inside the failure_recovery bucket to avoid mixing
    mutation/validator correctness into Layer A validation_commands routing field (15 points).
    """
    weight = RUBRIC_WEIGHTS["failure_recovery"]

    expected_exit_code = expected.get("expected_exit_code")
    expected_substrings = expected.get("expected_error_substrings")
    validation_commands = expected.get("validation_commands")

    if not isinstance(validation_commands, list) or not all(isinstance(x, str) for x in validation_commands):
        validation_commands = []

    actual_exit_code = actual.get("exit_code")
    stdout = actual.get("stdout", "")
    stderr = actual.get("stderr", "")
    executed_flag = actual.get("validation_command_executed")

    checks: Dict[str, Any] = {"max": weight, "earned": 0, "checks": {}}

    # Determine applicability: if no expectations are provided and there are no validation commands,
    # we treat this as non-applicable and score 0/0.
    applicable = bool(validation_commands) or (expected_exit_code is not None) or (expected_substrings is not None)
    if not applicable:
        return 0, {"detail": "not_applicable (no Layer D expectations provided)"}

    ok = True

    if expected_exit_code is not None:
        if not isinstance(expected_exit_code, int):
            ok = False
            checks["checks"]["exit_code"] = {"ok": False, "detail": "invalid expected_exit_code type (need int)"}
        elif not isinstance(actual_exit_code, int):
            ok = False
            checks["checks"]["exit_code"] = {"ok": False, "detail": "invalid actual.exit_code type (need int)"}
        elif expected_exit_code != actual_exit_code:
            ok = False
            checks["checks"]["exit_code"] = {
                "ok": False,
                "detail": f"mismatch (expected={expected_exit_code}, actual={actual_exit_code})",
            }
        else:
            checks["checks"]["exit_code"] = {"ok": True, "detail": "exact_match"}
    else:
        checks["checks"]["exit_code"] = {"ok": True, "detail": "not_applicable (missing expected_exit_code)"}

    if expected_substrings is not None:
        if not isinstance(expected_substrings, list) or not all(isinstance(s, str) for s in expected_substrings):
            ok = False
            checks["checks"]["expected_error_substrings"] = {"ok": False, "detail": "invalid expected_error_substrings type (need list[str])"}
        else:
            haystack = f"{stdout}\n{stderr}"
            found = next((s for s in expected_substrings if s and s in haystack), None)
            if found is None:
                ok = False
                checks["checks"]["expected_error_substrings"] = {
                    "ok": False,
                    "detail": "no expected substring found in stdout/stderr",
                    "expected_any_of": expected_substrings,
                }
            else:
                checks["checks"]["expected_error_substrings"] = {"ok": True, "detail": f"found: {found!r}"}
    else:
        checks["checks"]["expected_error_substrings"] = {"ok": True, "detail": "not_applicable (missing expected_error_substrings)"}

    if validation_commands:
        if executed_flag is True:
            checks["checks"]["validation_command_executed"] = {"ok": True, "detail": "true"}
        else:
            ok = False
            checks["checks"]["validation_command_executed"] = {"ok": False, "detail": "required true when validation_commands non-empty"}
    else:
        checks["checks"]["validation_command_executed"] = {"ok": True, "detail": "not_applicable (no validation_commands)"}

    checks["earned"] = weight if ok else 0
    return checks["earned"], checks


def _safe_int(x: Any) -> Optional[int]:
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    return None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_layer_d_artifacts(actual_path: Path, layer_d_case_ids: List[str]) -> Tuple[bool, List[str]]:
    """
    Enforce presence of Layer D runner artifacts under:
      <run_dir>/cases/<case_id>/{mutation_plan.json,stdout.txt,stderr.txt,trace.jsonl}
    """
    run_dir = actual_path.parent
    required = ["mutation_plan.json", "stdout.txt", "stderr.txt", "trace.jsonl"]
    missing: List[str] = []
    for cid in layer_d_case_ids:
        case_dir = run_dir / "cases" / cid
        for fname in required:
            p = case_dir / fname
            if not p.exists():
                missing.append(f"{cid}: missing {p}")
    return (len(missing) == 0), missing


def _print_golden_compare(
    *,
    golden_path: Path,
    golden: Dict[str, Any],
    actual_summary: Dict[str, Any],
    failures_count: int,
    gate_failures: List[str],
) -> None:
    g_cases_total = _safe_int(golden.get("cases_total"))
    g_score_total = _safe_int(golden.get("score_total"))
    g_failures = _safe_int(golden.get("failures"))

    a_cases_total = _safe_int(actual_summary.get("cases_total"))
    a_score_total = _safe_int(actual_summary.get("score_total"))
    a_failures = failures_count

    print("\n=== Golden comparison ===")
    print(f"Golden: {golden_path}")
    print(f"- cases_total: golden={g_cases_total} actual={a_cases_total}")
    print(f"- score_total: golden={g_score_total} actual={a_score_total}")
    print(f"- failures:    golden={g_failures} actual={a_failures}")
    if gate_failures:
        print("Result: FAIL")
        for r in gate_failures:
            print(f"- {r}")
    else:
        print("Result: PASS")


def main(argv: List[str]) -> int:
    benchmarks_root = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(
        prog="score_benchmark.py",
        description="Score actual benchmark results against expected (Phase 3A).",
    )
    parser.add_argument(
        "--actual",
        required=True,
        help="Path to actual_results.jsonl",
    )
    parser.add_argument(
        "--expected",
        default=str(benchmarks_root / "expected" / "expected_results.json"),
        help="Path to expected_results.json (default: benchmarks/expected/expected_results.json)",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional path to write summary JSON (default: write next to --actual as summary_scored.json)",
    )
    parser.add_argument(
        "--golden",
        default="",
        help="Optional path to golden summary JSON. If provided, enforce regression gates and Layer D artifacts.",
    )
    parser.add_argument(
        "--strict-case-count",
        action="store_true",
        help="When used with --golden, require actual cases_total == golden cases_total (default: actual must be >= golden).",
    )

    args = parser.parse_args(argv)

    actual_path = Path(args.actual).resolve()
    expected_path = Path(args.expected).resolve()
    golden_path = Path(args.golden).resolve() if args.golden else None

    if not actual_path.exists():
        print(f"ERROR: --actual not found: {actual_path}", file=sys.stderr)
        return 2
    if not expected_path.exists():
        print(f"ERROR: --expected not found: {expected_path}", file=sys.stderr)
        return 2
    if golden_path is not None and not golden_path.exists():
        print(f"ERROR: --golden not found: {golden_path}", file=sys.stderr)
        return 2

    expected_map = load_expected_map(expected_path)

    per_layer: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"cases": 0, "score_raw": 0, "score_100": 0})
    failures: List[Dict[str, Any]] = []
    layer_d_case_ids: List[str] = []

    score_raw_total = 0
    score_100_total = 0
    cases_total = 0
    printed_invalid_warning = False
    benchmark_valid = True
    any_perf_scored = False

    for line_no, row in _iter_jsonl(actual_path):
        cases_total += 1
        case_id = row.get("case_id")
        layer = row.get("layer") or "?"
        actual = row.get("actual", {})
        expected_inline = row.get("expected")

        layer_s = str(layer)
        if layer_s == "D" and isinstance(case_id, str) and case_id:
            layer_d_case_ids.append(case_id)

        # Track whether we have any performance-scored layers (A/B/C/E).
        if layer_s in {"A", "B", "C", "E"}:
            any_perf_scored = True

        # Do NOT let scaffold-only rows invalidate run-level performance by themselves.
        if layer_s in {"A", "B", "C", "E"} and isinstance(actual, dict) and actual.get("benchmark_valid") is False:
            benchmark_valid = False
            if not printed_invalid_warning:
                print("WARNING: benchmark_valid=false detected for A/B/C/E; results are scaffold/dry-run, not performance")
                printed_invalid_warning = True
        if isinstance(actual, dict) and actual.get("mode") == "dry_run":
            benchmark_valid = False
            if not printed_invalid_warning:
                print("WARNING: dry-run results are scaffold validation only, not benchmark performance")
                printed_invalid_warning = True

        if not isinstance(case_id, str) or not case_id:
            failures.append(
                {
                    "case_id": f"<missing:{line_no}>",
                    "expected": {},
                    "actual": row,
                    "reason": "missing case_id in actual row",
                }
            )
            continue

        # Prefer inline expected captured in actual_results.jsonl (source of truth for the run),
        # then fall back to expected_results.json map for legacy compatibility.
        expected = expected_inline if isinstance(expected_inline, dict) else expected_map.get(case_id)
        if expected is None:
            failures.append(
                {
                    "case_id": case_id,
                    "expected": {},
                    "actual": actual,
                    "reason": f"no expected found for case_id {case_id!r}",
                }
            )
            continue

        if not isinstance(actual, dict):
            failures.append(
                {
                    "case_id": case_id,
                    "expected": expected,
                    "actual": actual,
                    "reason": "actual field is not an object",
                }
            )
            continue

        applicable_weight = 0
        earned = 0
        field_breakdown: Dict[str, Any] = {}

        # Layer-specific scoring
        if layer_s in {"A", "E"}:
            for f in SCORABLE_FIELDS:
                ok, detail = compare_field(f, expected, actual)
                w = RUBRIC_WEIGHTS[f]
                if "not_applicable" in detail:
                    field_breakdown[f] = {"weight": w, "applicable": False, "earned": 0, "detail": detail}
                    continue

                applicable_weight += w
                if ok:
                    earned += w
                field_breakdown[f] = {"weight": w, "applicable": True, "earned": (w if ok else 0), "detail": detail}

            # Other categories not scored for Layer A
            field_breakdown["handoff_schema_completeness"] = {
                "weight": RUBRIC_WEIGHTS["handoff_schema_completeness"],
                "applicable": False,
                "earned": 0,
                "detail": "not_applicable (Layer A)",
            }
            field_breakdown["minimal_agent_selection"] = {
                "weight": RUBRIC_WEIGHTS["minimal_agent_selection"],
                "applicable": False,
                "earned": 0,
                "detail": "not_scored (Phase 3B.1)",
            }
            field_breakdown["failure_recovery"] = {
                "weight": RUBRIC_WEIGHTS["failure_recovery"],
                "applicable": False,
                "earned": 0,
                "detail": ("not_applicable (Layer A)" if layer_s == "A" else "not_applicable (Layer E scaffold)"),
            }

        elif layer_s == "B":
            hv = actual.get("handoff_validation") if isinstance(actual, dict) else None
            score_b, breakdown_b = _handoff_completeness_score(hv)

            applicable_weight += RUBRIC_WEIGHTS["handoff_schema_completeness"]
            earned += score_b
            field_breakdown["handoff_schema_completeness"] = {
                "weight": RUBRIC_WEIGHTS["handoff_schema_completeness"],
                "applicable": True,
                "earned": score_b,
                "detail": breakdown_b,
            }

            # Not scored in Layer B for now (still recorded for transparency)
            for f in SCORABLE_FIELDS:
                field_breakdown[f] = {
                    "weight": RUBRIC_WEIGHTS[f],
                    "applicable": False,
                    "earned": 0,
                    "detail": "not_applicable (Layer B)",
                }
            field_breakdown["minimal_agent_selection"] = {
                "weight": RUBRIC_WEIGHTS["minimal_agent_selection"],
                "applicable": False,
                "earned": 0,
                "detail": "not_scored (Phase 3B.1)",
            }
            field_breakdown["failure_recovery"] = {
                "weight": RUBRIC_WEIGHTS["failure_recovery"],
                "applicable": False,
                "earned": 0,
                "detail": "not_applicable (Layer B)",
            }

        elif layer_s == "C":
            # Layer C traces are case-specific and may live inline in the case row even if the
            # global expected_results.json lacks expected_trace for the case_id.
            expected_trace = expected.get("expected_trace")
            if expected_trace is None and isinstance(expected_inline, dict):
                expected_trace = expected_inline.get("expected_trace")
            predicted_trace = actual.get("predicted_trace") if isinstance(actual, dict) else None
            ok, detail = _trace_order_check(expected_trace, predicted_trace)

            # Represent trace correctness inside failure_recovery weight bucket? No: treat as failure_recovery not relevant.
            # For Phase 3B.1 we score trace correctness using the same 15/20/.. routing weights would be misleading.
            # Instead we score it as a binary gate reported in breakdown and mapped to 0/100 per-case.
            applicable_weight = 1
            earned = 1 if ok else 0
            field_breakdown["workflow_trace"] = {
                "weight": "binary",
                "applicable": True,
                "earned": earned,
                "detail": detail,
            }

        elif layer_s == "D":
            # Layer D: deterministic failure mutation validation scoring (Phase 3B.2).
            score_d, breakdown_d = _layer_d_failure_recovery_score(expected, actual)
            applicable_weight += RUBRIC_WEIGHTS["failure_recovery"]
            earned += score_d
            field_breakdown["failure_recovery"] = {
                "weight": RUBRIC_WEIGHTS["failure_recovery"],
                "applicable": True,
                "earned": score_d,
                "detail": breakdown_d,
            }
            # Explicitly mark Layer A fields as non-applicable for D.
            for f in SCORABLE_FIELDS:
                field_breakdown[f] = {
                    "weight": RUBRIC_WEIGHTS[f],
                    "applicable": False,
                    "earned": 0,
                    "detail": "not_applicable (Layer D)",
                }
            field_breakdown["handoff_schema_completeness"] = {
                "weight": RUBRIC_WEIGHTS["handoff_schema_completeness"],
                "applicable": False,
                "earned": 0,
                "detail": "not_applicable (Layer D)",
            }
            field_breakdown["minimal_agent_selection"] = {
                "weight": RUBRIC_WEIGHTS["minimal_agent_selection"],
                "applicable": False,
                "earned": 0,
                "detail": "not_scored (Phase 3B.2)",
            }
        else:
            # Unknown layer: not performance-scored.
            field_breakdown["not_scored"] = {
                "weight": 0,
                "applicable": False,
                "earned": 0,
                "detail": f"Unknown or unscored layer: {layer}",
            }
            applicable_weight = 0
            earned = 0

        score_raw_total += earned
        score_raw_case = earned
        score_100_case = int(round((earned / applicable_weight) * 100)) if applicable_weight > 0 else 0
        score_100_total += score_100_case

        per_layer[str(layer)]["cases"] += 1
        per_layer[str(layer)]["score_raw"] += score_raw_case
        per_layer[str(layer)]["score_100"] += score_100_case

        if earned != applicable_weight:
            failures.append(
                {
                    "case_id": case_id,
                    "expected": expected,
                    "actual": actual,
                    "reason": "one or more scoring checks failed",
                    "breakdown": field_breakdown,
                    "score": {"earned": earned, "applicable_total": applicable_weight, "score_100": score_100_case},
                }
            )

    avg_score_100 = int(round(score_100_total / cases_total)) if cases_total else 0

    if not any_perf_scored:
        benchmark_valid = False
        if not printed_invalid_warning:
            print("WARNING: no performance-scored layers (A/B/C) present; scaffold-only run")
            printed_invalid_warning = True

    summary = {
        "run_id": actual_path.parent.name,
        "timestamp": _now_iso(),
        "cases_total": cases_total,
        "score_total": (avg_score_100 if benchmark_valid else 0),
        "by_layer": dict(per_layer),
        "failures": failures,
        "benchmark_valid": benchmark_valid,
        "recommendations": [
            "Scorer scores Layer A routing fields, Layer B handoff structure, Layer C trace ordering, and Layer E like Layer A (ignoring ablation_axis).",
            "Layer D is scored deterministically inside failure_recovery (5 points) using validator exit_code and optional error substrings.",
        ],
        "scoring": {
            "weights": RUBRIC_WEIGHTS,
            "scorable_fields": SCORABLE_FIELDS,
            "note": "If benchmark_valid=false, score_total is forced to 0 and MUST NOT be presented as performance.",
        },
    }

    out_path = Path(args.out).resolve() if args.out else (actual_path.parent / "summary_scored.json")
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Cases: {cases_total}")
    print(f"Avg score (0-100 over applicable fields): {avg_score_100}")
    print(f"Failures: {len(failures)}")
    print(f"Wrote: {out_path}")

    # Golden regression gates (Phase 3C).
    if golden_path is not None:
        gate_failures: List[str] = []
        golden_any = _load_json(golden_path)
        if not isinstance(golden_any, dict):
            print(f"ERROR: golden file must be a JSON object: {golden_path}", file=sys.stderr)
            return 2
        golden: Dict[str, Any] = golden_any

        g_cases_total = _safe_int(golden.get("cases_total"))
        a_cases_total = _safe_int(summary.get("cases_total"))
        g_score_total = _safe_int(golden.get("score_total"))
        g_failures = _safe_int(golden.get("failures"))
        a_score_total = _safe_int(summary.get("score_total"))
        a_failures = len(failures)

        if g_cases_total is None or a_cases_total is None:
            gate_failures.append("golden gate: invalid/missing cases_total in golden or actual summary")
        else:
            if args.strict_case_count:
                if a_cases_total != g_cases_total:
                    gate_failures.append(
                        f"golden gate: cases_total mismatch (strict) (golden={g_cases_total}, actual={a_cases_total})"
                    )
            else:
                if a_cases_total < g_cases_total:
                    gate_failures.append(
                        f"golden gate: cases_total decreased (golden={g_cases_total}, actual={a_cases_total})"
                    )

        if g_score_total is None or a_score_total is None:
            gate_failures.append("golden gate: invalid/missing score_total in golden or actual summary")
        else:
            drop = g_score_total - a_score_total
            if drop > 5:
                gate_failures.append(f"golden gate: score_total dropped by {drop} (> 5) (golden={g_score_total}, actual={a_score_total})")

        if g_failures is None:
            gate_failures.append("golden gate: invalid/missing failures count in golden summary")
        else:
            if a_failures > g_failures:
                gate_failures.append(f"golden gate: failures increased (golden={g_failures}, actual={a_failures})")

        mutation_artifacts_required = golden.get("mutation_artifacts_required")
        if mutation_artifacts_required is True:
            ok, missing = _verify_layer_d_artifacts(actual_path=actual_path, layer_d_case_ids=layer_d_case_ids)
            if not ok:
                gate_failures.append("golden gate: Layer D artifacts missing")
                for m in missing:
                    gate_failures.append(f"artifact: {m}")

        _print_golden_compare(
            golden_path=golden_path,
            golden=golden,
            actual_summary=summary,
            failures_count=len(failures),
            gate_failures=gate_failures,
        )

        if gate_failures:
            return 1

    return 0 if len(failures) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

