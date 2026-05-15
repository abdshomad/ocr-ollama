# Chandra OCR 2 (vLLM)

**Date:** 2026-05-16  
**Status:** Implemented

## Goals

Add **Chandra OCR 2** (`datalab-to/chandra-ocr-2`) via vLLM on port **8103** — Run, Arena, History, GPU page start/stop (profile `chandra`).

## Approach

- Compose service `vllm-chandra` using `docker/Dockerfile.vllm-ocr` (transformers ≥ 5.4).
- Serve flags from upstream `chandra_vllm` (bfloat16, mm pixel bounds, single image per prompt).
- Registry: `backend/config/vllm_endpoints.json` id `chandra`.
- Default prompt: layout HTML OCR (condensed from `chandra.prompts.OCR_LAYOUT_PROMPT`).
- Higher default `max_tokens` for Chandra in `vllm_client.py` (layout HTML can be long).

## Tasks

- [x] Plan + issue docs
- [x] `vllm-chandra` Compose + entrypoint branch
- [x] `vllm_endpoints.json`, `prompts.json`, `.env.example`
- [x] `vllm_compose.py` GPU device env
- [x] Update `ocr-engines.md` / `medium-four-ocr-models.md`
- [x] Smoke: import app, `npm run build`

## Related

- [medium-four-ocr-models.md](./medium-four-ocr-models.md) Phase 2
- [issues/chandra-vllm-integration.md](../issues/chandra-vllm-integration.md)
