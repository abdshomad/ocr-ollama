# Issues — investigations and fixes

Write-ups for non-trivial bugs and integration problems. Format and when to add files: [AGENTS.md](../AGENTS.md#issue-documentation-issues).

| Issue | Summary |
|-------|---------|
| [docker-ollama-localhost-settings-override.md](docker-ollama-localhost-settings-override.md) | App shows Ollama offline in Docker while host Ollama works — `settings.json` loopback vs `OLLAMA_HOST` |
| [paddleocr-vl-ollama-load-failure.md](paddleocr-vl-ollama-load-failure.md) | `MedAIBase/PaddleOCR-VL:0.9b` fails to load — unsupported `paddleocr` architecture on Ollama 0.23.x |
| [glm-ocr-cuda-context-load-failure.md](glm-ocr-cuda-context-load-failure.md) | `glm-ocr:latest` fails on GPU — 131k default ctx triggers CUDA `INT_MAX` assert; fix with `num_ctx` |
