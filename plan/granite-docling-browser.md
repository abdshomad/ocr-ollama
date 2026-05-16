# Granite Docling 258M (browser / Transformers.js)

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [browser-ocr-pipeline.md](./browser-ocr-pipeline.md), [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 5), [issues/granite-docling-browser.md](../issues/granite-docling-browser.md)

## Goals

- Ship **IBM Granite Docling** for **offline browser scan** using the published ONNX build `onnx-community/granite-docling-258M-ONNX` (Apache 2.0), matching the upstream Transformers.js recipe.
- Keep **no server-side ML** for this path; results still persist via `POST /api/scan`.

## Approach

1. Worker engine module: `AutoProcessor` + `AutoModelForVision2Seq` from `@huggingface/transformers`, multimodal chat prompt (plain-text oriented for **Scan** SKU/expiry heuristics — not the full DocTags HTML pipeline).
2. **Memory:** `do_image_splitting: false` on `/scan` for typical single-crop / product photos.
3. Wire `WorkerEngine` **`granite`**; Scan UI option **“Granite Docling”**; `parseEntities` confidence offset aligned with other small VLMs.

## Tasks

- [x] `engines/graniteDocling.ts` load + run
- [x] `ocr.worker.ts`, `types.ts`, `OCRService.ts`, `ScanPage.tsx`, `entityParser.ts`
- [x] `npm run build`; production bundle via `nginx` Dockerfile
- [x] Update [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) / [ocr-engines.md](./ocr-engines.md) browser ladder

## Changelog

| Date | Change |
|------|--------|
| 2026-05-16 | Marked **Implemented**; docs + backlog sync. After frontend changes, rebuild nginx: `docker compose build nginx && docker compose up -d nginx`. |
