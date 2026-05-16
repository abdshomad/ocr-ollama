# PaddleOCR-VL-1.5 — vLLM integration

**Date:** 2026-05-16  
**Related:** [issues/paddleocr-vl-vllm-integration.md](paddleocr-vl-vllm-integration.md) (0.9B `PaddlePaddle/PaddleOCR-VL`), [plan/paddleocr-vl-15-vllm-integration.md](../plan/paddleocr-vl-15-vllm-integration.md), HF [`PaddlePaddle/PaddleOCR-VL-1.5`](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5)

## Summary

**PaddleOCR-VL-1.5** is an optional second vLLM service (**`vllm-paddleocr-vl-15`**, profile **`paddleocr-vl-15`**, port **8115**), separate from **`vllm-paddleocr-vl`** (0.9B, port 8107). The gateway catalog model id is **`PaddlePaddle/PaddleOCR-VL-1.5`**; routing uses **`VLLM_PADDLEOCR_VL_15_HOST`**. `docker/vllm-entrypoint.sh` selects the same PaddleOCR-VL serve flags when `VLLM_MODEL` matches `*paddleocr-vl*` (the 1.5 id matches).

## Symptoms (if integration fails)

- Service exits or healthcheck never passes during `start_period`.
- `/api/models` lists **`PaddlePaddle/PaddleOCR-VL-1.5`** with `available: false`.
- vLLM: unsupported architecture, missing `--trust-remote-code`, **engine core initialization failed** (see container logs — often **GPU OOM** or another vLLM already using the assigned GPU), or CUDA OOM — same class of errors as [paddleocr-vl-vllm-integration.md](paddleocr-vl-vllm-integration.md).

### Context length (1.5 checkpoint)

The 1.5 HF config can advertise a **very large** default `max_model_len` (e.g. 131k), which blows KV cache on typical GPUs. The **`vllm-paddleocr-vl-15`** service sets **`VLLM_PADDLEOCR_VL_15_MAX_MODEL_LEN`** (default **8192**), passed into `docker/vllm-entrypoint.sh` as `--max-model-len` when the model id matches `*paddleocr-vl-1.5*`.

## Resolution — bring up the service

1. **GPU:** default **`VLLM_PADDLEOCR_VL_15_CUDA_DEVICE=1`** in Compose. Do not run two large vLLM models on the same GPU without checking VRAM.
2. **Compose:**
   ```bash
   docker compose --profile paddleocr-vl-15 up -d --build vllm-paddleocr-vl-15
   ```
3. **Backend:** `VLLM_PADDLEOCR_VL_15_HOST=http://vllm-paddleocr-vl-15:8115` (default in `docker-compose.yml` for `backend`).
4. **Smoke (from a shell with the port published, or `docker compose exec` into the service network):**
   ```bash
   curl -sS http://vllm-paddleocr-vl-15:8115/v1/models
   ```

## Repo impact

| Area | Change |
|------|--------|
| `backend/config/vllm_endpoints.json` | Endpoint **`paddleocr-vl-15`**, model **`PaddlePaddle/PaddleOCR-VL-1.5`**, port **8115** |
| `docker-compose.yml` | Service **`vllm-paddleocr-vl-15`**, backend **`VLLM_PADDLEOCR_VL_15_HOST`** |
| `backend/app/vllm_compose.py` | **`VLLM_PADDLEOCR_VL_15_CUDA_DEVICE`** for GPU page assignments |
| `backend/app/vllm_client.py` | Optional **`VLLM_PADDLEOCR_VL_15_MAX_TOKENS`** |
| `backend/config/prompts.json` | Default prompt **`OCR:`** for the 1.5 model id |
