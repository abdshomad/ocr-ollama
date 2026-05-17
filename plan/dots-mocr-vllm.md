# Dots.MOCR — vLLM (`rednote-hilab/dots.mocr`)

**Date:** 2026-05-16  
**Status:** Implemented  
**Related:** [ocr-engine-expansion-backlog.md](./ocr-engine-expansion-backlog.md) (Wave 3), [rednote-hilab/dots.mocr](https://github.com/rednote-hilab/dots.mocr) (upstream; vLLM serve recipe)

## Goals

- Optional GPU vLLM service for **Dots.MOCR** layout/OCR, same patterns as Hunyuan / PaddleOCR-VL.
- Run / Arena / History / GPU page start-stop.

## Approach

- `vllm_endpoints.json` + `docker-compose.yml` (`vllm-dotsmocr`, profile `dotsmocr`, port **8108**).
- `docker/vllm-entrypoint.sh`: `--trust-remote-code`, `--chat-template-content-format string`, image limit, caps `max-model-len` for shared GPUs.
- `vllm_client.py`: default `max_tokens` **below** serve `max_model_len` so multimodal input fits (`VLLM_DOTS_MOCR_MAX_TOKENS`, default **2048**); optional `VLLM_DOTS_MOCR_CHAT_MODEL` when `--served-model-name` differs from the HF id.
- `prompts.json`: default `prompt_ocr`-style string (override for full layout JSON via UI).

## Tasks

- [x] Config + compose + entrypoint + backend env wiring
- [x] Client + classify + docs (`issues/`, backlog, `ocr-engines.md`, `AGENTS.md`, `.env.example`)
- [x] Smoke: `uv run python -c "from app.main import app"`; optional live vLLM OCR if GPU available
