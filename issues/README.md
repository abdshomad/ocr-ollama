# Issues — investigations and fixes

Write-ups for non-trivial bugs and integration problems. Format and when to add files: [AGENTS.md](../AGENTS.md#issue-documentation-issues).

| Issue | Summary |
|-------|---------|
| [vllm-deepseek-ocr-integration.md](vllm-deepseek-ocr-integration.md) | **vLLM default OCR** — Compose + DeepSeek-OCR working; GPU, ports, healthcheck, `max_tokens` fixes |
| [vllm-glm-ocr.md](vllm-glm-ocr.md) | **vLLM GLM-OCR** — `zai-org/GLM-OCR`, MTP flags, `docker-compose.glm-ocr.yml` |
| [lightonocr-vllm-integration.md](lightonocr-vllm-integration.md) | **vLLM LightOnOCR** — `lightonai/LightOnOCR-2-1B`, profile `lighton`, port 8102, transformers 5.4+ image |
| [mineru-diffusion-nano-dvlm-integration.md](mineru-diffusion-nano-dvlm-integration.md) | **MinerU-Diffusion** — `nano_dvlm` sidecar, profile `mineru`, port 8200, `POST /v1/ocr` |
| [liteparse-cli-integration.md](liteparse-cli-integration.md) | **LiteParse** — `lit` CLI subprocess, PDF + documents, `model=litparse`, Docker image installs `@llamaindex/liteparse` |
| [chandra-vllm-integration.md](chandra-vllm-integration.md) | **Chandra OCR 2** — `datalab-to/chandra-ocr-2`, profile `chandra`, port 8103 |
| [gemma4-vllm-integration.md](gemma4-vllm-integration.md) | **Gemma 4** — `google/gemma-4-E4B-it`, profile `gemma4`, port 8104, vision-tier OCR |
| [qwen3-vl-vllm-integration.md](qwen3-vl-vllm-integration.md) | **Qwen3-VL** — `Qwen/Qwen3-VL-*-Instruct`, profile `qwen3vl`, port 8105, vision-tier OCR |
| [vllm-lighton-gpu-compose-entrypoint-directory.md](vllm-lighton-gpu-compose-entrypoint-directory.md) | LightOn restart loop after GPU start — `/workspace` compose path created entrypoint as directory (exit 126) |
| [vllm-compose-unhealthy.md](vllm-compose-unhealthy.md) | Compose `vllm` unhealthy — chat-template crash, GPU 0 OOM, slow first start |
| [docker-ollama-localhost-settings-override.md](docker-ollama-localhost-settings-override.md) | App shows inference offline in Docker — `settings.json` loopback vs env host |
| [paddleocr-vl-ollama-load-failure.md](paddleocr-vl-ollama-load-failure.md) | `MedAIBase/PaddleOCR-VL:0.9b` fails to load — unsupported `paddleocr` architecture on Ollama 0.23.x |
| [glm-ocr-cuda-context-load-failure.md](glm-ocr-cuda-context-load-failure.md) | `glm-ocr:latest` fails on GPU — 131k default ctx triggers CUDA `INT_MAX` assert; fix with `num_ctx` |
