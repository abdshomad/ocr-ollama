# RapidOCR (ONNX) sidecar

**Date:** 2026-05-16

**Related:** [plan/rapidocr-integration.md](../plan/rapidocr-integration.md)

## Summary

**RapidOCR** is integrated as an optional **CPU** sidecar (`rapidocr`, compose profile **`rapidocr`**, port **8220**). The FastAPI backend calls `RAPIDOCR_HOST` using the same multipart contract as MinerU-Diffusion and Nemotron (`GET /health`, `POST /v1/ocr`). The `python:3.12-slim` base requires extra **apt** packages so OpenCV can load (`libgl1`, `libxcb1`, `libglib2.0-0`, `libgomp1`).

## Symptoms

- Sidecar crashes at import with `ImportError: libGL.so.1` or `libxcb.so.1` — OpenCV runtime libs missing on slim image.
- Model picker shows **rapidocr** offline — profile `rapidocr` not started or `RAPIDOCR_HOST` wrong for the backend.
- First start slow — ONNX artifacts download into `/root/.cache` (persisted via Compose volume `rapidocr-onnx-cache`).

## Run

```bash
docker compose --profile rapidocr build rapidocr
docker compose --profile rapidocr up -d rapidocr
curl -s http://rapidocr:8220/health   # from another container on the compose network; host has no port publish by default
```

From the **GPU** page, start service **`rapidocr`** (same compose controls as other engines). Default in-stack URL: `http://rapidocr:8220` (`RAPIDOCR_HOST`).

## Verification

`GET /api/models` should list **`rapidocr`** with `available: true` when the sidecar is healthy. `POST /api/ocr` with `model=rapidocr` and a PNG/JPEG returns plain text in `text`.

## Repo impact

- `docker/Dockerfile.rapidocr`, `docker/rapidocr/serve.py`
- `docker-compose.yml` service `rapidocr`, volume `rapidocr-onnx-cache`, backend `RAPIDOCR_HOST`
- `backend/config/ocr_engines.json` (`type`: **`rapidocr`**), `rapidocr_client.py`, `inference/factory.py`, `vllm_compose.py`
