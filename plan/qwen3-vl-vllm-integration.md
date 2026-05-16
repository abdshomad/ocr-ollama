# Qwen3-VL (vLLM) for OCR

**Date:** 2026-05-16  
**Status:** Implemented  

## Goals

- Add **latest Qwen VL** generation (**Qwen3-VL** Instruct) to Run/Arena/History via the existing vLLM gateway pattern.
- Run on **GPU 1** by default with a Compose profile so operators unload other GPU-1 models first.

## Approach

- New Compose service `vllm-qwen3-vl` (profile `qwen3vl`), port **8105**, same `Dockerfile.vllm-ocr` image as LightOn/Chandra/Gemma4.
- `docker/vllm-entrypoint.sh`: image-only path (`--limit-mm-per-prompt.video 0`) per vLLM Qwen3-VL recipe; configurable `VLLM_QWEN3_VL_MAX_MODEL_LEN`.
- `vllm_endpoints.json` + backend `VLLM_QWEN3_VL_HOST`; `vllm_compose.py` maps `VLLM_QWEN3_VL_CUDA_DEVICE` (default **1**).
- `classify.py`: treat `Qwen*VL*` as **vision** tier (`ocr_capable`).
- `prompts.json` + `vllm_client.py`: OCR-style user prompt and optional higher `max_tokens` for VL output.

## Tasks

- [x] Compose + entrypoint + registry + classify + prompts + client tuning
- [x] Issue + `issues/README` + `AGENTS.md` + `plan/ocr-engines.md`
- [ ] Operator: stop GPU-1 services, `docker compose --profile qwen3vl up -d vllm-qwen3-vl`, verify `/api/models` + Run UI

## Related

- [ocr-engines.md](./ocr-engines.md) (general VLMs tier)  
- [vllm-deepseek-ocr-migration.md](./vllm-deepseek-ocr-migration.md)  
- vLLM recipe: https://github.com/vllm-project/recipes/blob/main/Qwen/Qwen3-VL.md  
