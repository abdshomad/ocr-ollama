# vLLM GLM-OCR (`zai-org/GLM-OCR`)

**Date:** 2026-05-15  
**Recipe:** [vLLM GLM-OCR Usage Guide](https://docs.vllm.ai/projects/recipes/en/latest/GLM/GLM-OCR.html)  
**Related:** [vllm-deepseek-ocr-integration.md](vllm-deepseek-ocr-integration.md)

## Summary

GLM-OCR runs in **`vllm-glm`** alongside **`vllm-deepseek`** in `docker-compose.yml`. Users pick **`zai-org/GLM-OCR`** or **`deepseek-ai/DeepSeek-OCR`** from the Run/Arena model list; the backend routes to `VLLM_GLM_HOST` or `VLLM_DEEPSEEK_HOST`. Default prompt: **`Text Recognition:`**.

## Serve (Compose)

```bash
docker compose up -d --build
docker compose logs -f vllm-glm
```

Both services start by default; backend waits for both healthchecks.

Entrypoint adds MTP speculative decoding (recipe default):

```text
vllm serve zai-org/GLM-OCR \
  --speculative-config.method mtp \
  --speculative-config.num_speculative_tokens 1
```

Optional: `VLLM_MTP_SPECULATIVE_TOKENS=1` in `.env`.

## Serve (host)

```bash
vllm serve zai-org/GLM-OCR \
  --speculative-config.method mtp \
  --speculative-config.num_speculative_tokens 1 \
  --host 0.0.0.0 --port 8100
```

## API / app

- **Prompt:** `Text Recognition:` — in `backend/config/prompts.json` for `zai-org/GLM-OCR`
- **max_tokens:** use backend default `VLLM_MAX_TOKENS=2048` (recipe example)
- **No** DeepSeek `vllm_xargs` / ngram logits processor on GLM-OCR requests

## vLLM version notes

The recipe notes **transformers >= 5.0.0** and may require a **newer or nightly** vLLM build for full GLM-OCR support. If the container fails to load the model, try updating `VLLM_IMAGE` in `.env` per the recipe’s install section.

## Ollama vs vLLM GLM-OCR

| Path | Model id | Notes |
|------|----------|--------|
| Ollama | `glm-ocr:latest` | See [glm-ocr-cuda-context-load-failure.md](glm-ocr-cuda-context-load-failure.md) for `num_ctx` on 0.23.x |
| vLLM | `zai-org/GLM-OCR` | HuggingFace weights; MTP optional; set `INFERENCE_BACKEND=vllm` |

## Repo impact

| File | Change |
|------|--------|
| `docker/vllm-entrypoint.sh` | DeepSeek vs GLM-OCR serve flags |
| `docker-compose.glm-ocr.yml` | Override `VLLM_MODEL` |
| `docker-compose.yml` | Entrypoint + env for model selection |
| `backend/config/prompts.json` | `zai-org/GLM-OCR` prompt |
