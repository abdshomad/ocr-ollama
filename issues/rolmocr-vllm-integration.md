# RolmOCR — optional vLLM integration

**Date:** 2026-05-16

## Summary

**RolmOCR** (`reducto/RolmOCR`) is wired as an optional vLLM service: Compose service **`vllm-rolmocr`**, profile **`rolmocr`**, port **8110** on the Docker network, default GPU **1**. Backend routing uses `vllm_endpoints.json` and **`VLLM_ROLMOCR_HOST`**. Upstream recommends **`VLLM_USE_V1=1`** for serving ([HF model card](https://huggingface.co/reducto/RolmOCR)). **License:** Apache 2.0.

## Symptoms

- Model **`reducto/RolmOCR`** appears unavailable in the picker until `vllm-rolmocr` is running and `/v1/models` lists the served id (use **`VLLM_ROLMOCR_CHAT_MODEL`** if you override `--served-model-name`).

## Analysis / evidence

- Serve line (upstream): `export VLLM_USE_V1=1 && vllm serve reducto/RolmOCR`.
- OpenAI-style chat with image + text prompt; README uses `temperature=0.2`, `max_tokens=4096`.

## Resolution

1. Build/start (same image family as other OCR VLMs):

   ```bash
   docker compose --profile rolmocr build vllm-rolmocr
   docker compose --profile rolmocr up -d vllm-rolmocr
   ```

2. Backend env (Compose passes default):

   | Variable | Purpose |
   |----------|---------|
   | `VLLM_ROLMOCR_HOST` | Backend → vLLM (default `http://vllm-rolmocr:8110`) |
   | `VLLM_ROLMOCR_CUDA_DEVICE` | GPU index (default `1`) |
   | `VLLM_ROLMOCR_GPU_MEMORY_UTIL` | `--gpu-memory-utilization` (default `0.45`) |
   | `VLLM_ROLMOCR_MAX_MODEL_LEN` | Context cap (default `8192`) |
   | `VLLM_ROLMOCR_MAX_TOKENS` | Chat completion cap (default `4096`) |
   | `VLLM_ROLMOCR_TEMPERATURE` | Sampling (default `0.2`) |
   | `VLLM_ROLMOCR_CHAT_MODEL` | OpenAI `model` id if served under a different name |

3. Smoke: `curl -sS http://127.0.0.1:${PORT}/api/models` (via nginx) should list **`reducto/RolmOCR`** with `available: true` when the sidecar is healthy.

## Operational notes (2026-05-16)

- **VRAM:** On a shared GPU, RolmOCR may fail startup with `Free memory on device ... is less than desired GPU memory utilization`. Stop other vLLM containers on the same `device_ids` (or lower `VLLM_ROLMOCR_GPU_MEMORY_UTIL` only after enough memory is actually free).
- **EngineCore / port log:** vLLM may log `Port 8110 is already in use, trying port 8111` for the **internal** distributed rendezvous; the OpenAI server should still listen on **`VLLM_PORT` (8110)** for HTTP.

## Repo impact

- `backend/config/vllm_endpoints.json` — endpoint `rolmocr`
- `docker-compose.yml` — `vllm-rolmocr`, `VLLM_ROLMOCR_HOST` on backend
- `docker/vllm-entrypoint.sh` — `rolmocr` branch
- `backend/app/vllm_client.py` — max tokens, temperature, optional chat model alias
- `backend/config/prompts.json` — default prompt aligned with HF README
