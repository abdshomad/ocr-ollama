# LanyOCR sidecar integration

**Date:** 2026-05-16

## Summary

**LanyOCR** ([JC1DA/lanyocr](https://github.com/JC1DA/lanyocr), MIT) runs as an optional **CPU** HTTP sidecar. The backend talks to it over `LANYOCR_HOST` like other OCR sidecars (`/health`, `/v1/ocr`).

## Symptoms (when misconfigured)

- Model **`lanyocr`** appears **unavailable** in Run/Arena, or OCR returns connection errors.
- `/api/health` lists the `lanyocr` endpoint as unreachable.

## Setup

1. Build and start the service (from the repo root):

   ```bash
   docker compose --profile lanyocr up -d --build lanyocr
   ```

2. Ensure the backend can resolve the sidecar (Compose default):

   - `LANYOCR_HOST=http://lanyocr:8280` (set automatically in `docker-compose.yml` for the `backend` service, overridable via `.env`).

3. First run may **download ONNX weights** into the `lanyocr-cache` volume; allow several minutes before health turns healthy.

## Analysis / notes

- **`onnxruntime-gpu`:** the `lanyocr` PyPI package may depend on `onnxruntime-gpu`. The image **uninstalls the GPU wheel** and installs **`onnxruntime` (CPU)** for a slim CPU-only container.
- **Upstream:** last meaningful release ~2023; treat as **optional** / best-effort. Prefer **PaddleOCR**, **EasyOCR**, or **RapidOCR** for actively maintained stacks if LanyOCR breaks on dependency updates.

## Resolution

- If OCR fails with ONNX errors: rebuild the image (`docker compose build --no-cache lanyocr`) and confirm ample disk for the cache volume.
- For GPU inside the sidecar (unusual): set `LANYOCR_USE_GPU=1` and switch the Dockerfile to retain a GPU ORT build — **not** the default in this repo.

## Repo impact

- `docker/Dockerfile.lanyocr`, `docker/lanyocr/serve.py`
- `docker-compose.yml` service `lanyocr` (profile `lanyocr`), volume `lanyocr-cache`
- `backend/config/ocr_engines.json` — `type` **`lanyocr`**, model id **`lanyocr`**
- `backend/app/lanyocr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py`
