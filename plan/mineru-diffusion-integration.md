# MinerU-Diffusion (nano_dvlm) integration

**Date:** 2026-05-16  
**Status:** Implemented

## Goals

Add **MinerU-Diffusion** (`opendatalab/MinerU-Diffusion-V1-0320-2.5B`) via a GPU sidecar using the upstream **nano_dvlm** engine — Run, Arena, History, and GPU page start/stop.

## Approach

- `mineru-diffusion` Compose service (profile `mineru`, port **8200**) with FastAPI wrapper around `LLM.generate_messages`.
- `backend/config/ocr_engines.json` + `engine_registry.py` for routing (vLLM endpoints unchanged).
- `mineru_client.py` + `factory.py` dispatch for non-vLLM models.
- Default prompt: `Text Recognition:` (matches upstream `TASK_PROMPTS["text"]`).

## Tasks

- [x] Plan doc
- [x] Docker image + `serve.py` HTTP API
- [x] Compose service + `.env.example`
- [x] Backend registry, client, factory, compose GPU
- [x] `prompts.json`, classify, frontend types
- [x] `issues/mineru-diffusion-nano-dvlm-integration.md`
- [x] Update `ocr-engines.md` / `medium-four-ocr-models.md`
- [x] Smoke: import app, `npm run build`

## Related

- [medium-four-ocr-models.md](./medium-four-ocr-models.md) Phase 4
- [ocr-engines.md](./ocr-engines.md) workload B rank 4
