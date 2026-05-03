#!/usr/bin/env python3
"""
Benchmark runner (Phase 3B.1).

Key behaviors:
- Loads all cases from cases/*.jsonl
- Supports --dry-run:
  - keeps Phase 3A behavior (echo expected; benchmark_valid=false)
- Default real mode:
  - Layer A: deterministic routing prediction
  - Layer B: deterministic handoff contract validation against candidate_response
  - Layer C: deterministic workflow trace prediction
  - Layer D: schema-only actual (mutation_supported=false; no mutation execution)
  - Layer E: schema-only actual (ablation_supported=false; no ablation execution)
- ALWAYS writes an output folder containing:
  - run_config.json
  - trace_config_usage.json
  - actual_results.jsonl
  - summary.json
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import shlex
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


RUNNER_VERSION = "phase3b2-layerd-mutation-layerE-scaffold-1"


try:
    from . import predictor
except Exception:  # pragma: no cover
    # Support running as a script (python path/to/run_benchmark.py)
    import predictor  # type: ignore


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _iter_case_files(cases_dir: Path) -> List[Path]:
    return sorted(cases_dir.glob("*.jsonl"))


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


def load_cases(cases_dir: Path) -> List[Dict[str, Any]]:
    # Back-compat wrapper: canonical implementation lives in predictor.py per Phase 3B.1.
    return predictor.load_cases(cases_dir)


def ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True))
            f.write("\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def _append_trace(out_path: Path, event: Dict[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, sort_keys=True))
        f.write("\n")


def _safe_repo_relative_path(rel_path: str) -> Path:
    """
    Accept only ".cursor/**" relative paths for temp mutations.
    """
    if not isinstance(rel_path, str) or not rel_path.startswith(".cursor/"):
        raise ValueError(f"unsafe mutation path (expected '.cursor/...'): {rel_path!r}")
    return Path(rel_path)


def _copy_cursor_trees_to_temp(repo_root: Path, temp_root: Path, trace_path: Path) -> None:
    src_agents = repo_root / ".cursor" / "agents"
    src_rules = repo_root / ".cursor" / "rules"
    dst_agents = temp_root / ".cursor" / "agents"
    dst_rules = temp_root / ".cursor" / "rules"

    _append_trace(trace_path, {"step": "copy", "what": ".cursor/agents", "src": os.fspath(src_agents), "dst": os.fspath(dst_agents)})
    shutil.copytree(src_agents, dst_agents, dirs_exist_ok=True)

    _append_trace(trace_path, {"step": "copy", "what": ".cursor/rules", "src": os.fspath(src_rules), "dst": os.fspath(dst_rules)})
    shutil.copytree(src_rules, dst_rules, dirs_exist_ok=True)


def _mutate_temp_tree(temp_root: Path, mutation: Dict[str, Any], trace_path: Path) -> Dict[str, Any]:
    """
    Apply a deterministic mutation to temp_root only.
    Returns a mutation_plan dict suitable for artifact logging.
    """
    mtype = mutation.get("type")
    plan: Dict[str, Any] = {"type": mtype, "applied": False, "details": {}}

    # Back-compat / legacy mutation aliases (Phase 3B.1 prototypes).
    if mtype == "delete_file_in_temp_copy":
        rel = _safe_repo_relative_path(str(mutation.get("path") or ".cursor/agents/mappings/skill-finder.csv"))
        target = temp_root / rel
        _append_trace(trace_path, {"step": "mutate", "mutation_type": mtype, "op": "delete", "path": os.fspath(rel)})
        if target.exists():
            target.unlink()
        plan["applied"] = True
        plan["details"] = {"deleted": os.fspath(rel)}
        return plan

    if mtype == "corrupt_yaml_in_temp_copy":
        rel = _safe_repo_relative_path(str(mutation.get("path") or ".cursor/agents/routing/rules.yaml"))
        target = temp_root / rel
        _append_trace(trace_path, {"step": "mutate", "mutation_type": mtype, "op": "overwrite", "path": os.fspath(rel)})
        _write_text(target, ":\n  - [\n")  # deterministically invalid YAML
        plan["applied"] = True
        plan["details"] = {"overwrote": os.fspath(rel), "note": "invalid YAML injected"}
        return plan

    if mtype == "corrupt_mapping_in_temp_copy":
        rel = _safe_repo_relative_path(str(mutation.get("path") or ".cursor/agents/mappings/rule-map.csv"))
        target = temp_root / rel
        _append_trace(trace_path, {"step": "mutate", "mutation_type": mtype, "op": "append_invalid_row", "path": os.fspath(rel)})
        existing = target.read_text(encoding="utf-8")
        if not existing.strip():
            raise ValueError("mapping file is empty in temp copy")
        _write_text(target, existing.rstrip("\n") + "\ninvalid-rule-test,invalid-rule-test.mdc,backend,nonexistent-specialist,active,curated,\"benchmark-injected\",Injected by Layer D benchmark mutation\n")
        plan["applied"] = True
        plan["details"] = {"appended_invalid_row": os.fspath(rel)}
        return plan

    if mtype == "missing_rule_file":
        rule_file = mutation.get("rule_file") or mutation.get("path") or ".cursor/rules/backend-developer.mdc"
        rel = _safe_repo_relative_path(str(rule_file))
        target = temp_root / rel
        _append_trace(trace_path, {"step": "mutate", "mutation_type": mtype, "op": "delete", "path": os.fspath(rel)})
        if target.exists():
            target.unlink()
        plan["applied"] = True
        plan["details"] = {"deleted": os.fspath(rel)}
        return plan

    if mtype == "invalid_skill_finder_specialist":
        rel = _safe_repo_relative_path(".cursor/agents/mappings/skill-finder.csv")
        target = temp_root / rel
        route_id = mutation.get("route_id") or "backend-api"
        bad_specialist = mutation.get("bad_specialist_id") or "nonexistent-specialist"
        _append_trace(
            trace_path,
            {"step": "mutate", "mutation_type": mtype, "op": "edit_csv", "path": os.fspath(rel), "route_id": route_id, "bad_specialist_id": bad_specialist},
        )

        lines = target.read_text(encoding="utf-8").splitlines()
        if not lines:
            raise ValueError("skill-finder.csv is empty in temp copy")
        header = lines[0]
        rows = lines[1:]

        updated = False
        out_rows: List[str] = []
        for raw in rows:
            if not raw.strip():
                continue
            parts = raw.split(",")
            if len(parts) >= 3 and parts[0] == route_id:
                parts[2] = bad_specialist
                raw = ",".join(parts)
                updated = True
            out_rows.append(raw)

        if not updated:
            # Append a deterministic invalid row using a valid field_id but invalid specialist_id.
            out_rows.append(
                ",".join(
                    [
                        str(mutation.get("new_route_id") or "invalid-route-test"),
                        str(mutation.get("field_id") or "backend"),
                        bad_specialist,
                        '"benchmark-injected"',
                        '"injected invalid specialist_id row"',
                        "1",
                        "Injected by Layer D benchmark mutation",
                    ]
                )
            )

        target.write_text("\n".join([header] + out_rows) + "\n", encoding="utf-8")
        plan["applied"] = True
        plan["details"] = {"file": os.fspath(rel), "route_id": route_id, "bad_specialist_id": bad_specialist, "appended_row": (not updated)}
        return plan

    if mtype == "missing_specialist_scaffold":
        specialist_id = mutation.get("specialist_id") or "backend-developer"
        rel = _safe_repo_relative_path(f".cursor/agents/specialists/{specialist_id}")
        target = temp_root / rel
        _append_trace(trace_path, {"step": "mutate", "mutation_type": mtype, "op": "delete_tree", "path": os.fspath(rel)})
        if target.exists():
            shutil.rmtree(target)
        plan["applied"] = True
        plan["details"] = {"deleted_tree": os.fspath(rel), "specialist_id": specialist_id}
        return plan

    if mtype == "invalid_registry_reference":
        # Introduce a mapping to a specialist that does not exist in registry.yaml.
        rel = _safe_repo_relative_path(".cursor/agents/mappings/rule-map.csv")
        target = temp_root / rel
        rule_id = mutation.get("rule_id") or "backend-developer"
        bad_specialist = mutation.get("bad_specialist_id") or "nonexistent-specialist"
        _append_trace(
            trace_path,
            {"step": "mutate", "mutation_type": mtype, "op": "edit_csv", "path": os.fspath(rel), "rule_id": rule_id, "bad_specialist_id": bad_specialist},
        )
        lines = target.read_text(encoding="utf-8").splitlines()
        if not lines:
            raise ValueError("rule-map.csv is empty in temp copy")
        header = lines[0]
        rows = lines[1:]

        updated = False
        out_rows = []
        for raw in rows:
            if not raw.strip():
                continue
            parts = raw.split(",")
            # Columns: rule_id,rule_file,owner_field_id,owner_specialist_id,...
            if len(parts) >= 4 and parts[0] == rule_id:
                parts[3] = bad_specialist
                raw = ",".join(parts)
                updated = True
            out_rows.append(raw)

        if not updated:
            # Deterministic fallback: append an invalid mapping row referencing a missing specialist.
            out_rows.append(
                ",".join(
                    [
                        str(mutation.get("new_rule_id") or "invalid-rule-test"),
                        str(mutation.get("rule_file") or "invalid-rule-test.mdc"),
                        str(mutation.get("owner_field_id") or "backend"),
                        bad_specialist,
                        "active",
                        "curated",
                        '"benchmark-injected"',
                        "Injected by Layer D benchmark mutation",
                    ]
                )
            )

        target.write_text("\n".join([header] + out_rows) + "\n", encoding="utf-8")
        plan["applied"] = True
        plan["details"] = {"file": os.fspath(rel), "rule_id": rule_id, "bad_specialist_id": bad_specialist, "appended_row": (not updated)}
        return plan

    if mtype == "stale_docs_marker":
        # Create a rule file without updating rule-map.csv to force deterministic validation failure.
        rule_file = mutation.get("rule_file") or "stale-docs-marker.mdc"
        rel = _safe_repo_relative_path(f".cursor/rules/{rule_file}")
        target = temp_root / rel
        _append_trace(trace_path, {"step": "mutate", "mutation_type": mtype, "op": "create_file", "path": os.fspath(rel)})
        _write_text(
            target,
            "\n".join(
                [
                    "# STALE DOCS MARKER (benchmark mutation)",
                    "",
                    "This file is intentionally created by the benchmark runner in a temp copy.",
                    "It should trigger validate_agent_system.py because rule-map.csv does not reference it.",
                    "",
                ]
            ),
        )
        plan["applied"] = True
        plan["details"] = {"created": os.fspath(rel)}
        return plan

    raise ValueError(f"unsupported mutation.type: {mtype!r}")


def _run_validation_commands_in_temp(
    temp_root: Path,
    validation_commands: List[str],
    trace_path: Path,
) -> Dict[str, Any]:
    """
    Execute validation commands inside temp_root.
    Returns dict with exit_code, stdout, stderr, commands_executed.
    """
    combined_out: List[str] = []
    combined_err: List[str] = []
    commands_executed = 0
    exit_code = 0

    for cmd in validation_commands:
        if not isinstance(cmd, str) or not cmd.strip():
            continue
        argv = shlex.split(cmd)
        if not argv:
            continue
        if argv[0] == "python":
            argv[0] = sys.executable
        # Rewrite any ".cursor/..." args to point at temp_root.
        rewritten: List[str] = []
        for tok in argv:
            if isinstance(tok, str) and tok.startswith(".cursor/"):
                rewritten.append(os.fspath(temp_root / Path(tok)))
            else:
                rewritten.append(tok)

        _append_trace(trace_path, {"step": "run_cmd", "cmd": cmd, "argv": rewritten, "cwd": os.fspath(temp_root)})
        completed = subprocess.run(
            rewritten,
            cwd=os.fspath(temp_root),
            check=False,
            capture_output=True,
            text=True,
        )
        commands_executed += 1
        out = completed.stdout or ""
        err = completed.stderr or ""
        combined_out.append(out)
        combined_err.append(err)
        exit_code = completed.returncode
        if completed.returncode != 0:
            break

    return {
        "exit_code": int(exit_code),
        "stdout": "\n".join([s.rstrip() for s in combined_out if s is not None]).rstrip() + ("\n" if combined_out else ""),
        "stderr": "\n".join([s.rstrip() for s in combined_err if s is not None]).rstrip() + ("\n" if combined_err else ""),
        "commands_executed": int(commands_executed),
    }


def _predict_actual(case: Dict[str, Any]) -> Dict[str, Any]:
    layer = case.get("layer")
    prompt = case.get("prompt") or ""
    expected = case.get("expected", {})

    if not isinstance(prompt, str):
        prompt = str(prompt)

    if layer == "A":
        route = predictor.predict_route(prompt)
        route["mode"] = "real"
        route["benchmark_valid"] = True
        return route

    if layer == "B":
        candidate = case.get("candidate_response") or ""
        if not isinstance(candidate, str):
            candidate = str(candidate)
        report = predictor.validate_handoff_candidate(candidate)
        return {
            "mode": "real",
            "benchmark_valid": True,
            "handoff_validation": report,
            # Keep routing prediction available for audit.
            "predicted_route": predictor.predict_route(prompt),
        }

    if layer == "C":
        route = predictor.predict_route(prompt)
        trace = predictor.predict_workflow_trace(
            prompt=prompt,
            task_type=route.get("task_type", "mixed_task"),
            primary_agent=route.get("primary_agent", "orchestrator"),
            quality_gates=route.get("quality_gates", []),
        )
        return {
            "mode": "real",
            "benchmark_valid": True,
            "predicted_route": route,
            "predicted_trace": trace,
        }

    if layer == "D":
        return {
            "mode": "real",
            "benchmark_valid": False,
            "mutation_supported": False,
            "reason": "Layer D mutation execution requires runner context (temp repo + subprocess); call _execute_layer_d_case.",
            "expected_snapshot": expected if isinstance(expected, dict) else {},
        }

    if layer == "E":
        return {
            "mode": "real",
            "benchmark_valid": False,
            "ablation_supported": False,
            "reason": "Layer E scaffold requires runner context (trace + axis metadata); call _execute_layer_e_case.",
            "expected_snapshot": expected if isinstance(expected, dict) else {},
        }

    return {
        "mode": "real",
        "benchmark_valid": False,
        "reason": f"unknown layer: {layer!r}",
    }


def _execute_layer_d_case(repo_root: Path, out_dir: Path, case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = case.get("id") or "<missing>"
    expected = case.get("expected", {}) if isinstance(case.get("expected"), dict) else {}
    mutation = case.get("mutation", {})
    if not isinstance(mutation, dict):
        mutation = {"type": None}

    validation_commands = expected.get("validation_commands")
    if not isinstance(validation_commands, list) or not all(isinstance(x, str) for x in validation_commands):
        validation_commands = []

    case_out = out_dir / "cases" / str(case_id)
    trace_path = case_out / "trace.jsonl"
    mutation_plan_path = case_out / "mutation_plan.json"
    stdout_path = case_out / "stdout.txt"
    stderr_path = case_out / "stderr.txt"

    # Fresh artifacts for each run.
    for p in [trace_path, stdout_path, stderr_path]:
        if p.exists():
            p.unlink()

    temp_root_str = tempfile.mkdtemp(prefix="bench-layerd-")
    temp_root = Path(temp_root_str)
    scripts_executed = 0

    try:
        _append_trace(trace_path, {"step": "init", "case_id": case_id, "layer": "D"})
        _copy_cursor_trees_to_temp(repo_root, temp_root, trace_path)

        mutation_plan = _mutate_temp_tree(temp_root, mutation, trace_path)
        write_json(mutation_plan_path, mutation_plan)

        run_result = _run_validation_commands_in_temp(temp_root, validation_commands, trace_path)
        scripts_executed = int(run_result.get("commands_executed", 0))

        _write_text(stdout_path, run_result.get("stdout", "") or "")
        _write_text(stderr_path, run_result.get("stderr", "") or "")

        return {
            "mode": "real",
            "benchmark_valid": True,
            "mutation_supported": True,
            "mutation": mutation,
            "mutation_plan_path": os.fspath(mutation_plan_path),
            "validation_commands": validation_commands,
            "validation_command_executed": bool(validation_commands) and scripts_executed > 0,
            "exit_code": int(run_result.get("exit_code", 0)),
            # Keep stdout/stderr in actual for scorer convenience (also written to artifacts).
            "stdout": run_result.get("stdout", ""),
            "stderr": run_result.get("stderr", ""),
            "scripts_executed_count": scripts_executed,
        }
    except Exception as exc:
        _append_trace(trace_path, {"step": "error", "error": str(exc), "type": type(exc).__name__})
        _write_text(stderr_path, f"{type(exc).__name__}: {exc}\n")
        write_json(
            mutation_plan_path,
            {"type": mutation.get("type"), "applied": False, "details": {"error": str(exc), "exception_type": type(exc).__name__}},
        )
        return {
            "mode": "real",
            "benchmark_valid": True,
            "mutation_supported": False,
            "mutation": mutation,
            "validation_commands": validation_commands,
            "validation_command_executed": False,
            "exit_code": 2,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}\n",
            "scripts_executed_count": scripts_executed,
        }
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def _execute_layer_e_case(out_dir: Path, case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Layer E scaffold:
    - run Layer A deterministic route prediction
    - include ablation axis metadata in actual + per-case trace
    - mark ablation_supported="scaffold" and benchmark_valid=true
    """
    case_id = case.get("id") or "<missing>"
    prompt = case.get("prompt") or ""
    if not isinstance(prompt, str):
        prompt = str(prompt)

    ablation_axis = case.get("ablation_axis", {})
    if not isinstance(ablation_axis, dict):
        ablation_axis = {"_invalid_ablation_axis": True}

    case_out = out_dir / "cases" / str(case_id)
    trace_path = case_out / "trace.jsonl"
    if trace_path.exists():
        trace_path.unlink()

    _append_trace(trace_path, {"step": "init", "case_id": case_id, "layer": "E", "ablation_axis": ablation_axis})
    route = predictor.predict_route(prompt)
    _append_trace(trace_path, {"step": "predict_route", "route": route})

    route["mode"] = "real"
    route["benchmark_valid"] = True
    route["ablation_supported"] = "scaffold"
    route["ablation_axis"] = ablation_axis
    return route


