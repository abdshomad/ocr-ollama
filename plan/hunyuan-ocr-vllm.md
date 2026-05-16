# Hunyuan OCR (vLLM)

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [issues/hunyuanocr-vllm-integration.md](../issues/hunyuanocr-vllm-integration.md), [vllm_endpoints.json](../backend/config/vllm_endpoints.json)

## Goals

- Ship **Tencent HunyuanOCR** (`tencent/HunyuanOCR`) on the normal Run / Arena / History path via **vLLM** OpenAI API, behind the existing FastAPI gateway.
- Optional Compose service on port **8106**, profile **`hunyuanocr`**, aligned with [vLLM HunyuanOCR recipe](https://docs.vllm.ai/projects/recipes/en/latest/Tencent-Hunyuan/HunyuanOCR.html).

## Approach

- Catalog entry in `vllm_endpoints.json`; host env `VLLM_HUNYUAN_OCR_HOST`.
- `vllm-entrypoint.sh`: `--no-enable-prefix-caching`, `--mm-processor-cache-gb 0`, `--limit-mm-per-prompt '{"image": 1}'`.
- `vllm_client.py`: recipe-aligned `top_k` + `repetition_penalty` on the chat payload; higher default max tokens for long OCR output.
- `prompts.json`: default English prompt similar to the recipe (markdown body, HTML tables, LaTeX formulas).

## Tasks

- [x] `vllm_endpoints.json` + `docker-compose.yml` + backend `VLLM_HUNYUAN_OCR_HOST`
- [x] Entrypoint branch + `vllm_client` / `classify` / `prompts`
- [x] `.env.example`, `AGENTS.md`, `issues/*`, backlog / `ocr-engines.md` notes
