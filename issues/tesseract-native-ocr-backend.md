# Native Tesseract — server `/api/ocr` (`model=tesseract`)

**Date:** 2026-05-16

## Summary

The **`tesseract`** catalog entry in `backend/config/ocr_engines.json` runs the **`tesseract` CLI** inside the **backend** container (not Tesseract.js on `/scan`). The backend image must include **`tesseract-ocr`** and at least one language pack (e.g. **`tesseract-ocr-eng`**).

## Symptoms

- **`tesseract` missing from `/api/models`** while `ocr_engines.json` lists it — backend image built before the apt layer was added; **rebuild** `backend`.
- **`tesseract` always offline** — binary missing in container (`which tesseract` empty); rebuild image or set `TESSERACT_BIN` to a valid path.

## Resolution

1. Rebuild backend after Dockerfile change:

   ```bash
   docker compose build backend && docker compose up -d backend
   ```

2. Optional env (host or Compose):

   - `TESSERACT_BIN` — default `tesseract`
   - `TESSERACT_LANG` — default `eng`
   - `TESSERACT_PSM` — default `3`

## Repo impact

- `backend/Dockerfile` — `apt-get install tesseract-ocr tesseract-ocr-eng`
