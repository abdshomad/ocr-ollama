# MedAIBase/PaddleOCR-VL:0.9b — load failure analysis

**Date:** 2026-05-15 (updated)  
**Ollama version (host):** 0.23.3  
**Symptom (app):** `Ollama error: {'error': 'unable to load model: .../sha256-3ac47f4557c259c4c680c762729fb4b94e9572c9d52f9104c2f00013caaf9b0e'}` (often misread as corrupt download)

## Summary

This is **not** a corrupt or missing download. The model blob is present on disk (~936 MB), but **Ollama 0.23.3 cannot run the `paddleocr` architecture**. `ollama pull` will not fix it.

## Evidence

### Model appears in catalog

```bash
ollama list
# MedAIBase/PaddleOCR-VL:0.9b    2d9290d5ab53    935 MB
```

### Blob exists

```text
/usr/share/ollama/.ollama/models/blobs/sha256-3ac47f4557c259c4c680c762729fb4b94e9572c9d52f9104c2f00013caaf9b0e
-rw-r--r-- 1 ollama ollama 935768512 May 14 19:17
```

### HTTP API reproduces failure

```bash
curl -s http://localhost:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"MedAIBase/PaddleOCR-VL:0.9b","messages":[{"role":"user","content":"hi"}],"stream":false}'
```

Response:

```json
{"error":"unable to load model: /usr/share/ollama/.ollama/models/blobs/sha256-3ac47f4557c259c4c680c762729fb4b94e9572c9d52f9104c2f00013caaf9b0e"}
```

### Root cause (Ollama server log)

```text
journalctl -u ollama
```

Key line:

```text
llama_model_load: error loading model: error loading model architecture: unknown model architecture: 'paddleocr'
```

Ollama’s HTTP API only returns a generic `unable to load model: .../blobs/sha256-...`, which is easy to misread as a corrupt file.

## Workarounds

### Use another OCR model (works today)

Models that load on the same host:

| Model | Notes |
|-------|--------|
| `deepseek-ocr:latest` | Verified via `/api/chat` (HTTP 200) |
| `glm-ocr:latest` | Works with app `num_ctx` cap; see [glm-ocr-cuda-context-load-failure.md](glm-ocr-cuda-context-load-failure.md) |

In the OCR app, select one of these instead of `MedAIBase/PaddleOCR-VL:0.9b`.

### Optional: remove the unusable model

```bash
ollama rm 'MedAIBase/PaddleOCR-VL:0.9b'
```

Only needed to reclaim ~936 MB; not required for the app to work.

### Future: upgrade Ollama

`paddleocr` support is tracked upstream (e.g. [ollama/ollama#12685](https://github.com/ollama/ollama/issues/12685)). The architecture exists in llama.cpp, but Ollama 0.23.x does not expose it yet. Re-test after upgrading Ollama when a release includes `paddleocr`.

## App / repo impact

- **Docker / `OLLAMA_HOST`:** Not the cause; same error when calling host Ollama directly. See [docker-ollama-localhost-settings-override.md](docker-ollama-localhost-settings-override.md) for the separate “offline” issue.
- **Default model selection:** The app used to auto-pick the first OCR model (PaddleOCR). Now `frontend/src/utils/models.ts` `pickDefaultOcrModel()` prefers standalone dedicated OCR models (`deepseek-ocr`, `glm-ocr`) over adapter-style entries.
- **Model list API:** `GET /api/models` includes `has_parent_blob: true` when `api/show` reports a non-empty `details.parent_model` (PaddleOCR sets this). UI shows an **Adapter** badge in `ModelPicker`.
- **Error text:** `backend/app/ollama_client.py` `format_ollama_error()` — PaddleOCR-specific message for `unable to load model`; generic path suggests `ollama pull` and checking `journalctl -u ollama` for `unknown model architecture`.

## Configuration reference

- `.env`: `OLLAMA_HOST=http://host.docker.internal:11434`
- Default prompt for this model: `backend/config/prompts.json` → `MedAIBase/PaddleOCR-VL:0.9b`

## Related

- [MedAIBase/PaddleOCR-VL on Ollama](https://ollama.com/MedAIBase/PaddleOCR-VL)
- Plan note: PaddleOCR may lack `vision` in capabilities; classified as OCR by family (`plan/ocr-ollama-app.md`)
