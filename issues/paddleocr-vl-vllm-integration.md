# PaddleOCR-VL — vLLM integration

**Date:** 2026-05-16  
**Related:** [vLLM recipe: PaddleOCR-VL](https://github.com/vllm-project/recipes/blob/main/PaddlePaddle/PaddleOCR-VL.md), [paddleocr-vl-ollama-load-failure.md](paddleocr-vl-ollama-load-failure.md) (Ollama still does not load `paddleocr` architecture)

## Summary

**PaddleOCR-VL** is wired as an optional **vLLM** service (`vllm-paddleocr-vl`), separate from the CPU **PP-OCR** sidecar (`paddleocr`). **PaddleOCR-VL-1.5** is a second optional service (`vllm-paddleocr-vl-15`, profile `paddleocr-vl-15`) — see [paddleocr-vl-15-vllm-integration.md](paddleocr-vl-15-vllm-integration.md). The backend uses the same OpenAI-compatible multimodal path as other vLLM OCR models (`/v1/chat/completions`). Catalog model id: **`PaddlePaddle/PaddleOCR-VL`** (and **`PaddlePaddle/PaddleOCR-VL-1.5`** for the 1.5 container).

## Symptoms (if integration fails)

- `docker compose` service exits or healthcheck never passes after `start_period`.
- `/api/models` shows `PaddlePaddle/PaddleOCR-VL` with `available: false`.
- vLLM logs: unsupported architecture, missing `--trust-remote-code`, or CUDA OOM.

## Analysis / evidence

- **Serve command** is selected in `docker/vllm-entrypoint.sh` when `VLLM_MODEL` matches `*paddleocr-vl*` (default `PaddlePaddle/PaddleOCR-VL`): `--trust-remote-code`, `--max-num-batched-tokens` (default 16384, override `VLLM_PADDLEOCR_VL_MAX_NUM_BATCHED_TOKENS`), `--no-enable-prefix-caching`, `--mm-processor-cache-gb 0`, `--limit-mm-per-prompt '{"image": 1}'`. The **1.5** checkpoint (`*paddleocr-vl-1.5*`) also gets `--max-model-len` (default **8192**, env `VLLM_PADDLEOCR_VL_15_MAX_MODEL_LEN` in the **`vllm-paddleocr-vl-15`** service) because the HF config’s default context is very large and can prevent healthy startup on mid-range GPUs.
- Optional **`VLLM_PADDLEOCR_VL_SERVED_MODEL_NAME`**: if vLLM serves under a different id, set this so `/v1/models` matches the app’s catalog (see recipe note on `PaddleOCR-VL-0.9B`).
- **vLLM version:** upstream recipe historically required a **new enough** vLLM build for PaddleOCR-VL; the stack uses `vllm/vllm-openai:latest` / `docker/Dockerfile.vllm-ocr`. If load fails, bump the image tag or follow the recipe’s install notes.

## Resolution — bring up the service

1. **GPU:** assign a free device (default compose: GPU **1** via `VLLM_PADDLEOCR_VL_CUDA_DEVICE`). Stop other large vLLM services on the same GPU if VRAM is tight.
2. **Compose:**
   ```bash
   docker compose --profile paddleocr-vl up -d --build vllm-paddleocr-vl
   ```
3. **Backend env (already defaulted in Compose):** `VLLM_PADDLEOCR_VL_HOST=http://vllm-paddleocr-vl:8107`
4. **Smoke:**
   ```bash
   curl -sS http://127.0.0.1:8107/v1/models
   ```
   From the app host, only if you publish the port; inside the stack, the backend reaches the service on the Compose network.

## Repo impact

| Area | Change |
|------|--------|
| `backend/config/vllm_endpoints.json` | Endpoints `paddleocr-vl` (model `PaddlePaddle/PaddleOCR-VL`, port 8107) and `paddleocr-vl-15` (`PaddlePaddle/PaddleOCR-VL-1.5`, port 8115) |
| `docker-compose.yml` | Services `vllm-paddleocr-vl`, `vllm-paddleocr-vl-15`, profile `paddleocr-vl-15`, backend env `VLLM_PADDLEOCR_VL_15_HOST` |
| `docker/vllm-entrypoint.sh` | PaddleOCR-VL serve branch |
| `backend/app/vllm_compose.py` | `VLLM_PADDLEOCR_VL_CUDA_DEVICE` mapping |
| `backend/app/vllm_client.py` | `VLLM_PADDLEOCR_VL_MAX_TOKENS` (default 4096) |
| `backend/config/prompts.json` | Default prompt `OCR:` (recipe task prefix) |
