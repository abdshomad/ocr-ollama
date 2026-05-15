# AGENTS.md — OCR Ollama

Guidance for AI agents working in this repository.

## Project summary

Monorepo: **Vite + React** frontend and **FastAPI** backend for OCR via **vLLM + DeepSeek-OCR** (default) or **Ollama**. Docker Compose runs `vllm`, `backend`, and `nginx` on one host port. Users upload or capture images, run OCR or **arena** compare, optional **browser scan**, and browse **history**. Inference backend and host URL are configurable in **Settings**.

Spec: [plan/ocr-ollama-app.md](plan/ocr-ollama-app.md), [plan/vllm-deepseek-ocr-migration.md](plan/vllm-deepseek-ocr-migration.md), [plan/browser-ocr-pipeline.md](plan/browser-ocr-pipeline.md), [plan/ocr-engines.md](plan/ocr-engines.md) (speed ranking), [plan/medium-four-ocr-models.md](plan/medium-four-ocr-models.md) (integration queue). **Working vLLM setup:** [issues/vllm-deepseek-ocr-integration.md](issues/vllm-deepseek-ocr-integration.md).

## Plan documentation (`plan/`)

**Always** create a plan in **`plan/`** before starting non-trivial work — do not leave design and approach only in chat.

**When to write a file**

- New features, refactors, integrations, or any change touching multiple areas (backend, frontend, Docker, config)
- When the user asks for a plan (or says “plan this”)
- Before implementing; update the same file as scope or approach changes

**When to skip**

- One-line fixes, typos, or trivial single-file tweaks
- When the user explicitly says to skip planning

**Filename:** `plan/<short-kebab-slug>.md` (e.g. `plan/vllm-glm-ocr.md`).

**Each plan should include**

1. **Status** — Draft | In progress | Implemented
2. **Goals** — what to build and why
3. **Approach** — architecture, key paths, API or config changes
4. **Tasks** — ordered checklist (mark done during implementation)
5. **Related** — links to other `plan/`, `issues/`, or spec docs

Update the plan as work progresses; add a short **Date** or changelog line at the top when revisiting.

## Next engine (`next` / `n`)

When the user sends **`next`** or **`n`** alone (or clearly means “ship the next OCR engine”), implement **one** engine — the **fastest not yet in the repo** — end to end. Do not only plan or scaffold; finish Run/Arena/History (and browser path if the engine is browser-tier) for that engine.

**How to pick the engine**

1. Open [plan/ocr-engines.md](plan/ocr-engines.md) and use the **master speed ladder** for the active workload:
   - **Default:** workload **B** (scanned page, server `/api/ocr` / Arena) — today the top **Planned** entry is **LightOnOCR**, then MinerU-Diffusion (batched), then Chandra, etc.
   - **PDF / digital text focus** (user context or open PDF work): workload **A** — **LiteParse** when still unimplemented.
   - **Browser `/scan` only** (user context): workload **C** — pick the fastest ladder row not marked **In repo**.
2. Skip engines marked **In repo** or **Yes** in the ladder; skip **out of scope** in [plan/medium-four-ocr-models.md](plan/medium-four-ocr-models.md).
3. If multiple workloads tie, prefer workload **B** (primary server path).

**How to implement**

