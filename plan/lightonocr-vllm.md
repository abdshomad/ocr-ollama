# LightOnOCR via vLLM

**Date:** 2026-05-15  
**Status:** Implemented (smoke on GPU pending)  
**Related:** [medium-four-ocr-models.md](./medium-four-ocr-models.md), [ocr-engines.md](./ocr-engines.md)

## Goals

Add `lightonai/LightOnOCR-2-1B` on `vllm-lighton:8102` with Run / Arena / History / GPU page parity with DeepSeek and GLM.

## Approach

- Extend `vllm_endpoints.json` (same registry pattern as DeepSeek/GLM).
- Compose service `vllm-lighton` with profile `lighton` (not started on default `up` — avoids GPU 0 OOM with DeepSeek).
- `docker/Dockerfile.vllm-ocr` pins `transformers>=5.4` for LightOn.
- Entrypoint: `--limit-mm-per-prompt '{"image": 1}'`, `--mm-processor-cache-gb 0`, `--no-enable-prefix-caching`.
- Image-only OCR prompt (`""` in `prompts.json` per HF card).

## Tasks

- [x] `vllm_endpoints.json` + compose + entrypoint + `.env.example`
- [x] `classify.py`, `prompts.json`, `vllm_compose.py` profiles
- [x] Frontend default model preference
- [x] `issues/lightonocr-vllm-integration.md`
- [ ] Smoke: `/api/health`, `/api/models`, one OCR (needs GPU + `docker compose --profile lighton up -d vllm-lighton`)
- [x] Mark **In repo** in `ocr-engines.md` / Phase 1 tasks in `medium-four-ocr-models.md`
