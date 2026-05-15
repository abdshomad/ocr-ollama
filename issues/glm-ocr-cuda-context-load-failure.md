# glm-ocr:latest — GPU load failure (context / CUDA)

**Date:** 2026-05-15  
**Ollama version (host):** 0.23.3  
**Symptom (app):** `Ollama could not load model 'glm-ocr:latest' (missing or corrupt files…)` with detail `model failed to load, this may be due to resource limitations or an internal error`

## Summary

The model **is present** (~2.2 GB) and `ollama pull` is **not** the fix. Ollama 0.23.3 crashes while loading `glm-ocr` on CUDA when it tries to allocate the model’s **131072-token** default context. The runner aborts with `GGML_ASSERT(ggml_nbytes(src0) <= INT_MAX) failed` in `ggml-cuda/cpy.cu`. Passing a smaller **`num_ctx`** (e.g. 4096–8192) in `/api/chat` loads and runs successfully.

## Symptoms

- HTTP 500 from `POST /api/chat` with `model failed to load…`
- App message suggests `ollama pull` (misleading for this case)
- `journalctl -u ollama` shows runner SIGABRT, not missing blob

## Evidence

### Model listed and blob on disk

```bash
ollama list | grep glm-ocr
# glm-ocr:latest    6effedd0dc8a    2.2 GB

ls -la /usr/share/ollama/.ollama/models/blobs/sha256-65493e1f85b9ea4ba3ed793515fde13cbdbea7d74ad2c662b566b146eab0081e
# ~2.2 GB, present
```

### Default chat request fails

```bash
curl -s http://localhost:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"glm-ocr:latest","messages":[{"role":"user","content":"test"}],"stream":false}'
# {"error":"model failed to load, this may be due to resource limitations..."}
```

### Server log (root cause)

```text
/ml/backend/ggml/ggml/src/ggml-cuda/cpy.cu:396: GGML_ASSERT(ggml_nbytes(src0) <= INT_MAX) failed
SIGABRT: abort
llama runner terminated exit status 2
```

VRAM was **not** exhausted (~35 GiB free per GPU); this is not a simple OOM.

### Workaround: reduce context

```bash
curl -s http://localhost:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"glm-ocr:latest","messages":[{"role":"user","content":"hi"}],"stream":false,"options":{"num_ctx":4096}}'
# HTTP 200, model loads
```

`ollama show glm-ocr:latest` reports `context length 131072`; Ollama may also log `requested context size too large for model num_ctx=262144`.

## Resolution

### In this repo

- `backend/app/ollama_client.py` — all OCR `/api/chat` calls include `"options": {"num_ctx": OCR_NUM_CTX}` (default **8192**, env `OCR_NUM_CTX`).
- `format_ollama_error()` — glm-ocr-specific hint when load still fails.

Restart backend or `docker compose up --build` after pulling the change.

### Manual alternatives

| Action | When |
|--------|------|
| Use **deepseek-ocr:latest** | Works without context workaround on same host |
| Set `OCR_NUM_CTX=4096` in backend env | If 8192 still fails on a future Ollama build |
| Upgrade **Ollama** | When a release fixes glmocr + large ctx on CUDA |

## Repo impact

- `backend/app/config.py` — `OCR_NUM_CTX`
- `backend/app/ollama_client.py` — `num_ctx` on OCR chat; error text for glm-ocr

## Related

- [paddleocr-vl-ollama-load-failure.md](paddleocr-vl-ollama-load-failure.md) — different failure (unsupported `paddleocr` arch)
- Default prompt: `backend/config/prompts.json` → `glm-ocr:latest`
