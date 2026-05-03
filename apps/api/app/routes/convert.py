import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.models import ConvertResponse
from app.services.job_store import JobStore
from app.services.mineru_runner import (
    build_mineru_cmd,
    mineru_process_env,
    resolve_mineru_executable,
    spawn_mineru_task,
)
from app.services.safe_paths import new_job_id, sanitize_filename, validate_upload_extension

router = APIRouter(prefix="/api", tags=["convert"])


def _find_mineru_source_dir(repo_root: Path) -> Path | None:
    """README layout packages/mineru, or legacy apps/api/packages/mineru."""
    for d in (
        repo_root / "packages" / "mineru",
        repo_root / "apps" / "api" / "packages" / "mineru",
    ):
        if (d / "pyproject.toml").is_file() or (d / "setup.py").is_file():
            return d
    return None


def _parse_optional_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if s == "":
        return None
    try:
        v = int(s)
        return v if v > 0 else None
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_MAX_PAGES", "message": "maxPages must be an integer"}},
        ) from None


def _parse_bool(raw: str | None, default: bool) -> bool:
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


ALLOWED_BACKENDS = frozenset({"pipeline", "vlm-auto-engine", "hybrid-auto-engine"})

# MinerU CLI `-l` choices (must stay in sync with apps/web/lib/ocrLanguages.ts)
ALLOWED_OCR_LANG = frozenset(
    {
        "ch",
        "ch_lite",
        "ch_server",
        "en",
        "korean",
        "japan",
        "chinese_cht",
        "ta",
        "te",
        "ka",
        "th",
        "el",
        "latin",
        "arabic",
        "east_slavic",
        "cyrillic",
        "devanagari",
    }
)


@router.post("/convert")
async def convert(
    file: UploadFile = File(...),
    backend: str = Form("pipeline"),
    maxPages: str = Form(""),
    ocrLanguage: str = Form("ch"),
    enableTableRecognition: str = Form("true"),
    enableFormulaRecognition: str = Form("true"),
    forceOcr: str = Form("false"),
) -> ConvertResponse:
    settings = get_settings()
    if backend not in ALLOWED_BACKENDS:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_BACKEND", "message": f"Unknown backend: {backend}"}},
        )

    if ocrLanguage not in ALLOWED_OCR_LANG:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_OCR_LANGUAGE",
                    "message": f"Unsupported OCR language: {ocrLanguage}",
                }
            },
        )

    filename = sanitize_filename(file.filename or "upload.bin")
    validate_upload_extension(filename)

    max_pages = _parse_optional_int(maxPages)
    enable_table = _parse_bool(enableTableRecognition, True)
    enable_formula = _parse_bool(enableFormulaRecognition, True)
    force_ocr = _parse_bool(forceOcr, False)

    env = mineru_process_env(settings.repo_root, settings.hf_home, settings.xdg_cache_home)
    mineru_exe = resolve_mineru_executable(env)
    if mineru_exe is None:
        found_src = _find_mineru_source_dir(settings.repo_root)
        if not found_src:
            msg = (
                "MinerU is not in this repository: expected packages/mineru (see README) "
                "or apps/api/packages/mineru with pyproject.toml. Clone MinerU, then "
                "pnpm setup:mineru or restart pnpm dev."
            )
        else:
            try:
                rel = found_src.relative_to(settings.repo_root).as_posix()
            except ValueError:
                rel = str(found_src)
            msg = (
                f"MinerU source exists at {rel} but the mineru CLI is not installed "
                "in apps/api/.venv. From the repo root run: pnpm setup:mineru"
            )
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "MINERU_CLI_MISSING", "message": msg}},
        )

    job_id = new_job_id()
    store = JobStore(settings.jobs_dir)

    uploads = settings.uploads_dir / job_id
    uploads.mkdir(parents=True, exist_ok=True)
    dest = uploads / filename

    size = 0
    max_bytes = settings.max_upload_mb * 1024 * 1024
    with dest.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                shutil.rmtree(uploads, ignore_errors=True)
                raise HTTPException(
                    status_code=413,
                    detail={
                        "error": {
                            "code": "FILE_TOO_LARGE",
                            "message": f"Max upload size is {settings.max_upload_mb} MB",
                        }
                    },
                )
            out.write(chunk)

    output_dir = settings.outputs_dir / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    options = {
        "maxPages": max_pages,
        "ocrLanguage": ocrLanguage,
        "enableTableRecognition": enable_table,
        "enableFormulaRecognition": enable_formula,
        "forceOcr": force_ocr,
    }
    store.create(
        job_id,
        filename,
        dest,
        output_dir,
        backend,
        options,
    )

    cmd = build_mineru_cmd(
        mineru_exe,
        dest,
        output_dir,
        backend,
        max_pages=max_pages,
        ocr_language=ocrLanguage,
        enable_table=enable_table,
        enable_formula=enable_formula,
        force_ocr=force_ocr,
    )
    spawn_mineru_task(job_id, store, cmd, env)

    return ConvertResponse(jobId=job_id)
