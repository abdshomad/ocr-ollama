# AGENTS.md — OCR Ollama

Guidance for AI agents working in this repository.

## Karpathy / Cursor rules (submodule)

**Always** read and follow the rules in [andrej-karpathy-skills/CURSOR.md](andrej-karpathy-skills/CURSOR.md). That file is maintained in the [`andrej-karpathy-skills`](andrej-karpathy-skills/) submodule and **updated periodically**—treat the latest version in the working tree as binding general guidance alongside this document. For OCR Ollama–specific requirements (plans, architecture, `next` / `test` workflows, issues), this `AGENTS.md` and linked `plan/` / `issues/` docs take precedence when they conflict with generic rules there.

## Project summary

Monorepo: **Vite + React** frontend and **FastAPI** backend for OCR via **vLLM + DeepSeek-OCR** (default) or **Ollama**. Docker Compose runs `vllm`, `backend`, and `nginx` on one host port. Users upload or capture images, run OCR or **arena** compare, optional **browser scan**, and browse **history**. Inference backend and host URL are configurable in **Settings**.

Spec: [plan/ocr-ollama-app.md](plan/ocr-ollama-app.md), [plan/vllm-deepseek-ocr-migration.md](plan/vllm-deepseek-ocr-migration.md), [plan/browser-ocr-pipeline.md](plan/browser-ocr-pipeline.md), [plan/ocr-engine-expansion-backlog.md](plan/ocr-engine-expansion-backlog.md) (**primary `next` queue**), [plan/ocr-engines.md](plan/ocr-engines.md) (speed ranking + in-repo ladder), [plan/medium-four-ocr-models.md](plan/medium-four-ocr-models.md) (registry / adapter patterns). **Working vLLM setup:** [issues/vllm-deepseek-ocr-integration.md](issues/vllm-deepseek-ocr-integration.md).

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

When the user sends **`next`** or **`n`** alone (or clearly means “ship the next OCR engine”), implement **one** engine — the **next eligible item from the expansion backlog** — end to end. Do not only plan or scaffold; finish Run/Arena/History (and browser path if the engine is browser-tier) for that engine.

**How to pick the engine**

1. Open [plan/ocr-engine-expansion-backlog.md](plan/ocr-engine-expansion-backlog.md) — this is the **canonical queue** for `next` / `n`.
2. Choose the **next unimplemented** candidate by **Suggested waves** (Wave 1 → 7), unless the user’s context clearly targets one workload (then see step 4). Within a wave, prefer rows that are **not** listed under **Already in repo** in that doc.
3. Skip engines **already in the repo** (backlog § “Already in repo”, plus **In repo** / **Yes** in [plan/ocr-engines.md](plan/ocr-engines.md) ladders). Skip backlog rows still in **Research** or **Blocked** (license, no weights, API-only with no adapter) until triaged to a concrete **Ship** path — if the next wave is all blocked, run a **spike** documented in `issues/` and update the backlog row.
4. Use [plan/ocr-engines.md](plan/ocr-engines.md) **workload ladders** to disambiguate when several backlog candidates are ready:
   - **Default:** workload **B** (scanned page, server `/api/ocr` / Arena).
   - **PDF / digital text focus:** workload **A** (pick the next backlog engine that fits **digital PDF / extraction**, e.g. parser-class tools).
   - **Browser `/scan` only:** workload **C** (pick the next backlog engine tagged **Browser** / WebGPU in the backlog table).
5. If a candidate was historically **out of scope** in [plan/medium-four-ocr-models.md](plan/medium-four-ocr-models.md) but is **in scope** in the backlog (e.g. GPL sidecar with explicit profile), follow the **backlog** license/mitigation notes.

**How to implement**

