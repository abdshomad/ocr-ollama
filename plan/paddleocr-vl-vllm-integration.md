# PaddleOCR-VL — vLLM integration

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [issues/paddleocr-vl-vllm-integration.md](../issues/paddleocr-vl-vllm-integration.md), [issues/paddleocr-vl-ollama-load-failure.md](../issues/paddleocr-vl-ollama-load-failure.md) (Ollama path still broken)

## Goals

1. Ship **PaddleOCR-VL** (`PaddlePaddle/PaddleOCR-VL`) on **vLLM** with OpenAI-compatible `/v1/chat/completions`, distinct from CPU **PP-OCR** sidecar `paddleocr`.
2. Optional Compose profile **`paddleocr-vl`**, GPU service `vllm-paddleocr-vl`, port **8107**; Run/Arena/History via existing `vllm_client` routing.

## Approach

- Extend `vllm_endpoints.json` + `docker/vllm-entrypoint.sh` (recipe flags: `--trust-remote-code`, `--max-num-batched-tokens`, `--no-enable-prefix-caching`, `--mm-processor-cache-gb 0`).
- Reuse `docker/Dockerfile.vllm-ocr` image; backend `VLLM_PADDLEOCR_VL_HOST` env.

## Tasks

- [x] `vllm_endpoints.json` + `vllm-entrypoint.sh` + `docker-compose.yml` + backend env
- [x] `vllm_compose.py` GPU device mapping + `vllm_client.py` max-tokens helper
- [x] `prompts.json`, `.env.example`, `AGENTS.md`, `plan/ocr-engines.md`, backlog changelog
- [x] `issues/paddleocr-vl-vllm-integration.md` + README row; Ollama issue cross-link
