# MinerU-Diffusion (nano_dvlm sidecar)

**Date:** 2026-05-16  
**Weights:** [opendatalab/MinerU-Diffusion-V1-0320-2.5B](https://huggingface.co/opendatalab/MinerU-Diffusion-V1-0320-2.5B)  
**Related:** [plan/mineru-diffusion-integration.md](../plan/mineru-diffusion-integration.md), [medium-four-ocr-models.md](../plan/medium-four-ocr-models.md)

## Summary

MinerU-Diffusion runs in **`mineru-diffusion`** on port **8200** with Compose profile **`mineru`**. The container wraps upstream **nano_dvlm** (`LLM.generate_messages`) behind `POST /v1/ocr`. The FastAPI backend routes `opendatalab/MinerU-Diffusion-V1-0320-2.5B` via `MINERU_DIFFUSION_HOST` and `backend/config/ocr_engines.json`. Default prompt: **`Text Recognition:`** (nano_dvlm adds a leading newline when needed).

## Image layout

`docker/Dockerfile.mineru-diffusion` uses a **multi-stage** build:

- **builder** — `git`, `curl`, `pip`, clone MinerU-Diffusion, install into `/opt/venv`, prune docs/assets/unused engines.
- **runtime** — CUDA base + `python3` only; copies venv and slim repo (no git/pip in final image).

Rebuild after Dockerfile changes: `docker compose --profile mineru build --no-cache mineru-diffusion`.

## Serve (Compose)

```bash
docker compose --profile mineru build mineru-diffusion
docker compose --profile mineru up -d mineru-diffusion
docker compose logs -f mineru-diffusion
```

Or **GPU** page → start **MinerU-Diffusion** (`service_id`: `mineru-diffusion`).

Stop other GPU services on the same device first (2.5B + diffusion decode needs exclusive VRAM on 16GB).

## Serve (host)

Build the image locally, run with GPU:

```bash
docker compose --profile mineru up -d mineru-diffusion
# or set MINERU_DIFFUSION_HOST=http://127.0.0.1:8200 after publishing port (dev only)
```

## API

| Route | Purpose |
|-------|---------|
| `GET /health` | Sidecar ready + model loaded |
| `GET /v1/models` | GPU page / catalog availability |
| `POST /v1/ocr` | Multipart `image`, form `prompt`, optional `model` |

## Environment

| Variable | Default | Notes |
|----------|---------|-------|
| `MODEL_PATH` | HF repo id | Local dir or Hugging Face id (snapshot download) |
| `MINERU_GPU_MEMORY_UTILIZATION` | `0.8` | nano_dvlm `LLM` arg |
| `MINERU_ENFORCE_EAGER` | `1` in Compose | Safer on 16GB; disable compile path |
| `MINERU_GEN_LENGTH` | `1024` | `max_new_tokens` |
| `MINERU_DIFFUSION_CUDA_DEVICE` | `0` | Compose GPU index |

## Known issues (upstream / article)

- **Hallucinations / duplicate blocks** on some pages — diffusion decoding artifact.
- **Sequential** mode slower (~15.6 s/page) vs **batched** (~10.5 s/page); sidecar uses single-message batch API (one page per request).
- **Russian / stray tokens** reported in article — post-process if needed.
- First start downloads ~2.5B weights; allow long `start_period` healthcheck (30 min).

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Build fails on `flash-attn` wheel | Python must be 3.12; wheel file must keep the full release name (not `flash_attn.whl`) |
| `Cannot uninstall pip` during image build | Do not `pip install --upgrade pip` over Debian `python3-pip`; use apt pip as-is |
| Crash: `Failed to find C compiler` / `gcc` + `-lcuda` on startup | Set `MINERU_ENFORCE_EAGER=1` (default); `serve.py` skips nano_dvlm warmup in eager mode |
| GPU OOM with LightOn on same device | Stop `vllm-lighton` before starting `mineru-diffusion` when both use `MINERU_DIFFUSION_CUDA_DEVICE=1` |
| CUDA OOM | Stop other vLLM services; lower `MINERU_GPU_MEMORY_UTILIZATION` |
| `503` from `/api/ocr` | `curl http://mineru-diffusion:8200/health` from backend network |
| Model offline in picker | Profile `mineru` not started; start via GPU page |

## Repo impact

| File | Change |
|------|--------|
| `backend/config/ocr_engines.json` | `mineru-diffusion` engine |
| `backend/app/engine_registry.py`, `mineru_client.py` | Routing + HTTP client |
| `backend/app/inference/factory.py` | Merge models/health/OCR dispatch |
| `docker/Dockerfile.mineru-diffusion`, `docker/mineru-diffusion/serve.py` | Sidecar |
| `docker-compose.yml` | `mineru-diffusion` service + profile |
| `backend/config/prompts.json` | Text Recognition prompt |
