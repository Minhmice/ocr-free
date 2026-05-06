#!/usr/bin/env bash
# Idempotent launcher for tools/mineru-tui (macOS/Linux).
# Usage: ./scripts/run-mineru-tui.sh [-- extra args for mineru-tui]

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

pick_python() {
  for c in python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1; then
      echo "$c"
      return
    fi
  done
  echo "python3"
}

PY="$(pick_python)"
VENV="$REPO_ROOT/.venv-mineru-tui"
if [[ ! -x "$VENV/bin/python" ]]; then
  "$PY" -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install -U pip setuptools wheel >/dev/null
"$VENV/bin/python" -m pip install -e "$REPO_ROOT/tools/mineru-tui" >/dev/null
exec "$VENV/bin/mineru-tui" "$@"
