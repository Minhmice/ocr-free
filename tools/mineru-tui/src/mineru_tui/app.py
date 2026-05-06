from __future__ import annotations

import asyncio
import shutil
import time
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, RichLog, Static

from mineru_tui import metrics
from mineru_tui.orchestrator import pdf_end_page_for_cli
from mineru_tui.state import (
    QueueEntry,
    load_queue_state,
    merge_scan_with_state,
    run_dir_for_file,
    save_queue_state,
    scan_input_files,
    state_path,
)


def _tilde_path(p: Path) -> str:
    try:
        home = Path.home().resolve()
        rp = p.resolve()
        if rp == home:
            return "~"
        rel = rp.relative_to(home)
        return "~/" + rel.as_posix()
    except (OSError, ValueError):
        pass
    return str(p)


def _short_name(p: Path, max_len: int = 44) -> str:
    s = p.name
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _fmt_size(n: int) -> str:
    if n <= 0:
        return "—"
    kb = 1024
    mb = kb * 1024
    if n >= mb:
        return f"{n / mb:.1f}MB"
    if n >= kb:
        return f"{n / kb:.1f}KB"
    return f"{n}B"


def _fmt_mmss(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    sec = max(0, int(seconds))
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"


def _pages_cell(entry: QueueEntry, path: Path) -> str:
    if path.suffix.lower() != ".pdf":
        return "—"
    d = entry.pages_done
    t = entry.pages_total
    if d is None and t is None:
        return entry.pages_hint
    if d is None:
        return f"?/{t}" if t is not None else "?"
    if t is None:
        return f"{d}/?"
    return f"{d}/{t}"


class MineruTUIApp(App[None]):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "rescan", "Rescan input"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }
    #title_row {
        border: heavy $primary;
        height: 3;
        padding: 0 1;
        background: $panel;
    }
    #path_row {
        border: heavy $primary;
        height: 3;
        padding: 0 1;
        background: $panel;
    }
    #mid_row {
        height: 12;
        border: heavy $primary;
    }
    #system_col {
        width: 1fr;
        border-right: heavy $primary;
        padding: 0 1;
    }
    #queue_col {
        width: 1fr;
        padding: 0 1;
    }
    .section_title {
        text-style: bold;
        height: 1;
    }
    #queue_table {
        height: 1fr;
        border: heavy $primary;
    }
    #job_log {
        height: 12;
        border: heavy $primary;
        padding: 0 1;
    }
    #mineru_banner {
        height: auto;
        padding: 0 1;
    }
    #selection_hint {
        height: auto;
        padding: 0 1;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        backend: str,
        max_pages: int,
        concurrency: int,
        container: str | None,
        batch_mode: str,
    ) -> None:
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.backend = backend
        self.max_pages = max(0, max_pages)
        self.concurrency = max(1, concurrency)
        self.container = container
        self.batch_mode = batch_mode

        self.entries: dict[str, QueueEntry] = {}
        self.order: list[str] = []
        self._run_started: dict[str, float] = {}
        self._table_ready = False
        self._max_pages_note_logged = False
        self._active: set[asyncio.Task[None]] = set()
        self._claim_lock = asyncio.Lock()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("", id="mineru_banner")
            yield Static("", id="title_row")
            yield Static("", id="path_row")
            with Horizontal(id="mid_row"):
                with Vertical(id="system_col"):
                    yield Static("SYSTEM", classes="section_title")
                    yield Static("", id="system_metrics")
                with Vertical(id="queue_col"):
                    yield Static("QUEUE SUMMARY", classes="section_title")
                    yield Static("", id="queue_summary")
            yield Static("QUEUE (PDF + images + office)", classes="section_title")
            yield DataTable(id="queue_table", zebra_stripes=True)
            yield Static("", id="selection_hint")
            yield Static("ACTIVE JOB LOG", classes="section_title")
            yield RichLog(id="job_log", highlight=True, markup=True, max_lines=400)
        yield Footer()

    def on_mount(self) -> None:
        self.title = "MinerU Local Testing TUI"
        banner = self.query_one("#mineru_banner", Static)
        if not shutil.which("mineru"):
            banner.update(
                "[bold red]mineru[/] not found on PATH. Install MinerU (e.g. "
                "`pip install -e ./mineru` with `mineru[core]`) or activate the venv, then restart."
            )
        else:
            banner.update("")
        self._load_state_and_merge()
        t = self.query_one("#queue_table", DataTable)
        t.add_columns("#", "Status", "Pages", "Size", "Time", "File")
        self._table_ready = True
        self._rebuild_table()
        self._refresh_header()
        self.set_interval(0.35, self._tick)
        self.run_worker(self._queue_loop(), exclusive=False, name="mineru-queue")

    def _load_state_and_merge(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        raw = load_queue_state(state_path(self.output_dir))
        batch_mode = self.batch_mode or str(raw.get("batch_mode", ""))
        existing: dict[str, QueueEntry] = {}
        for k, v in raw.get("entries", {}).items():
            if isinstance(v, dict):
                try:
                    existing[str(k)] = QueueEntry.from_json(v)
                except (KeyError, TypeError, ValueError):
                    continue
        order = [str(k) for k in (raw.get("order") or []) if str(k) in existing]
        self.entries, self.order = merge_scan_with_state(
            self.input_dir,
            self.output_dir,
            batch_mode,
            self.max_pages,
            existing,
            order,
        )

    def action_rescan(self) -> None:
        self._load_state_and_merge()
        self._rebuild_table()
        self._refresh_header()
        self.query_one("#job_log", RichLog).write("[yellow]Rescanned input; queue updated.[/]")

    def _persist(self) -> None:
        save_queue_state(
            state_path(self.output_dir),
            self.batch_mode,
            self.order,
            self.entries,
        )

    @on(DataTable.RowHighlighted)
    def on_queue_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id != "queue_table":
            return
        idx = event.cursor_row
        if idx is None or idx < 0 or idx >= len(self.order):
            return
        key = self.order[idx]
        ent = self.entries.get(key)
        if not ent:
            return
        self.query_one("#selection_hint", Static).update(f"Full path: {ent.path}")

    def _container_pretty(self) -> str:
        cname = self.container or "—"
        if self.container:
            try:
                running = metrics.docker_ps_running(self.container)
            except Exception:
                running = False
            dot = "[green]●[/]" if running else "[red]●[/]"
            return f"{cname} {dot}"
        return cname

    def _refresh_header(self) -> None:
        title = self.query_one("#title_row", Static)
        path_row = self.query_one("#path_row", Static)
        host = metrics.hostname()
        mp = "∞" if self.max_pages <= 0 else str(self.max_pages)
        title.update(
            f"Host: {host} | Container: {self._container_pretty()} | "
            f"Backend: {self.backend} | Max pages: {mp} | Concurrency: {self.concurrency}"
        )
        path_row.update(
            f"Input: {_tilde_path(self.input_dir)} | Output: {_tilde_path(self.output_dir)}"
        )

    def _queue_summary_block(self) -> str:
        files = scan_input_files(self.input_dir)
        pdf_found = sum(1 for p in files if p.suffix.lower() == ".pdf")
        by_s = {"PENDING": 0, "RUNNING": 0, "DONE": 0, "FAILED": 0}
        for k in self.order:
            e = self.entries.get(k)
            if not e:
                continue
            by_s[e.status] = by_s.get(e.status, 0) + 1

        running_n = by_s.get("RUNNING", 0)
        conc_line = f"{running_n} / {self.concurrency}"
        lines = [
            f"Files in queue    {len(self.order)}  (PDFs in input: {pdf_found})",
            f"Pending           {by_s.get('PENDING', 0)}",
            f"Running           {by_s.get('RUNNING', 0)}",
            f"Done              {by_s.get('DONE', 0)}",
            f"Failed            {by_s.get('FAILED', 0)}",
            f"Concurrency       {conc_line}",
            f"Batch mode        {self.batch_mode}",
        ]
        return "\n".join(lines)

    def _tick(self) -> None:
        self._refresh_header()
        sys_body = self.query_one("#system_metrics", Static)
        summ = self.query_one("#queue_summary", Static)
        try:
            sys_body.update(metrics.format_system_block(self.output_dir, self.container))
        except Exception as exc:
            sys_body.update(f"System metrics error: {exc}")
        try:
            summ.update(self._queue_summary_block())
        except Exception as exc:
            summ.update(f"Queue summary error: {exc}")
        if self._table_ready:
            self._rebuild_table()

    def _elapsed_live(self, key: str, e: QueueEntry) -> float | None:
        if e.status == "RUNNING":
            t0 = self._run_started.get(key)
            if t0 is not None:
                return time.monotonic() - t0
            return None
        return e.duration_sec

    def _rebuild_table(self) -> None:
        table = self.query_one("#queue_table", DataTable)
        table.clear()
        for i, key in enumerate(self.order, start=1):
            e = self.entries.get(key)
            if not e:
                continue
            p = Path(e.path)
            status = e.status
            pages = _pages_cell(e, p)
            size_s = _fmt_size(e.size_bytes)
            elapsed = _elapsed_live(key, e)
            time_s = _fmt_mmss(elapsed)
            table.add_row(
                str(i),
                status,
                pages,
                size_s,
                time_s,
                _short_name(p),
                key=key,
            )

    def _log(self, msg: str) -> None:
        self.query_one("#job_log", RichLog).write(msg)

    async def _queue_loop(self) -> None:
        sem = asyncio.Semaphore(self.concurrency)

        async def run_one(path_key: str) -> None:
            async with sem:
                await self._run_mineru_job(path_key)

        while True:
            self._active = {t for t in self._active if not t.done()}
            pending = [k for k in self.order if self.entries[k].status == "PENDING"]
            while pending and len(self._active) < self.concurrency:
                key = pending.pop(0)
                task = asyncio.create_task(run_one(key))
                self._active.add(task)
            await asyncio.sleep(0.25)

    async def _run_mineru_job(self, path_key: str) -> None:
        async with self._claim_lock:
            entry = self.entries.get(path_key)
            if entry is None or entry.status != "PENDING":
                return

            fp = Path(entry.path)
            if not fp.is_file():
                entry.status = "FAILED"
                entry.error = "file missing"
                entry.updated = time.time()
                self._persist()
                return

            exe = shutil.which("mineru")
            if not exe:
                entry.status = "FAILED"
                entry.error = "mineru not found on PATH"
                entry.updated = time.time()
                self._persist()
                self._log(
                    "[red]ERROR:[/] `mineru` is not on PATH. Install MinerU or activate the correct venv.",
                )
                return

            run_dir = run_dir_for_file(self.output_dir, fp)
            try:
                run_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                entry.status = "FAILED"
                entry.error = str(exc)
                entry.updated = time.time()
                self._persist()
                return

            rel_run = str(run_dir.relative_to(self.output_dir))
            entry.status = "RUNNING"
            entry.run_dir = rel_run
            entry.error = None
            entry.updated = time.time()
            self._run_started[path_key] = time.monotonic()
            self._persist()

        short = _short_name(fp, max_len=16)
        self._log(f"[bold cyan][{short}][/] start")
        self._log(f"[dim][{short}][/] output: {run_dir}")

        cmd = [
            exe,
            "-p",
            str(fp),
            "-o",
            str(run_dir),
            "-b",
            self.backend,
        ]
        is_pdf = fp.suffix.lower() == ".pdf"
        if is_pdf and self.max_pages > 0:
            end_idx = pdf_end_page_for_cli(fp, self.max_pages)
            if end_idx is not None:
                cmd.extend(["-s", "0", "-e", str(end_idx)])
                self._log(f"[dim][{short}][/] pdf range: -s 0 -e {end_idx}")
        elif self.max_pages > 0 and not self._max_pages_note_logged:
            self._max_pages_note_logged = True
            self._log(
                "[dim]max-pages applies to PDFs only; skipping -s/-e for non-PDF inputs.[/]",
            )

        t0 = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except OSError as exc:
            entry.status = "FAILED"
            entry.error = str(exc)
            entry.duration_sec = time.monotonic() - t0
            entry.updated = time.time()
            self._run_started.pop(path_key, None)
            self._persist()
            self._log(f"[red][{short}][/] spawn failed: {exc}")
            return

        assert proc.stdout is not None
        while True:
            line_b = await proc.stdout.readline()
            if not line_b:
                break
            try:
                line = line_b.decode("utf-8", errors="replace").rstrip()
            except Exception:
                line = repr(line_b)
            done, total = metrics.parse_pages_from_log_line(line)
            if done is not None:
                entry.pages_done = done
            if total is not None:
                entry.pages_total = total
            if entry.pages_total is not None and entry.pages_done is not None:
                entry.pages_hint = f"{entry.pages_done}/{entry.pages_total}"
            self._persist()
            self._log(f"[{short}] {line}")

        rc = await proc.wait()
        elapsed = time.monotonic() - t0
        self._run_started.pop(path_key, None)
        entry.duration_sec = elapsed
        entry.updated = time.time()
        if rc == 0:
            entry.status = "DONE"
            entry.error = None
            if is_pdf and entry.pages_total is not None:
                entry.pages_done = entry.pages_total
            self._log(f"[green][{short}][/] done ({elapsed:.1f}s)")
        else:
            entry.status = "FAILED"
            entry.error = f"exit {rc}"
            self._log(f"[red][{short}][/] failed (exit {rc})")
        self._persist()
