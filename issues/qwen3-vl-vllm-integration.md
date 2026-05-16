# Qwen3-VL (vLLM) integration

**Date:** 2026-05-16  

## Summary

Adds **Qwen3-VL Instruct** as an optional vLLM sidecar (`vllm-qwen3-vl`, profile **`qwen3vl`**, port **8105**, default GPU **1**) for image OCR through the normal `/api/ocr` path. The stack uses the same **`Dockerfile.vllm-ocr`** image as LightOn/Chandra/Gemma4.

**First boot / HTTP:** vLLM 0.21 does not open `8105` until the engine finishes weight load + KV init (can be **several minutes** on first pull). The entrypoint uses **`--enforce-eager`** so torch.compile does not extend that silent period. Stop other GPU-1 vLLM services before start or the load can stall. **`VLLM_QWEN3_VL_MODEL`** (e.g. `Qwen/Qwen3-VL-2B-Instruct`) trims VRAM and load time vs 8B.

## Symptoms / operator notes

- VRAM on GPU 1 is usually occupied by **`vllm-glm`** (default compose). Starting Qwen3-VL on the same device requires **stopping** GLM and any other GPU-1 profile services (LightOn, Chandra, Gemma4, MinerU-Diffusion).

## Analysis / evidence

- vLLM recipe: [Qwen3-VL.md](https://github.com/vllm-project/recipes/blob/main/Qwen/Qwen3-VL.md) — for OCR we disable video (`--limit-mm-per-prompt.video 0`) to save memory.
- Default served checkpoint: **`Qwen/Qwen3-VL-8B-Instruct`**. Override with **`VLLM_QWEN3_VL_MODEL`** (e.g. `Qwen/Qwen3-VL-4B-Instruct` on tighter VRAM). The model picker lists 2B/4B/8B IDs; only the weight actually loaded in the container shows as **available** in `/api/models`.

## Resolution — runbook

1. **Free GPU 1** (from repo root, adjust profiles if you use them):

   ```bash
   docker compose stop vllm-glm
   docker compose --profile lighton stop vllm-lighton 2>/dev/null || true
   docker compose --profile chandra stop vllm-chandra 2>/dev/null || true
   docker compose --profile gemma4 stop vllm-gemma4 2>/dev/null || true
   docker compose --profile mineru stop mineru-diffusion 2>/dev/null || true
   ```

2. **Build (first time) and start Qwen3-VL:**

   ```bash
   docker compose --profile qwen3vl build vllm-qwen3-vl
   docker compose --profile qwen3vl up -d vllm-qwen3-vl
   ```

3. **Backend** must see `VLLM_QWEN3_VL_HOST` (set in `docker-compose.yml` for the `backend` service by default).

4. **Verify:** `curl -s http://127.0.0.1:${PORT:-3036}/api/models | jq` — look for `Qwen/Qwen3-VL-*` with `available: true` for the loaded id.

5. **GPU page:** start/stop service id **`qwen3vl`** (same pattern as `gemma4` / `chandra`).

## Repo impact

- `docker-compose.yml` — `vllm-qwen3-vl` + `VLLM_QWEN3_VL_HOST` on backend  
- `docker/vllm-entrypoint.sh` — `qwen3-vl` serve branch  
- `backend/config/vllm_endpoints.json` — endpoint `qwen3vl`  
- `backend/app/vllm_compose.py` — `VLLM_QWEN3_VL_CUDA_DEVICE`  
- `backend/app/inference/classify.py` — Qwen `*VL*` → vision tier (`ocr_capable`)  
- `backend/app/vllm_client.py` — optional `VLLM_QWEN3_VL_MAX_TOKENS`  
- `backend/config/prompts.json` — per-model OCR prompts  
- `plan/qwen3-vl-vllm-integration.md`  
