# Qwen3-Omni (vLLM-Omni) integration

**Date:** 2026-05-16

## Summary

Adds **Qwen3-Omni** as an optional **vLLM-Omni** service for multimodal (image) OCR through `/api/ocr` and Arena. Unlike Qwen3-VL, Omni models require **`vllm serve … --omni`** ([recipe](https://github.com/vllm-project/vllm-omni/blob/main/recipes/Qwen/Qwen3-Omni.md)), so this stack uses the **`vllm/vllm-omni`** image—not `vllm/vllm-openai`.

## Symptoms / operator notes

- **VRAM:** `Qwen/Qwen3-Omni-30B-A3B-*` is a large MoE; expect **high GPU memory** and long first pull. Prefer an **exclusive GPU** and stop other GPU-1 vLLM services before start.
- **First boot:** HTTP on **8112** may appear only after load + init completes (healthcheck allows a long `start_period`).

## Resolution / runbook

1. **Image:** default `VLLM_OMNI_IMAGE=vllm/vllm-omni:v0.20.0` (pin in `.env` if you need reproducibility).

2. **Start:**
   ```bash
   docker compose --profile qwen3omni up -d vllm-qwen3-omni
   ```

3. **Backend:** `VLLM_QWEN3_OMNI_HOST` (default `http://vllm-qwen3-omni:8112`) is set on the `backend` service in `docker-compose.yml`.

4. **Verify:** `curl -s http://127.0.0.1:${PORT:-3036}/api/models | jq` — look for `Qwen/Qwen3-Omni-30B-A3B-*` with `available: true` for the loaded id.

5. **GPU page:** start/stop service id **`qwen3omni`**.

6. **Optional env:** `VLLM_QWEN3_OMNI_MODEL`, `VLLM_QWEN3_OMNI_CUDA_DEVICE`, `VLLM_QWEN3_OMNI_GPU_MEMORY_UTIL`, `VLLM_QWEN3_OMNI_MAX_MODEL_LEN`, `VLLM_QWEN3_OMNI_MAX_TOKENS`, `VLLM_QWEN3_OMNI_CHAT_MODEL` (when vLLM uses `--served-model-name`), `VLLM_QWEN3_OMNI_DEPLOY_CONFIG` (custom Omni deploy YAML).

## Repo impact

- `docker-compose.yml` — `vllm-qwen3-omni` + `VLLM_QWEN3_OMNI_HOST`  
- `docker/vllm-omni-entrypoint.sh`  
- `backend/config/vllm_endpoints.json` — endpoint `qwen3omni`  
- `backend/app/vllm_compose.py` — `VLLM_QWEN3_OMNI_CUDA_DEVICE`  
- `backend/app/vllm_client.py` — `modalities: ["text"]` for Omni OCR requests; Thinking `<answer>` strip  
- `backend/config/prompts.json` — per-model prompts  
- `plan/qwen3-omni-vllm.md`
