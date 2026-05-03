import asyncio
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.services.job_store import JobStore


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def resolve_mineru_executable(env: dict[str, str]) -> str | None:
    """Return absolute path to mineru if found on PATH under env."""
    path = env.get("PATH", "")
    exe = shutil.which("mineru", path=path)
    return exe


def build_mineru_cmd(
    mineru_exe: str,
    input_path: Path,
    output_dir: Path,
    backend: str,
    *,
    max_pages: int | None,
    ocr_language: str,
    enable_table: bool,
    enable_formula: bool,
    force_ocr: bool,
) -> list[str]:
    cmd: list[str] = [
        mineru_exe,
        "-p",
        str(input_path),
        "-o",
        str(output_dir),
        "-b",
        backend,
        "-l",
        ocr_language,
        "-t",
        str(enable_table).lower(),
        "-f",
        str(enable_formula).lower(),
    ]
    method = "ocr" if force_ocr else "auto"
    cmd.extend(["-m", method])
    if max_pages is not None and max_pages > 0:
        end = max_pages - 1
        cmd.extend(["-s", "0", "-e", str(end)])
    return cmd


async def _drain_stream(
    stream: asyncio.StreamReader | None,
    job_id: str,
    store: JobStore,
    *,
    is_stderr: bool,
) -> None:
    """
    Read in chunks so we are not blocked on readline() when MinerU omits newlines for long periods.
    """

    def emit_line(raw: bytes) -> None:
        text = raw.replace(b"\r", b"").decode(errors="replace").strip()
        if not text:
            return
        if is_stderr:
            store.append_stderr(job_id, text)
        else:
            store.append_stdout(job_id, text)

    if stream is None:
        return
    buf = bytearray()
    while True:
        chunk = await stream.read(65536)
        if not chunk:
            break
        buf.extend(chunk)
        while b"\n" in buf:
            line, _, buf = buf.partition(b"\n")
            emit_line(line)

    if buf:
        emit_line(bytes(buf))


async def run_mineru_job(
    job_id: str,
    store: JobStore,
    cmd: list[str],
    env: dict[str, str],
) -> None:
    finished = _utcnow()

    try:
        store.patch(
            job_id,
            status="running",
            progress_message="Starting MinerU…",
            started_at=_utcnow(),
        )

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        assert proc.stdout is not None
        assert proc.stderr is not None

        await asyncio.gather(
            _drain_stream(proc.stdout, job_id, store, is_stderr=False),
            _drain_stream(proc.stderr, job_id, store, is_stderr=True),
        )

        exit_code = await proc.wait()
        finished = _utcnow()
        job = store.load(job_id)
        stderr_tail = job.stderr_tail if job else []

        if exit_code == 0:
            store.patch(
                job_id,
                status="succeeded",
                progress_message="Finished",
                finished_at=finished,
                exit_code=exit_code,
                error=None,
            )
        else:
            err_msg = "\n".join(stderr_tail[-20:]) if stderr_tail else f"Exit code {exit_code}"
            store.patch(
                job_id,
                status="failed",
                progress_message="MinerU failed",
                finished_at=finished,
                exit_code=exit_code,
                error=err_msg[:8000],
            )
    except FileNotFoundError as e:
        finished = _utcnow()
        msg = (
            f"Cannot start MinerU ({e}). Install MinerU in the same Python env as the API "
            f"(e.g. `apps/api/.venv/bin/pip install -e packages/mineru[all]`) and ensure "
            f"`mineru` is on PATH for that process. Current PATH begins with: "
            f"{env.get('PATH', '')[:200]!r}…"
        )
        store.patch(
            job_id,
            status="failed",
            progress_message="MinerU executable not found",
            finished_at=finished,
            exit_code=-1,
            error=msg[:8000],
        )
    except Exception as e:  # noqa: BLE001 — surface any runner crash to the job record
        finished = _utcnow()
        msg = f"{type(e).__name__}: {e}"
        store.patch(
            job_id,
            status="failed",
            progress_message="MinerU runner error",
            finished_at=finished,
            exit_code=-1,
            error=msg[:8000],
        )


def mineru_process_env(repo_root: Path, hf_home: Path, xdg_cache: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HF_HOME"] = str(hf_home)
    env["XDG_CACHE_HOME"] = str(xdg_cache)
    env.setdefault("PYTHONUNBUFFERED", "1")
    # Subprocess inherits parent PATH (often npm/pnpm node paths). Prepend the venv bin dir
    # for this interpreter so `mineru` installed next to `python` is always discoverable.
    bindir = Path(sys.executable).resolve().parent
    if bindir.is_dir():
        prefix = str(bindir)
        path = env.get("PATH", "")
        if not path.startswith(prefix):
            env["PATH"] = f"{prefix}{os.pathsep}{path}"
    return env


def spawn_mineru_task(
    job_id: str,
    store: JobStore,
    cmd: list[str],
    env: dict[str, str],
) -> asyncio.Task[None]:
    return asyncio.create_task(run_mineru_job(job_id, store, cmd, env))