1. Follow [plan/medium-four-ocr-models.md](plan/medium-four-ocr-models.md) for **registry / adapter / compose** patterns (Phase 0 if `ocr_engines.json` or adapters need extending for the new `engine.type`).
2. Obey [Architecture rules](#architecture-rules) (FastAPI gateway, no browser → vLLM, sequential arena, uv-only backend).
3. Smoke-test: `/api/health`, `/api/models`, one OCR run (e.g. `curl` or Python client), update GPU/compose docs if a new service was added.
4. **Browser verification (required):** Use the **Cursor IDE browser** MCP — navigate to the running app (`http://localhost:${PORT}` from `.env`, default **3036**), open **Run** (`/`), pick the **new model** in the picker, upload **at least one sample** with readable content (add tiny tracked fixtures under `fixtures/ocr/` if the repo has none), run OCR / extraction, and confirm **non-empty plausible output** in the UI (fresh **snapshot**; screenshot optional). For **Arena**, include the new model in a compare if that is the primary workflow. For **browser-tier** engines (`/scan`), repeat on **Scan** with the same samples. If the stack is not running locally, start `docker compose up` (or dev frontend + backend) first; if browser automation is blocked (login, GPU unavailable), say so and attach API/smoke evidence instead.

   **LiteParse (`litparse`) — VERY IMPORTANT:** When this `next` cycle ships **LiteParse**, treating browser proof as optional is **not allowed**. After coding, you **must** use Cursor IDE browser tools on **Run** with **`litparse`** selected and verify extraction using **all applicable samples** under `fixtures/ocr/` — at minimum a small **digital PDF** with embedded text (LiteParse’s primary workload A path), **plus any PNG/JPEG samples** the app accepts for LiteParse in that build. Expected text must appear in the result panel (snapshot). Add or extend fixtures if none exist; do not close the task without this check.

5. On completion: update [plan/ocr-engine-expansion-backlog.md](plan/ocr-engine-expansion-backlog.md) (master checklist / wave notes if present); set **In repo** / ladder notes in [plan/ocr-engines.md](plan/ocr-engines.md) and phase checkboxes in [plan/medium-four-ocr-models.md](plan/medium-four-ocr-models.md) where applicable; add `issues/<engine>-integration.md` if setup was non-trivial.

**When the backlog has no further Ship-ready engines**, reply briefly that the queue is empty (or only Research/Blocked items remain) and point at [plan/ocr-engine-expansion-backlog.md](plan/ocr-engine-expansion-backlog.md) and [plan/ocr-engines.md](plan/ocr-engines.md).

## Verify engine (`test` / `t`)

When the user sends **`test`** or **`t`** alone (or clearly means “verify the OCR engine we just added or are working on”), **do not** pick a new backlog engine or expand scope. **Test and verify** that the engine in context produces real OCR / extraction in the UI.

**Which engine**

- Prefer the **model / engine from the current conversation** (the one the user or prior agent just implemented or fixed).
- If the user names a model or registry id, use that.
- If ambiguous, ask once which engine to verify.

**How to verify (browser required)**

1. Ensure the app and any sidecar inference services that engine needs are running (`docker compose` with the right profile, or dev frontend + backend). Use `http://localhost:${PORT}` from `.env` (default **3036**).

2. Use the **Cursor IDE browser** MCP: open **Run** (`/`), select that engine in the model picker, upload **at least one** sample with readable content from **`fixtures/ocr/`** (add or extend fixtures if the repo has none suitable). Run OCR / extraction and confirm **non-empty plausible text** in the result panel (capture a fresh **snapshot**; screenshot optional).

3. Match the **`next`** workflow depth where it applies: for **Arena**-centric engines, optionally run a compare including this model; for **browser-tier** engines (`/scan`), repeat on **Scan** with the same samples.

4. **LiteParse (`litparse`):** Same rule as in **`next`** — verify on **Run** with **all applicable samples** under `fixtures/ocr/` (at minimum a small **digital PDF** with embedded text, plus any PNG/JPEG the build accepts for LiteParse). Expected text must appear in the result panel.

5. If the stack cannot run or browser automation is blocked (login, missing GPU, etc.), state the blocker and attach the best alternative evidence (e.g. `curl` to `/api/ocr`, `/api/health`, `/api/models`, or logs).

This workflow is **manual browser proof** for the engine in context; routine automated checks stay under [Testing expectations](#testing-expectations).

## Issue documentation (`issues/`)

**Always** persist non-trivial problems, investigations, **and their solutions** under **`issues/`** — do not leave diagnosis or fixes only in chat. If you resolved something, the **`issues/*.md` file must record how** (commands, env vars, compose/service actions), not only what went wrong.

**When to write or update a file**

- After diagnosing bugs, Ollama/model failures, Docker/network misconfig, or integration errors
- **Whenever you land a fix or workaround** — update the existing issue for that topic or add `issues/<slug>.md` so the next run (human or agent) can repeat the solution
- When the user asks to save analysis (or says “document this issue”)
- Before closing a debugging session that took more than a quick one-liner fix

**Filename:** `issues/<short-kebab-slug>.md` (e.g. `issues/paddleocr-vl-ollama-load-failure.md`).

**Each doc should include**

1. **Summary** — one paragraph: what failed and the actual root cause (not guesses)
2. **Symptoms** — user-visible errors, HTTP status, log lines
3. **Analysis / evidence** — commands run, paths, versions, repro steps
4. **Resolution** — what fixed it: **concrete steps** (shell/compose/API), config keys, or explicit “unresolved” + next experiments. Do not leave this section vague once solved.
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

- `docker compose up --build` — **`vllm`** (GPU, DeepSeek-OCR), **`backend`**, **`nginx`** on `${PORT:-3036}`. Optional image overrides: `BACKEND_IMAGE`, `NGINX_IMAGE` (see `.env.example`).
- **CPU OCR sidecars** (RapidOCR, OnnxTR, EasyOCR, docTR, PaddleOCR, Docling, LanyOCR) share [docker/Dockerfile.cpu-ocr-sidecars](docker/Dockerfile.cpu-ocr-sidecars) (Compose `build.target` = service name). Publishable layers: [docker/Dockerfile.base-cv](docker/Dockerfile.base-cv), [docker/Dockerfile.base-torch-cpu](docker/Dockerfile.base-torch-cpu); profile **`bases`** builds those tags; ordered multi-image build: `docker buildx bake -f docker-bake.hcl cpu-sidecars` (set `REGISTRY_PREFIX` for your CR).
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
| Run vLLM (Gemma 4) | `docker compose --profile gemma4 up -d vllm-gemma4` — [issues/gemma4-vllm-integration.md](issues/gemma4-vllm-integration.md) |
| Run vLLM (Qwen3-VL) | `docker compose --profile qwen3vl up -d vllm-qwen3-vl` — [issues/qwen3-vl-vllm-integration.md](issues/qwen3-vl-vllm-integration.md) |
| Run vLLM (Hunyuan OCR) | `docker compose --profile hunyuanocr up -d vllm-hunyuanocr` — [issues/hunyuanocr-vllm-integration.md](issues/hunyuanocr-vllm-integration.md) |
| Run vLLM (PaddleOCR-VL) | `docker compose --profile paddleocr-vl up -d vllm-paddleocr-vl` — [issues/paddleocr-vl-vllm-integration.md](issues/paddleocr-vl-vllm-integration.md) |
| Run vLLM (Dots.MOCR) | `docker compose --profile dotsmocr up -d vllm-dotsmocr` — [issues/dots-mocr-vllm-integration.md](issues/dots-mocr-vllm-integration.md) |
| Run vLLM (Phi-4-multimodal) | `docker compose --profile phi4mm up -d vllm-phi4-mm` — [issues/phi4-multimodal-vllm-integration.md](issues/phi4-multimodal-vllm-integration.md) |
| Run RapidOCR (ONNX CPU) | `docker compose --profile rapidocr up -d rapidocr` — [issues/rapidocr-integration.md](issues/rapidocr-integration.md) |
| Run OnnxTR (ONNX CPU) | `docker compose --profile onnxtr up -d onnxtr` — [issues/onnxtr-integration.md](issues/onnxtr-integration.md) |
| Run EasyOCR (PyTorch CPU) | `docker compose --profile easyocr up -d easyocr` — [issues/easyocr-integration.md](issues/easyocr-integration.md) |
| Run docTR (PyTorch CPU) | `docker compose --profile doctr up -d doctr` — [issues/doctr-integration.md](issues/doctr-integration.md) |
| Run PaddleOCR (PaddlePaddle CPU) | `docker compose --profile paddleocr up -d paddleocr` — [issues/paddleocr-integration.md](issues/paddleocr-integration.md) |
| Run Docling (layout + OCR CPU) | `docker compose --profile docling up -d docling` — [issues/docling-integration.md](issues/docling-integration.md) |
| Run LanyOCR (ONNX CPU line-merge OCR) | `docker compose --profile lanyocr up -d lanyocr` — [issues/lanyocr-integration.md](issues/lanyocr-integration.md) |
| Native Tesseract (`tesseract` model) | No extra service — `tesseract-ocr` in **backend** image; [issues/tesseract-native-ocr-backend.md](issues/tesseract-native-ocr-backend.md) |
| Load/unload vLLM per GPU | **GPU** page or `POST /api/vllm/services/{deepseek\|glm}/start\|stop` |
| GPU metrics + compose control | `GET /api/gpu` (backend needs Docker socket; `COMPOSE_PROJECT_NAME` must match stack) |

## Testing expectations

After backend changes: `cd backend && uv run python -c "from app.main import app"` or hit `/api/health` and `/api/models`.

After frontend changes: `cd frontend && npm run build`.

After Docker changes: `docker compose build` and verify `curl http://127.0.0.1:${PORT}/api/health`.
