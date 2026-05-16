# DeepSeek-OCR-2 — vLLM integration

**Date:** 2026-05-16  
**Related:** [plan/deepseek-ocr-2-vllm-integration.md](../plan/deepseek-ocr-2-vllm-integration.md), [vLLM recipe](https://docs.vllm.ai/projects/recipes/en/stable/DeepSeek/DeepSeek-OCR-2.html)

## Summary

**DeepSeek-OCR-2** (`deepseek-ai/DeepSeek-OCR-2`, ~3.4B) is served as an **optional** Compose service **`vllm-deepseek-ocr2`** (profile **`deepseek-ocr2`**, port **8114**), using the same **`docker/vllm-entrypoint.sh`** branch as **DeepSeek-OCR (v1)** (`*deepseek-ocr*` matches the v2 model id). The FastAPI gateway resolves the model to **`VLLM_DEEPSEEK_OCR2_HOST`** and sends OpenAI **`/v1/chat/completions`** with the same **DeepSeek** `extra_body` (`skip_special_tokens`, `vllm_xargs`) as v1.

## Symptoms / operator notes

- **Not in default `docker compose up`:** start with  
  `docker compose --profile deepseek-ocr2 up -d vllm-deepseek-ocr2`  
  or use the **GPU** page when the backend has Docker socket + `COMPOSE_HOST_PROJECT_DIR`.
- **GPU collision:** Default **`VLLM_DEEPSEEK_OCR2_CUDA_DEVICE=1`** so v2 does not share **GPU 0** with **`vllm-deepseek`** (v1). Adjust if your host layout differs.
- **VRAM:** ~3.4B BF16 — ensure no other large vLLM service on the same GPU.
- **vLLM crash loop / `ValueError: Free memory on device cuda:0 ... less than desired GPU memory utilization`:** vLLM compares **free VRAM** to `gpu_memory_utilization × card_size`. If GPU **1** already runs Hunyuan / RolmOCR / Smol Docling / Nemotron / etc., **free memory can be ~5 GiB** while the default **0.72** (from `.env`) asks for **~32 GiB** headroom. **Fix:** set a lower fraction and/or use a freer GPU, then recreate the service:
  - `VLLM_DEEPSEEK_OCR2_GPU_MEMORY_UTIL=0.22` (≈10 GiB reservation on a 46 GiB card — tune with `nvidia-smi`)
  - `VLLM_DEEPSEEK_OCR2_CUDA_DEVICE=0` if GPU **0** has more free memory than GPU **1**
  - Or **stop** other containers on that GPU via the GPU page / `docker compose stop …`

## Resolution / runbook

1. **Pull weights** (first run): ensure `HUGGING_FACE_HUB_TOKEN` in `.env` only if upstream gates (card is public).
2. **Start service:**  
   `docker compose --profile deepseek-ocr2 up -d --build vllm-deepseek-ocr2`
3. **Backend host:** default `VLLM_DEEPSEEK_OCR2_HOST=http://vllm-deepseek-ocr2:8114` is wired in `docker-compose.yml` for **`backend`**.
4. **UI:** **Run** / **Arena** — select **`deepseek-ai/DeepSeek-OCR-2`** when the endpoint is healthy.
5. **Prompts:** Default in `prompts.json` uses HF **document** style:  
   `<|grounding|>Convert the document to markdown.`  
   For plain text OCR without layout, use **Free OCR.** (per [HF README](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2)).

## Repo impact

- `backend/config/vllm_endpoints.json` — endpoint id **`deepseek-ocr2`**
- `docker-compose.yml` — service **`vllm-deepseek-ocr2`**, backend env **`VLLM_DEEPSEEK_OCR2_HOST`**
- `backend/app/vllm_compose.py` — **`VLLM_DEEPSEEK_OCR2_CUDA_DEVICE`** for GPU page
- `backend/config/prompts.json` — per-model prompt for **`deepseek-ai/DeepSeek-OCR-2`**
- `frontend/src/utils/models.ts` — default picker prefers exact **v1** id **`deepseek-ai/DeepSeek-OCR`** over v2 when both are listed

## Smoke (API)

```bash
curl -s http://127.0.0.1:${PORT:-3036}/api/models | jq '.models[] | select(.name|test("DeepSeek-OCR-2"))'
```

When the service is up, `/v1/models` inside the container should list `deepseek-ai/DeepSeek-OCR-2`.
