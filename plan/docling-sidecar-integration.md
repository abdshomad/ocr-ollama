# Docling CPU sidecar integration

**Date:** 2026-05-16  
**Status:** Implemented  

## Goals

- Expose **Docling** (IBM docling-project, MIT) as a **Run / Arena / History** engine via the existing FastAPI gateway.
- Run as an **optional Compose profile** CPU sidecar with the same `/health`, `/v1/models`, `/v1/ocr` contract as OnnxTR / docTR.

## Approach

- **HTTP sidecar** `docker/docling/serve.py`: `DocumentConverter`, temp file from upload, `export_to_markdown(strict_text=True)` for plain-ish text suitable for comparison.
- **Catalog:** `backend/config/ocr_engines.json` — `type: docling`, model id `docling`, port **8270**, profile `docling`.
- **Backend:** `docling_client.py` + `engine_registry` + `inference/factory.py` + `vllm_compose.py` probe tuples.
- **Docker:** `docker/Dockerfile.cpu-ocr-sidecars` (target `docling`) — `pip install docling` (pulls torch + layout stack; first run downloads HF artifacts).

## Tasks

- [x] Plan (this file)
- [x] `docker/docling/serve.py`, `Dockerfile.cpu-ocr-sidecars` (target `docling`), Compose service + volume + `DOCLING_HOST`
- [x] Registry, client, factory, compose probes, classify regex
- [x] `.env.example`, `AGENTS.md`, `issues/docling-integration.md`, backlog + `ocr-engines.md`
- [x] Smoke: Docker `docling` image build + `/v1/ocr`; browser Run with **`docling`** + sample **1.jpeg** → result heading **Result — docling** with non-empty text (~43s first warm cache).

## Related

- [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 3)
- [medium-four-ocr-models.md](./medium-four-ocr-models.md) (Docling was article “out of scope”; backlog supersedes for expansion queue)
