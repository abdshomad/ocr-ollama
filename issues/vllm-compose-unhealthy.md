# vLLM Compose container unhealthy

**Date:** 2026-05-15  
**See also:** [vllm-deepseek-ocr-integration.md](vllm-deepseek-ocr-integration.md) — full working setup and all fixes (including `max_tokens`).

## Summary

`docker compose up` failed with `container ocr-ollama-vllm-1 is unhealthy` for three separate reasons: invalid `--chat-template` path, GPU memory contention on device 0, and Compose marking the service unhealthy before the model finished loading.

## Symptoms

- `dependency failed to start: container ocr-ollama-vllm-1 is unhealthy`
- Backend/nginx stay in `Created` state

## Analysis / evidence

1. **Chat template crash (immediate):**
   ```
   ValueError: The supplied chat template string (vllm/transformers_utils/chat_templates/template_deepseek_ocr.jinja) ... doesn't exist!
   ```
   Official [DeepSeek-OCR vLLM recipe](https://docs.vllm.ai/projects/recipes/en/latest/DeepSeek/DeepSeek-OCR.html) does not use `--chat-template`. Removed from `docker-compose.yml`.

2. **GPU OOM on cuda:0:**
   ```
   ValueError: Free memory on device cuda:0 (37.35/44.39 GiB) ... less than desired GPU memory utilization (0.92, 40.84 GiB)
   ```
   Host had ~7 GiB used on GPU 0 (Ollama / host vLLM on port 8100). GPU 1 was idle. Fixed with `CUDA_VISIBLE_DEVICES=1` and `--gpu-memory-utilization 0.85`.

3. **Slow first start:** DeepSeek-OCR load can take many minutes. Healthcheck `start_period` increased to 1800s; `docker compose up` waits for `service_healthy`.

## Resolution

- `docker-compose.yml`: positional model arg, no chat-template, `VLLM_CUDA_VISIBLE_DEVICES` (default `1`), `VLLM_GPU_MEMORY_UTILIZATION` (default `0.85`), longer healthcheck grace.
- `.env.example`: document GPU env vars.

## Repo impact

`docker-compose.yml`, `.env.example`, `README.md`
