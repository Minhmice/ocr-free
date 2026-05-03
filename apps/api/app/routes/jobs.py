import asyncio
import json
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.config import get_settings
from app.models import JobPublic, JobRecord
from app.services.job_store import JobStore
from app.services.output_reader import build_result_payload

router = APIRouter(prefix="/api", tags=["jobs"])


def _to_public(job: JobRecord) -> JobPublic:
    return JobPublic(
        jobId=job.job_id,
        fileName=job.original_file_name,
        status=job.status,
        backend=job.backend,
        createdAt=job.created_at.isoformat(),
        updatedAt=job.updated_at.isoformat(),
        progressMessage=job.progress_message,
        stdoutTail=job.stdout_tail,
        stderrTail=job.stderr_tail,
        error=job.error,
    )


@router.get("/jobs")
async def list_jobs() -> list[dict]:
    settings = get_settings()
    store = JobStore(settings.jobs_dir)
    jobs = store.list_all()
    return [j.model_dump(by_alias=True, mode="json") for j in (_to_public(x) for x in jobs)]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    settings = get_settings()
    store = JobStore(settings.jobs_dir)
    job = store.load(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Job not found"}},
        )
    return _to_public(job).model_dump(by_alias=True, mode="json")


@router.get("/jobs/{job_id}/events")
async def job_events(job_id: str) -> StreamingResponse:
    settings = get_settings()
    store = JobStore(settings.jobs_dir)

    async def gen():
        last: str | None = None
        while True:
            job = store.load(job_id)
            if job is None:
                payload = json.dumps(
                    {"error": {"code": "NOT_FOUND", "message": "Job not found"}},
                )
                yield f"event: job\ndata: {payload}\n\n"
                return
            public = _to_public(job)
            blob = json.dumps(public.model_dump(by_alias=True, mode="json"))
            if blob != last:
                last = blob
                yield f"event: job\ndata: {blob}\n\n"
            if job.status in ("succeeded", "failed", "cancelled"):
                return
            await asyncio.sleep(0.35)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/jobs/{job_id}/result")
async def job_result(job_id: str) -> dict:
    settings = get_settings()
    store = JobStore(settings.jobs_dir)
    job = store.load(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Job not found"}},
        )
    if job.status != "succeeded":
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "NOT_READY",
                    "message": f"Job is {job.status}; result available when succeeded",
                }
            },
        )
    out = Path(job.output_dir)
    payload = build_result_payload(out, job_id)
    return payload.model_dump(by_alias=True, mode="json")


def _find_existing_zip(output_dir: Path) -> Path | None:
    zips = sorted(output_dir.rglob("*.zip"))
    return zips[0] if zips else None


def _make_zip(output_dir: Path) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, prefix="mineru-out-", suffix=".zip")
    tmp.close()
    path = Path(tmp.name)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(output_dir.rglob("*")):
            if p.is_file():
                arc = p.relative_to(output_dir)
                zf.write(p, arc.as_posix())
    return path


@router.get("/jobs/{job_id}/download")
async def download_job(job_id: str) -> FileResponse:
    settings = get_settings()
    store = JobStore(settings.jobs_dir)
    job = store.load(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Job not found"}},
        )
    out = Path(job.output_dir)
    if not out.is_dir():
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NO_OUTPUT", "message": "Output directory missing"}},
        )

    existing = _find_existing_zip(out)
    if existing and existing.is_file():
        return FileResponse(
            existing,
            filename=f"{job_id}_result.zip",
            media_type="application/zip",
        )

    zpath = _make_zip(out)
    return FileResponse(
        zpath,
        filename=f"{job_id}_result.zip",
        media_type="application/zip",
        background=None,
    )
