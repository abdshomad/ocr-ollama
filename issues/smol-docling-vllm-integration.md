# Smol Docling — optional vLLM integration

**Date:** 2026-05-16

## Summary

**Smol Docling** ([`docling-project/SmolDocling-256M-preview`](https://huggingface.co/docling-project/SmolDocling-256M-preview)) is exposed as an optional **vLLM OpenAI** service on port **8113** (Compose profile **`smoldocling`**). The FastAPI gateway calls `/v1/chat/completions` as for other VLMs, then converts the model’s **DocTags** output to **Markdown** using **`docling-core`** (same pattern as the Hugging Face model card).

## Symptoms / when to use this doc

- You enabled profile `smoldocling` but **Run** does not list the model or OCR fails with vLLM errors.
- You need the exact **serve flags** and **env vars** to reproduce the stack.

## Analysis / configuration

| Item | Value |
|------|--------|
| Model id (catalog) | `docling-project/SmolDocling-256M-preview` |
| Compose service | `vllm-smoldocling` |
| Profile | `smoldocling` |
| HTTP (Docker network) | `http://vllm-smoldocling:8113` |
| Backend env | `VLLM_SMOLDOCLING_HOST` (default set in `docker-compose.yml`) |
| GPU index | `VLLM_SMOLDOCLING_CUDA_DEVICE` (default **1**) |
| License | **CDLA-Permissive-2.0** (see HF card) |

Serve line is implemented in `docker/vllm-entrypoint.sh` when `VLLM_MODEL` matches `*smoldocling*`: `--trust-remote-code`, `--limit-mm-per-prompt '{"image": 1}'`, `--max-model-len` from `VLLM_SMOLDOCLING_MAX_MODEL_LEN` (default 8192), `--enforce-eager`, MM cache off.

The optional image build uses `docker/Dockerfile.vllm-ocr` (pinned `transformers>=5.4.0` on top of `vllm/vllm-openai`) so newer multimodal stacks load reliably.

## Resolution / commands

1. Build and start the sidecar (from repo root):

   ```bash
   docker compose --profile smoldocling up -d --build vllm-smoldocling
   ```

2. Ensure the **backend** container sees the host (default in compose: `VLLM_SMOLDOCLING_HOST=http://vllm-smoldocling:8113`). Recreate backend after changing `.env`.

3. Smoke API:

   ```bash
   curl -s http://127.0.0.1:${PORT:-3036}/api/health
   curl -s http://127.0.0.1:${PORT:-3036}/api/models | jq '.[] | select(.name|test("SmolDocling"))'
   ```

4. If vLLM uses `--served-model-name`, set **`VLLM_SMOLDOCLING_CHAT_MODEL`** to that id so chat completions and `/api/models` stay aligned.

5. If OCR returns **vLLM 400** about **maximum context length** vs **`max_tokens`/output**, the image consumes part of **`--max-model-len`**; lower **`VLLM_SMOLDOCLING_MAX_TOKENS`** (gateway default **4096**) before raising **`VLLM_SMOLDOCLING_MAX_MODEL_LEN`**.

6. **GPU page:** start/stop via `POST /api/vllm/services/smoldocling/start|stop` when Docker socket + `COMPOSE_HOST_PROJECT_DIR` are configured.

## Repo impact

- `backend/config/vllm_endpoints.json` — endpoint `smoldocling`
- `docker-compose.yml` — `vllm-smoldocling` + `VLLM_SMOLDOCLING_HOST` on backend
- `docker/vllm-entrypoint.sh` — Smol Docling branch
- `backend/app/vllm_client.py` — max tokens, optional chat model alias, DocTags→markdown
- `backend/pyproject.toml` / `uv.lock` — `docling-core` (and transitive deps) for conversion
- `backend/config/prompts.json` — default instruction “Convert this page to docling.”
- `plan/smol-docling-vllm-integration.md` — design note
