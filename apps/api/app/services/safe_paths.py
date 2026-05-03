import re
import uuid
from pathlib import Path

from fastapi import HTTPException

ALLOWED_UPLOAD_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".svg",
        ".docx",
        ".pptx",
        ".xlsx",
    }
)


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^\w.\-]", "_", base, flags=re.UNICODE)
    if not base or base.strip(".") == "":
        base = "upload.bin"
    return base[:255]


def validate_upload_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_EXTENSION",
                    "message": f"Unsupported file type: {ext or '(none)'}",
                }
            },
        )
    return ext


def safe_asset_path(output_dir: Path, rel: str) -> Path:
    rel = rel.replace("\\", "/").lstrip("/")
    if ".." in rel.split("/"):
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "PATH_TRAVERSAL", "message": "Invalid path"}},
        )
    out = output_dir.resolve()
    candidate = (out / rel).resolve()
    try:
        candidate.relative_to(out)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "PATH_ESCAPE", "message": "Path outside output"}},
        ) from None
    return candidate


def new_job_id() -> str:
    return str(uuid.uuid4())
