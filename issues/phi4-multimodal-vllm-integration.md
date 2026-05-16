# Phi-4-multimodal — vLLM (`microsoft/Phi-4-multimodal-instruct`)

**Date:** 2026-05-16

**Changelog (2026-05-16):** First load can fail with **`ImportError: ... requires ... scipy`** when building the HF processor from the model repo — the base `vllm-openai` image may not include **scipy**. **`docker/Dockerfile.vllm-ocr`** installs `scipy` alongside `transformers>=5.4.0`. Rebuild: `docker compose --profile phi4mm build vllm-phi4-mm && docker compose --profile phi4mm up -d --force-recreate vllm-phi4-mm`.

**Changelog (2026-05-16):** Optional services use the **baked** `/docker/vllm-entrypoint.sh` from the **`ocr-ollama-vllm-ocr`** image (no host bind mount). After editing `docker/vllm-entrypoint.sh`, rebuild that image (same pattern as [dots-mocr-vllm-integration.md](dots-mocr-vllm-integration.md)):  
`docker compose --profile phi4mm build vllm-phi4-mm && docker compose --profile phi4mm up -d --force-recreate vllm-phi4-mm`.

## Summary

**Phi-4-multimodal-instruct** is integrated as an **optional vLLM** service: `vllm-phi4-mm`, Compose profile **`phi4mm`**, port **8109** on the Docker network, default GPU **1**. Uses the same **`docker/Dockerfile.vllm-ocr`** image as other OCR VLMs. Backend routing uses `vllm_endpoints.json` and `VLLM_PHI4_MM_HOST`. **License:** Microsoft Research License — verify terms on the [Hugging Face model card](https://huggingface.co/microsoft/Phi-4-multimodal-instruct) before production use.

## Symptoms (if misconfigured)

- Model **`microsoft/Phi-4-multimodal-instruct`** appears in `/api/models` as unavailable — container not running, wrong `VLLM_PHI4_MM_HOST`, or vLLM still starting (first load can take many minutes).
- **OOM / crash on start** — stop other optional vLLM services on the same GPU; lower `VLLM_PHI4_MM_GPU_MEMORY_UTIL` or `VLLM_PHI4_MM_MAX_MODEL_LEN`.
- **Restart loop / engine init failed** — logs show **`Free memory on device … is less than desired GPU memory utilization`**. Stop other vLLM (or heavy) processes on the **same GPU index**, lower `VLLM_PHI4_MM_GPU_MEMORY_UTIL`, or move Phi-4 to a free GPU via `VLLM_PHI4_MM_CUDA_DEVICE`.
- **Remote code / trust** — serve path must include `--trust-remote-code` (handled in `docker/vllm-entrypoint.sh`; requires **rebuilt** `ocr-ollama-vllm-ocr` image — see changelog above).

## Operator steps

1. Build (first time or after Dockerfile change):

   ```bash
   docker compose --profile phi4mm build vllm-phi4-mm
   ```

2. Start (prefer an exclusive or lightly loaded GPU — stop other GPU-1 vLLM services if VRAM is tight):

   ```bash
   docker compose --profile phi4mm up -d vllm-phi4-mm
   ```

3. Verify:

   ```bash
   curl -s http://127.0.0.1:${PORT:-3036}/api/models | jq '.[] | select(.name=="microsoft/Phi-4-multimodal-instruct")'
   ```

## Analysis / evidence

- [vLLM Phi-4 recipe](https://docs.vllm.ai/projects/recipes/en/latest/Microsoft/Phi-4.html): multimodal server uses `microsoft/Phi-4-multimodal-instruct` with `--trust-remote-code`; demo uses `--max-model-len 4000` — this repo defaults **8192** via `VLLM_PHI4_MM_MAX_MODEL_LEN` for OCR while keeping KV usage bounded vs the model’s 128k card default.
- Entrypoint adds `--limit-mm-per-prompt '{"image": 1}'`, `--no-enable-prefix-caching`, `--mm-processor-cache-gb 0` for parity with other vision endpoints.
- Client: `VLLM_PHI4_MM_MAX_TOKENS` default **4096** in `vllm_client.py` (override via env).

## Resolution

Follow **Operator steps** above; set **`HUGGING_FACE_HUB_TOKEN`** if Hub access requires it.

Optional `.env` / Compose overrides:

| Variable | Purpose |
|---------|---------|
| `VLLM_PHI4_MM_HOST` | Backend → vLLM (default `http://vllm-phi4-mm:8109` in Compose) |
| `VLLM_PHI4_MM_MODEL` | Weight id (default `microsoft/Phi-4-multimodal-instruct`) |
| `VLLM_PHI4_MM_CUDA_DEVICE` | GPU index (default `1`) |
| `VLLM_PHI4_MM_GPU_MEMORY_UTIL` | `--gpu-memory-utilization` (default **0.45** — vLLM compares `util × total_vram` to **free** mem at init; **0.55** often fails on 48GB-class GPUs with headroom already reserved) |
| `VLLM_PHI4_MM_MAX_MODEL_LEN` | Passed into entrypoint (default `8192`) |
| `VLLM_PHI4_MM_MAX_TOKENS` | Backend chat cap (default `4096`) |
| `VLLM_PHI4_MM_CHAT_MODEL` | OpenAI `model` field override if `--served-model-name` differs |

## Repo impact

- `docker/Dockerfile.vllm-ocr` — **`scipy`** pip install (Phi-4 HF processor dynamic import)
- `backend/config/vllm_endpoints.json` — endpoint `phi4multimodal`
- `docker-compose.yml` — `vllm-phi4-mm`, `VLLM_PHI4_MM_HOST` on backend
- `docker/vllm-entrypoint.sh` — Phi-4 multimodal branch
- `backend/app/vllm_client.py` — max_tokens + optional chat model alias
- `backend/app/inference/classify.py` — vision tier
- `backend/app/vllm_compose.py` — `VLLM_PHI4_MM_CUDA_DEVICE`
- `backend/config/prompts.json` — default OCR prompt
- `plan/phi-4-multimodal-vllm.md`, `plan/ocr-engines.md`, `plan/ocr-engine-expansion-backlog.md`, `.env.example`, `AGENTS.md`