def main(argv: List[str]) -> int:
    repo_root = Path(__file__).resolve().parents[4]  # .../.cursor/agents/benchmarks/scripts/run_benchmark.py
    benchmarks_root = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(
        prog="run_benchmark.py",
        description="Run deterministic benchmark scaffold (Phase 3A).",
    )
    parser.add_argument(
        "--cases-dir",
        default=str(benchmarks_root / "cases"),
        help="Directory containing cases/*.jsonl (default: benchmarks/cases)",
    )
    parser.add_argument(
        "--out-dir",
        default=str(benchmarks_root / "runs" / "latest"),
        help="Output directory (default: benchmarks/runs/latest)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print loaded cases (id/layer/prompt/expected). Outputs are still written.",
    )

    args = parser.parse_args(argv)
    cases_dir = Path(args.cases_dir).resolve()
    out_dir = Path(args.out_dir).resolve()

    if not cases_dir.exists():
        print(f"ERROR: cases dir not found: {cases_dir}", file=sys.stderr)
        return 2

    cases = load_cases(cases_dir)

    if args.dry_run:
        for c in cases:
            print("=" * 80)
            print(f"id: {c.get('id')}")
            print(f"layer: {c.get('layer')}")
            print("prompt:")
            print(c.get("prompt", ""))
            print("expected:")
            print(json.dumps(c.get("expected", {}), indent=2, sort_keys=True))

    ensure_out_dir(out_dir)

    run_id = out_dir.name
    timestamp = _now_iso()
    start_ts = time.time()
    start_iso = timestamp

    run_config = {
        "run_id": run_id,
        "timestamp": timestamp,
        "runner_version": RUNNER_VERSION,
        "dry_run": bool(args.dry_run),
        "cases_dir": os.fspath(cases_dir),
        "cases_files": [p.name for p in _iter_case_files(cases_dir)],
        "repo_root": os.fspath(repo_root),
    }

    actual_rows: List[Dict[str, Any]] = []
    scripts_executed_total = 0
    mutation_cases_count = 0
    ablation_cases_count = 0
    counts_by_layer: Dict[str, int] = {}
    for c in cases:
        expected = c.get("expected", {})
        layer = c.get("layer")
        layer_s = str(layer) if layer is not None else "?"
        counts_by_layer[layer_s] = counts_by_layer.get(layer_s, 0) + 1

        if args.dry_run:
            # Preserve Phase 3A "echo expected" behavior.
            actual = dict(expected) if isinstance(expected, dict) else {"_invalid_expected": True}
            actual["mode"] = "dry_run"
            actual["benchmark_valid"] = False
            actual["reason"] = "dry-run echoes expected values; not a real benchmark score"
        else:
            if layer_s == "D":
                mutation_cases_count += 1
                actual = _execute_layer_d_case(repo_root=repo_root, out_dir=out_dir, case=c)
                scripts_executed_total += int(actual.get("scripts_executed_count", 0) or 0)
            elif layer_s == "E":
                ablation_cases_count += 1
                actual = _execute_layer_e_case(out_dir=out_dir, case=c)
            else:
                actual = _predict_actual(c)
        actual_rows.append(
            {
                "case_id": c.get("id"),
                "layer": layer,
                "prompt": c.get("prompt"),
                "expected": expected,
                "actual": actual,
            }
        )

    cases_total = len(actual_rows)
    summary = {
        "run_id": run_id,
        "timestamp": timestamp,
        "cases_total": cases_total,
        "score_total": 0,
        "by_layer": {},
        "failures": [],
        "recommendations": ["Scaffold runner wrote placeholder actual results; use score_benchmark.py to compare."],
    }

    end_iso = _now_iso()
    duration_seconds = max(0.0, time.time() - start_ts)

    trace_config_usage = {
        "runner_version": RUNNER_VERSION,
        "system_under_test": {
            "repo_root": os.fspath(repo_root),
            "benchmarks_root": os.fspath(benchmarks_root),
        },
        "environment": {
            "os": platform.platform(),
            "platform": sys.platform,
            "python": sys.version.split()[0],
            "python_full": sys.version,
        },
        "timing": {
            "start_timestamp": start_iso,
            "end_timestamp": end_iso,
            "duration_seconds": round(duration_seconds, 6),
        },
        "seeds_used": [],
        "counts": {
            "cases_total": cases_total,
            "counts_by_layer": dict(sorted(counts_by_layer.items())),
            "mode": ("dry_run" if args.dry_run else "real"),
            "benchmark_valid": (False if args.dry_run else True),
            "passes": 0,
            "failures": 0,
            "scripts_executed_count": int(scripts_executed_total),
            "mutation_cases_count": int(mutation_cases_count),
            "ablation_cases_count": int(ablation_cases_count),
        },
        "predictor": {
            "module": "predictor.py",
            "deterministic": True,
            "layers_supported": ["A", "B", "C"],
            "layers_supported_extended": ["D", "E"],
        },
    }

    write_json(out_dir / "run_config.json", run_config)
    write_json(out_dir / "trace_config_usage.json", trace_config_usage)
    write_jsonl(out_dir / "actual_results.jsonl", actual_rows)
    write_json(out_dir / "summary.json", summary)

    print(f"Wrote benchmark outputs to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

