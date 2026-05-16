# OnnxTR integration

**Date:** 2026-05-16  
**Related:** [plan/onnxtr-integration.md](../plan/onnxtr-integration.md)

## Summary

**OnnxTR** is integrated as an optional **CPU** sidecar (`onnxtr`, compose profile **`onnxtr`**, port **8230**). The FastAPI backend calls `ONNXTR_HOST` using the same multipart contract as MinerU-Diffusion, Nemotron, and RapidOCR (`GET /health`, `POST /v1/ocr`). The slim image installs system libraries so OpenCV behaves like the RapidOCR sidecar (`libgl1`, `libglib2.0-0`, …). First run may download ONNX/HF artifacts into `/root/.cache` (volume `onnxtr-onnx-cache`).

## Symptoms

- Model picker shows **onnxtr** offline — profile `onnxtr` not started or `ONNXTR_HOST` wrong for the backend.
- Slow or OOM on first request — OnnxTR pulls default detection/recognition weights; allow **start_period** in healthcheck and inspect container logs.

## Analysis / evidence

```bash
docker compose --profile onnxtr build onnxtr
docker compose --profile onnxtr up -d onnxtr
# In-stack: backend reaches http://onnxtr:8230/health
curl -s http://127.0.0.1:${PORT:-3036}/api/models | jq '.models[] | select(.name=="onnxtr")'
```

From the **GPU** page, start service **`onnxtr`** (compose controls use the same `/api/vllm/services/...` plumbing as other engines). Default in-stack URL: `http://onnxtr:8230` (`ONNXTR_HOST`).

## Resolution

- Start the sidecar: `docker compose --profile onnxtr up -d onnxtr`.
- Ensure backend env `ONNXTR_HOST` points at the running container (Compose default above).
- Wait for `GET /health` → `model_loaded: true` before Arena compares.

## Repo impact

- `docker/Dockerfile.onnxtr`, `docker/onnxtr/serve.py`
- `docker-compose.yml` service `onnxtr`, volume `onnxtr-onnx-cache`, backend `ONNXTR_HOST`
- `backend/config/ocr_engines.json` (`type`: **`onnxtr`**), `onnxtr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py`
