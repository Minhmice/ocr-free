# External Integrations

**Analysis Date:** 2026-05-06

## APIs & External Services

**Model and AI Services:**
- OpenAI-compatible model servers - remote VLM parsing endpoint support.
  - SDK/Client: `openai`, `httpx`
  - Auth: service-side key/env handled by upstream OpenAI-compatible endpoint; MinerU references `server_url` parameters in `mineru/cli/fast_api.py`.
- Local vLLM / LMDeploy model serving - internal server modes.
  - SDK/Client: CLI scripts `mineru-vllm-server`, `mineru-lmdeploy-server`, `mineru-openai-server` in `pyproject.toml`
  - Auth: Not required for local process mode.

**HTTP File Integrations:**
- Generic HTTP source/sink - read/write binary documents over HTTP.
  - SDK/Client: `requests` in `mineru/data/io/http.py`
  - Auth: Not built into `HttpReader`/`HttpWriter`; caller-managed.

## Data Storage

**Databases:**
- Not detected.

**File Storage:**
- Local filesystem as default output/input paths (`./output` defaults in `mineru/cli/fast_api.py`).
- S3-compatible object storage via `boto3` in `mineru/data/io/s3.py` and `mineru/data/data_reader_writer/s3.py`.

**Caching:**
- In-process memory caches for model/runtime objects (for example VLM preload and cached model shutdown paths in `mineru/cli/fast_api.py`); no dedicated Redis/Memcached.

## Authentication & Identity

**Auth Provider:**
- Custom/no first-party identity layer in API/router endpoints.
  - Implementation: request validation focuses on public-bind safety policy in `mineru/cli/public_http_client_policy.py` and bind checks in `mineru/cli/fast_api.py`/`mineru/cli/router.py`.

## Monitoring & Observability

**Error Tracking:**
- None detected (no Sentry/NewRelic SDK in project metadata).

**Logs:**
- `loguru` logs to stderr in `mineru/cli/client.py`, `mineru/cli/fast_api.py`, and `mineru/cli/router.py`.

## CI/CD & Deployment

**Hosting:**
- Self-hosted runtime via Python process or Docker (`docker/compose.yaml`, `docker/global/Dockerfile`, `docker/china/*.Dockerfile`).

**CI Pipeline:**
- GitHub Actions workflows in `.github/workflows/` (`python-package.yml`, `cli.yml`, `mkdocs.yml`, `cla.yml`).

## Environment Configuration

**Required env vars:**
- `MINERU_LOG_LEVEL`
- `MINERU_DEVICE_MODE`
- `MINERU_TOOLS_CONFIG_JSON`
- `MINERU_API_MAX_CONCURRENT_REQUESTS`
- `MINERU_PROCESSING_WINDOW_SIZE`
- `MINERU_API_PUBLIC_BIND_EXPOSED`
- `MINERU_API_ALLOW_PUBLIC_HTTP_CLIENT`
- `MINERU_ROUTER_PUBLIC_BIND_EXPOSED`
- `MINERU_ROUTER_ALLOW_PUBLIC_HTTP_CLIENT`

**Secrets location:**
- `~/mineru.json` bucket credentials (`bucket_info`) read by `get_s3_config()` in `mineru/utils/config_reader.py`.

## Webhooks & Callbacks

**Incoming:**
- API endpoints include synchronous and async task endpoints in `mineru/cli/fast_api.py` (for example `/file_parse`, `/tasks`, status/result URLs).

**Outgoing:**
- Router forwards requests to upstream MinerU API workers using `httpx` in `mineru/cli/router.py`.

---

*Integration audit: 2026-05-06*
