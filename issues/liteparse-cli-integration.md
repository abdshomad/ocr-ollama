# LiteParse (`lit` CLI) integration

**Date:** 2026-05-16  
**Status:** Resolved (in-app)

## Summary

LiteParse runs as a **local subprocess** (`lit parse …`) from the FastAPI backend, not as a GPU HTTP service. The `litparse` catalog entry is **always listed**; availability is **true** when `lit --version` succeeds (`LITEPARSE_BIN` or `lit` on `PATH`). The backend Docker image installs `@llamaindex/liteparse` globally so Compose deployments have the CLI unless the image layer is skipped.

## Symptoms

- Model **litparse** shows **Offline** in the UI: Node/global CLI missing on the host, or custom image without the `npm install -g` step.
- **502** from `/api/ocr` with `ImageMagick is not installed`: backend image missing `imagemagick` (LiteParse uses it for raster formats). Rebuild the backend image after Dockerfile fix.
- **PDF / PS rasterization fails** while ImageMagick is present: install **`ghostscript`** (`gs`) — the backend image includes it next to `imagemagick` for common delegates.
- **502** with other `lit parse failed: …` messages: corrupt PDF, encrypted PDF without password, or LiteParse CLI error (see stderr in message).
- **502** with `ExperimentalWarning: Importing JSON modules is an experimental feature` (or similar Node stderr): usually **`NODE_OPTIONS=--warnings-as-errors`** (or inherited strict Node flags) combined with warnings from the global `lit` install; the backend now runs `lit` with **`NODE_NO_WARNINGS=1`** and strips `--warnings-as-errors` / `--throw-deprecation` from inherited **`NODE_OPTIONS`** for that subprocess only.
- **400** on PDF upload with a GPU model: expected — PDF is restricted to `model=litparse`.

## Analysis / evidence

- CLI reference: [LiteParse CLI](https://developers.llamaindex.ai/liteparse/cli-reference/) — `lit parse <file> -q`; backend uses `--format json` (joined `pages[].text`), **`--dpi`** (default 300), optional **`--ocr-server-url`**, **`--preserve-small-text`**.
- Repo wiring: `backend/app/liteparse_client.py`, `backend/config/ocr_engines.json` (`type: litparse`, `gpu_device: -1`), `factory.py` routing, `ocr_service.py` PDF allowlist, `backend/Dockerfile` `npm install -g @llamaindex/liteparse`.

## Resolution

- Install CLI on the host: `npm i -g @llamaindex/liteparse`, or set **`LITEPARSE_BIN`** to the full path of `lit`.
- For long documents, increase **`LITEPARSE_TIMEOUT`** (seconds, default 600).
- **Scanned PDFs / images look bad vs GPU models:** LiteParse uses Tesseract on rendered pages. The CLI default render DPI is **150** — the backend uses **`LITEPARSE_DPI`** default **300** plus **`--preserve-small-text`** so OCR is closer to usable. Raise DPI further if needed (`LITEPARSE_DPI=400`), set **`LITEPARSE_OCR_LANGUAGE`** for non-English, or point **`LITEPARSE_OCR_SERVER_URL`** at a compatible HTTP OCR service (see LiteParse docs). LiteParse still will not match full vision OCR on difficult scans; pick Chandra / DeepSeek for those.
- **Digital PDF garbage / mojibake:** That is usually broken embedded fonts or encoding in the PDF, not OCR; LiteParse extracts the text layer. Use a GPU model on an exported image, or repair the PDF.
- Use **Rebuild** backend image after Dockerfile changes so `lit` exists in the container.
- **Node warnings breaking `lit`:** Avoid setting **`NODE_OPTIONS=--warnings-as-errors`** on the **backend process** if you need LiteParse without pulling this fix; with current code, `lit` subprocesses use a sanitized env (see `liteparse_client._lit_subprocess_env`).

**Date changelog:** 2026-05-17 — LiteParse subprocess: **`NODE_NO_WARNINGS=1`** + strip strict **`NODE_OPTIONS`** flags so ExperimentalWarning from dependencies does not yield exit code 1 / misleading 502.

**Date changelog:** 2026-05-16 — OCR defaults: DPI 300, preserve-small-text, JSON page join (`LITEPARSE_FORMAT=json`).  
**Date changelog:** 2026-05-16 — Backend image: **`ghostscript`** alongside ImageMagick for PS/PDF delegates used by `convert`/LiteParse paths.

## Repo impact

- `backend/app/liteparse_client.py` — `_lit_subprocess_env()` for **`lit`** / **`lit --version`** only (warning suppression + safe **`NODE_OPTIONS`**).
- `backend/Dockerfile` — optional **`ghostscript`** alongside ImageMagick for delegates that shell out to `gs`.
- OCR uploads: `application/pdf` allowed for `/api/ocr` and `/api/arena` with validation tied to `litparse`.
- `/api/health` can report **ok** when only LiteParse is available (vLLM/Ollama down).
- GPU page: LiteParse appears under **All OCR services** as **local_cli** (no Load/Unload).
