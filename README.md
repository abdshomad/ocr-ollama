# OCR Ollama

Web app for optical character recognition via **vLLM + DeepSeek-OCR** (default in Docker Compose) or [Ollama](https://ollama.com). Compare models in an arena, optional browser scan, run history, and per-model prompts. Server inference is always via FastAPI — the browser never calls vLLM or Ollama directly.

**Working stack (Compose):** `docker compose up --build -d` → http://localhost:3036. See [issues/vllm-deepseek-ocr-integration.md](issues/vllm-deepseek-ocr-integration.md) for setup, env vars, and troubleshooting.

## Stack

- **Frontend:** Vite + React + TypeScript (`frontend/`)
- **Backend:** FastAPI (`backend/`)
- **Inference (default):** vLLM OpenAI API at `http://localhost:8100` — [DeepSeek-OCR recipe](https://docs.vllm.ai/projects/recipes/en/latest/DeepSeek/DeepSeek-OCR.html)
- **Inference (optional):** Ollama at `http://localhost:11434` — set `INFERENCE_BACKEND=ollama` in **Settings** or env

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- **Docker Compose (recommended):** NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) — includes `vllm`, `backend`, and `nginx` services
- **Or local vLLM:** GPU host running DeepSeek-OCR on port **8100** (see [Development](#development))
- **Ollama (optional):** set `INFERENCE_BACKEND=ollama` in **Settings** or `.env`, e.g. `ollama pull deepseek-ocr`

## Setup

### Backend

```bash
cd backend
uv sync
```

Dependencies are declared in `pyproject.toml`; `uv sync` creates `.venv` and installs from `uv.lock`.

### Frontend

```bash
cd frontend
npm install
```

## Development

Terminal 1 — API (from repo root, port 8000):

```bash
cd backend
export INFERENCE_BACKEND=vllm
export VLLM_HOST=http://localhost:8100
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Add packages with `uv add <package>`. After editing `pyproject.toml` manually, run `uv sync`.

Terminal 2 — UI (proxies `/api` to port 8000):

```bash
cd frontend
npm run dev
```

Open http://localhost:5173

## Docker Compose

Runs the built frontend and FastAPI backend behind **nginx** on a single host port.

```bash
cp .env.example .env   # edit PORT, VLLM_HOST, INFERENCE_BACKEND if needed
docker compose up --build -d
```

Open http://localhost:3036 (or whatever `PORT` is in `.env`).

| Service | Role |
|---------|------|
| `vllm` | DeepSeek-OCR via vLLM (internal `:8100`, GPU required; not published on host) |
| `nginx` | Serves UI at `/`, proxies `/api/` → backend |
| `backend` | FastAPI (internal port 8000, not published) |

**Requirements:** NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html). By default vLLM uses **GPU 1** (`VLLM_CUDA_VISIBLE_DEVICES=1`) so it does not collide with Ollama or a host vLLM on GPU 0. First `docker compose up` downloads the model into volume `vllm-hf-cache` (healthcheck allows up to ~30 min for download + load).

**`.env` (compose):**

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3036` | Host port mapped to nginx |
| `INFERENCE_BACKEND` | `vllm` | `vllm` or `ollama` |
| `VLLM_HOST` | `http://vllm:8100` | vLLM URL for backend (Compose service name) |
| `VLLM_IMAGE` | `vllm/vllm-openai:latest` | vLLM Docker image |
| `VLLM_MODEL` | `deepseek-ai/DeepSeek-OCR` | Model id passed to `vllm serve` |
| `VLLM_CUDA_VISIBLE_DEVICES` | `1` | GPU index (use `0` if only one GPU) |
| `VLLM_GPU_MEMORY_UTILIZATION` | `0.85` | vLLM VRAM fraction |
| `VLLM_MAX_TOKENS` | `2048` (backend default) | Max **output** tokens per OCR request |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama on host when `INFERENCE_BACKEND=ollama` |

For **Ollama-only**, set `INFERENCE_BACKEND=ollama` and start without the vLLM service: `docker compose up --build backend nginx -d` (skips GPU container).

Change inference URL in **Settings** or `.env`. Loopback in `settings.json` is overridden by non-loopback `VLLM_HOST` in Docker (see `issues/docker-ollama-localhost-settings-override.md`).

Data volumes (bind mounts): `./upload`, `./result`, `./backend/config`.

```bash
docker compose logs -f vllm
docker compose down
```

Optional: publish vLLM on the host (default `127.0.0.1:18100` to avoid clashing with a local vLLM on 8100):

```bash
docker compose -f docker-compose.yml -f docker-compose.vllm-publish.yml up -d
curl http://127.0.0.1:18100/v1/models
```

### Environment variables (local dev)

| Variable | Default | Description |
|----------|---------|-------------|
| `INFERENCE_BACKEND` | `vllm` | `vllm` or `ollama` |
| `VLLM_HOST` | `http://localhost:8100` | vLLM base URL (no `/v1` suffix) |
| `VLLM_TIMEOUT` | `600` | vLLM request timeout (seconds) |
| `VLLM_MAX_TOKENS` | `2048` | Max output tokens (keep below 8192; image uses input budget) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama URL when backend is `ollama` |
| `UPLOAD_DIR` | `<repo>/upload` | Saved input images |
| `RESULT_DIR` | `<repo>/result` | JSON run history |
| `MAX_IMAGE_BYTES` | `10485760` | Max upload size (10 MB) |
| `OLLAMA_TIMEOUT` | `300` | Ollama request timeout (seconds) |

## Features

- **Run:** Upload or capture an image, pick an OCR-capable model, run OCR
- **Arena:** Compare 2–6 models on the same image (sequential server-side)
- **Scan:** Offline browser OCR (Transformers.js / Tesseract) for product SKU and expiry date; saves via `POST /api/scan`
- **History:** Browse and reopen past single, arena, and browser scan runs
- **Settings:** General prompt, per-model overrides, clear browser model cache

Uploaded images are stored under `upload/`; results under `result/`. Both directories are gitignored (only `.gitkeep` is tracked).

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Inference server reachability |
| GET/PUT | `/api/settings` | Backend (`vllm`/`ollama`) and host URL |
| GET | `/api/models` | Models with OCR classification |
| GET/PUT | `/api/prompts` | Prompt configuration |
| POST | `/api/ocr` | Single-model OCR (`multipart`: image, model, optional prompt) |
| POST | `/api/arena` | Multi-model compare (`multipart`: image, models JSON array) |
| POST | `/api/scan` | Save browser scan (`multipart`: image, sku, expiry_date, confidence, engine, duration_ms) |
| GET | `/api/history` | List runs |
| GET | `/api/history/{id}` | Run detail |
| DELETE | `/api/history/{id}` | Delete run record |

## Model classification

**vLLM:** models from `GET /v1/models`; OCR tier by name (`deepseek-ocr`, etc.).

**Ollama:** classification uses `POST /api/show`:

- **Dedicated OCR:** name/family contains `ocr` or `paddleocr`
- **Vision:** `vision` in capabilities (general VLMs usable for OCR)
- **Text-only:** neither (hidden from OCR picker)

## Testing checklist

- [ ] `docker compose ps` — `vllm` healthy, `backend` and `nginx` up
- [ ] `curl http://localhost:3036/api/health` — `inference_reachable: true`, `inference_backend: vllm`
- [ ] `/api/models` lists `deepseek-ai/DeepSeek-OCR` (or served model)
- [ ] Single OCR on Run page returns text
- [ ] Arena / History / Settings (backend + host URL) work
- [ ] `upload/` and `result/` not tracked by git

## Troubleshooting

| Problem | Doc |
|---------|-----|
| vLLM unhealthy, GPU, ports, `max_tokens` 400 | [issues/vllm-deepseek-ocr-integration.md](issues/vllm-deepseek-ocr-integration.md) |
| Settings `localhost` breaks Docker | [issues/docker-ollama-localhost-settings-override.md](issues/docker-ollama-localhost-settings-override.md) |
| Ollama PaddleOCR / glm-ocr failures | [issues/README.md](issues/README.md) |

## Plan

See [plan/ocr-ollama-app.md](plan/ocr-ollama-app.md) and [plan/vllm-deepseek-ocr-migration.md](plan/vllm-deepseek-ocr-migration.md).
