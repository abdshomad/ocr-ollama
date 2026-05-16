# PaddleOCR sidecar integration

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 2), [medium-four-ocr-models.md](./medium-four-ocr-models.md), [issues/paddleocr-integration.md](../issues/paddleocr-integration.md)

## Goals

1. Ship **PaddleOCR** as an optional **CPU** HTTP sidecar (Apache 2.0), distinct from Ollama **PaddleOCR-VL** VLMs.
2. Wire **Run / Arena / History** through `paddleocr_client`, `ocr_engines.json`, and GPU page compose start/stop.

## Approach

- **Docker:** `docker/Dockerfile.cpu-ocr-sidecars` (target `paddleocr`) — PaddlePaddle CPU wheels (official mirror), `paddleocr` 2.x, FastAPI + uvicorn.
- **Sidecar:** `docker/paddleocr/serve.py` — `PaddleOCR` at startup; `ocr()` on uploaded image (temp file); flatten line texts with newlines.
- **Registry:** `ocr_engines.json` — `type: paddleocr`, model id **`paddleocr`**, profile **`paddleocr`**, port **8260**, `PADDLEOCR_HOST`.
- **Backend:** `paddleocr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py` (`/health` + `model_loaded`).

## Tasks

- [x] Plan (`plan/paddleocr-integration.md`)
- [x] Dockerfile + `serve.py` + compose service + backend wiring + docs
