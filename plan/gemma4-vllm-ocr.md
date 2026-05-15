# Gemma 4 — vLLM OCR path

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [vLLM Gemma 4 recipes](https://docs.vllm.ai/projects/recipes/en/latest/Google/Gemma4.html), [ocr-engines.md](./ocr-engines.md)

## Goals

- Expose **Google Gemma 4** (`google/gemma-4-E4B-it` by default) on a dedicated Compose service so Run / Arena / History can call it like other vLLM multimodal models.
- Classify catalog entries as **vision** OCR-capable (general VLM, not a dedicated OCR checkpoint).

## Approach

- New endpoint in `backend/config/vllm_endpoints.json` → `vllm_registry` routing.
- Compose service `vllm-gemma4` on port **8104**, profile **`gemma4`**, image `Dockerfile.vllm-ocr` (transformers ≥ 5.4).
- `docker/vllm-entrypoint.sh`: Gemma-specific `limit-mm-per-prompt` (image-only), `max-model-len`, vision soft-token budget per vLLM docs.

## Tasks

- [x] `vllm_endpoints.json` + `.env.example` + backend `docker-compose` env `VLLM_GEMMA4_HOST`
- [x] Compose service + entrypoint branch
- [x] `classify.py` → `vision` tier for `gemma-4` names; `vllm_client` optional `VLLM_GEMMA4_MAX_TOKENS`
- [x] `prompts.json` default OCR-style prompt
- [x] `vllm_compose.py` GPU device env `VLLM_GEMMA4_CUDA_DEVICE`
- [x] Issue note `issues/gemma4-vllm-integration.md`

## Notes

- vLLM docs recommend **≥24 GB** VRAM for E2B/E4B in BF16; use smaller `VLLM_GEMMA4_MAX_MODEL_LEN` if tight on memory.
- Swap `VLLM_MODEL` / endpoint model list to `google/gemma-4-E2B-it` if you prefer the smaller variant (same serve flags pattern).
