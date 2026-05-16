# NuMarkdown-8B-Thinking (vLLM) integration

**Date:** 2026-05-16

## Summary

Adds **NuMarkdown** (`numind/NuMarkdown-8B-Thinking`, MIT) as an optional vLLM service for **image → markdown** extraction (reasoning Qwen2.5-VL VLM). Compose service **`vllm-numarkdown`**, profile **`numarkdown`**, port **8111** on the Docker network, default GPU **1**. Backend routing uses `vllm_endpoints.json` and **`VLLM_NUMARKDOWN_HOST`**. Serve flags follow the [model card](https://huggingface.co/numind/NuMarkdown-8B-Thinking): `--trust-remote-code`, `--limit-mm-per-prompt '{"image": 1}'`, **`VLLM_USE_V1=1`** (same pattern as RolmOCR).

## Symptoms / operator notes

- **VRAM:** ~8B class — treat like RolmOCR/Phi-4; use `VLLM_NUMARKDOWN_GPU_MEMORY_UTIL` (default **0.45** in compose) or stop other GPU-1 vLLM services before start.
- **Tokens:** Reasoning can consume many tokens; backend defaults **`VLLM_NUMARKDOWN_MAX_TOKENS=8192`** (override per GPU).
- **Output:** The model emits a final markdown block inside **`<answer>...</answer>`**; the backend strips to that block for Run/Arena/History when tags are present.

## Runbook

1. **Build (first time) and start:**

   ```bash
   docker compose --profile numarkdown build vllm-numarkdown
   docker compose --profile numarkdown up -d vllm-numarkdown
   ```

2. **Backend:** ensure `VLLM_NUMARKDOWN_HOST` points at the service (default in `docker-compose.yml`).

3. **Verify:** `curl -s "http://127.0.0.1:${PORT:-3036}/api/models" | jq` — look for `numind/NuMarkdown-8B-Thinking` with `available: true`.

4. **GPU page:** start/stop service id **`numarkdown`**.

## Environment reference

| Variable | Purpose |
|----------|---------|
| `VLLM_NUMARKDOWN_HOST` | Backend → vLLM (default `http://vllm-numarkdown:8111`) |
| `VLLM_NUMARKDOWN_MODEL` | HF model id (default `numind/NuMarkdown-8B-Thinking`) |
| `VLLM_NUMARKDOWN_CUDA_DEVICE` | GPU index for compose deploy |
| `VLLM_NUMARKDOWN_GPU_MEMORY_UTIL` | `gpu_memory_utilization` passed to entrypoint |
| `VLLM_NUMARKDOWN_MAX_MODEL_LEN` | `--max-model-len` |
| `VLLM_NUMARKDOWN_MAX_TOKENS` | Chat completion cap in backend |
| `VLLM_NUMARKDOWN_TEMPERATURE` | Sampling (default **0.4**) |
| `VLLM_NUMARKDOWN_CHAT_MODEL` | Optional OpenAI `model` id if using `--served-model-name` |

## Repo impact

- `docker-compose.yml` — `vllm-numarkdown` + `VLLM_NUMARKDOWN_HOST` on backend  
- `docker/vllm-entrypoint.sh` — `numarkdown` serve branch  
- `backend/config/vllm_endpoints.json` — endpoint `numarkdown`  
- `backend/app/vllm_client.py` — max tokens, temperature, optional chat alias, `<answer>` stripping  
- `backend/app/vllm_compose.py` — `VLLM_NUMARKDOWN_CUDA_DEVICE`  
- `backend/config/prompts.json` — default prompt for NuMarkdown  
- `plan/numarkdown-vllm-integration.md`  
