# Nemotron OCR v2 integration

**Date:** 2026-05-16  
**Status:** Implemented  

## Goals

- Ship **NVIDIA Nemotron OCR v2** (latest on Hugging Face: `nvidia/nemotron-ocr-v2`, default **v2_multilingual**) in **Run / Arena / History** via the existing FastAPI gateway.
- Keep the **browser → nginx → backend** rule; inference runs in an optional **GPU sidecar** (not vLLM — custom PyTorch + CUDA extension).

## Approach

- **Sidecar:** FastAPI app loads `NemotronOCRV2(model_dir=...)` from checkpoints baked under `/opt/nemotron-ocr-v2/v2_multilingual` (clone + `git lfs pull` at image build).
- **Registry:** New `ocr_engines.json` entry `type: "nemotron"`, `host_env: NEMOTRON_OCR_HOST`, compose profile `nemotron`, port **8210**.
- **Backend:** `nemotron_client.py` mirrors `mineru_client.py` (`/health`, `/v1/models`, `POST /v1/ocr` multipart).
- **GPU page:** Reuse `load_all_endpoints()` + `vllm_compose` health path extended for `nemotron` (same `/health` + `model_loaded` pattern as MinerU).

## Tasks

- [x] Plan (this file)
- [x] `docker/Dockerfile.nemotron-ocr` + `docker/nemotron-ocr/serve.py`
- [x] `docker-compose.yml` service `nemotron-ocr-v2` + backend `NEMOTRON_OCR_HOST`
- [x] `ocr_engines.json`, `engine_registry.py`, `nemotron_client.py`, `inference/factory.py`, `vllm_compose.py`
- [x] `prompts.json`, `classify.py`, `.env.example`, `frontend/src/utils/models.ts`
- [x] `plan/ocr-engines.md` + `issues/nemotron-ocr-v2-integration.md`
- [x] Smoke: `uv run python -c "from app.main import app"`, `npm run build`

## Related

- [ocr-engines.md](./ocr-engines.md), [medium-four-ocr-models.md](./medium-four-ocr-models.md)  
- Upstream: [nvidia/nemotron-ocr-v2](https://huggingface.co/nvidia/nemotron-ocr-v2)
