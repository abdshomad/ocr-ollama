# LightOnOCR via vLLM (`lightonai/LightOnOCR-2-1B`)

**Date:** 2026-05-15  
**Model card:** [lightonai/LightOnOCR-2-1B](https://huggingface.co/lightonai/LightOnOCR-2-1B)  
**Related:** [medium-four-ocr-models.md](../plan/medium-four-ocr-models.md), [vllm-deepseek-ocr-integration.md](vllm-deepseek-ocr-integration.md)

## Summary

LightOnOCR runs in **`vllm-lighton`** on port **8102** with Compose profile **`lighton`** (not started on a plain `docker compose up`, to avoid colliding with DeepSeek on GPU 0). The backend routes `lightonai/LightOnOCR-2-1B` to `VLLM_LIGHTON_HOST`. Default prompt is **empty** (image-only request per HF card). Serve image uses `docker/Dockerfile.vllm-ocr` (`transformers>=5.4`).

## Serve (Compose)

```bash
docker compose --profile lighton build vllm-lighton
docker compose --profile lighton up -d vllm-lighton
docker compose logs -f vllm-lighton
```

Or use the **GPU** page → start **LightOnOCR** (backend passes `--profile lighton`).

Stop **GLM-OCR** first if both use `VLLM_LIGHTON_CUDA_DEVICE=1` (default).

Entrypoint flags:

```text
vllm serve lightonai/LightOnOCR-2-1B \
  --limit-mm-per-prompt '{"image": 1}' \
  --mm-processor-cache-gb 0 \
  --no-enable-prefix-caching
```

## Serve (host)

```bash
vllm serve lightonai/LightOnOCR-2-1B \
  --limit-mm-per-prompt '{"image": 1}' \
  --mm-processor-cache-gb 0 \
  --no-enable-prefix-caching \
  --host 0.0.0.0 --port 8102
```

Set `VLLM_LIGHTON_HOST=http://127.0.0.1:8102` for local backend.

## API / app

- **Prompt:** `""` in `backend/config/prompts.json` (image-only multimodal message)
- **No** DeepSeek `vllm_xargs` / ngram logits on LightOn requests
- **`speed_tier`:** `fast` in `vllm_endpoints.json`
- **Registry:** `backend/config/vllm_endpoints.json` id `lighton`

## vLLM / transformers

LightOnOCR-2 needs **transformers ≥ 5** (v5 release). If load fails on stock `vllm/vllm-openai:latest`, rebuild `vllm-lighton` from `docker/Dockerfile.vllm-ocr` or bump `VLLM_IMAGE` after validating vLLM release notes.

## VRAM

~1B weights — fits on one L40 with another service only if total utilization allows. **One heavy OCR model per GPU** is the safe default; use GPU page stop/start.

## Troubleshooting

GPU-page restart loop (`entrypoint.sh: Is a directory`, exit 126): see [vllm-lighton-gpu-compose-entrypoint-directory.md](vllm-lighton-gpu-compose-entrypoint-directory.md).

## Repo impact

| File | Change |
|------|--------|
| `backend/config/vllm_endpoints.json` | `lighton` endpoint |
| `docker-compose.yml` | `vllm-lighton` + profile |
| `docker/Dockerfile.vllm-ocr` | transformers 5.4+ |
| `docker/vllm-entrypoint.sh` | LightOn serve branch |
| `backend/config/prompts.json` | empty per-model prompt |
| `backend/app/vllm_compose.py` | compose profiles for ps/up/stop |
| `frontend/src/utils/models.ts` | prefer LightOn when online |
