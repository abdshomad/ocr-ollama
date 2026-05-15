# Chandra OCR 2 via vLLM (`datalab-to/chandra-ocr-2`)

**Date:** 2026-05-16  
**Model card:** [datalab-to/chandra-ocr-2](https://huggingface.co/datalab-to/chandra-ocr-2)  
**Related:** [plan/chandra-vllm-integration.md](../plan/chandra-vllm-integration.md), [medium-four-ocr-models.md](../plan/medium-four-ocr-models.md)

## Summary

Chandra OCR 2 runs in **`vllm-chandra`** on port **8103** with Compose profile **`chandra`**. The backend routes `datalab-to/chandra-ocr-2` to `VLLM_CHANDRA_HOST`. Default prompt follows upstream **`ocr_layout`** (layout HTML with `data-bbox` / `data-label`). Serve image uses `docker/Dockerfile.vllm-ocr` (`transformers>=5.4`).

## Serve (Compose)

```bash
docker compose --profile chandra build vllm-chandra
docker compose --profile chandra up -d vllm-chandra
docker compose logs -f vllm-chandra
```

Or **GPU** page → start **Chandra OCR 2** (`service_id`: `chandra`).

Stop **GLM-OCR**, **LightOnOCR**, or **MinerU-Diffusion** on the same GPU before starting Chandra (~4B + long context is VRAM-heavy).

Entrypoint flags (from [chandra.scripts.vllm](https://github.com/datalab-to/chandra)):

```text
vllm serve datalab-to/chandra-ocr-2 \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --limit-mm-per-prompt '{"image": 1}' \
  --mm-processor-kwargs '{"min_pixels": 3136, "max_pixels": 6291456}'
```

## Serve (host)

```bash
VLLM_MODEL=datalab-to/chandra-ocr-2 VLLM_PORT=8103 /docker/vllm-entrypoint.sh
```

Set `VLLM_CHANDRA_HOST=http://127.0.0.1:8103` for local backend.

## API / app

- **Prompt:** layout HTML instruction in `backend/config/prompts.json`
- **No** DeepSeek `vllm_xargs` on Chandra requests
- **`speed_tier`:** `slow` in `vllm_endpoints.json`
- **`max_tokens`:** `VLLM_CHANDRA_MAX_TOKENS` default **4096** (override via env)
- **`top_p`:** `0.1` default (matches upstream vLLM client)

## VRAM

~5.3B parameters (BF16). Treat as **one heavy model per GPU** on 16–24GB cards. Official `chandra_vllm` uses `max-model-len` **18000** on H100; this repo defaults **8192** via `VLLM_CHANDRA_MAX_MODEL_LEN` to fit L40/A10-class GPUs.

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| Model offline in picker | Profile `chandra` not started |
| CUDA OOM on start | Another vLLM service on same GPU; stop via GPU page |
| Truncated HTML output | Raise `VLLM_CHANDRA_MAX_TOKENS` |
| Load / template errors | Rebuild `vllm-chandra` from `Dockerfile.vllm-ocr` |

## Repo impact

| File | Change |
|------|--------|
| `backend/config/vllm_endpoints.json` | `chandra` endpoint |
| `docker-compose.yml` | `vllm-chandra` + profile |
| `docker/vllm-entrypoint.sh` | Chandra serve branch |
| `backend/app/vllm_client.py` | Chandra max_tokens / top_p |
| `backend/config/prompts.json` | layout HTML prompt |
