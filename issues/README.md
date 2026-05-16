# Issues — investigations and fixes

Write-ups for non-trivial bugs and integration problems. Format and when to add files: [AGENTS.md](../AGENTS.md#issue-documentation-issues).

| Issue | Summary |
|-------|---------|
| [vllm-deepseek-ocr-integration.md](vllm-deepseek-ocr-integration.md) | **vLLM default OCR** — Compose + DeepSeek-OCR working; GPU, ports, healthcheck, `max_tokens` fixes |
| [deepseek-ocr-2-vllm-integration.md](deepseek-ocr-2-vllm-integration.md) | **DeepSeek-OCR-2** — `deepseek-ai/DeepSeek-OCR-2`, profile `deepseek-ocr2`, port 8114, optional second DeepSeek vLLM |
| [vllm-glm-ocr.md](vllm-glm-ocr.md) | **vLLM GLM-OCR** — `zai-org/GLM-OCR`, MTP flags, `docker-compose.glm-ocr.yml` |
| [lightonocr-vllm-integration.md](lightonocr-vllm-integration.md) | **vLLM LightOnOCR** — `lightonai/LightOnOCR-2-1B`, profile `lighton`, port 8102, transformers 5.4+ image |
| [mineru-diffusion-nano-dvlm-integration.md](mineru-diffusion-nano-dvlm-integration.md) | **MinerU-Diffusion** — `nano_dvlm` sidecar, profile `mineru`, port 8200, `POST /v1/ocr` |
| [rapidocr-integration.md](rapidocr-integration.md) | **RapidOCR** — ONNX CPU sidecar, profile `rapidocr`, port 8220, model id `rapidocr` |
| [onnxtr-integration.md](onnxtr-integration.md) | **OnnxTR** — ONNX CPU sidecar, profile `onnxtr`, port 8230, model id `onnxtr` |
| [easyocr-integration.md](easyocr-integration.md) | **EasyOCR** — PyTorch CPU sidecar, profile `easyocr`, port 8240, model id `easyocr` |
| [doctr-integration.md](doctr-integration.md) | **docTR** — PyTorch CPU sidecar, profile `doctr`, port 8250, model id `doctr` |
| [paddleocr-integration.md](paddleocr-integration.md) | **PaddleOCR** — PaddlePaddle CPU sidecar (PP-OCR), profile `paddleocr`, port 8260, model id `paddleocr` |
| [docling-integration.md](docling-integration.md) | **Docling** — layout + OCR CPU sidecar, profile `docling`, port 8270, model id `docling` |
| [lanyocr-integration.md](lanyocr-integration.md) | **LanyOCR** — ONNX CPU line-merge OCR sidecar, profile `lanyocr`, port 8280, model id `lanyocr` |
| [tesseract-native-ocr-backend.md](tesseract-native-ocr-backend.md) | **Tesseract (native)** — `model=tesseract`, CLI in backend container |
| [nemotron-ocr-v2-integration.md](nemotron-ocr-v2-integration.md) | **Nemotron OCR v2** — PyTorch sidecar, profile `nemotron`, port 8210, `nvidia/nemotron-ocr-v2` |
| [liteparse-cli-integration.md](liteparse-cli-integration.md) | **LiteParse** — `lit` CLI subprocess, PDF + documents, `model=litparse`, Docker image installs `@llamaindex/liteparse` |
| [chandra-vllm-integration.md](chandra-vllm-integration.md) | **Chandra OCR 2** — `datalab-to/chandra-ocr-2`, profile `chandra`, port 8103 |
| [gemma4-vllm-integration.md](gemma4-vllm-integration.md) | **Gemma 4** — `google/gemma-4-E4B-it`, profile `gemma4`, port 8104, vision-tier OCR |
| [qwen3-vl-vllm-integration.md](qwen3-vl-vllm-integration.md) | **Qwen3-VL** — `Qwen/Qwen3-VL-*-Instruct`, profile `qwen3vl`, port 8105, vision-tier OCR |
| [hunyuanocr-vllm-integration.md](hunyuanocr-vllm-integration.md) | **Hunyuan OCR** — `tencent/HunyuanOCR`, profile `hunyuanocr`, port 8106, dedicated OCR VLM |
| [paddleocr-vl-vllm-integration.md](paddleocr-vl-vllm-integration.md) | **PaddleOCR-VL** — `PaddlePaddle/PaddleOCR-VL`, profile `paddleocr-vl`, port 8107, vLLM (not Ollama) |
| [dots-mocr-vllm-integration.md](dots-mocr-vllm-integration.md) | **Dots.MOCR** — `rednote-hilab/dots.mocr`, profile `dotsmocr`, port 8108, layout OCR VLM (vLLM ≥ 0.11) |
| [phi4-multimodal-vllm-integration.md](phi4-multimodal-vllm-integration.md) | **Phi-4-multimodal** — `microsoft/Phi-4-multimodal-instruct`, profile `phi4mm`, port 8109, MS multimodal VLM |
| [rolmocr-vllm-integration.md](rolmocr-vllm-integration.md) | **RolmOCR** — `reducto/RolmOCR`, profile `rolmocr`, port 8110, Qwen2.5-VL doc OCR (Apache 2.0) |
| [numarkdown-vllm-integration.md](numarkdown-vllm-integration.md) | **NuMarkdown** — `numind/NuMarkdown-8B-Thinking`, profile `numarkdown`, port 8111, reasoning doc → markdown (MIT) |
| [qwen3-omni-vllm-integration.md](qwen3-omni-vllm-integration.md) | **Qwen3-Omni** — `Qwen/Qwen3-Omni-30B-A3B-*`, vLLM-Omni (`--omni`), profile `qwen3omni`, port 8112 |
| [smol-docling-vllm-integration.md](smol-docling-vllm-integration.md) | **Smol Docling** — `docling-project/SmolDocling-256M-preview`, profile `smoldocling`, port 8113, DocTags→markdown (CDLA-Permissive-2.0) |
| [doc-owl-wave-r-triage.md](doc-owl-wave-r-triage.md) | **Doc OWL (Wave R)** — mPLUG-DocOwl lineage pinned (`mPLUG/DocOwl2`); Apache-2.0; no stock vLLM path; optional GPU Transformers sidecar for future Ship |
| [aya-vision-ocr-wave-r-triage.md](aya-vision-ocr-wave-r-triage.md) | **Aya Vision OCR (Wave R)** — `CohereLabs/aya-vision-8b` / 32B; CC-BY-NC + HF gated; vLLM `AyaVisionForConditionalGeneration`; Ollama not pinned |
| [dolphin-wave-r-triage.md](dolphin-wave-r-triage.md) | **Dolphin / ByteDance (Wave R)** — `ByteDance/Dolphin` (MIT), `Dolphin-v2` (Qwen Research NC); Transformers path; vLLM one-liner unverified |
| [vendor-ocr-products-wave-r-triage.md](vendor-ocr-products-wave-r-triage.md) | **Wave R #5** — DocParse (Aryn commercial), DocuMagnet, OCR Studio SDK, OCRbro/n8n; bundle Ship **deferred** |
| [wave-r-6-vlm-doc-models-triage.md](wave-r-6-vlm-doc-models-triage.md) | **Wave R #6** — Gemma 3, Falcon-OCR, Youtu-VL, ExaOCR pipeline, ColPali retrieval, Pixl API |
| [marketing-ocr-names-wave-r-triage.md](marketing-ocr-names-wave-r-triage.md) | **Wave R #4** — owlOCR vs OlmOCR; OCRFlux (Qwen NC LICENSE); MonkeyOCR (non-commercial); Nanonets-OCR-s (license TBD) |
| [pikepdf-wave-r-triage.md](pikepdf-wave-r-triage.md) | **Wave R #7** — “Pike PDF” = **pikepdf** Python PDF library (MPL-2.0), not an HF/vLLM OCR model |
| [wave-r-8-upstream-watchlist-triage.md](wave-r-8-upstream-watchlist-triage.md) | **Wave R #8** — DeepSeek-OCR-2 / PaddleOCR-VL-1.5 HF pins; MinerU AGPL; Dolphin-v2 NC; LightOnOCR-2-1B in repo |
| [granite-docling-browser.md](granite-docling-browser.md) | **Granite Docling 258M** — `/scan` worker, `onnx-community/granite-docling-258M-ONNX`, engine `granite`; rebuild nginx after frontend updates |
| [vllm-lighton-gpu-compose-entrypoint-directory.md](vllm-lighton-gpu-compose-entrypoint-directory.md) | LightOn restart loop after GPU start — `/workspace` compose path created entrypoint as directory (exit 126) |
| [vllm-compose-unhealthy.md](vllm-compose-unhealthy.md) | Compose `vllm` unhealthy — chat-template crash, GPU 0 OOM, slow first start |
| [cors-non-localhost-ui-empty-model-picker.md](cors-non-localhost-ui-empty-model-picker.md) | Hosted UI (non-localhost) — CORS blocked `/api/models` → “No models match filter” |
| [docker-ollama-localhost-settings-override.md](docker-ollama-localhost-settings-override.md) | App shows inference offline in Docker — `settings.json` loopback vs env host |
| [paddleocr-vl-ollama-load-failure.md](paddleocr-vl-ollama-load-failure.md) | `MedAIBase/PaddleOCR-VL:0.9b` fails to load — unsupported `paddleocr` architecture on Ollama 0.23.x |
| [glm-ocr-cuda-context-load-failure.md](glm-ocr-cuda-context-load-failure.md) | `glm-ocr:latest` fails on GPU — 131k default ctx triggers CUDA `INT_MAX` assert; fix with `num_ctx` |