1. Follow [plan/medium-four-ocr-models.md](plan/medium-four-ocr-models.md) for the matching **Phase** (Phase 0 registry/router first if `ocr_engines.json` / adapters are not in place yet — that unblocks the fastest pending model).
2. Obey [Architecture rules](#architecture-rules) (FastAPI gateway, no browser → vLLM, sequential arena, uv-only backend).
3. Smoke-test: `/api/health`, `/api/models`, one OCR run, update GPU/compose docs if a new service was added.
4. On completion: set **In repo** / phase checkboxes in `plan/ocr-engines.md` and `plan/medium-four-ocr-models.md`; add `issues/<engine>-integration.md` if setup was non-trivial.

**When all planned engines are done**, reply briefly that the queue is empty and point at [plan/ocr-engines.md](plan/ocr-engines.md).

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

Index: [issues/README.md](issues/README.md). Primary vLLM reference: [issues/vllm-deepseek-ocr-integration.md](issues/vllm-deepseek-ocr-integration.md).

## Architecture rules

1. **Browser never calls vLLM/Ollama.** Server OCR traffic goes through FastAPI (`/api/ocr`, `/api/arena`). **Browser scan** (`/scan`) runs Transformers.js / Tesseract in a Web Worker; only structured results + images are posted via `POST /api/scan`.
2. **Production traffic** enters only via **nginx** on `PORT` (from `.env`, default `3036`). Do not expose the backend port in Compose.
3. **Persistence:** images → `upload/`; run JSON → `result/`; plans → `plan/`; issue write-ups → `issues/`; prompts → `backend/config/prompts.json`; inference settings → `backend/config/settings.json` (gitignored).
4. **Inference resolution:** `INFERENCE_BACKEND` (`vllm` default) + `settings.json` (`inference_backend`, `vllm_host` / `ollama_host`) → env → defaults (`http://vllm:8100` in Compose, `http://localhost:8100` local). Loopback in `settings.json` is overridden by non-loopback env in Docker. Use `get_inference_backend()`, `get_inference_host()`, `get_vllm_host()`, or `get_ollama_host()` from `settings_store.py`. OCR calls go through `app.inference.factory`. vLLM OCR uses `VLLM_MAX_TOKENS` default **2048** (model ctx 8192; image consumes input budget).

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

- **TypeScript + React Router** (`/`, `/arena`, `/history`, `/gpu`, `/settings`).
- API client: `frontend/src/api/client.ts` — use relative `/api/...` paths (works with Vite proxy and nginx).
- Shared image for Run/Arena: `ImageContext` — do not duplicate file state per page.
- Local dev: `npm run dev` (port 5173); proxy in `vite.config.ts` → backend `:8000`.
- Use valid JSX: **`div` / `span`**, not typo tags. Build with `npm run build` before considering UI work done.

## Docker

- `docker compose up --build` — **`vllm`** (GPU, DeepSeek-OCR), **`backend`**, **`nginx`** on `${PORT:-3036}`.
- Copy `backend/pyproject.toml` + **`uv.lock`** in Dockerfile before `uv sync --frozen --no-dev --no-install-project`.
- Do not publish backend `8000` or vLLM `8100` on the host by default (avoids port conflicts). Backend uses `http://vllm:8100` on the Compose network. Optional host publish: `docker-compose.vllm-publish.yml` (port **18100**).
- **vLLM services:** `vllm-deepseek` + `vllm-glm` (dual GPU). Routing: `backend/config/vllm_endpoints.json` + `vllm_registry.py`. `/api/models` lists both with `available` + `vllm_endpoint_label`; frontend `ModelPicker` radio/checkbox. `docker/vllm-entrypoint.sh` sets per-model serve flags.
- **Ollama-only:** `INFERENCE_BACKEND=ollama` and `docker compose up backend nginx` (skip `vllm`).
- Troubleshooting: [issues/vllm-deepseek-ocr-integration.md](issues/vllm-deepseek-ocr-integration.md).

## Configuration files

| File | Tracked | Purpose |
|------|---------|---------|
| `.env` | No | `PORT`, `INFERENCE_BACKEND`, `VLLM_*`, `OLLAMA_HOST` for Compose |
| `.env.example` | Yes | Template |
| `backend/config/prompts.json` | Yes | Default + per-model prompts (`Free OCR.` for DeepSeek) |
| `backend/config/settings.json` | No | UI-saved inference backend + host URLs |

## API conventions

- Prefix routes with `/api/`.
- Multipart for OCR: `image`, `model`, optional `prompt`; arena adds `models` (JSON string) and optional `prompt_overrides`.
- Return structured JSON; use `HTTPException` with clear `detail` for client errors and inference failures (502/503).
- Model list includes `tier`, `ocr_capable` for UI filtering.

## Git and scope

- Do **not** commit `.env`, `upload/*` (except `.gitkeep`), `result/*` (except `.gitkeep`), `backend/config/settings.json`, `node_modules`, `.venv`, `frontend/dist`.
- **Always** add new plans under `plan/` (see [Plan documentation](#plan-documentation-plan)); do **not** edit `plan/ocr-ollama-app.md` (master spec) unless the user asks for plan updates.
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
| Run vLLM (DeepSeek-OCR) | `docker compose up --build` or [issues/vllm-deepseek-ocr-integration.md](issues/vllm-deepseek-ocr-integration.md) |
| Run vLLM (GLM-OCR) | `docker compose -f docker-compose.yml -f docker-compose.glm-ocr.yml up -d` — [issues/vllm-glm-ocr.md](issues/vllm-glm-ocr.md) |
| Load/unload vLLM per GPU | **GPU** page or `POST /api/vllm/services/{deepseek\|glm}/start\|stop` |
| GPU metrics + compose control | `GET /api/gpu` (backend needs Docker socket; `COMPOSE_PROJECT_NAME` must match stack) |

## Testing expectations

After backend changes: `cd backend && uv run python -c "from app.main import app"` or hit `/api/health` and `/api/models`.

After frontend changes: `cd frontend && npm run build`.

After Docker changes: `docker compose build` and verify `curl http://127.0.0.1:${PORT}/api/health`.
