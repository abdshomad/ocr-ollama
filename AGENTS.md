# AGENTS.md — OCR Ollama

Guidance for AI agents working in this repository.

## Karpathy / Cursor rules (submodule)

**Always** read and follow the rules in [andrej-karpathy-skills/CURSOR.md](andrej-karpathy-skills/CURSOR.md). That file is maintained in the [`andrej-karpathy-skills`](andrej-karpathy-skills/) submodule and **updated periodically**—treat the latest version in the working tree as binding general guidance alongside this document. - If the user inputs 'enhance' or 'e', run the 'enhance' subtask to generate 3 enhancement ideas for each of the key pages (Run, Arena, History) and save them to plan/next-enhancements.md.

## Project summary

## Project summary

Monorepo: **Vite + React** frontend and **FastAPI** backend for OCR via **vLLM + DeepSeek-OCR** (default) or **Ollama**. Docker Compose runs `vllm`, `backend`, and `nginx` on one host port. Users upload or capture images, run OCR or **arena** compare, optional **browser scan**, and browse **history**. Inference backend and host URL are configurable in **Settings**.

**Enhancement/Idea Generation (`enhance` / `e`)**
* If the user inputs 'enhance' or 'e', run the 'enhance' subtask to generate 3 structured enhancement ideas for the key pages (Run, Arena, History). These ideas must be saved to `plan/next-enhancements.md` structured as: `Idea`, `Description`, and `Status` (pending/draft).

Spec: [plan/ocr-ollama-app.md](plan/ocr-ollama-app.md), [plan/vllm-deepseek-ocr-migration.md](plan/vllm-deepseek-ocr-migration.md), [plan/browser-ocr-pipeline.md](plan/browser-ocr-pipeline.md), [plan/ocr-engine-expansion-backlog.md](plan/ocr-engine-expansion-backlog.md) (**primary `next` queue**), [plan/ocr-engines.md](plan/ocr-engines.md) (speed ranking + in-repo ladder), [plan/medium-four-ocr-models.md](plan/medium-four-ocr-models.md) (registry / adapter patterns). **Working vLLM setup:** [issues/vllm-deepseek-ocr-integration.md](issues/vllm-deepseek-ocr-integration.md).

## Next Enhancement (`next` / `n`)
When the user sends **`next`** or **`n`** alone (or clearly means “ship the next enhancement”), implement **one** structured enhancement — the next active item from `plan/next-enhancements.md` — end to end. Do not only plan or scaffold; finish the implementation, testing, and documentation for the enhancement.

**How to pick the enhancement**

1. Open [plan/next-enhancements.md](plan/next-enhancements.md) — this is the **canonical queue for requested enhancements**.
2. Check the **Status** column: Select the next item that is marked `pending` or `Draft` and is structurally ready for implementation.
3. If the list is empty or only contains `completed` items, reply stating that the enhancement queue is empty and point the user to [plan/next-enhancements.md](plan/next-enhancements.md).

**How to implement**

1. Follow the general implementation steps applicable to the type of enhancement (e.g., UI changes need frontend work, API changes need backend work). Always aim for a minimal, complete, feature-ready slice of work.
2. Smoke-test the new functionality: Check relevant endpoints or run UI paths to confirm the new behavior is present.
3. On completion: Update [plan/next-enhancements.md](plan/next-enhancements.md) and set the status to `completed`.

## Verify enhancement (`test` / `t`)
When the user sends **`test`** or **`t`** alone, verify the enhancement currently in scope by ensuring it meets its specified goals and is functional in the UI (similar to the OCR verification workflow).

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

1. **Browser never calls vLLM/Ollama.** Server OCR traffic goes through FastAPI (`/api/ocr`, `/api/arena`). **Browser scan** (`/scan`) runs Transformers.js / Tesseract in a Web Worker (including optional **Granite Docling** ONNX); only structured results + images are posted via `POST /api/scan`.
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
| Run vLLM (DeepSeek-OCR-2) | `docker compose --profile deepseek-ocr2 up -d vllm-deepseek-ocr2` — [issues/deepseek-ocr-2-vllm-integration.md](issues/deepseek-ocr-2-vllm-integration.md) |
| Run vLLM (GLM-OCR) | `docker compose -f docker-compose.yml -f docker-compose.glm-ocr.yml up -d` — [issues/vllm-glm-ocr.md](issues/vllm-glm-ocr.md) |
| Run vLLM (Gemma 4) | `docker compose --profile gemma4 up -d vllm-gemma4` — [issues/gemma4-vllm-integration.md](issues/gemma4-vllm-integration.md) |
| Run vLLM (Qwen3-VL) | `docker compose --profile qwen3vl up -d vllm-qwen3-vl` — [issues/qwen3-vl-vllm-integration.md](issues/qwen3-vl-vllm-integration.md) |
| Run vLLM (Hunyuan OCR) | `docker compose --profile hunyuanocr up -d vllm-hunyuanocr` — [issues/hunyuanocr-vllm-integration.md](issues/hunyuanocr-vllm-integration.md) |
| Run vLLM (PaddleOCR-VL) | `docker compose --profile paddleocr-vl up -d vllm-paddleocr-vl` — [issues/paddleocr-vl-vllm-integration.md](issues/paddleocr-vl-vllm-integration.md) |
| Run vLLM (PaddleOCR-VL-1.5) | `docker compose --profile paddleocr-vl-15 up -d vllm-paddleocr-vl-15` — [issues/paddleocr-vl-15-vllm-integration.md](issues/paddleocr-vl-15-vllm-integration.md) |
| Run vLLM (Dots.MOCR) | `docker compose --profile dotsmocr up -d vllm-dotsmocr` — [issues/dots-mocr-vllm-integration.md](issues/dots-mocr-vllm-integration.md) |
| Run vLLM (Phi-4-multimodal) | `docker compose --profile phi4mm up -d vllm-phi4-mm` — [issues/phi4-multimodal-vllm-integration.md](issues/phi4-multimodal-vllm-integration.md) |
| Run vLLM (RolmOCR) | `docker compose --profile rolmocr up -d vllm-rolmocr` — [issues/rolmocr-vllm-integration.md](issues/rolmocr-vllm-integration.md) |
| Run vLLM (NuMarkdown) | `docker compose --profile numarkdown up -d vllm-numarkdown` — [issues/numarkdown-vllm-integration.md](issues/numarkdown-vllm-integration.md) |
| Run vLLM (Qwen3-Omni) | `docker compose --profile qwen3omni up -d vllm-qwen3-omni` — [issues/qwen3-omni-vllm-integration.md](issues/qwen3-omni-vllm-integration.md) |
| Run vLLM (Smol Docling) | `docker compose --profile smoldocling up -d vllm-smoldocling` — [issues/smol-docling-vllm-integration.md](issues/smol-docling-vllm-integration.md) |
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
