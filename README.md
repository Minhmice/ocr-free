# ocr-free — MinerU (PDF / Office / images → Markdown & JSON)

This repository wraps **[MinerU](https://github.com/opendatalab/MinerU)** for local document parsing: **Gradio WebUI**, **FastAPI**, optional **Docker Compose**, and a small **terminal UI (TUI)** for batch CLI runs.

---

## Requirements (quick)

- **Python 3.10–3.12** is the safe baseline everywhere (especially **Windows**).
- **Python 3.13**: usable on many Linux/macOS setups for `mineru[core]`; on **Windows amd64** avoid dependency sets that pull **`lmdeploy` → `ray`** (see below).
- **Docker Desktop** (optional) for the Compose path.

---

## Windows: do **not** default to `mineru[all]`

The upstream extra **`mineru[all]`** includes **`mineru[lmdeploy]` on Windows** (`mineru/pyproject.toml`). That pulls **`ray`**, which **does not ship wheels for Python 3.13 on `win_amd64`**, so installs fail or become fragile.

**Recommended on Windows:**

1. Use **Python 3.10–3.12** (e.g. from [python.org](https://www.python.org/downloads/) or `py -3.12`).
2. Install **`mineru[core]`** (Gradio + pipeline/VLM stack) instead of `[all]` unless you know you need an extra backend.
3. Prefer **`uv`** (or `pip`) in a **clean venv**.

Example (PowerShell, from repo root):

```powershell
cd .\mineru
py -3.12 -m venv ..\.venv-mineru
..\.venv-mineru\Scripts\Activate.ps1
python -m pip install -U pip uv
uv pip install -e ".[core]"
```

Then `mineru`, `mineru-gradio`, and `mineru-api` should be on `PATH` inside that venv.

---

## Install paths (native)

### Editable install from `mineru/`

```bash
cd mineru
python -m pip install -U pip
pip install uv
uv pip install -e ".[core]"
```

Use **`".[all]"` only when you understand the extras** (platform-conditional `vllm` / `lmdeploy` / `mlx`).

### Run Gradio WebUI

Default: starts a local API if you omit `--api-url`.

```bash
mineru-gradio --server-name 0.0.0.0 --server-port 7860
```

- Browser: `http://127.0.0.1:7860`
- LAN: use the host IP instead of `127.0.0.1` (see `docs/AGENT_PORT_FORWARDING.md`).

### Run FastAPI

```bash
mineru-api --host 0.0.0.0 --port 8000
```

- OpenAPI: `http://127.0.0.1:8000/docs`

### Output directory

- Env: **`MINERU_API_OUTPUT_ROOT`** (default `./output` relative to the process working directory unless set).
- In Docker, bind-mount a host folder and point `MINERU_API_OUTPUT_ROOT` at the in-container path (see Compose below).

---

## Docker Compose

### Root `compose.yaml` (recommended)

From **repository root**:

```bash
docker compose -f compose.yaml up --build
```

- **Gradio** container `mineru-gradio` → `http://127.0.0.1:7860`
- **API** (optional profile):  
  `docker compose -f compose.yaml --profile api up --build` → `http://127.0.0.1:8000`

Stop:

```bash
docker compose -f compose.yaml down
```

Services use image **`mineru:local`** built from `mineru/docker/global/Dockerfile`, bind-mount `./output` → `/output`, and set `MINERU_API_OUTPUT_ROOT=/output`.

### Legacy upstream compose: `mineru/docker/compose.yaml`

- Assumes an existing **`mineru:latest`** image (no `build:` stanza in that file).
- Example:

```bash
docker compose -f mineru/docker/compose.yaml --profile gradio up -d
docker compose -f mineru/docker/compose.yaml --profile api up -d
```

Use **root `compose.yaml`** when you want a reproducible local build from this repo.

---

## Reverse proxy / CORS (FastAPI)

These are **implemented** in `mineru/mineru/cli/fast_api.py`:

| Environment variable | Role |
|----------------------|------|
| `MINERU_API_ROOT_PATH` | `root_path` when served under a sub-path behind a proxy. |
| `MINERU_API_CORS_ALLOW_ORIGINS` | Comma-separated list; if set, enables `CORSMiddleware`. |
| `MINERU_API_TRUST_PROXY_HEADERS` | Enables Uvicorn `proxy_headers` + `forwarded_allow_ips` handling. |
| `MINERU_API_FORWARDED_ALLOW_IPS` | Trusted IPs for forwarded headers (default `127.0.0.1`). |

Enable **`MINERU_API_TRUST_PROXY_HEADERS` only behind a trusted reverse proxy** you control.

Gradio reads **`MINERU_API_TRUST_PROXY_HEADERS`** as well (`mineru/mineru/cli/gradio_app.py`) for spawned/local API scenarios.

---

## Batch terminal UI (`tools/mineru-tui`)

Python **Textual** UI that:

- Recursively scans an **input** directory for PDFs, images, and office files.
- Persists a resumable queue at **`<output>/.mineru-tui/queue.json`** (migrates legacy `<output>/queue_state.json` once).
- Runs **`mineru -p … -o … -b …`** as subprocesses (default backend **`pipeline`**; override with `-b`).
- Shows host metrics, Docker CPU for a named container (default **`mineru-gradio`**), queue counts, and a live log.

### One-liners (install + run)

**Windows (PowerShell)** — prefers `py -3.12` / `3.11` / `3.10` for the venv:

```powershell
Set-Location ~\Documents\projects\ocr-free; .\scripts\run-mineru-tui.ps1
```

**macOS / Linux (bash)**:

```bash
cd ~/path/to/ocr-free && chmod +x scripts/run-mineru-tui.sh && ./scripts/run-mineru-tui.sh
```

**Manual** (any OS, from repo root):

```bash
python3.12 -m venv .venv-mineru-tui
.venv-mineru-tui/bin/python -m pip install -U pip
.venv-mineru-tui/bin/python -m pip install -e ./tools/mineru-tui
.venv-mineru-tui/bin/mineru-tui -i ./input -o ./output
```

CLI flags: `mineru-tui -h`. Useful env vars: `MINERU_TUI_INPUT_DIR`, `MINERU_TUI_OUTPUT_DIR`, `MINERU_TUI_BACKEND`, `MINERU_TUI_MAX_PAGES`, `MINERU_TUI_CONCURRENCY`, `MINERU_TUI_CONTAINER`.

**PDF page cap:** `--max-pages N` maps to `mineru -s 0 -e …` when page count is known (`pypdf`). If the PDF page count cannot be read, the TUI falls back to `-e (N-1)` and may not match true length — see CLI help. **`--max-pages 0`** means full document (no `-s/-e`).

---

## Security note (SSRF)

`mineru-api` supports **`--allow-public-http-client`**. Keep it **disabled** unless required: with public bind addresses, it can increase **SSRF** risk for `*-http-client` backends. See upstream docs and `docs/AGENT_PORT_FORWARDING.md`.

---

## Tiếng Việt (tóm tắt thao tác)

- **Windows:** tránh mặc định `mineru[all]`; dùng **Python 3.10–3.12** + **`mineru[core]`** hoặc Docker.
- **Chạy nhanh WebUI:** `mineru-gradio --server-name 0.0.0.0 --server-port 7860`
- **Docker (khuyến nghị):** từ root repo: `docker compose -f compose.yaml up --build`
- **TUI xử lý hàng loạt:** `.\scripts\run-mineru-tui.ps1` hoặc `./scripts/run-mineru-tui.sh`
- **Mở cổng LAN / firewall:** xem `docs/AGENT_PORT_FORWARDING.md`

---

## Reference

- Upstream usage: `mineru/docs/en/usage/quick_usage.md`
- Port forwarding / proxies: `docs/AGENT_PORT_FORWARDING.md`
