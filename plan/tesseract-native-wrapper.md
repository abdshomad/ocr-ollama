# Native Tesseract wrapper (subprocess)

**Date:** 2026-05-16
**Status:** Implemented

## Goals
Add a **native Tesseract** server-side OCR engine via subprocess (`tesseract` binary), matching the LiteParse subprocess pattern. Complements the existing browser Tesseract.js and provides a CPU-baseline server OCR path.

## Approach
- Subprocess pattern (like `liteparse_client.py`): detect `tesseract` binary via `shutil.which`, write image to temp file, run `tesseract <file> stdout -l eng`, return text.
- No Docker sidecar needed — Tesseract runs directly in the backend container (install via apt).
- Engine type `tesseract`, model id `tesseract`, speed tier `fast`.

## Tasks
- [x] Add `tesseract` entry to `backend/config/ocr_engines.json`
- [x] Create `backend/app/tesseract_client.py` (subprocess wrapper)
- [x] Add `is_tesseract_model` / `all_tesseract_models` to `backend/app/engine_registry.py`
- [x] Register in `backend/app/inference/factory.py`
- [x] Add `tesseract` default prompt to `backend/config/prompts.json`
- [x] Update `plan/ocr-engines.md` and backlog

## Related
- [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) — Wave 1
- [plan/ocr-engines.md](../plan/ocr-engines.md)
