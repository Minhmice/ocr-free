# MinerU local document extraction

Next.js + FastAPI wrapper around the **MinerU CLI** (`mineru`) with file-based jobs, SSE progress, and result inspection (Markdown, JSON, assets, ZIP download). Uploads, outputs, jobs, and model caches live under `data/` in the repository.

## Prerequisites

- **Python 3.12** (recommended) or **3.13**. Python 3.14 may not have wheels for all dependencies yet; use 3.12 if installs fail.
- [**uv**](https://docs.astral.sh/uv/) (recommended) or `pip` + `venv`
- **Node.js** 20+
- **pnpm** 9+

## 1. Install MinerU from source (editable)

```bash
mkdir -p packages
git clone https://github.com/opendatalab/MinerU.git packages/mineru
cd packages/mineru
uv pip install -e ".[all]"
# or: pip install -e ".[all]"
```

Confirm the CLI is on your `PATH`:

```bash
mineru --help
```

## 2. Install app dependencies

From the **repository root**:

```bash
pnpm install
pnpm setup:web
pnpm setup:api
```

`setup:api` runs `cd apps/api && uv pip install -e .` — install in the same environment where you installed MinerU so `mineru` is available to the API process. Alternatively, activate your MinerU venv first, then run `uv pip install -e apps/api` from the repo root.

## 3. Run

```bash
pnpm dev
```

- **Web UI:** [http://localhost:3000](http://localhost:3000)  
- **API:** [http://localhost:8000](http://localhost:8000) (proxied through Next.js route handlers at `/api/...`)

Optional: point the web app at a different API base (e.g. remote):

```bash
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## 4. Test flow

1. Open the web UI.
2. Upload a PDF (or supported image / DOCX / PPTX / XLSX).
3. Choose backend **`pipeline`** (default in UI; CPU-friendly).
4. Click **Convert**.
5. Watch status via SSE; when **succeeded**, review Preview / Markdown / JSON / Assets and use **Download ZIP**.

## Project layout

| Path | Purpose |
|------|---------|
| `apps/web` | Next.js App Router UI + BFF proxies under `app/api/*` |
| `apps/api` | FastAPI app (`mineru` subprocess, job store, SSE, assets) |
| `data/uploads` | Stored uploads per job |
| `data/outputs` | MinerU output per job |
| `data/jobs` | JSON job records (`{jobId}.json`) |
| `data/models/huggingface` | `HF_HOME` for model downloads |
| `data/models/cache` | `XDG_CACHE_HOME` |

## Environment (API)

| Variable | Description |
|----------|-------------|
| `MINERU_API_DATA_DIR` | Override `data/` directory (absolute path recommended) |
| `MINERU_API_MAX_UPLOAD_MB` | Max upload size in MB (default `512`) |
| `MINERU_API_CORS_ORIGINS` | JSON list of allowed origins (default includes `http://localhost:3000`) |

## Troubleshooting

### `mineru` command not found

Install MinerU in the **same** Python environment that runs `uvicorn`, or activate that venv before `pnpm dev:api`. Ensure `which mineru` resolves when the shell that starts the API is the same one you use for MinerU.

### Model download is slow

First runs download models into `data/models/huggingface` and `data/models/cache`. Use a stable network; disk space must be sufficient.

### No Markdown in results

MinerU layout varies by version. This app picks the **first** `*.md` file under the job output directory. If none exist, Preview/Markdown may be empty — inspect `data/outputs/<jobId>/` and stderr in the UI.

### Permission errors under `data/`

Ensure the user running the API can create and write `data/uploads`, `data/outputs`, `data/jobs`, and `data/models`.

### `pipeline` is slow

The **pipeline** backend is CPU-oriented; large PDFs take time. Optionally try **VLM / hybrid** backends if you have a suitable GPU and MinerU docs for your hardware.

### VLM / hybrid backends need GPU or extra config

Backends like `vlm-auto-engine` or `hybrid-auto-engine` expect compatible drivers and models. See [MinerU documentation](https://opendatalab.github.io/MinerU/) for backend-specific setup.

## Development scripts

| Script | Command |
|--------|---------|
| Both apps | `pnpm dev` |
| Web only | `pnpm dev:web` |
| API only | `pnpm dev:api` |

## License

Application code in this repository is provided as-is. MinerU is licensed under its own terms — see `packages/mineru` after clone.
