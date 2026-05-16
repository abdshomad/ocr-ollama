# OnnxTR (ONNX CPU) sidecar integration

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 1 — ONNX cluster), [medium-four-ocr-models.md](./medium-four-ocr-models.md), [issues/onnxtr-integration.md](../issues/onnxtr-integration.md)

## Goals

1. Ship **OnnxTR** ([felixdittrich92/OnnxTR](https://github.com/felixdittrich92/OnnxTR), Apache 2.0) in **Run / Arena / History** via the FastAPI gateway.
2. Optional **CPU** sidecar (compose profile **`onnxtr`**) distinct from RapidOCR: docTR-derived detection + recognition on ONNX Runtime.
3. Same HTTP contract as other sidecars: `GET /health`, `GET /v1/models`, `POST /v1/ocr` (multipart).

## Approach

- **Docker:** `docker/Dockerfile.onnxtr` — Python 3.12 slim, apt libs for OpenCV, `onnxtr[cpu]`, FastAPI + uvicorn.
- **Sidecar:** `docker/onnxtr/serve.py` — `ocr_predictor()` at startup; `Document.render()` for plain text.
- **Registry:** `backend/config/ocr_engines.json` — `type: onnxtr`, model id **`onnxtr`**, profile **`onnxtr`**, port **8230**.
- **Backend:** `onnxtr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py` (`/health` + `model_loaded`).
- **UI:** Model picker offline hint.

## Tasks

- [x] Dockerfile + `serve.py`
- [x] `docker-compose.yml` service `onnxtr` + `ONNXTR_HOST` on backend
- [x] `ocr_engines.json`, registry, factory, compose health
- [x] `prompts.json`, `classify.py`, frontend hint
- [x] Backlog / `ocr-engines.md` / issue write-up + sample fixture path
