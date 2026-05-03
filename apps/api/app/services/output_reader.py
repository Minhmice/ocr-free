import json
import re
from pathlib import Path
from typing import Any

from app.models import AssetRef, ResultPayload

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def _first_markdown_file(root: Path) -> Path | None:
    md_files = sorted(root.rglob("*.md"))
    return md_files[0] if md_files else None


def _collect_json_files(root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for p in sorted(root.rglob("*.json")):
        rel = p.relative_to(root).as_posix()
        try:
            with p.open("r", encoding="utf-8") as f:
                out[rel] = json.load(f)
        except (json.JSONDecodeError, OSError):
            out[rel] = {"_parseError": True, "_path": rel}
    return out


def _collect_images(root: Path, job_id: str) -> list[AssetRef]:
    refs: list[AssetRef] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in IMAGE_EXT:
            continue
        rel = p.relative_to(root).as_posix()
        url = f"/api/jobs/{job_id}/assets/{rel}"
        refs.append(AssetRef(path=rel, url=url))
    return sorted(refs, key=lambda a: a.path)


_MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def rewrite_markdown_assets(md: str, job_id: str) -> str:
    def repl(m: re.Match[str]) -> str:
        alt, target = m.group(1), m.group(2).strip()
        if target.startswith(("http://", "https://", "data:")):
            return m.group(0)
        if target.startswith("/"):
            return m.group(0)
        clean = target.split("?", 1)[0].split("#", 1)[0]
        rel = clean.lstrip("./")
        new_url = f"/api/jobs/{job_id}/assets/{rel}"
        return f"![{alt}]({new_url})"

    return _MD_IMG_RE.sub(repl, md)


def build_result_payload(output_dir: Path, job_id: str) -> ResultPayload:
    root = output_dir.resolve()
    md_path = _first_markdown_file(root)
    plain = ""
    if md_path and md_path.is_file():
        plain = md_path.read_text(encoding="utf-8", errors="replace")
    rendered = rewrite_markdown_assets(plain, job_id)

    json_payload: Any = _collect_json_files(root)
    if len(json_payload) == 0:
        json_payload = {}
    elif len(json_payload) == 1:
        json_payload = next(iter(json_payload.values()))

    assets = _collect_images(root, job_id)
    download_url = f"/api/jobs/{job_id}/download"

    return ResultPayload(
        markdown=rendered,
        markdownPlain=plain,
        json=json_payload,
        assets=assets,
        downloadUrl=download_url,
    )
