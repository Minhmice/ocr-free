from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings
from app.services.job_store import JobStore
from app.services.safe_paths import safe_asset_path

router = APIRouter(prefix="/api", tags=["assets"])


@router.get("/jobs/{job_id}/assets/{asset_path:path}")
async def get_asset(job_id: str, asset_path: str) -> FileResponse:
    settings = get_settings()
    store = JobStore(settings.jobs_dir)
    job = store.load(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Job not found"}},
        )
    output_dir = Path(job.output_dir)
    path = safe_asset_path(output_dir, asset_path)
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Asset not found"}},
        )
    return FileResponse(path)
