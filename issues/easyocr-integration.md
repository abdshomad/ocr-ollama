# EasyOCR sidecar integration

**Date:** 2026-05-16  
**Related:** [plan/easyocr-integration.md](../plan/easyocr-integration.md)

## Summary

**EasyOCR** is integrated as an optional **PyTorch CPU** HTTP sidecar (`easyocr`, compose profile **`easyocr`**, port **8240**). The FastAPI backend calls `EASYOCR_HOST` with the same contract as RapidOCR and OnnxTR (`GET /health`, `POST /v1/ocr`). The default image installs **CPU** PyTorch wheels so the service runs without an NVIDIA runtime; weights download into the `easyocr-model-cache` volume on first start.

## Symptoms

- Model picker shows **easyocr** as unavailable — profile `easyocr` not started or `EASYOCR_HOST` wrong for the backend.
- First start very slow or healthcheck pending — CRAFT + recognition models download (~100MB+) into `/root/.EasyOCR` (volume `easyocr-model-cache`). `start_period` is **900s** in Compose.

## Resolution

```bash
docker compose --profile easyocr build easyocr
docker compose --profile easyocr up -d easyocr
# In-stack: backend reaches http://easyocr:8240/health
curl -s "http://127.0.0.1:${PORT:-3036}/api/models" | jq '.models[] | select(.name=="easyocr")'
```

From the **GPU** page, start service **`easyocr`** (same compose controls as other OCR sidecars). Default in-stack URL: `http://easyocr:8240` (`EASYOCR_HOST`).

Optional languages (comma-separated, passed to `easyocr.Reader`):

- Set `EASYOCR_LANGS=en,de` in Compose or `.env` for the `easyocr` service.

GPU inside the container is **not** enabled in the default Dockerfile (CPU torch only). To experiment with CUDA, you would need a CUDA base image, matching `torch` wheels, NVIDIA Container Toolkit, `deploy.resources`, and `EASYOCR_USE_GPU=1` — not shipped as the default path.

## Repo impact

- `docker/Dockerfile.easyocr`, `docker/easyocr/serve.py`
- `docker-compose.yml` service `easyocr`, volumes `easyocr-model-cache` / `easyocr-torch-cache`, backend `EASYOCR_HOST`
- `backend/config/ocr_engines.json` (`type`: **`easyocr`**), `easyocr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py`
