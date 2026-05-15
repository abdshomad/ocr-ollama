# LiteParse integration

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [medium-four-ocr-models.md](./medium-four-ocr-models.md) (Phase 3), [ocr-engines.md](./ocr-engines.md) (workload A)

## Goals

- Wire **LiteParse** (`lit` CLI from `@llamaindex/liteparse`) into Run, Arena, and History for **PDF and images**.
- Keep browser → FastAPI only; no direct subprocess from the frontend.

## Approach

- Register engine `litparse` in `ocr_engines.json` (no Compose service; `gpu_device: -1`).
- `liteparse_client.py`: probe `LITEPARSE_BIN` (default `lit`), run `lit parse <file> -q --format text` in a thread pool with `LITEPARSE_TIMEOUT`.
- Sniff upload bytes for suffix (`.pdf` / image types) so `lit parse` receives a sensible extension.
- `POST /api/ocr` and `/api/arena`: allow `application/pdf`; reject PDF unless every selected model is `litparse` where required (single-model rule: only `litparse` accepts PDF).
- Backend Docker image: install Node + `npm install -g @llamaindex/liteparse` + **ImageMagick** (`imagemagick` Debian package — required by LiteParse for raster formats).
- Health: treat CLI-ready LiteParse as an endpoint so `/api/health` can be **ok** without vLLM when LiteParse alone is available.

## Tasks

- [x] `ocr_engines.json`, `liteparse_client.py`, `factory.py`, `engine_registry.py`, `vllm_compose.py`
- [x] `config.py`, `ocr_service.py`, `main.py`
- [x] `prompts.json`, `.env.example`, `Dockerfile`
- [x] Frontend: PDF in capture component, types, ModelPicker hint, GPU list (no compose actions)
- [x] `issues/liteparse-cli-integration.md`
- [x] Mark Phase 3 done in `medium-four-ocr-models.md`; update `ocr-engines.md` bucket
