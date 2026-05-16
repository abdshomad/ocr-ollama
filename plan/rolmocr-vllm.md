# RolmOCR — optional vLLM

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md), [issues/rolmocr-vllm-integration.md](../issues/rolmocr-vllm-integration.md)

## Goals

- Ship **RolmOCR** (`reducto/RolmOCR`) as an optional vLLM service (Run / Arena / History / GPU page), with upstream **`VLLM_USE_V1=1`** and OpenAI-compatible chat.

## Approach

- Endpoint **`rolmocr`** in `vllm_endpoints.json` (port **8110**, profile **`rolmocr`**).
- Compose service **`vllm-rolmocr`** + `docker/vllm-entrypoint.sh` branch; backend **`VLLM_ROLMOCR_HOST`**.
- Client: **4096** default max tokens, temperature **0.2**, optional **`VLLM_ROLMOCR_CHAT_MODEL`**.

## Tasks

- [x] Compose + entrypoint + registry + client tuning
- [x] Docs: `.env.example`, `AGENTS.md`, `issues/*`, backlog + `ocr-engines.md`
- [x] Smoke: import app, `/api/models` shape (when service up)
