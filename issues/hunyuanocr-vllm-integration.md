# Hunyuan OCR — vLLM (`tencent/HunyuanOCR`)

**Date:** 2026-05-16  
**Changelog (2026-05-16):** `VLLM_HUNYUAN_OCR_MAX_MODEL_LEN` / `--max-model-len 8192` in entrypoint (HF default 32k blows KV on mid GPUs). Default **`VLLM_HUNYUAN_OCR_MAX_TOKENS`** in backend is **2048** (8192 ctx cannot fit 8192 output + image). Compose sets **`VLLM_HUNYUAN_OCR_GPU_MEMORY_UTIL`** default **0.42** when sharing a GPU. **`MODEL_LIST_HTTP_TIMEOUT`** raised (default **30s** in code; **45s** in Compose) so `/api/models` does not mark healthy vLLM offline on slow `/v1/models`. **Nginx** `proxy_read_timeout` / `proxy_send_timeout` **600s** for long first OCR. First **`POST /api/ocr`** through nginx can take **~60–120s** (cold GPU).

## Summary

Adds **Tencent HunyuanOCR** as an optional vLLM sidecar (`vllm-hunyuanocr`, profile **`hunyuanocr`**, port **8106**, default GPU **1**) for image OCR through `/api/ocr` and Arena. Uses the same **`Dockerfile.vllm-ocr`** image as LightOn / Chandra / Gemma4 / Qwen3-VL. Backend routing uses `vllm_endpoints.json` and `VLLM_HUNYUAN_OCR_HOST`.

## Symptoms (if misconfigured)

- Model **`tencent/HunyuanOCR`** appears in `/api/models` as unavailable, or OCR returns connection errors — Hunyuan container not running or wrong host.
- **OOM / slow first start** — another vLLM service holds the same GPU; stop it first (GPU page or `docker compose stop …`).

## Operator steps

1. Build (first time or after Dockerfile change):

   ```bash
   docker compose --profile hunyuanocr build vllm-hunyuanocr
   ```

2. Start (prefer exclusive GPU 1 — stop `vllm-glm`, `vllm-lighton`, `vllm-chandra`, `vllm-gemma4`, `vllm-qwen3-vl` on that device if needed):

   ```bash
   docker compose --profile hunyuanocr up -d vllm-hunyuanocr
   ```

3. Verify:

   ```bash
   curl -s http://127.0.0.1:${PORT:-3036}/api/models | jq '.[] | select(.name=="tencent/HunyuanOCR")'
   ```

4. Optional env (`.env`):

   - `VLLM_HUNYUAN_OCR_HOST` — default `http://vllm-hunyuanocr:8106` in Compose
   - `VLLM_HUNYUAN_OCR_CUDA_DEVICE` — default `1`
   - `VLLM_HUNYUAN_OCR_MODEL` — default `tencent/HunyuanOCR`
   - `VLLM_HUNYUAN_OCR_MAX_TOKENS` — default **2048** in backend (fits 8192 max context with image + prompt; raise via env if you increase `--max-model-len`)
   - `VLLM_HUNYUAN_OCR_TOP_K`, `VLLM_HUNYUAN_OCR_REPETITION_PENALTY` — match [vLLM recipe](https://docs.vllm.ai/projects/recipes/en/latest/Tencent-Hunyuan/HunyuanOCR.html)

## Analysis / evidence

- Serve flags: `--no-enable-prefix-caching`, `--mm-processor-cache-gb 0`, `--limit-mm-per-prompt '{"image": 1}'` in `docker/vllm-entrypoint.sh` (`hunyuanocr` branch).
- Client: `backend/app/vllm_client.py` adds `top_k` and `repetition_penalty` for Hunyuan model ids.

## Resolution

Follow **Operator steps** above; ensure **`HUGGING_FACE_HUB_TOKEN`** is set if Hub access requires it.

## Repo impact

- `backend/config/vllm_endpoints.json` — endpoint `hunyuanocr`
- `docker-compose.yml` — `vllm-hunyuanocr`, `VLLM_HUNYUAN_OCR_HOST` on backend
- `docker/vllm-entrypoint.sh` — Hunyuan branch
- `backend/app/vllm_client.py` — Hunyuan max tokens + sampling extras
- `backend/config/prompts.json` — default prompt for `tencent/HunyuanOCR`
