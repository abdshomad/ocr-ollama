# Granite Docling 258M (browser / Transformers.js)

**Date:** 2026-05-16  
**Status:** In progress  
**Related:** [browser-ocr-pipeline.md](./browser-ocr-pipeline.md), [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 6)

## Goals

- Ship **IBM Granite Docling** for **offline browser scan** using the published ONNX build `onnx-community/granite-docling-258M-ONNX` (Apache 2.0), matching the upstream Transformers.js recipe.
- Keep **no server-side ML** for this path; results still persist via `POST /api/scan`.

## Approach

1. New worker engine module: `AutoProcessor` + `AutoModelForVision2Seq` from `@huggingface/transformers`, chat prompt aligned with HF README (`Convert this page to docling.`).
2. **Memory:** default `do_image_splitting: false` on `/scan` (single crop / product photo); users can rely on PaliGemma for heavy layout if needed.
3. Wire `WorkerEngine` / Scan UI option **“Granite Docling”**; `parseEntities` treats output as raw text / DocTags (same heuristics as other engines).

## Tasks

- [ ] `engines/graniteDocling.ts` load + run
- [ ] `ocr.worker.ts`, `types.ts`, `OCRService.ts`, `ScanPage.tsx`, `entityParser.ts`
- [ ] `npm run build`; browser verify `/scan` with a sample image
- [ ] Update [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) / [ocr-engines.md](./ocr-engines.md) browser ladder
