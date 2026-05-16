# DeepSeek-OCR-2 — optional vLLM service

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [issues/deepseek-ocr-2-vllm-integration.md](../issues/deepseek-ocr-2-vllm-integration.md), [issues/wave-r-8-upstream-watchlist-triage.md](../issues/wave-r-8-upstream-watchlist-triage.md), [vLLM recipe](https://docs.vllm.ai/projects/recipes/en/stable/DeepSeek/DeepSeek-OCR-2.html)

## Goals

1. Expose **DeepSeek-OCR-2** (`deepseek-ai/DeepSeek-OCR-2`) as an optional **vLLM** endpoint on port **8114**, same OpenAI `/v1` contract as other GPU models.
2. Wire **registry** (`vllm_endpoints.json`), **backend** env, **GPU page** compose start/stop, **prompts** (default markdown-oriented prompt per HF card), **Run/Arena/History**.
3. Keep **DeepSeek-OCR (v1)** as the default `vllm-deepseek` stack; v2 is **profile `deepseek-ocr2`** only.

## Approach

- **Serve line:** Same as [vLLM DeepSeek-OCR-2 recipe](https://docs.vllm.ai/projects/recipes/en/stable/DeepSeek/DeepSeek-OCR-2.html): `NGramPerReqLogitsProcessor`, prefix cache off, `mm-processor-cache-gb 0`. Existing `docker/vllm-entrypoint.sh` branch `*deepseek-ocr*` matches **`DeepSeek-OCR-2`** (substring `deepseek-ocr`).
- **Image:** Same as `vllm-deepseek` — `vllm/vllm-openai` + bind-mounted entrypoint (no `Dockerfile.vllm-ocr` required).
- **GPU default:** **1** (`VLLM_DEEPSEEK_OCR2_CUDA_DEVICE`) to avoid colliding with **v1 on GPU 0** when both are used.

## Tasks

- [x] `vllm_endpoints.json` + `vllm_compose.py` (CUDA env + GPU resolution)
- [x] `docker-compose.yml` service + backend `VLLM_DEEPSEEK_OCR2_HOST`
- [x] `.env.example`
- [x] `prompts.json` for `deepseek-ai/DeepSeek-OCR-2`
- [x] `frontend/src/utils/models.ts` — default picker prefers exact v1 id over v2
- [x] `plan/ocr-engines.md`, `plan/ocr-engine-expansion-backlog.md`, `issues/*`, `AGENTS.md` common-tasks row
