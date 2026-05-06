#!/usr/bin/env python3
"""
Secret hygiene scanner (stdlib-only).

Scans repo text files for common secret/token patterns and fails on real findings.

Exclusions:
- .git/**
- .cursor/agents/benchmarks/runs/**
- .cursor/agents/logs/**
- docs/agent-tools/**
- docs/agent-benchmarks/**

Allows placeholders:
- example, placeholder, dummy, fake, your_key_here, <...>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


PLACEHOLDER_WORDS = {
    "example",
    "placeholder",
    "dummy",
    "fake",
    "your_key_here",
}


EXCLUDE_PREFIXES = [
    ".git/",
    ".cursor/agents/benchmarks/runs/",
    ".cursor/agents/logs/",
    "docs/agent-tools/",
    "docs/agent-benchmarks/",
]


PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("OPENAI_API_KEY_ASSIGN", re.compile(r"(?m)\bOPENAI_API_KEY\s*=\s*([^\s#]+)")),
    ("SUPABASE_SERVICE_ROLE_KEY_ASSIGN", re.compile(r"(?m)\bSUPABASE_SERVICE_ROLE_KEY\s*=\s*([^\s#]+)")),
    ("GITHUB_PAT_GHP", re.compile(r"\bghp_[A-Za-z0-9]{10,}\b")),
    ("SLACK_BOT_XOXB", re.compile(r"\bxoxb-[A-Za-z0-9-]{10,}\b")),
    ("OPENAI_SK_PROJ", re.compile(r"\bsk-proj-[A-Za-z0-9]{8,}\b")),
    # Generic sk- tokens are noisy; require a minimum length after prefix.
    ("OPENAI_SK", re.compile(r"\bsk-[A-Za-z0-9]{16,}\b")),
    ("BEGIN_PRIVATE_KEY", re.compile(r"(?m)^-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----$")),
    ("PRIVATE_KEY_WORD", re.compile(r"(?i)\bprivate_key\b")),
]


@dataclass(frozen=True)
class Finding:
    rule: str
    rel_path: str
    line: int
    excerpt: str


def _is_excluded(rel_posix: str) -> bool:
    return any(rel_posix.startswith(p) for p in EXCLUDE_PREFIXES)


def _looks_binary(data: bytes) -> bool:
    return b"\x00" in data


def _read_text_lossy(path: Path, max_bytes: int = 2_000_000) -> Optional[str]:
    try:
        data = path.read_bytes()
    except Exception:
        return None
    if len(data) > max_bytes:
        data = data[:max_bytes]
    if _looks_binary(data):
        return None
    try:
        return data.decode("utf-8")
    except Exception:
        # Lossy decode to avoid hard-failing on mixed encodings.
        return data.decode("utf-8", errors="ignore")


def _is_placeholder_value(val: str) -> bool:
    v = (val or "").strip().strip('"').strip("'").lower()
    if not v:
        return True
    if v in PLACEHOLDER_WORDS:
        return True
    if v.startswith("<") and v.endswith(">"):
        return True
    if "your_key_here" in v:
        return True
    # allow any value containing placeholder hints
    if any(w in v for w in ["example", "placeholder", "dummy", "fake"]):
        return True
    return False


def _line_number_from_index(text: str, idx: int) -> int:
    # 1-based
    return text.count("\n", 0, max(0, idx)) + 1


def _make_excerpt(line: str, match_span: Tuple[int, int]) -> str:
    s, e = match_span
    s = max(0, s)
    e = min(len(line), e)
    # redact the exact match region, keep limited context
    prefix = line[:s]
    suffix = line[e:]
    ex = (prefix + "<REDACTED>" + suffix).strip()
    if len(ex) > 200:
        ex = ex[:200] + "…"
    return ex


def _iter_repo_files(repo_root: Path) -> Iterable[Tuple[str, Path]]:
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(repo_root)
        rel_posix = rel.as_posix()
        if _is_excluded(rel_posix):
            continue
        yield rel_posix, p


def scan(repo_root: Path) -> List[Finding]:
    findings: List[Finding] = []
    for rel_posix, p in _iter_repo_files(repo_root):
        text = _read_text_lossy(p)
        if text is None:
            continue

        # Quick placeholder skip for entire file if it is clearly a template.
        # (We still scan; this just reduces false positives by allowing explicit placeholder markers.)
        lines = text.splitlines()

        for rule, rx in PATTERNS:
            for m in rx.finditer(text):
                # Assignment-style rules: allow placeholder values.
                if rule.endswith("_ASSIGN"):
                    val = m.group(1) if m.lastindex and m.lastindex >= 1 else ""
                    if _is_placeholder_value(val):
                        continue
                # Token-style rules: allow if the matched token itself contains placeholder hints (rare)
                token = m.group(0)
                if _is_placeholder_value(token):
                    continue

                idx = m.start()
                line_no = _line_number_from_index(text, idx)
                line = lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else token

                # For PRIVATE_KEY_WORD, ignore if clearly documenting placeholders.
                if rule == "PRIVATE_KEY_WORD":
                    if any(w in (line or "").lower() for w in ["example", "placeholder", "dummy", "fake", "<...>"]):
                        continue

                # Excerpt redaction: try to redact match on this line.
                try:
                    line_start = text.rfind("\n", 0, idx) + 1
                    line_end = text.find("\n", idx)
                    if line_end == -1:
                        line_end = len(text)
                    line_text = text[line_start:line_end]
                    span = (m.start() - line_start, m.end() - line_start)
                    excerpt = _make_excerpt(line_text, span)
                except Exception:
                    excerpt = "<REDACTED>"

                findings.append(Finding(rule=rule, rel_path=rel_posix, line=line_no, excerpt=excerpt))
    return findings


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(prog="check_secrets_hygiene.py", description="Scan repo for likely secrets and fail on real findings.")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    findings = scan(repo_root)
    if not findings:
        print("PASS: no secret-like tokens detected")
        return 0

    print("FAIL: secret-like tokens detected", file=sys.stderr)
    for f in findings[:200]:
        print(f"- {f.rule}: {f.rel_path}:{f.line}: {f.excerpt}", file=sys.stderr)
    if len(findings) > 200:
        print(f"... and {len(findings) - 200} more", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

