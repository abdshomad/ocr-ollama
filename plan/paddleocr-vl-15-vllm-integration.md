# PaddleOCR-VL-1.5 — vLLM integration

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [issues/paddleocr-vl-15-vllm-integration.md](../issues/paddleocr-vl-15-vllm-integration.md), [issues/paddleocr-vl-vllm-integration.md](../issues/paddleocr-vl-vllm-integration.md), HF [`PaddlePaddle/PaddleOCR-VL-1.5`](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5)

## Goals

1. Expose **`PaddlePaddle/PaddleOCR-VL-1.5`** as an optional vLLM service (**separate container** from 0.9B `PaddlePaddle/PaddleOCR-VL`), OpenAI `/v1` contract, Run/Arena/History + GPU page.
2. Reuse **`docker/vllm-entrypoint.sh`** PaddleOCR-VL branch (`*paddleocr-vl*` matches the 1.5 model id).

## Approach

- New endpoint id **`paddleocr-vl-15`** in `vllm_endpoints.json`, host env **`VLLM_PADDLEOCR_VL_15_HOST`**, port **8115**.
- Compose: **`vllm-paddleocr-vl-15`**, profile **`paddleocr-vl-15`**, GPU via **`VLLM_PADDLEOCR_VL_15_CUDA_DEVICE`**.
- Backend: `vllm_compose.py` CUDA mapping; optional `VLLM_PADDLEOCR_VL_15_MAX_TOKENS` in `vllm_client.py`; prompt **`OCR:`** in `prompts.json`.

## Tasks

- [x] `vllm_endpoints.json` + `prompts.json`
- [x] `docker-compose.yml` service + backend `environment`
- [x] `vllm_compose.py` GPU env mapping
- [x] `vllm_client.py` max-token override for 1.5
- [x] `.env.example` + `issues/` + backlog / `ocr-engines.md` / `AGENTS.md`
