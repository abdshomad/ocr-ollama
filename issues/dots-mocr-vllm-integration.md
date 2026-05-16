# Dots.MOCR — vLLM (`rednote-hilab/dots.mocr`)

**Date:** 2026-05-16  
**Changelog (2026-05-16):** If the container was created **before** `docker/vllm-entrypoint.sh` gained the `dots.mocr` branch, vLLM falls through to the generic `serve` path **without** `--trust-remote-code` and crashes at model config (`Please pass trust_remote_code=True`). **Fix:** `docker compose --profile dotsmocr build vllm-dotsmocr && docker compose --profile dotsmocr up -d --force-recreate vllm-dotsmocr`.

## Summary

**Dots.MOCR** ([GitHub](https://github.com/rednote-hilab/dots.mocr), weights `rednote-hilab/dots.mocr` on Hugging Face) is integrated as an **optional vLLM** service: `vllm-dotsmocr`, Compose profile **`dotsmocr`**, host port **8108** on the Docker network, default GPU **1**. Upstream recommends **vLLM ≥ 0.11** (model is registered in vLLM). Image: same `docker/Dockerfile.vllm-ocr` as other OCR VLMs.

## Symptoms (if misconfigured)

- **`rednote-hilab/dots.mocr`** stays unavailable in `/api/models` — container not running, wrong `VLLM_DOTS_MOCR_HOST`, or `/v1/models` id does not match catalog (see served-name note below).
- **OOM / slow first start** — another vLLM service on the same GPU; stop it from the GPU page or `docker compose stop …`.
- **400 on chat** — OpenAI `model` must match the id returned by `GET /v1/models` on that host.

## Operator steps

1. Build (if needed):

   ```bash
   docker compose --profile dotsmocr build vllm-dotsmocr
   ```

2. Start (prefer a free GPU; default device **1**):

   ```bash
   docker compose --profile dotsmocr up -d vllm-dotsmocr
   ```

3. Verify:

   ```bash
   curl -s http://127.0.0.1:${PORT:-3036}/api/models | jq '.[] | select(.name=="rednote-hilab/dots.mocr")'
   ```

4. **Served model name:** This repo’s entrypoint does **not** set `--served-model-name` by default, so vLLM usually exposes the same id as `VLLM_MODEL` (e.g. `rednote-hilab/dots.mocr`). If you add `--served-model-name model` (upstream demo style), set on the **backend**:

   - `VLLM_DOTS_MOCR_CHAT_MODEL=model`

   so `POST /v1/chat/completions` uses the correct id. `/api/models` treats the model as available if either the catalog id **or** `VLLM_DOTS_MOCR_CHAT_MODEL` appears in `GET /v1/models`.

## Env reference

| Variable | Role |
|----------|------|
| `VLLM_DOTS_MOCR_HOST` | Backend → vLLM (default `http://vllm-dotsmocr:8108` in Compose) |
| `VLLM_DOTS_MOCR_MODEL` | Weight id (default `rednote-hilab/dots.mocr`) |
| `VLLM_DOTS_MOCR_CUDA_DEVICE` | GPU index (default `1`) |
| `VLLM_DOTS_MOCR_GPU_MEMORY_UTIL` | `--gpu-memory-utilization` (default `0.55`) |
| `VLLM_DOTS_MOCR_MAX_MODEL_LEN` | Passed into `vllm-entrypoint.sh` (default `8192`) |
| `VLLM_DOTS_MOCR_MAX_TOKENS` | Backend chat cap (default `8192`; lower if you hit context limits) |
| `VLLM_DOTS_MOCR_SERVED_MODEL_NAME` | Optional `--served-model-name` for the container |
| `VLLM_DOTS_MOCR_CHAT_MODEL` | OpenAI `model` field override for `/v1/chat/completions` |

## Repo impact

- `backend/config/vllm_endpoints.json` — endpoint `dotsmocr`
- `docker-compose.yml` — `vllm-dotsmocr`, `VLLM_DOTS_MOCR_HOST` on backend
- `docker/vllm-entrypoint.sh` — `dots.mocr` branch (`--trust-remote-code`, `--chat-template-content-format string`, …)
- `backend/app/vllm_client.py` — max tokens, optional chat model id, availability alias
- `backend/app/vllm_compose.py` — `VLLM_DOTS_MOCR_CUDA_DEVICE`
- `backend/config/prompts.json` — default short OCR prompt (override in UI for full layout JSON per upstream `dots_mocr/utils/prompts.py`)
