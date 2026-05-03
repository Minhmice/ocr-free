# MinerU local document extraction

Next.js + FastAPI wrapper around the **MinerU CLI** (`mineru`) with file-based jobs, SSE progress, and result inspection (Markdown, JSON, assets, ZIP download). Uploads, outputs, jobs, and model caches live under `data/` in the repository.

## Prerequisites

- **Python 3.12** (recommended) or **3.11 / 3.13**. **Do not use Python 3.14** for `apps/api` — `pydantic-core` does not build on 3.14 yet (PyO3). On macOS, `brew install python@3.12` and put `opt/python@3.12/bin` on your `PATH`, or rely on `scripts/ensure-api-venv.cjs` (runs before `npm run dev` / `npm start`) to find a 3.11–3.13 interpreter.
- [**uv**](https://docs.astral.sh/uv/) (recommended) or `pip` + `venv`
- **Node.js** 20+
- **npm** 10+ (or **pnpm** 9+ if you use it at the repo root)

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
npm install
npm run setup:web
npm run setup:api
```

You can use **pnpm** instead (`pnpm install`, `pnpm setup:web`) if you prefer.

**`npm run setup:api`** runs **`scripts/ensure-api-venv.cjs`**: it picks Python **3.11–3.13**, creates **`apps/api/.venv`** if needed, and runs **`pip install -e .`**. The same script runs automatically as **`predev`** and **`prestart`**, so a plain **`npm run dev`** prepares the API venv before starting servers.

Install **MinerU** into that same environment (or a shared env) so the **`mineru`** CLI is available to the API — e.g. after `setup:api`, from the repo root: `apps/api/.venv/bin/pip install -e "packages/mineru[all]"` (adjust path if you cloned MinerU elsewhere), or follow MinerU’s docs.

The API is started with **`.venv/bin/python -m uvicorn`** so you do not need **`uvicorn`** on your global `PATH`.

## 3. Run

```bash
npm run dev
```

`npm run dev` runs **`scripts/dev.mjs`**, which starts web + API in parallel and forwards **Ctrl+C (SIGINT)** to **both** processes so ports usually clear without manual `kill`.

- **Web UI:** [http://localhost:3000](http://localhost:3000)  
- **API:** [http://localhost:8000](http://localhost:8000) (proxied through Next.js route handlers at `/api/...`)

Optional: point the web app at a different API base (e.g. remote):

```bash
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

**API port:** the dev API listens on **`API_PORT`** (default **8000**). The Next.js BFF must target the same origin; if you change the port, set **`NEXT_PUBLIC_API_BASE_URL`** to match (see [Troubleshooting](#port-8000-already-in-use-errno-48)).

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

### Port 8000 already in use (Errno 48)

Another process (often a previous **`uvicorn`**) is bound to the API port. **`predev`** runs **`scripts/check-api-port.cjs`** and prints this early with fix hints.

**Free the port (macOS / Linux):**

```bash
kill $(lsof -ti:8000)
```

**Or use a different port** (set both so the web app’s API proxy still works):

```bash
export API_PORT=8001
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001
pnpm dev
```

### `mineru` command not found

Install MinerU in the **same** Python environment that runs `uvicorn`, or activate that venv before `npm run dev:api`. Ensure `which mineru` resolves when the shell that starts the API is the same one you use for MinerU.

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
| Both apps | `npm run dev` (or `pnpm dev`) — runs **`predev`** → ensures API venv |
| Web only | `npm run dev:web` |
| API only | `npm run dev:api` |
| Production bundle | `npm run build` (Next.js in `apps/web` only) |
| Production run | `npm start` — **`prestart`** ensures API venv, then web + API |

Root dev uses **`npm-run-all2`** (`run-p`) instead of `concurrently` to avoid npm peer-resolution bugs.

## License

Application code in this repository is provided as-is. MinerU is licensed under its own terms — see `packages/mineru` after clone.
