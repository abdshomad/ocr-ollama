# Phi-4-multimodal — vLLM

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [issues/phi4-multimodal-vllm-integration.md](../issues/phi4-multimodal-vllm-integration.md), [vLLM Phi-4 recipe](https://docs.vllm.ai/projects/recipes/en/latest/Microsoft/Phi-4.html), [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 4)

## Goals

- Ship **`microsoft/Phi-4-multimodal-instruct`** as an optional vLLM sidecar for image OCR via existing `/api/ocr` and Arena (OpenAI chat + vision).
- Follow the same patterns as Gemma 4 / Qwen3-VL: `vllm_endpoints.json`, `Dockerfile.vllm-ocr`, `vllm-entrypoint.sh`, GPU page start/stop.

## Approach

- Compose service **`vllm-phi4-mm`**, profile **`phi4mm`**, port **8109**, default GPU **1**.
- Entrypoint branch: `--trust-remote-code`, capped `--max-model-len` (default **8192** via `VLLM_PHI4_MM_MAX_MODEL_LEN`), image limit + no prefix cache / mm cache (align with other VLMs).
- Backend: `VLLM_PHI4_MM_HOST`; classify as **vision** (`ocr_capable`); default **`VLLM_PHI4_MM_MAX_TOKENS=4096`**.

## Tasks

- [x] `vllm_endpoints.json` + `docker-compose.yml` + backend `VLLM_PHI4_MM_HOST`
- [x] `docker/vllm-entrypoint.sh` — Phi-4 multimodal branch
- [x] `vllm_compose.py` — `phi4multimodal` CUDA device env
- [x] `classify.py` / `vllm_client.py` — tier + max_tokens
- [x] `prompts.json` — per-model OCR prompt
- [x] `.env.example`, `AGENTS.md`, backlog + `ocr-engines.md`, `issues/*`
