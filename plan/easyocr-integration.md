# EasyOCR sidecar integration

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 2 — PyTorch OCR), [medium-four-ocr-models.md](./medium-four-ocr-models.md), [issues/easyocr-integration.md](../issues/easyocr-integration.md)

## Goals

1. Ship **EasyOCR** as an optional **HTTP sidecar** (Apache 2.0), same multipart contract as RapidOCR/OnnxTR (`GET /health`, `POST /v1/ocr`).
2. Wire **Run / Arena / History** via existing FastAPI paths (`easyocr_client`, `inference/factory`).
3. **CPU-first** image (PyTorch CPU wheels) so the profile runs without NVIDIA; optional GPU documented in `issues/` for hosts that swap the base image or set `EASYOCR_USE_GPU=1` with CUDA runtime.

## Approach

- **Docker:** `docker/Dockerfile.cpu-ocr-sidecars` (target `easyocr`) — slim + OpenCV system libs, CPU `torch`/`torchvision`, `easyocr`, FastAPI + uvicorn.
- **Sidecar:** `docker/easyocr/serve.py` — `easyocr.Reader` at startup; `readtext` on uploaded image (temp file); join line texts with newlines.
- **Registry:** `ocr_engines.json` — `type: easyocr`, model id **`easyocr`**, profile **`easyocr`**, port **8240**, `EASYOCR_HOST`.
- **Backend:** `easyocr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py` (`/health` + `model_loaded`).

## Tasks

- [x] Plan (`plan/easyocr-integration.md`)
- [x] Dockerfile + `serve.py`
- [x] `docker-compose.yml` service + volume + backend `EASYOCR_HOST`
- [x] Registry + client + factory + compose probe + classify regex
- [x] `prompts.json`, `.env.example`, `ModelPicker` hint
- [x] `issues/easyocr-integration.md`, backlog + `ocr-engines.md` + `AGENTS.md` + `issues/README.md`
- [x] Smoke: import backend, `npm run build`
