import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models import JobRecord, JobStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobStore:
    def __init__(self, jobs_dir: Path) -> None:
        self.jobs_dir = jobs_dir
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def save(self, job: JobRecord) -> None:
        job.updated_at = _utcnow()
        path = self._path(job.job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = job.model_dump(mode="json")
        fd, tmp = tempfile.mkstemp(
            dir=str(path.parent), prefix=f".{job.job_id}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def load(self, job_id: str) -> JobRecord | None:
        path = self._path(job_id)
        if not path.is_file():
            return None
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return JobRecord.model_validate(raw)

    def list_all(self) -> list[JobRecord]:
        out: list[JobRecord] = []
        for p in sorted(self.jobs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with p.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                out.append(JobRecord.model_validate(raw))
            except (json.JSONDecodeError, OSError, ValueError):
                continue
        out.sort(key=lambda j: j.created_at, reverse=True)
        return out

    def create(
        self,
        job_id: str,
        original_file_name: str,
        stored_input_path: Path,
        output_dir: Path,
        backend: str,
        options: dict[str, Any],
    ) -> JobRecord:
        now = _utcnow()
        job = JobRecord(
            job_id=job_id,
            original_file_name=original_file_name,
            stored_input_path=str(stored_input_path),
            output_dir=str(output_dir),
            backend=backend,
            options=options,
            status="queued",
            progress_message="Queued",
            created_at=now,
            updated_at=now,
        )
        self.save(job)
        return job

    def patch(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        progress_message: str | None = None,
        stdout_tail: list[str] | None = None,
        stderr_tail: list[str] | None = None,
        error: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        exit_code: int | None = None,
    ) -> JobRecord | None:
        job = self.load(job_id)
        if job is None:
            return None
        if status is not None:
            job.status = status
        if progress_message is not None:
            job.progress_message = progress_message
        if stdout_tail is not None:
            job.stdout_tail = stdout_tail[-100:]
        if stderr_tail is not None:
            job.stderr_tail = stderr_tail[-100:]
        if error is not None:
            job.error = error
        if started_at is not None:
            job.started_at = started_at
        if finished_at is not None:
            job.finished_at = finished_at
        if exit_code is not None:
            job.exit_code = exit_code
        self.save(job)
        return job

    def append_stdout(self, job_id: str, line: str) -> None:
        job = self.load(job_id)
        if job is None:
            return
        tail = job.stdout_tail + [line]
        job.stdout_tail = tail[-100:]
        job.progress_message = line[:500] if line else job.progress_message
        self.save(job)

    def append_stderr(self, job_id: str, line: str) -> None:
        job = self.load(job_id)
        if job is None:
            return
        tail = job.stderr_tail + [line]
        job.stderr_tail = tail[-100:]
        self.save(job)
