"""Helpers for building MinerU CLI invocations (keeps UI code smaller)."""

from __future__ import annotations

from pathlib import Path

from mineru_tui.state import pdf_page_count


def pdf_end_page_for_cli(path: Path, max_pages: int) -> int | None:
    """Return inclusive 0-based end page for `mineru -e`, or None when unlimited."""
    if max_pages <= 0:
        return None
    total = pdf_page_count(path)
    if total is None:
        return max_pages - 1
    span = min(max_pages, total)
    return span - 1 if span > 0 else 0
