# RapidOCR (ONNX) sidecar integration

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 1), [medium-four-ocr-models.md](./medium-four-ocr-models.md), [issues/rapidocr-integration.md](../issues/rapidocr-integration.md)

## Goals

1. Ship **RapidOCR** ([RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR), Apache 2.0) in **Run / Arena / History** via the FastAPI gateway.
2. Optional **CPU** sidecar (no GPU in default compose) to match Wave 1 “classical / ONNX cluster”.
3. Same HTTP contract as MinerU / Nemotron: `GET /health`, `GET /v1/models`, `POST /v1/ocr` (multipart).

## Approach

- **Docker:** `docker/Dockerfile.cpu-ocr-sidecars` (target `rapidocr`) — Python 3.12 slim, apt libs for OpenCV (`libgl1`, `libxcb1`, …), `rapidocr-onnxruntime`, FastAPI + uvicorn.
- **Sidecar:** `docker/rapidocr/serve.py` — load `RapidOCR()` at startup; join line texts with newlines.
- **Registry:** `backend/config/ocr_engines.json` — `type: rapidocr`, model id **`rapidocr`**, profile **`rapidocr`**, port **8220**.
- **Backend:** `rapidocr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py` (`/health` + `model_loaded`).
- **UI:** Model picker hint when sidecar is down.

## Tasks

- [x] Dockerfile + `serve.py`
- [x] `docker-compose.yml` service `rapidocr` + `RAPIDOCR_HOST` on backend
- [x] `ocr_engines.json`, registry, factory, compose health
- [x] `prompts.json`, `classify.py`, frontend hint
- [x] Backlog / `ocr-engines.md` / issue write-up
