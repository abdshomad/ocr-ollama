# LanyOCR CPU sidecar

**Date:** 2026-05-16  
**Status:** Implemented  

## Goals

- Ship **LanyOCR** ([JC1DA/lanyocr](https://github.com/JC1DA/lanyocr), MIT) as an optional Docker **CPU** sidecar with the same HTTP contract as other OCR sidecars (`/health`, `/v1/models`, `/v1/ocr`).
- Wire **Run / Arena / History** via `ocr_engines.json`, `lanyocr_client.py`, and `inference/factory.py`.

## Approach

- **Image:** `docker/Dockerfile.lanyocr` — `lanyocr` pulls `onnxruntime-gpu` on some platforms; **uninstall GPU wheel and install `onnxruntime` (CPU)** for a sane slim image.
- **Serve:** `docker/lanyocr/serve.py` — load `LanyOcr` at startup (`merge_rotated_boxes` / `merge_vertical_boxes` / optional `merge_boxes_inference` from env).
- **Port:** `8280`, profile `lanyocr`, env `LANYOCR_HOST`.
- **GPU page:** extend `vllm_compose.py` tuples for health probe / host resolution (same pattern as easyocr).

## Tasks

- [x] Dockerfile + serve script + compose service + volume
- [x] `ocr_engines.json`, `engine_registry`, `lanyocr_client`, `factory`
- [x] `vllm_compose`, `ModelPicker`, `classify.py`, `prompts.json`, `.env.example`, `AGENTS.md`
- [x] `issues/lanyocr-integration.md`; update expansion backlog + `ocr-engines.md`
- [x] Smoke: import backend, `docker compose --profile lanyocr build`

## Related

- [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md), [medium-four-ocr-models.md](./medium-four-ocr-models.md)
