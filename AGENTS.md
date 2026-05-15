# AGENTS.md — OCR Ollama

Guidance for AI agents working in this repository.

## Project summary

Monorepo: **Vite + React** frontend and **FastAPI** backend for OCR via **vLLM** (default) or **Ollama**. Users upload or capture images, run single-model OCR or an **arena** comparison (2+ models), and browse **history**. Inference backend and host URL are configurable in **Settings**.

Spec: [plan/ocr-ollama-app.md](plan/ocr-ollama-app.md), [plan/vllm-deepseek-ocr-migration.md](plan/vllm-deepseek-ocr-migration.md)

## Issue documentation (`issues/`)

**Always** persist non-trivial problems, investigations, and fixes under **`issues/`** — do not leave analysis only in chat.

**When to write a file**

- After diagnosing bugs, Ollama/model failures, Docker/network misconfig, or integration errors
- When the user asks to save analysis (or says “document this issue”)
- Before closing a debugging session that took more than a quick one-liner fix

**Filename:** `issues/<short-kebab-slug>.md` (e.g. `issues/paddleocr-vl-ollama-load-failure.md`).

**Each doc should include**

1. **Summary** — one paragraph: what failed and the actual root cause (not guesses)
2. **Symptoms** — user-visible errors, HTTP status, log lines
3. **Analysis / evidence** — commands run, paths, versions, repro steps
4. **Resolution** — what fixed it (or explicit workarounds if unresolved)
5. **Repo impact** — code/config changes in this project, if any

Update the same file when the resolution changes; add a short **Date** or changelog line at the top when revisiting.

Index: [issues/README.md](issues/README.md). Examples: [issues/docker-ollama-localhost-settings-override.md](issues/docker-ollama-localhost-settings-override.md), [issues/paddleocr-vl-ollama-load-failure.md](issues/paddleocr-vl-ollama-load-failure.md).

## Architecture rules

1. **Browser never calls vLLM/Ollama.** All model/OCR traffic goes through FastAPI (`/api/*`).
2. **Production traffic** enters only via **nginx** on `PORT` (from `.env`, default `3036`). Do not expose the backend port in Compose.
3. **Persistence:** images → `upload/`; run JSON → `result/`; issue write-ups → `issues/`; prompts → `backend/config/prompts.json`; inference settings → `backend/config/settings.json` (gitignored).
4. **Inference resolution:** `INFERENCE_BACKEND` (`vllm` default) + `settings.json` → `VLLM_HOST` / `OLLAMA_HOST` env → defaults (`8100` / `11434`). Loopback in `settings.json` is overridden by non-loopback env in Docker. Use `get_inference_backend()`, `get_inference_host()`, `get_vllm_host()`, or `get_ollama_host()` from `settings_store.py`. OCR calls go through `app.inference.factory`.

## Python backend (`backend/`)

- Use **[uv](https://docs.astral.sh/uv/) only** for dependencies:
  - `uv sync` — install from lockfile
  - `uv add <pkg>` — add dependency (updates `pyproject.toml` + `uv.lock`)
  - `uv run <cmd>` — run in project venv (e.g. `uv run uvicorn app.main:app --reload`)
- Do **not** add `requirements.txt` or document `pip install` for this project.
- App layout: `[tool.uv] package = false` — not an installable package; modules live under `backend/app/`.
- Python **3.12+** (see `backend/.python-version`).
- Keep inference in `vllm_client.py` / `ollama_client.py` (via `inference/factory.py`), file/persistence in `ocr_service.py`, history in `history.py`, prompts in `prompts.py`, settings in `settings_store.py`. Routes stay in `main.py` unless the file grows large enough to split.
- Arena runs models **sequentially** to reduce GPU OOM risk; do not parallelize without an explicit design change.
- Validate uploads: `ALLOWED_CONTENT_TYPES`, `MAX_IMAGE_BYTES` in `config.py`.
- Commit **`uv.lock`** when dependencies change.

## Frontend (`frontend/`)

- **TypeScript + React Router** (`/`, `/arena`, `/history`, `/settings`).
- API client: `frontend/src/api/client.ts` — use relative `/api/...` paths (works with Vite proxy and nginx).
- Shared image for Run/Arena: `ImageContext` — do not duplicate file state per page.
- Local dev: `npm run dev` (port 5173); proxy in `vite.config.ts` → backend `:8000`.
- Use valid JSX: **`div` / `span`**, not typo tags. Build with `npm run build` before considering UI work done.

## Docker

- `docker compose up --build` — builds `backend` (uv) and `nginx` (frontend static + reverse proxy).
- Copy `backend/pyproject.toml` + **`uv.lock`** in Dockerfile before `uv sync --frozen --no-dev --no-install-project`.
- Do not publish backend `8000` on the host; only `${PORT}:80` on nginx.
- **Compose includes `vllm` service** (GPU, port 8100, volume `vllm-hf-cache`). Backend default `VLLM_HOST=http://vllm:8100`. Requires NVIDIA Container Toolkit. For Ollama-only: `INFERENCE_BACKEND=ollama` and `docker compose up backend nginx` (no `vllm`). Warn if `settings.json` has loopback while env uses `vllm` or `host.docker.internal`.

## Configuration files

| File | Tracked | Purpose |
|------|---------|---------|
| `.env` | No | `PORT`, `INFERENCE_BACKEND`, `VLLM_HOST`, `OLLAMA_HOST` for Compose |
| `.env.example` | Yes | Template |
| `backend/config/prompts.json` | Yes | Default + per-model prompts |
| `backend/config/settings.json` | No | UI-saved Ollama URL |

## API conventions

- Prefix routes with `/api/`.
- Multipart for OCR: `image`, `model`, optional `prompt`; arena adds `models` (JSON string) and optional `prompt_overrides`.
- Return structured JSON; use `HTTPException` with clear `detail` for client errors and Ollama failures (502/503).
- Model list includes `tier`, `ocr_capable` for UI filtering.

## Git and scope

- Do **not** commit `.env`, `upload/*` (except `.gitkeep`), `result/*` (except `.gitkeep`), `backend/config/settings.json`, `node_modules`, `.venv`, `frontend/dist`.
- Do **not** edit `plan/ocr-ollama-app.md` unless the user asks for plan updates.
- Prefer focused diffs; match existing naming and patterns; no drive-by refactors.
- Do not create git commits unless the user explicitly requests them.

## Common tasks

| Task | Command / location |
|------|-------------------|
| Run backend locally | `cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000` |
| Run frontend locally | `cd frontend && npm run dev` |
| Run full stack | `docker compose up --build` → `http://localhost:${PORT}` |
| Add Python dep | `cd backend && uv add <package>` |
| Change exposed port | `.env` → `PORT=...` |
| Change inference backend/URL | Settings UI or `PUT /api/settings` |
| Run vLLM (DeepSeek-OCR) | See [plan/vllm-deepseek-ocr-migration.md](plan/vllm-deepseek-ocr-migration.md) |

## Testing expectations

After backend changes: `cd backend && uv run python -c "from app.main import app"` or hit `/api/health` and `/api/models`.

After frontend changes: `cd frontend && npm run build`.

After Docker changes: `docker compose build` and verify `curl http://127.0.0.1:${PORT}/api/health`.
