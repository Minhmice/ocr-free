# Architecture

**Analysis Date:** 2026-05-06

## Pattern Overview

**Overall:** Layered parsing platform with orchestrator frontends and pluggable backend engines.

**Key Characteristics:**
- CLI/API/router entrypoints route to shared parse workflows.
- Engine-specific backend modules (`pipeline`, `vlm`, `hybrid`, `office`) normalize output into middle JSON and markdown content.
- IO abstractions separate local files, HTTP, and S3 object access.

## Layers

**Entry/Interface Layer:**
- Purpose: expose user interfaces for parsing.
- Location: `mineru/cli/`
- Contains: Click commands, FastAPI app, router/proxy, local API client.
- Depends on: backend analyzers, config reader, output helpers.
- Used by: end users (`mineru`), service clients (`mineru-api`, `mineru-router`).

**Backend Orchestration Layer:**
- Purpose: dispatch document types and engines into concrete analyze pipelines.
- Location: `mineru/backend/`
- Contains: `pipeline_analyze.py`, `vlm_analyze.py`, `hybrid_analyze.py`, office analyzers.
- Depends on: `mineru/model/`, `mineru/utils/`, conversion/middle-json helpers.
- Used by: CLI common parse functions and API task workers.

**Model Layer:**
- Purpose: inference and conversion logic for OCR, layout, table, formula, and office formats.
- Location: `mineru/model/`
- Contains: OCR/model wrappers, VLM servers, DOCX/PPTX/XLSX converters, table/formula models.
- Depends on: torch/transformers/onnxruntime/paddle-compatible utilities.
- Used by: backend layer.

**Data & IO Layer:**
- Purpose: abstract reading/writing from filesystem, HTTP, and S3.
- Location: `mineru/data/`
- Contains: reader/writer base classes and implementations.
- Depends on: `requests`, `boto3`.
- Used by: parse workflows and integrations.

**Utility Layer:**
- Purpose: cross-cutting helpers for config, device selection, PDF/image ops, parsing utilities.
- Location: `mineru/utils/` and `mineru/backend/utils/`
- Contains: env/config readers, PDF helpers, formatting/cleanup tools.
- Depends on: standard library and core dependencies.
- Used by: all upper layers.

## Data Flow

**CLI/API Parse Flow:**

1. Request enters via `mineru/cli/client.py` or `mineru/cli/fast_api.py`.
2. Input documents are normalized, split, and scheduled; backend and parse method are resolved.
3. Backend analyzer (`mineru/backend/*/*_analyze.py`) invokes model layer and emits intermediate/middle JSON.
4. Middle JSON is transformed into markdown/content outputs (`*_middle_json_mkcontent.py`) and written to output directories.

**State Management:**
- API and router keep in-memory task records (`AsyncParseTask`/`RouterTaskRecord`) with periodic cleanup in `mineru/cli/fast_api.py` and `mineru/cli/router.py`.

## Key Abstractions

**Task-Oriented Parsing:**
- Purpose: process one or more input files as units with status progression.
- Examples: `PlannedTask` in `mineru/cli/client.py`, `AsyncParseTask` in `mineru/cli/fast_api.py`.
- Pattern: dataclass-based task state with pending/processing/completed/failed transitions.

**Reader/Writer Interfaces:**
- Purpose: decouple storage backends.
- Examples: `mineru/data/io/base.py`, `mineru/data/io/http.py`, `mineru/data/io/s3.py`.
- Pattern: interface + concrete adapters.

## Entry Points

**CLI Main:**
- Location: `mineru/cli/client.py`
- Triggers: `mineru` script from `pyproject.toml`.
- Responsibilities: local/remote parse orchestration, batch control, visualization hooks.

**API Service:**
- Location: `mineru/cli/fast_api.py`
- Triggers: `mineru-api` script.
- Responsibilities: synchronous/asynchronous parse endpoints, task lifecycle, file/result serving.

**Router Service:**
- Location: `mineru/cli/router.py`
- Triggers: `mineru-router` script.
- Responsibilities: upstream worker pool selection, retries, load-balanced task proxying.

## Error Handling

**Strategy:** Explicit HTTP exceptions in APIs plus logged warnings/errors in workers/CLI.

**Patterns:**
- API validation and `HTTPException` returns in `mineru/cli/fast_api.py`.
- Retry and upstream failure counters in `mineru/cli/router.py`.

## Cross-Cutting Concerns

**Logging:** `loguru` setup in CLI/API/router entry modules.
**Validation:** Upload suffix and parse-method checks in `mineru/cli/common.py` and `mineru/cli/fast_api.py`.
**Authentication:** No built-in user auth; network exposure controls through public-bind policy env flags in `mineru/cli/public_http_client_policy.py`.

---

*Architecture analysis: 2026-05-06*
