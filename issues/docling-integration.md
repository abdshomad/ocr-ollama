# Docling sidecar integration

**Date:** 2026-05-16

## Summary

Docling is integrated as an **optional CPU sidecar** (`docling` Compose service, port **8270**, profile **`docling`**). The backend uses `DOCLING_HOST` and the catalog model id **`docling`**. Output is **Markdown/plain text** from `DoclingDocument.export_to_markdown(strict_text=True)` for sensible Arena/History comparison.

**Image build:** `docker/Dockerfile.docling` installs **CPU** `torch` / `torchvision` from the PyTorch CPU index **before** `pip install docling`, so pip does not resolve the default CUDA wheel stack on Linux.

## Run

```bash
docker compose --profile docling up -d docling
```

Ensure `backend` has `DOCLING_HOST=http://docling:8270` (default in `docker-compose.yml`).

## Symptoms / pitfalls

- **Very slow first request:** Hugging Face layout + OCR artifacts download on first conversion; health returns `model_loaded` once `DocumentConverter()` finishes startup (weights may still lazy-load on first OCR).
- **Large image / timeout:** Sidecar and backend use `VLLM_TIMEOUT` (default 600s in Compose). Increase if needed.
- **Memory:** Docling pulls PyTorch and document models; allocate enough RAM for the container (often **several GB**).

## Smoke

```bash
curl -sS http://127.0.0.1:8270/health
# Optional: small PNG
curl -sS -X POST http://127.0.0.1:8270/v1/ocr -F "image=@fixtures/ocr/sample.png" -F "model=docling"
```

## Repo impact

- `docker/docling/serve.py`, `docker/Dockerfile.docling`, `docker-compose.yml` service + volume
- `backend/app/docling_client.py`, `engine_registry.py`, `inference/factory.py`, `vllm_compose.py`, `classify.py`
- `backend/config/ocr_engines.json`
