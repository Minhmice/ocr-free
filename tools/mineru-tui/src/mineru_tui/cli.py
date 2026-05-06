from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from mineru_tui.app import MineruTUIApp


def _expand(p: Path) -> Path:
    return p.expanduser().resolve()


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def main() -> None:
    repo = Path.cwd()
    default_in = Path(os.environ.get("MINERU_TUI_INPUT_DIR", "") or (repo / "input"))
    default_out = Path(os.environ.get("MINERU_TUI_OUTPUT_DIR", "") or (repo / "output"))
    default_backend = os.environ.get("MINERU_TUI_BACKEND", "pipeline").strip() or "pipeline"
    default_container = os.environ.get("MINERU_TUI_CONTAINER", "mineru-gradio").strip() or None
    max_env = os.environ.get("MINERU_TUI_MAX_PAGES", "").strip()
    default_max = 0
    if max_env.isdigit():
        default_max = int(max_env)

    parser = argparse.ArgumentParser(
        description=(
            "MinerU batch queue TUI (Textual). Scans input/, runs mineru CLI, "
            "persists queue under output/.mineru-tui/."
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=default_in,
        help="Input directory (recursive scan). Default: ./input or MINERU_TUI_INPUT_DIR",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=default_out,
        help="Output root. Queue: .mineru-tui/queue.json. Default: ./output or MINERU_TUI_OUTPUT_DIR",
    )
    parser.add_argument(
        "-b",
        "--backend",
        type=str,
        default=default_backend,
        help="mineru -b backend (default: pipeline, or MINERU_TUI_BACKEND)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=default_max,
        help=(
            "PDF page cap (0 = full document). When page count is unknown, -e uses max_pages-1. "
            "Env: MINERU_TUI_MAX_PAGES"
        ),
    )
    parser.add_argument(
        "-j",
        "--concurrency",
        type=int,
        default=_env_int("MINERU_TUI_CONCURRENCY", 1),
        help="Parallel mineru processes (default: 1)",
    )
    parser.add_argument(
        "--container",
        type=str,
        default=default_container,
        help="Docker container for status dot + CPU (default: mineru-gradio; empty to disable)",
    )
    parser.add_argument(
        "--batch-mode",
        type=str,
        default=os.getenv("MINERU_TUI_BATCH_MODE", "dir-scan").strip() or "dir-scan",
        help="Label stored in queue JSON",
    )

    args = parser.parse_args()
    inp = _expand(args.input)
    out = _expand(args.output)
    container = (args.container or "").strip() or None

    if args.concurrency < 1:
        print("--concurrency must be >= 1", file=sys.stderr)
        sys.exit(2)
    if args.max_pages < 0:
        print("--max-pages must be >= 0 (0 = unlimited)", file=sys.stderr)
        sys.exit(2)

    app = MineruTUIApp(
        input_dir=inp,
        output_dir=out,
        backend=args.backend,
        max_pages=args.max_pages,
        concurrency=args.concurrency,
        container=container,
        batch_mode=args.batch_mode,
    )
    app.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
