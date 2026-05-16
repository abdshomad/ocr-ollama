# Granite Docling (browser / Transformers.js)

**Date:** 2026-05-16

## Summary

**Granite Docling 258M** runs on **`/scan`** in a Web Worker via `@huggingface/transformers`, model ID **`onnx-community/granite-docling-258M-ONNX`** (Apache 2.0). Engine id in the UI/worker is **`granite`**. There is no FastAPI adapter: inference stays in the browser; only **`POST /api/scan`** persists results.

## Symptoms

- **Stale Scan UI:** Engine list missing “Granite Docling” after pulling newer frontend — nginx image still serves an old `dist/`. **Fix:** `docker compose build nginx && docker compose up -d nginx`.
- **First load slow:** ONNX + WASM artifacts download from Hugging Face (hundreds of MB). The engine `<select>` is disabled while the **current** engine finishes init (default **Auto** → TrOCR), so TrOCR download can block switching engines until it completes or fails.
- **Automation:** Cursor IDE browser may sit on “Loading model…” for a long time while HF fetches complete; verify in a normal desktop browser if needed.

## Analysis / evidence

- Worker: `frontend/src/browser-ocr/engines/graniteDocling.ts`
- Routing: `frontend/src/browser-ocr/ocr.worker.ts` (`loadGraniteDocling` / `runGraniteDocling`)
- UI: `frontend/src/pages/ScanPage.tsx` — option **Granite Docling** (`value: granite`)

## Resolution

1. Rebuild and restart nginx after frontend changes (see above).
2. For `/scan` proof: open **`http://localhost:${PORT:-3036}/scan`**, choose **Granite Docling**, load a sample image, **Run scan** — expect non-empty **Raw OCR** and structured fields when the entity parser matches.
3. Optional: pick **Fast scan** (Tesseract) first if TrOCR download is slow, then switch to Granite once the picker enables — or wait for Auto/TrOCR init to finish.

## Repo impact

- Frontend-only integration under `frontend/src/browser-ocr/` + `ScanPage.tsx`.
- No `ocr_engines.json` entry (browser tier is not routed through `/api/ocr`).
