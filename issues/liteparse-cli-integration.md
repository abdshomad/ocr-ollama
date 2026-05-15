# LiteParse (`lit` CLI) integration

**Date:** 2026-05-16  
**Status:** Resolved (in-app)

## Summary

LiteParse runs as a **local subprocess** (`lit parse …`) from the FastAPI backend, not as a GPU HTTP service. The `litparse` catalog entry is **always listed**; availability is **true** when `lit --version` succeeds (`LITEPARSE_BIN` or `lit` on `PATH`). The backend Docker image installs `@llamaindex/liteparse` globally so Compose deployments have the CLI unless the image layer is skipped.

## Symptoms

- Model **litparse** shows **Offline** in the UI: Node/global CLI missing on the host, or custom image without the `npm install -g` step.
- **502** from `/api/ocr` with `ImageMagick is not installed`: backend image missing `imagemagick` (LiteParse uses it for raster formats). Rebuild the backend image after Dockerfile fix.
- **502** with other `lit parse failed: …` messages: corrupt PDF, encrypted PDF without password, or LiteParse CLI error (see stderr in message).
- **400** on PDF upload with a GPU model: expected — PDF is restricted to `model=litparse`.

## Analysis / evidence

- CLI reference: [LiteParse CLI](https://developers.llamaindex.ai/liteparse/cli-reference/) — `lit parse <file> -q --format text`.
- Repo wiring: `backend/app/liteparse_client.py`, `backend/config/ocr_engines.json` (`type: litparse`, `gpu_device: -1`), `factory.py` routing, `ocr_service.py` PDF allowlist, `backend/Dockerfile` `npm install -g @llamaindex/liteparse`.

## Resolution

- Install CLI on the host: `npm i -g @llamaindex/liteparse`, or set **`LITEPARSE_BIN`** to the full path of `lit`.
- For long documents, increase **`LITEPARSE_TIMEOUT`** (seconds, default 600).
- Use **Rebuild** backend image after Dockerfile changes so `lit` exists in the container.

## Repo impact

- OCR uploads: `application/pdf` allowed for `/api/ocr` and `/api/arena` with validation tied to `litparse`.
- `/api/health` can report **ok** when only LiteParse is available (vLLM/Ollama down).
- GPU page: LiteParse appears under **All OCR services** as **local_cli** (no Load/Unload).
