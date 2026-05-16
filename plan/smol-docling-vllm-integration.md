# Smol Docling — optional vLLM integration

**Date:** 2026-05-16  
**Status:** Implemented  

## Goals

- Ship **Smol Docling** ([`docling-project/SmolDocling-256M-preview`](https://huggingface.co/docling-project/SmolDocling-256M-preview): IDEFICS3 / SmolVLM-based document conversion to DocTags) on **Run / Arena / History** via the FastAPI gateway.
- Return **Markdown** in the UI by converting DocTags with **`docling-core`** in the backend (same idea as upstream HF examples).

## Approach

1. **`vllm_endpoints.json`** — endpoint **`smoldocling`**, Compose service **`vllm-smoldocling`**, profile **`smoldocling`**, Docker port **8113**, env **`VLLM_SMOLDOCLING_HOST`**.
2. **`docker/vllm-entrypoint.sh`** — branch for `smoldocling`: `--trust-remote-code`, `--limit-mm-per-prompt '{"image": 1}'`, capped `--max-model-len`, caching off; optional **`VLLM_SMOLDOCLING_SERVED_MODEL_NAME`**.
3. **Gateway (`vllm_client.py`)** — model-specific `max_tokens` (8192), optional **`VLLM_SMOLDOCLING_CHAT_MODEL`** alias; DocTags → markdown via Pillow + **`docling-core`** (`DocTagsDocument` / `DoclingDocument.load_from_doctags`).
4. **Prompts (`prompts.json`)** — default instruction aligned with the model card (“Convert this page to docling.”).

## Tasks

- [x] Plan + Compose + entrypoint + registry + prompts
- [x] Backend deps (`docling-core`) + markdown post-process
- [x] `vllm_compose` GPU device mapping + OCR tier regex
- [x] Docs: `issues/`, `.env.example`, `AGENTS.md`, backlog / engines ladders

## Related

- [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md)
- [ocr-engines.md](./ocr-engines.md)
- Existing vLLM pattern: [issues/rolmocr-vllm-integration.md](../issues/rolmocr-vllm-integration.md)
