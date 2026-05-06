# Technology Stack

**Analysis Date:** 2026-05-06

## Languages

**Primary:**
- Python 3.10-3.13 - Core runtime for CLI, API server, router, and parsing pipelines in `mineru/`.

**Secondary:**
- Shell/Docker config - Deployment/runtime packaging in `docker/` and GitHub workflows in `.github/workflows/`.

## Runtime

**Environment:**
- CPython 3.10-3.13 (`requires-python = ">=3.10,<3.14"` in `pyproject.toml`).

**Package Manager:**
- `pip`/`uv` with PEP 621 metadata in `pyproject.toml`.
- Lockfile: missing (no `poetry.lock`, `uv.lock`, or `requirements.lock`).

## Frameworks

**Core:**
- FastAPI - HTTP parsing API implementation in `mineru/cli/fast_api.py`.
- Click - CLI command surface in `mineru/cli/client.py`, `mineru/cli/router.py`, `mineru/cli/vlm_server.py`.
- Uvicorn - ASGI server runtime for API and router from `pyproject.toml` scripts.

**Testing:**
- Pytest + Coverage - configured under `[tool.pytest.ini_options]` and `[tool.coverage.*]` in `pyproject.toml`.

**Build/Dev:**
- Setuptools/wheel - packaging backend in `[build-system]` in `pyproject.toml`.
- MkDocs - documentation site config in `mkdocs.yml` and `docs/`.

## Key Dependencies

**Critical:**
- `pdfminer.six`, `pypdfium2`, `pypdf`, `pdftext` - PDF parsing/extraction core.
- `openai` - OpenAI-compatible VLM server/client integration path.
- `transformers`, `torch`, `onnxruntime` (optional sets) - model inference backends.
- `python-docx`, `pypptx-with-oxml`, `openpyxl`, `pandas` - Office format parsing.

**Infrastructure:**
- `httpx` + `requests` - API client and HTTP IO.
- `boto3` - S3 reader/writer implementation in `mineru/data/io/s3.py` and `mineru/data/data_reader_writer/s3.py`.
- `loguru` - structured runtime logging used across CLI/API modules.

## Configuration

**Environment:**
- Runtime flags are read from env vars in `mineru/utils/config_reader.py`, `mineru/cli/fast_api.py`, and `mineru/cli/router.py`.
- Persistent config file is `~/mineru.json` by default (`MINERU_TOOLS_CONFIG_JSON` override) in `mineru/utils/config_reader.py`.

**Build:**
- Package metadata and entrypoints in `pyproject.toml`.
- Container builds in `docker/global/Dockerfile` and `docker/china/*.Dockerfile`.

## Platform Requirements

**Development:**
- Python 3.10-3.13 and pip/uv; optional GPU/MPS/NPU stacks selected at runtime by `get_device()` in `mineru/utils/config_reader.py`.

**Production:**
- Local CLI mode, FastAPI service mode (`mineru-api`), and routed multi-worker mode (`mineru-router`) from scripts in `pyproject.toml`.

---

*Stack analysis: 2026-05-06*
