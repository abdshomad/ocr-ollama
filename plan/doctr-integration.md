# docTR integration

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 1 — docTR), [medium-four-ocr-models.md](./medium-four-ocr-models.md), [issues/doctr-integration.md](../issues/doctr-integration.md)

## Goals

1. Ship **docTR** (mindee/doctr, Apache 2.0) as an optional **CPU PyTorch** HTTP sidecar for workload **B** (scanned page images).
2. Wire **Run / Arena / History** via existing FastAPI paths (`doctr_client`, `inference/factory`).

## Approach

- **Docker:** `docker/Dockerfile.doctr` — slim + OpenCV libs, CPU `torch`/`torchvision`, `python-doctr`, FastAPI + uvicorn.
- **Sidecar:** `docker/doctr/serve.py` — `ocr_predictor(pretrained=True)` at startup; `Document.render()` for plain text.
- **Registry:** `ocr_engines.json` — `type: doctr`, model id **`doctr`**, profile **`doctr`**, port **8250**, `DOCTR_HOST`.
- **Backend:** `doctr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py` (`/health` + `model_loaded`).

## Tasks

- [x] Plan (`plan/doctr-integration.md`)
- [x] Sidecar + Dockerfile + compose profile `doctr`
- [x] Registry + backend client + factory + GPU compose probes
- [x] Frontend ModelPicker hint + prompts.json
- [x] Smoke: `/api/health`, `/api/models`, `POST /api/ocr` + browser Run
- [x] `issues/doctr-integration.md`, backlog + `ocr-engines.md` + `AGENTS.md`
