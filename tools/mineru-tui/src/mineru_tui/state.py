from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SUPPORTED_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".tif",
    ".tiff",
    ".docx",
    ".pptx",
    ".xlsx",
}


def normalize_key(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return str(path.absolute())


def pdf_page_count(path: Path) -> int | None:
    """Optional: install `pypdf` for local page totals without running mineru."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(str(path), strict=False)
        return len(reader.pages)
    except Exception:
        return None


def _digest_path(p: Path) -> str:
    key = normalize_key(p).encode("utf-8", errors="surrogateescape")
    return hashlib.md5(key, usedforsecurity=False).hexdigest()[:8]


def run_dir_for_file(output_root: Path, file_path: Path) -> Path:
    stem = file_path.stem.replace(" ", "_")[:80] or "file"
    digest = _digest_path(file_path)
    return output_root / "runs" / f"{stem}__{digest}"


@dataclass
class QueueEntry:
    path: str
    status: str = "PENDING"  # PENDING, RUNNING, DONE, FAILED
    run_dir: str | None = None
    pages_hint: str = "?"
    pages_done: int | None = None
    pages_total: int | None = None
    size_bytes: int = 0
    error: str | None = None
    duration_sec: float | None = None
    updated: float = field(default_factory=lambda: time.time())

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> QueueEntry:
        return cls(
            path=str(data["path"]),
            status=str(data.get("status", "PENDING")),
            run_dir=data.get("run_dir"),
            pages_hint=str(data.get("pages_hint", "?")),
            pages_done=(
                int(data["pages_done"])
                if data.get("pages_done") is not None
                else None
            ),
            pages_total=(
                int(data["pages_total"])
                if data.get("pages_total") is not None
                else None
            ),
            size_bytes=int(data.get("size_bytes", 0)),
            error=data.get("error"),
            duration_sec=(
                float(data["duration_sec"])
                if data.get("duration_sec") is not None
                else None
            ),
            updated=float(data.get("updated", time.time())),
        )


def scan_input_files(input_root: Path) -> list[Path]:
    found: list[Path] = []
    if not input_root.is_dir():
        return found
    for p in input_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES:
            try:
                found.append(p.resolve())
            except OSError:
                found.append(p)
    found.sort(key=lambda x: str(x).lower())
    return found


def state_path(output_root: Path) -> Path:
    """Persistent queue JSON at output root (resumable)."""
    return output_root / "queue_state.json"


def migrate_legacy_state_if_needed(output_root: Path) -> None:
    """Prefer `queue_state.json`; pick up older `.mineru-tui/queue.json` once."""
    target = state_path(output_root)
    if target.is_file():
        return
    legacy_dot = output_root / ".mineru-tui" / "queue.json"
    if not legacy_dot.is_file():
        return
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        legacy_dot.replace(target)
    except OSError:
        pass


def load_queue_state(path: Path) -> dict[str, Any]:
    migrate_legacy_state_if_needed(path.parent)
    if not path.is_file():
        return {"version": 2, "batch_mode": "", "order": [], "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"version": 2, "batch_mode": "", "order": [], "entries": {}}
        ver = int(data.get("version", 1))
        data["version"] = ver
        data.setdefault("batch_mode", "")
        data.setdefault("entries", {})
        if not isinstance(data["entries"], dict):
            data["entries"] = {}
        data.setdefault("order", [])
        if not isinstance(data["order"], list):
            data["order"] = []
        if not data["order"]:
            data["order"] = sorted(data["entries"].keys(), key=lambda k: str(k).lower())
        return data
    except (OSError, json.JSONDecodeError):
        return {"version": 2, "batch_mode": "", "order": [], "entries": {}}


def save_queue_state(
    path: Path,
    batch_mode: str,
    order: list[str],
    entries: dict[str, QueueEntry],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    clean_order = [k for k in order if k in entries]
    for k in entries:
        if k not in clean_order:
            clean_order.append(k)
    payload = {
        "version": 2,
        "batch_mode": batch_mode,
        "order": clean_order,
        "entries": {k: entries[k].to_json() for k in clean_order if k in entries},
    }
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _entry_for_new_file(fp: Path, max_pages: int) -> QueueEntry:
    try:
        st = fp.stat()
        size_b = st.st_size
    except OSError:
        size_b = 0

    pages_total: int | None = None
    pages_done: int | None = None
    if fp.suffix.lower() == ".pdf":
        doc_pages = pdf_page_count(fp)
        if doc_pages is None:
            pages_total = max_pages if max_pages > 0 else None
            pages_done = 0
        elif max_pages > 0:
            pages_total = min(doc_pages, max_pages)
            pages_done = 0
        else:
            pages_total = doc_pages
            pages_done = 0

    hint = "—"
    if pages_total is not None and pages_done is not None:
        hint = f"{pages_done}/{pages_total}"
    elif pages_total is not None:
        hint = f"?/{pages_total}"

    return QueueEntry(
        path=normalize_key(fp),
        status="PENDING",
        pages_hint=hint,
        pages_done=pages_done,
        pages_total=pages_total,
        size_bytes=size_b,
    )


def merge_scan_with_state(
    input_root: Path,
    output_root: Path,
    batch_mode: str,
    max_pages: int,
    existing_entries: dict[str, QueueEntry],
    existing_order: list[str],
) -> tuple[dict[str, QueueEntry], list[str]]:
    files = scan_input_files(input_root)
    out: dict[str, QueueEntry] = {}
    order: list[str] = []

    for k in existing_order:
        if k in existing_entries:
            e = existing_entries[k]
            if e.status == "RUNNING":
                e = QueueEntry(
                    path=e.path,
                    status="PENDING",
                    run_dir=e.run_dir,
                    pages_hint=e.pages_hint,
                    pages_done=e.pages_done,
                    pages_total=e.pages_total,
                    size_bytes=e.size_bytes,
                    error=None,
                    duration_sec=None,
                    updated=time.time(),
                )
            out[k] = e
            order.append(k)

    seen = set(order)
    for fp in files:
        key = normalize_key(fp)
        if key in out:
            try:
                out[key].size_bytes = fp.stat().st_size
            except OSError:
                pass
            if fp.suffix.lower() == ".pdf" and out[key].pages_total is None:
                doc_pages = pdf_page_count(fp)
                if doc_pages is not None and max_pages > 0:
                    out[key].pages_total = min(doc_pages, max_pages)
                elif doc_pages is not None:
                    out[key].pages_total = doc_pages
                if out[key].pages_done is None:
                    out[key].pages_done = 0
            continue
        out[key] = _entry_for_new_file(fp, max_pages)
        if key not in seen:
            order.append(key)
            seen.add(key)

    pruned = {normalize_key(p) for p in files}
    order = [k for k in order if k in pruned]
    out = {k: out[k] for k in order}

    save_queue_state(state_path(output_root), batch_mode, order, out)
    return out, order
