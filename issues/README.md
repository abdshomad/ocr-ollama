# Issues — investigations and fixes

Write-ups for non-trivial bugs and integration problems. Format and when to add files: [AGENTS.md](../AGENTS.md#issue-documentation-issues).

| Issue | Summary |
|-------|---------|
| [vllm-deepseek-ocr-integration.md](vllm-deepseek-ocr-integration.md) | **vLLM default OCR** — Compose + DeepSeek-OCR working; GPU, ports, healthcheck, `max_tokens` fixes |
| [vllm-glm-ocr.md](vllm-glm-ocr.md) | **vLLM GLM-OCR** — `zai-org/GLM-OCR`, MTP flags, `docker-compose.glm-ocr.yml` |
| [vllm-compose-unhealthy.md](vllm-compose-unhealthy.md) | Compose `vllm` unhealthy — chat-template crash, GPU 0 OOM, slow first start |
| [docker-ollama-localhost-settings-override.md](docker-ollama-localhost-settings-override.md) | App shows inference offline in Docker — `settings.json` loopback vs env host |
| [paddleocr-vl-ollama-load-failure.md](paddleocr-vl-ollama-load-failure.md) | `MedAIBase/PaddleOCR-VL:0.9b` fails to load — unsupported `paddleocr` architecture on Ollama 0.23.x |
| [glm-ocr-cuda-context-load-failure.md](glm-ocr-cuda-context-load-failure.md) | `glm-ocr:latest` fails on GPU — 131k default ctx triggers CUDA `INT_MAX` assert; fix with `num_ctx` |
