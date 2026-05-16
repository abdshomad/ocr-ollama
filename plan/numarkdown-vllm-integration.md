# NuMarkdown-8B-Thinking (vLLM) for document → markdown OCR

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [medium-four-ocr-models.md](./medium-four-ocr-models.md), [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md), [issues/numarkdown-vllm-integration.md](../issues/numarkdown-vllm-integration.md)

## Goals

- Ship **NuMarkdown** (`numind/NuMarkdown-8B-Thinking`, MIT) as an optional vLLM sidecar for **image → markdown** extraction (reasoning VLM, Qwen2.5-VL family), aligned with Run / Arena / History and GPU page start/stop.

## Approach

- Same stack as RolmOCR / Phi-4: `Dockerfile.vllm-ocr`, `docker/vllm-entrypoint.sh` branch (`--trust-remote-code`, image-only limits).
- `vllm_endpoints.json` endpoint **`numarkdown`**, Compose **`vllm-numarkdown`**, profile **`numarkdown`**, port **8111**, env **`VLLM_NUMARKDOWN_HOST`**.
- Backend: `vllm_client` — higher default **`max_tokens`**, optional temperature; strip **`<answer>...</answer>`** from model output when present (thinking lives outside `<answer>`).

## Tasks

- [x] `vllm_endpoints.json` + `vllm-entrypoint.sh` + `docker-compose.yml` + backend env
- [x] `vllm_client.py` / `vllm_compose.py` / `classify.py` / `prompts.json`
- [x] `issues/numarkdown-vllm-integration.md`, backlog + `ocr-engines.md` + `.env.example` + `AGENTS.md`
