#!/usr/bin/env python3
"""
Validate benchmark case JSONL files.

Requirements (Phase 3A):
- Validate each JSONL object has: id/layer/prompt/expected/tags/notes
- layer in A|B|C|D|E
- duplicate IDs fail
- expected includes: task_type/primary_agent/secondary_agents/quality_gates/validation_commands
- Print pass/fail summary; exit non-zero on failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ALLOWED_LAYERS = {"A", "B", "C", "D", "E"}
REQUIRED_TOP_LEVEL_KEYS = ["id", "layer", "prompt", "expected", "tags", "notes"]
REQUIRED_EXPECTED_KEYS = [
    "task_type",
    "primary_agent",
    "secondary_agents",
    "quality_gates",
    "validation_commands",
]


def _iter_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{line_no}: expected object, got {type(obj).__name__}")
            yield line_no, obj


def _validate_case(obj: Dict[str, Any], origin: str) -> List[str]:
    errors: List[str] = []

    for k in REQUIRED_TOP_LEVEL_KEYS:
        if k not in obj:
            errors.append(f"{origin}: missing key '{k}'")

    case_id = obj.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        errors.append(f"{origin}: 'id' must be a non-empty string")

    layer = obj.get("layer")
    if layer not in ALLOWED_LAYERS:
        errors.append(f"{origin}: 'layer' must be one of {sorted(ALLOWED_LAYERS)}")

    prompt = obj.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        errors.append(f"{origin}: 'prompt' must be a non-empty string")

    tags = obj.get("tags")
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        errors.append(f"{origin}: 'tags' must be a list of strings")

    notes = obj.get("notes")
    if not isinstance(notes, str):
        errors.append(f"{origin}: 'notes' must be a string")

    expected = obj.get("expected")
    if not isinstance(expected, dict):
        errors.append(f"{origin}: 'expected' must be an object")
        return errors

    for k in REQUIRED_EXPECTED_KEYS:
        if k not in expected:
            errors.append(f"{origin}: expected missing key '{k}'")

    if "task_type" in expected and (not isinstance(expected["task_type"], str) or not expected["task_type"].strip()):
        errors.append(f"{origin}: expected.task_type must be a non-empty string")
    if "primary_agent" in expected and (
        not isinstance(expected["primary_agent"], str) or not expected["primary_agent"].strip()
    ):
        errors.append(f"{origin}: expected.primary_agent must be a non-empty string")

    for list_key in ["secondary_agents", "quality_gates", "validation_commands"]:
        if list_key in expected:
            v = expected[list_key]
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                errors.append(f"{origin}: expected.{list_key} must be a list of strings")

    # Phase 3B.1: layer-specific required fields (hard requirements, not warnings)
    layer = obj.get("layer")
    if layer == "B":
        if "candidate_response" not in obj:
            errors.append(f"{origin}: layer B requires top-level 'candidate_response'")
        elif not isinstance(obj.get("candidate_response"), str):
            errors.append(f"{origin}: layer B 'candidate_response' must be a string")
    elif layer == "C":
        if "expected_trace" in obj:
            errors.append(f"{origin}: layer C expected_trace must be nested under expected.expected_trace (not top-level)")
        if "expected_trace" not in expected:
            errors.append(f"{origin}: layer C requires 'expected.expected_trace'")
        else:
            et = expected.get("expected_trace")
            if not isinstance(et, list) or not all(isinstance(x, dict) for x in et):
                errors.append(f"{origin}: expected.expected_trace must be a list of objects")
    elif layer == "D":
        if "mutation" not in obj:
            errors.append(f"{origin}: layer D requires top-level 'mutation'")
        else:
            mut = obj.get("mutation")
            if not isinstance(mut, dict):
                errors.append(f"{origin}: layer D 'mutation' must be an object")
    elif layer == "E":
        if "ablation_axis" not in obj:
            errors.append(f"{origin}: layer E requires top-level 'ablation_axis'")
        else:
            ax = obj.get("ablation_axis")
            if not isinstance(ax, dict):
                errors.append(f"{origin}: layer E 'ablation_axis' must be an object")

    return errors


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_cases.py",
        description="Validate benchmark cases JSONL schema and constraints.",
    )
    parser.add_argument(
        "--cases-dir",
        default=str(Path(__file__).resolve().parents[1] / "cases"),
        help="Directory containing cases/*.jsonl (default: benchmarks/cases)",
    )
    args = parser.parse_args(argv)

    cases_dir = Path(args.cases_dir).resolve()
    if not cases_dir.exists() or not cases_dir.is_dir():
        print(f"FAIL: cases dir not found: {cases_dir}", file=sys.stderr)
        return 2

    jsonl_files = sorted(cases_dir.glob("*.jsonl"))
    if not jsonl_files:
        print(f"FAIL: no .jsonl files found under: {cases_dir}", file=sys.stderr)
        return 2

    all_errors: List[str] = []
    seen_ids: Dict[str, str] = {}
    cases_total = 0
    warnings_total = 0
    layer_e_cases = 0

    for p in jsonl_files:
        file_cases = 0
        file_errors = 0
        try:
            for line_no, obj in _iter_jsonl(p):
                cases_total += 1
                file_cases += 1
                origin = f"{p}:{line_no}"
                # Enforce global uniqueness across *all* jsonl files even if a row has other schema errors.
                cid = obj.get("id")
                if isinstance(cid, str) and cid.strip():
                    prev = seen_ids.get(cid)
                    if prev is not None:
                        all_errors.append(f"{origin}: duplicate id '{cid}' (already seen at {prev})")
                        file_errors += 1
                    else:
                        seen_ids[cid] = origin

                errs = _validate_case(obj, origin)
                if errs:
                    all_errors.extend(errs)
                    file_errors += len(errs)
                    continue

                # Non-failing, layer-specific warnings (Phase 3A.5)
                layer = obj.get("layer")
                if layer == "E":
                    layer_e_cases += 1
        except ValueError as e:
            all_errors.append(str(e))
            file_errors += 1

        status = "PASS" if file_errors == 0 else "FAIL"
        print(f"{status}: {p.name} (cases={file_cases}, errors={file_errors})")

    if all_errors:
        print("\nErrors:", file=sys.stderr)
        for e in all_errors:
            print(f"- {e}", file=sys.stderr)
        print(f"\nFAIL: total_cases={cases_total}, total_errors={len(all_errors)}", file=sys.stderr)
        return 1

    if layer_e_cases == 0:
        print("WARNING: no Layer E cases present (allowed in Phase 3B.1)", file=sys.stderr)
        warnings_total += 1

    print(f"\nPASS: total_cases={cases_total}, total_files={len(jsonl_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

