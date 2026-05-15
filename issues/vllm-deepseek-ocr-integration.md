# vLLM + DeepSeek-OCR integration (working setup)

**Date:** 2026-05-15  
**Status:** Resolved — OCR via `deepseek-ai/DeepSeek-OCR` in Docker Compose confirmed working  
**Plan:** [plan/vllm-deepseek-ocr-migration.md](../plan/vllm-deepseek-ocr-migration.md)

## Summary

The app now defaults to **vLLM** instead of Ollama for server-side OCR. A `vllm` service in Docker Compose serves [deepseek-ai/DeepSeek-OCR](https://huggingface.co/deepseek-ai/DeepSeek-OCR) using the [official vLLM recipe](https://docs.vllm.ai/projects/recipes/en/latest/DeepSeek/DeepSeek-OCR.html). FastAPI talks to vLLM over the internal network (`http://vllm:8100/v1/chat/completions`); the browser never calls vLLM directly. Several startup and request issues were fixed (invalid chat template, GPU contention, host port bind, context length). Ollama remains available via `INFERENCE_BACKEND=ollama` in Settings or `.env`.

## Architecture

```text
Browser → nginx (:3036) → FastAPI backend → vLLm (:8100, Compose network)
                              ↓
                         upload/  result/  settings.json
```

| Component | Location |
|-----------|----------|
| Inference factory | `backend/app/inference/factory.py` |
| vLLM client | `backend/app/vllm_client.py` |
| Ollama client | `backend/app/ollama_client.py` |
| Settings / host resolution | `backend/app/settings_store.py` |
| Compose stack | `docker-compose.yml` |

## Working Compose configuration

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f vllm   # first run: model download + load (can take 10–30 min)
# UI: http://localhost:3036
```

Key `.env` values (see `.env.example`):

| Variable | Compose default | Purpose |
|----------|-----------------|--------|
| `INFERENCE_BACKEND` | `vllm` | `vllm` or `ollama` |
| `VLLM_HOST` | `http://vllm:8100` | Backend → vLLM (no `/v1` suffix) |
| `VLLM_CUDA_VISIBLE_DEVICES` | `1` | Avoid GPU 0 when Ollama/host vLLM uses it |
| `VLLM_GPU_MEMORY_UTILIZATION` | `0.85` | Leave headroom on shared GPUs |
| `VLLM_MAX_TOKENS` | `2048` (backend default) | Output cap; model total ctx is 8192 |

vLLM serve flags (in `docker-compose.yml`): `NGramPerReqLogitsProcessor`, `--no-enable-prefix-caching`, `--mm-processor-cache-gb 0`, internal port **8100**. Model weights persist in volume **`vllm-hf-cache`**.

**Ollama-only:** `INFERENCE_BACKEND=ollama` and `docker compose up --build backend nginx -d` (skips GPU container).

**Optional host access to vLLM:** `docker compose -f docker-compose.yml -f docker-compose.vllm-publish.yml up -d` → `http://127.0.0.1:18100/v1/models` (avoids conflict with a process on host port 8100).

## Issues encountered and fixes

### 1. Host port 8100 already allocated

**Symptom:** `Bind for 0.0.0.0:8100 failed: port is already allocated`  
**Cause:** Another vLLM or service on the host used 8100.  
**Fix:** Removed host `ports:` from the `vllm` service; backend uses Docker DNS `vllm:8100` only. Optional publish via `docker-compose.vllm-publish.yml` on **18100**.

### 2. Container unhealthy (immediate crash)

**Symptom:** `dependency failed to start: container ocr-ollama-vllm-1 is unhealthy`  
**Cause:** Invalid `--chat-template` path (`vllm/transformers_utils/...` doubled); vLLM exited before healthcheck passed.  
**Fix:** Removed `--chat-template`; use positional model id per vLLM 0.21+ CLI. See also [vllm-compose-unhealthy.md](vllm-compose-unhealthy.md).

### 3. GPU OOM on cuda:0

**Symptom:** `Free memory on device cuda:0 ... less than desired GPU memory utilization (0.92, 40.84 GiB)`  
**Cause:** GPU 0 partially used (e.g. Ollama); default `gpus: all` picked device 0.  
**Fix:** `CUDA_VISIBLE_DEVICES=1` and `--gpu-memory-utilization 0.85` in Compose.

### 4. Slow first start

**Symptom:** Backend/nginx stay `Created` while vLLM is `health: starting`.  
**Cause:** HuggingFace download + model load on first run.  
**Fix:** Healthcheck `start_period: 1800s`; `docker compose up` waits for `service_healthy`.

### 5. HTTP 400 — max_tokens vs context

**Symptom:** `This model's maximum context length is 8192 tokens. However, you requested 8192 output tokens...`  
**Cause:** `VLLM_MAX_TOKENS=8192` reserved the full window for output; image + prompt need input tokens.  
**Fix:** Default `VLLM_MAX_TOKENS=2048` in `backend/app/config.py` (matches vLLM online recipe). Do not set output tokens near 8192 for this model.

## OCR request shape (backend)

`vllm_client.ocr_chat` sends OpenAI-compatible multimodal chat:

- `image_url` data URI + text prompt (e.g. `"Free OCR."` from `prompts.json`)
- `max_tokens`: `VLLM_MAX_TOKENS` (default 2048)
- For DeepSeek-OCR: `extra_body` with `vllm_xargs` (ngram processor) and `skip_special_tokens: false`

## Verification

- [x] `docker compose ps` — `vllm` healthy, `backend` and `nginx` running
- [x] `GET /api/health` — `inference_reachable: true`, `inference_backend: vllm`
- [x] `GET /api/models` — lists `deepseek-ai/DeepSeek-OCR`
- [x] `POST /api/ocr` — returns transcribed text for a test image

## Repo impact

| Area | Files |
|------|--------|
| Inference abstraction | `backend/app/inference/*`, `vllm_client.py`, `ocr_service.py` |
| Config | `backend/app/config.py`, `settings_store.py`, `main.py` |
| Prompts | `backend/config/prompts.json` (`Free OCR.`, per-model DeepSeek entry) |
| Compose | `docker-compose.yml`, `docker-compose.vllm-publish.yml`, `.env.example` |
| UI | Settings: backend selector + `VLLM_HOST` / `OLLAMA_HOST` |
| Docs | `README.md`, `AGENTS.md`, `plan/vllm-deepseek-ocr-migration.md` |

## Local dev (vLLM on host, not Compose)

```bash
vllm serve deepseek-ai/DeepSeek-OCR \
  --logits_processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching --mm-processor-cache-gb 0 \
  --host 0.0.0.0 --port 8100

cd backend && export INFERENCE_BACKEND=vllm VLLM_HOST=http://localhost:8100
uv run uvicorn app.main:app --reload --port 8000
```
