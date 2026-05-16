# Qwen3-Omni (vLLM-Omni)

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md), [issues/qwen3-omni-vllm-integration.md](../issues/qwen3-omni-vllm-integration.md), [vLLM-Omni Qwen3-Omni guide](https://docs.vllm.ai/projects/vllm-omni/en/latest/user_guide/examples/online_serving/qwen3_omni/)

## Goals

- Ship **Qwen3-Omni** (`Qwen/Qwen3-Omni-*`) on Run/Arena/History using the **vLLM-Omni** stack (`vllm serve … --omni`), distinct from stock `vllm/vllm-openai`.

## Approach

- Compose service **`vllm-qwen3-omni`**, profile **`qwen3omni`**, image **`vllm/vllm-omni:v0.20.0`** (override via `VLLM_OMNI_IMAGE`), port **8112**, entrypoint **`docker/vllm-omni-entrypoint.sh`**.
- `vllm_endpoints.json` endpoint **`qwen3omni`** + **`VLLM_QWEN3_OMNI_HOST`** on backend.
- Gateway: `modalities: ["text"]` on chat completions for OCR (text-only responses per vLLM-Omni API); optional **`VLLM_QWEN3_OMNI_CHAT_MODEL`** when using `--served-model-name`.
- Thinking variant: prompts ask for `<answer>…</answer>`; backend strips `<answer>` like NuMarkdown.

## Tasks

- [x] `docker/vllm-omni-entrypoint.sh` + compose service + backend env
- [x] `vllm_endpoints.json`, `vllm_compose.py`, `vllm_client.py`, `classify.py`, `prompts.json`
- [x] `issues/qwen3-omni-vllm-integration.md`, backlog + `ocr-engines.md` + `.env.example` + `AGENTS.md`
