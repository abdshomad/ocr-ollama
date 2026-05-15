# OCR Ollama

Web app for optical character recognition via **vLLM** (default) or [Ollama](https://ollama.com). Compare multiple models in an arena, keep run history, and configure per-model prompts.

## Stack

- **Frontend:** Vite + React + TypeScript (`frontend/`)
- **Backend:** FastAPI (`backend/`)
- **Inference (default):** vLLM OpenAI API at `http://localhost:8100` — [DeepSeek-OCR recipe](https://docs.vllm.ai/projects/recipes/en/latest/DeepSeek/DeepSeek-OCR.html)
- **Inference (optional):** Ollama at `http://localhost:11434` — set `INFERENCE_BACKEND=ollama` in **Settings** or env

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- **vLLM (default):** GPU host with vLLM serving `deepseek-ai/DeepSeek-OCR` on port **8100** (avoids clash with FastAPI dev on 8000):

```bash
vllm serve deepseek-ai/DeepSeek-OCR \
  --logits_processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching --mm-processor-cache-gb 0 \
  --host 0.0.0.0 --port 8100
```

List models: `curl http://localhost:8100/v1/models`

- **Ollama (optional):** switch backend in **Settings** and pull models, e.g. `ollama pull deepseek-ocr`

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
| `vllm` | DeepSeek-OCR via vLLM OpenAI API (`:8100`, GPU required) |
| `nginx` | Serves UI at `/`, proxies `/api/` → backend |
| `backend` | FastAPI (internal port 8000, not published) |

**Requirements:** NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html). First `docker compose up` downloads the model into volume `vllm-hf-cache` (can take several minutes; healthcheck allows up to ~10 min).

**`.env` (compose):**

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3036` | Host port mapped to nginx |
| `INFERENCE_BACKEND` | `vllm` | `vllm` or `ollama` |
| `VLLM_HOST` | `http://vllm:8100` | vLLM URL for backend (Compose service name) |
| `VLLM_PORT` | `8100` | Host port published for vLLM (debug `curl localhost:8100/v1/models`) |
| `VLLM_IMAGE` | `vllm/vllm-openai:latest` | vLLM Docker image |
| `VLLM_MODEL` | `deepseek-ai/DeepSeek-OCR` | Model id passed to `vllm serve` |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` | Ollama on host when `INFERENCE_BACKEND=ollama` |

For **Ollama-only**, set `INFERENCE_BACKEND=ollama` and start without the vLLM service: `docker compose up --build backend nginx -d` (skips GPU container).

Change inference URL in **Settings** or `.env`. Loopback in `settings.json` is overridden by non-loopback `VLLM_HOST` in Docker (see `issues/docker-ollama-localhost-settings-override.md`).

Data volumes (bind mounts): `./upload`, `./result`, `./backend/config`.

```bash
docker compose logs -f
docker compose down
```

### Environment variables (local dev)

| Variable | Default | Description |
|----------|---------|-------------|
| `INFERENCE_BACKEND` | `vllm` | `vllm` or `ollama` |
| `VLLM_HOST` | `http://localhost:8100` | vLLM base URL (no `/v1` suffix) |
| `VLLM_TIMEOUT` | `600` | vLLM request timeout (seconds) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama URL when backend is `ollama` |
| `UPLOAD_DIR` | `<repo>/upload` | Saved input images |
| `RESULT_DIR` | `<repo>/result` | JSON run history |
| `MAX_IMAGE_BYTES` | `10485760` | Max upload size (10 MB) |
| `OLLAMA_TIMEOUT` | `300` | Ollama request timeout (seconds) |

## Features

- **Run:** Upload or capture an image, pick an OCR-capable model, run OCR
- **Arena:** Compare 2–6 models on the same image (sequential server-side)
- **History:** Browse and reopen past single and arena runs
- **Settings:** General prompt and per-model overrides

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

- [ ] `curl http://localhost:8000/api/health` shows `inference_reachable: true`
- [ ] `/api/models` lists OCR-capable models with correct tiers
- [ ] Upload and camera save files under `upload/`
- [ ] Single OCR with `deepseek-ocr:latest` returns text
- [ ] Arena with 2+ models writes one JSON file under `result/`
- [ ] History lists runs; per-model prompt overrides general
- [ ] `upload/` and `result/` contents are not in `git status`

## Plan

See [plan/ocr-ollama-app.md](plan/ocr-ollama-app.md) and [plan/vllm-deepseek-ocr-migration.md](plan/vllm-deepseek-ocr-migration.md).
