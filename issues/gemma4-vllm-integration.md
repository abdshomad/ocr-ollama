# Gemma 4 — vLLM OCR integration

**Date:** 2026-05-16  
**Changelog:** 2026-05-16 — VRAM coexistence with Chandra, orphan `VLLM::EngineCore`, first-load compile time, `POST /api/ocr` smoke verification.

## Summary

Gemma 4 is wired as an optional **vLLM multimodal** endpoint (`google/gemma-4-E4B-it` by default): catalog in `vllm_endpoints.json`, Compose `vllm-gemma4` on **8104**, profile **`gemma4`**, flags in `docker/vllm-entrypoint.sh` per the [vLLM Gemma 4 recipe](https://docs.vllm.ai/projects/recipes/en/latest/Google/Gemma4.html). Catalog IDs matching `gemma-4` are **`vision`** tier (`ocr_capable: true`).

Operational failures seen on a dual-L40 host were **vLLM GPU memory reservation vs free VRAM** when another large vLLM service held the same GPU, and a **zombie EngineCore** after restarts. Both are resolved by freeing the GPU and/or lowering utilization; OCR was verified end-to-end via `POST /api/ocr`.

## Symptoms

- `/api/models` shows `google/gemma-4-E4B-it` with `available: false` while `vllm-gemma4` is down or still compiling.
- vLLM logs: `ValueError: Free memory on device cuda:0 (… GiB) on startup is less than desired GPU memory utilization (0.72, … GiB). Decrease GPU memory utilization or reduce GPU memory used by other processes.`
- `docker compose` health stuck **starting**; `nvidia-smi` shows **`VLLM::EngineCore`** on the Gemma GPU with no healthy API on 8104 (stuck first load or crash after partial init).

## Analysis / evidence

- vLLM’s `--gpu-memory-utilization` applies to **fraction of total VRAM** it tries to reserve; it fails if **free** VRAM is lower (e.g. **Chandra** ~17 GiB + Gemma target ~32 GiB on a 46 GiB card).
- EngineCore logged **“Port 8104 is already in use, trying port 8105”** during worker bring-up; a bad restart can leave a process holding memory until the container is **stopped**, not only restarted in place.
- **Repro (fixed path):**  
  - `docker compose --profile chandra stop vllm-chandra` (or stop whatever else uses that GPU).  
  - `docker compose --profile gemma4 stop vllm-gemma4` then `up -d vllm-gemma4` if VRAM still held.  
  - Wait until `docker exec <backend> python3 -c "import urllib.request; urllib.request.urlopen('http://vllm-gemma4:8104/v1/models')"` succeeds (first run can be **10–20+ minutes** for compile + CUDA graphs).

## Resolution

- **Coexistence:** Run **at most one large vLLM model per GPU**, or lower **`VLLM_GPU_MEMORY_UTILIZATION`** in `.env` for the Gemma service only (compose passes it into the entrypoint).
- **Stuck VRAM:** `docker compose --profile gemma4 stop vllm-gemma4`; confirm `nvidia-smi` no orphan **`VLLM::EngineCore`** on that GPU; then `up -d vllm-gemma4`.
- **Config:** `VLLM_GEMMA4_HOST`, `VLLM_GEMMA4_CUDA_DEVICE`, optional `VLLM_GEMMA4_MAX_MODEL_LEN`, `VLLM_GEMMA4_MAX_TOKENS`; image must support Gemma 4 (`VLLM_OCR_IMAGE` / `Dockerfile.vllm-ocr`).
- **Smaller variant:** use `google/gemma-4-E2B-it` — change **`VLLM_MODEL`** for `vllm-gemma4` and the **`models`** entry in `vllm_endpoints.json` together.
- **Verified OCR (2026-05-16):** after healthy `/v1/models`,  
  `curl -sS -X POST http://127.0.0.1:${PORT:-3036}/api/ocr -F "image=@SAMPLES/IMAGES/1.jpeg;type=image/jpeg" -F "model=google/gemma-4-E4B-it"`  
  returned plausible extracted text (product codes / “Best Before” style lines) in a few seconds.

## Repo impact

- `backend/config/vllm_endpoints.json`, `docker-compose.yml`, `docker/vllm-entrypoint.sh`, `backend/app/inference/classify.py`, `backend/app/vllm_client.py`, `backend/app/vllm_compose.py`, `backend/config/prompts.json`, `.env.example`, `plan/gemma4-vllm-ocr.md`.
