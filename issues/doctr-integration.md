# docTR integration

**Date:** 2026-05-16  
**Related:** [plan/doctr-integration.md](../plan/doctr-integration.md)

## Summary

**docTR** (mindee/doctr, Apache 2.0) is integrated as an optional **PyTorch CPU** HTTP sidecar (`doctr`, compose profile **`doctr`**, port **8250**). The FastAPI backend calls `DOCTR_HOST` with the same multipart contract as RapidOCR, OnnxTR, and EasyOCR (`GET /health`, `POST /v1/ocr`). The image installs CPU PyTorch wheels; pretrained detection/recognition weights download into `/root/.cache` (volume `doctr-torch-cache`) on first start.

## Symptoms

- Model picker shows **doctr** offline — profile `doctr` not started or `DOCTR_HOST` wrong for the backend.
- Slow first request — docTR downloads default pretrained weights; allow **start_period** in healthcheck and inspect container logs.

## Analysis / evidence

```bash
docker compose --profile doctr build doctr
docker compose --profile doctr up -d doctr
# In-stack: backend reaches http://doctr:8250/health
curl -s "http://127.0.0.1:${PORT:-3036}/api/models" | jq '.models[] | select(.name=="doctr")'
curl -sS -X POST "http://127.0.0.1:${PORT:-3036}/api/ocr" \
  -F "image=@fixtures/ocr/sample.png;type=image/png" \
  -F "model=doctr"
```

From the **GPU** page, start service **`doctr`** (same compose controls as other OCR sidecars). Default in-stack URL: `http://doctr:8250` (`DOCTR_HOST`).

## Resolution

- Start the sidecar: `docker compose --profile doctr up -d doctr`.
- Ensure backend env `DOCTR_HOST` points at the running container (Compose default above).
- Wait for `GET /health` → `model_loaded: true` before Arena compares.

## Repo impact

- `docker/Dockerfile.doctr`, `docker/doctr/serve.py`
- `docker-compose.yml` service `doctr`, volume `doctr-torch-cache`, backend `DOCTR_HOST` (+ `EASYOCR_HOST`)
- `backend/config/ocr_engines.json` (`type`: **`doctr`**), `doctr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py`
