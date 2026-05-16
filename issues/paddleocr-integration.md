# PaddleOCR CPU sidecar integration

**Date:** 2026-05-16  
**Related:** [plan/paddleocr-integration.md](../plan/paddleocr-integration.md)

## Summary

**Classical PaddleOCR** (PP-OCR, Apache 2.0) is integrated as an optional **PaddlePaddle CPU** HTTP sidecar (`paddleocr`, compose profile **`paddleocr`**, port **8260**). **PaddleOCR-VL** (0.9B VLM) runs on optional **vLLM** (`vllm-paddleocr-vl`, profile **`paddleocr-vl`**, model **`PaddlePaddle/PaddleOCR-VL`**) — see [paddleocr-vl-vllm-integration.md](paddleocr-vl-vllm-integration.md). This is **not** Ollama **PaddleOCR-VL** ([paddleocr-vl-ollama-load-failure.md](paddleocr-vl-ollama-load-failure.md)). The FastAPI backend calls `PADDLEOCR_HOST` with the same contract as other CPU sidecars (`GET /health`, `POST /v1/ocr`). Model id in the picker: **`paddleocr`**.

## Symptoms

- Model picker shows **paddleocr** as unavailable — profile `paddleocr` not started or `PADDLEOCR_HOST` wrong for the backend.
- First start slow — detection/recognition weights download into `/root/.paddleocr` (volume `paddleocr-model-cache`). Compose `start_period` is **900s**.

## Analysis / evidence

- Sidecar startup failed with `ImportError: libGL.so.1` until **`libgl1`** was added to the shared CPU sidecar base / `paddleocr` target in `docker/Dockerfile.cpu-ocr-sidecars` (OpenCV via `paddleocr`).

## Resolution

```bash
docker compose --profile paddleocr build paddleocr
docker compose --profile paddleocr up -d paddleocr
# In-stack: backend reaches http://paddleocr:8260/health
curl -s "http://127.0.0.1:${PORT:-3036}/api/models" | jq '.models[] | select(.name=="paddleocr")'
```

From the **GPU** page, start service **`paddleocr`**. Default in-stack URL: `http://paddleocr:8260` (`PADDLEOCR_HOST`).

Language (PaddleOCR `lang` code, default `en`):

- Set `PADDLEOCR_LANG=en` or `ch`, etc., on the `paddleocr` service in Compose or `.env`.

## Repo impact

- `docker/Dockerfile.cpu-ocr-sidecars` (build target `paddleocr`), `docker/paddleocr/serve.py`
- `docker-compose.yml` service `paddleocr`, volumes `paddleocr-model-cache` / `paddleocr-paddle-cache`, backend `PADDLEOCR_HOST`
- `backend/config/ocr_engines.json` (`type`: **`paddleocr`**), `paddleocr_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py`
