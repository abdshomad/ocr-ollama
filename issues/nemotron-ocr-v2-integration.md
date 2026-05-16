# Nemotron OCR v2 sidecar integration

**Date:** 2026-05-16

## Changelog

- **2026-05-16:** Sidecar failed at runtime with `ModuleNotFoundError: No module named 'uvicorn'` — fixed by installing `uvicorn[standard]`, `fastapi`, and `python-multipart` in `docker/Dockerfile.nemotron-ocr`. Rebuild image before `up`.

## Summary

**Nemotron OCR v2** (`nvidia/nemotron-ocr-v2`, default **v2_multilingual**) is integrated as an optional **GPU sidecar** (FastAPI + `nemotron_ocr` PyTorch pipeline with a CUDA extension), not via vLLM. The app backend calls `NEMOTRON_OCR_HOST` with the same multipart pattern as MinerU-Diffusion (`/health`, `/v1/models`, `POST /v1/ocr`).

## Symptoms

- N/A at integration time (greenfield).

## Analysis / evidence

- Model card: [nvidia/nemotron-ocr-v2](https://huggingface.co/nvidia/nemotron-ocr-v2) — install from `nemotron-ocr/` in the HF repo; weights under `v2_multilingual/` and `v2_english/` (Git LFS).
- Runtime requires **Python 3.12** per upstream `pyproject.toml` (`requires-python = ">=3.12,<3.13"`). Base image **`nvcr.io/nvidia/pytorch:25.09-py3`** matches.
- English vs multilingual: set compose env **`NEMOTRON_VARIANT=english`** (or `en`) to load `v2_english/`; default **`multilingual`** uses `v2_multilingual/`.

## Resolution

0. **Runtime deps (required):** The sidecar `serve.py` imports `uvicorn` and `fastapi`; the NVIDIA PyTorch base image does not include them. The Dockerfile now runs:
   `pip install "uvicorn[standard]" fastapi python-multipart` after installing `nemotron_ocr`. Rebuild: `docker compose --profile nemotron build nemotron-ocr-v2`.

1. **Build sidecar:**  
   `docker compose --profile nemotron build nemotron-ocr-v2`  
   First build clones the HF repo and runs `git lfs pull` (large); CUDA extension builds with `BUILD_CPP_FORCE=1`.

2. **Run:**  
   `docker compose --profile nemotron up -d nemotron-ocr-v2`  
   Assign GPU with **`NEMOTRON_OCR_CUDA_DEVICE`** (default `0` in compose). Stop other GPU-heavy services on the same device if VRAM is tight (sidecar is smaller than VLMs but still needs a CUDA GPU).

3. **Backend:**  
   Ensure **`NEMOTRON_OCR_HOST`** points at the sidecar (default in compose: `http://nemotron-ocr-v2:8210`). After changing Python under `backend/app/`, **rebuild the backend image** (`docker compose build backend && docker compose up -d backend`) so the container picks up new modules (only `backend/config` is bind-mounted by default).

4. **Merge level:**  
   Sidecar accepts `merge_level` form field: `word` | `sentence` | `paragraph` (default `paragraph`). The backend passes `paragraph` unless the user prompt contains one of those words (same heuristic style as other engines).

5. **Verification (this repo, 2026-05-16):** After `docker compose --profile nemotron up -d nemotron-ocr-v2` (rebuilt image), `GET /api/models` shows `nvidia/nemotron-ocr-v2` with `available: true`. `POST /api/ocr` with a PNG containing the string `Nemotron OCR verification 2026` returned `text` exactly that string (~24 s first inference via nginx).

## Repo impact

- `docker/Dockerfile.nemotron-ocr`, `docker/nemotron-ocr/serve.py`
- `docker-compose.yml` service `nemotron-ocr-v2` (profile **`nemotron`**), backend env `NEMOTRON_OCR_HOST`
- `backend/config/ocr_engines.json` (`type`: **`nemotron`**), `nemotron_client.py`, `inference/factory.py`, `vllm_compose.py`
- Plan: [plan/nemotron-ocr-v2-integration.md](../plan/nemotron-ocr-v2-integration.md)
