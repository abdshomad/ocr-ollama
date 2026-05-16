# OCR engines — speed ranking and categorization

**Date:** 2026-05-16  
**Status:** Reference  
**Related:** [medium-four-ocr-models.md](./medium-four-ocr-models.md), [browser-ocr-pipeline.md](./browser-ocr-pipeline.md), [vllm-deepseek-ocr-migration.md](./vllm-deepseek-ocr-migration.md)

Benchmark source for Medium four: [Which Small vLLM OCR Model Is the Best For Private Use in 2026?](https://medium.com/@AiDocTakes/i-tested-four-ocr-models-on-scanned-medical-records-and-the-smallest-one-won-ed7185b1c0b2) (RTX 4090 laptop, pages at 200 DPI, longest side ≤ 1540px).

## How to read this

| Axis | Meaning |
|------|--------|
| **Workload A** | Native/digital PDF (embedded text) |
| **Workload B** | Scanned page image (article normalization) |
| **Workload C** | Small crop / SKU label (browser `/scan`) |
| **Evidence** | **Measured** = article · **Estimated** = size/heuristics · **In-app** = this repo today |

Rankings are **not interchangeable across workloads** — input type and hardware dominate.

---

## Master speed ladder — scanned page (workload B, GPU server)

Fastest at top. Compare only within this workload.

| Rank | Engine / model | Typical latency | Evidence | In repo |
|------|----------------|-----------------|----------|---------|
| 1 | **LightOnOCR** (`lightonai/LightOnOCR-1B-1025` / `2-1B`) | **~3–7 s** typical; **~23–25 s** on dense tables | Measured | Yes (`LightOnOCR-2-1B` vLLM) |
| 2 | **Hunyuan OCR** (`tencent/HunyuanOCR`) | **~similar tier to small VLMs** (~1B) | Estimated | Yes (optional `vllm-hunyuanocr`, profile `hunyuanocr`) |
| 3 | **DeepSeek-OCR** (`deepseek-ai/DeepSeek-OCR`) | **~5–15 s** | Estimated | Yes (vLLM) |
| 4 | **GLM-OCR** (`zai-org/GLM-OCR`) | **~6–20 s** | Estimated | Yes (vLLM) |
| 5 | **MinerU-Diffusion** (batched, `nano_dvlm`) | **~10.5 s/page** avg | Measured | Yes (`mineru-diffusion` sidecar) |
| 6 | **MinerU-Diffusion** (sequential / no batch) | **~15.6 s/page** | Measured | Same service (single-page requests) |
| 7 | **Chandra** (vLLM / `chandra_vllm`) | **~20–40 s** | Partial (article) | Yes (`vllm-chandra`, profile `chandra`) |
| 8 | **Chandra** (HuggingFace local) | **~66 s/page** | Measured | Fallback only |
| 9 | **General VLMs** (Qwen, Mistral, etc. via Ollama) | **~30–120+ s** | Estimated | Prompts only |
| 10 | **Hybrid** MinerU layout → LightOn text | **~15–35 s+** | Sum of stages | Optional (Phase 5) |

### Article throughput (30 scanned medical pages)

| Engine | Total | Per page (avg) |
|--------|-------|----------------|
| LightOnOCR | 203 s | **6.8 s/page** |
| MinerU-Diffusion (batched) | — | **10.5 s/page** |
| LightOnOCR (33-page academic paper) | 143 s | **4.3 s/page** |

Single-page article notes: LightOnOCR was the fastest GPU method (~3× faster than MinerU-Diffusion, ~18× faster than Chandra on page 1).

---

## Master speed ladder — native/digital PDF (workload A)

| Rank | Engine | Typical latency | Notes |
|------|--------|-----------------|-------|
| 1 | **LiteParse** | **Sub-second → few seconds** / doc | Not neural OCR; reads embedded PDF text |
| 2 | **LightOnOCR** (if PDF is rasterized) | Same as workload B | Overkill for digital PDFs |
| 3 | **MinerU / Chandra / DeepSeek / GLM** | GPU speeds from scanned ladder | Use when PDF is scan-only or layout-heavy |

On **scanned** PDFs LiteParse is fast but **low quality** — speed is misleading.

---

## Master speed ladder — browser `/scan` (workload C)

Runs on user CPU/GPU; no vLLM.

| Rank | Engine | Typical latency | In repo |
|------|--------|-----------------|---------|
| 1 | **Tesseract.js** | **~0.5–3 s** | Yes (“Fast scan”) |
| 2 | **TrOCR** (`Xenova/trocr-base-handwritten`) | **~2–10 s** | Yes (default) |
| 3 | **Granite Docling 258M** (`onnx-community/granite-docling-258M-ONNX`) | **~5–30+ s** (first run includes large download) | Yes (“Granite Docling” on `/scan`) |
| 4 | **PaliGemma 2** (`onnx-community/paligemma2-3b-pt-224`) | **~15–60+ s** | Yes (“slow”) |
| 5 | **Chrome Built-in AI** refine | **+2–20 s** on top | Yes (optional) |

Server GPU models are usually faster and better than browser VLMs for full pages but require a GPU host.

---

## Category: by mechanism

| Category | Engines | Speed profile | Best for |
|----------|---------|---------------|----------|
| **Text extraction** | LiteParse | Fastest on **A**; poor on raw scans | Digital PDFs, embedded text |
| **Classical OCR** | Tesseract.js | Fast, limited | Labels, high contrast, offline |
| **Seq2seq OCR (small)** | TrOCR | Fast–medium | Short text, handwriting-ish crops |
| **Autoregressive VLM (small)** | LightOnOCR ~1B, Hunyuan OCR ~1B | Fastest GPU OCR in article; Hunyuan similar class | Scanned docs, markdown/tables |
| **Autoregressive VLM (medium)** | DeepSeek-OCR, GLM-OCR | Medium | General OCR + tables (repo baselines) |
| **Diffusion decoder** | MinerU-Diffusion | Medium–slow; custom engine | Layout + coordinates |
| **Layout VLM (large)** | Chandra ~3–4B; Dots.MOCR (optional vLLM `dotsmocr`); **RolmOCR** ~7B (optional `rolmocr`, plain text); **NuMarkdown** ~8B (optional `numarkdown`, reasoning → markdown) | Chandra slow (HF path very slow) | Layout HTML/MD + bboxes; RolmOCR text-only doc OCR; NuMarkdown GFM tables |
| **General-purpose VLM** | Qwen3-VL (vLLM, optional `qwen3vl`); Qwen3-Omni (vLLM-Omni, optional `qwen3omni`); Phi-4-multimodal (vLLM, optional `phi4mm`); Qwen, Mistral (Ollama); Gemma 4 (vLLM, optional profile `gemma4`) | Slowest server path | “Can OCR” but not specialized checkpoints |
| **Browser VLM** | PaliGemma 2 | Slow in WASM | Offline quality on crops |
| **Pipeline** | MinerU → LightOn | Slowest useful stack | Coordinates + clean text |

---

## Category: by runtime / integration

| Category | Engines | Planned `engine.type` |
|----------|---------|------------------------|
| **vLLM OpenAI** | DeepSeek / **DeepSeek-OCR-2** (optional `deepseek-ocr2`), GLM, LightOn, Chandra, Gemma 4 (optional `gemma4`), Qwen3-VL (optional `qwen3vl`), **Qwen3-Omni** (optional **`qwen3omni`**, **vLLM-Omni** image + `vllm serve --omni`), **Phi-4-multimodal** (optional `phi4mm`, `microsoft/Phi-4-multimodal-instruct`), **RolmOCR** (optional `rolmocr`, `reducto/RolmOCR`), **NuMarkdown** (optional `numarkdown`, `numind/NuMarkdown-8B-Thinking`), **Smol Docling** (optional `smoldocling`, `docling-project/SmolDocling-256M-preview`), Hunyuan OCR (optional `hunyuanocr`), **PaddleOCR-VL** (optional `paddleocr-vl`), **Dots.MOCR** (optional `dotsmocr`, `rednote-hilab/dots.mocr`) | `vllm` |
| **Custom GPU sidecar** | MinerU (`nano_dvlm`), Nemotron OCR v2 (`nemotron`) | `nano_dvlm`, `nemotron` |
| **Custom CPU sidecar** | RapidOCR ONNX (`rapidocr`), OnnxTR (`onnxtr`), EasyOCR (`easyocr`), docTR (`doctr`), PaddleOCR (`paddleocr`), Docling (`docling`), LanyOCR (`lanyocr`) | `rapidocr`, `onnxtr`, `easyocr`, `doctr`, `paddleocr`, `docling`, `lanyocr` |
| **Subprocess** | LiteParse, Tesseract (native) | `litparse`, `tesseract` |
| **Ollama** | `deepseek-ocr`, `glm-ocr`, PaddleOCR-VL, Qwen, Mistral | `ollama` (global backend) |
| **Browser worker** | TrOCR, Tesseract, PaliGemma, **Granite Docling** (`granite`) | N/A (`POST /api/scan` only) |

---

## Category: quality vs speed (scanned medical, workload B)

| Tier | Engines |
|------|---------|
| **Fast + best quality** | LightOnOCR |
| **Fast + good** | DeepSeek-OCR, GLM-OCR (repo; not in article bake-off) |
| **Medium + layout coords** | MinerU-Diffusion |
| **Fast + wrong on scans** | LiteParse |
| **Slow + unreliable (article HF)** | Chandra local |
| **Fast + weak** | Tesseract, TrOCR (narrow use cases) |

---

## Category: plan / repo status

| Bucket | Engines |
|--------|---------|
| **In repo today** | DeepSeek-OCR, **DeepSeek-OCR-2** (optional `vllm-deepseek-ocr2`, profile `deepseek-ocr2`, port 8114), GLM-OCR (vLLM); Gemma 4 E4B (optional `vllm-gemma4`); Qwen3-VL Instruct (optional `vllm-qwen3-vl`); **Qwen3-Omni** (optional `vllm-qwen3-omni`, **vLLM-Omni**, profile `qwen3omni`); **Phi-4-multimodal** (optional `vllm-phi4-mm`, profile `phi4mm`); **RolmOCR** (optional `vllm-rolmocr`, profile `rolmocr`); **NuMarkdown** (optional `vllm-numarkdown`, profile `numarkdown`); **Smol Docling** (optional `vllm-smoldocling`, profile `smoldocling`, `docling-project/SmolDocling-256M-preview`); Hunyuan OCR (optional `vllm-hunyuanocr`); **PaddleOCR-VL** (optional `vllm-paddleocr-vl`, profile `paddleocr-vl`); **Dots.MOCR** (optional `vllm-dotsmocr`, profile `dotsmocr`, `rednote-hilab/dots.mocr`); TrOCR, Tesseract, PaliGemma, **Granite Docling** (`granite`, ONNX on `/scan`) (browser); Tesseract (native server subprocess); Ollama catalog |
| **In repo (RapidOCR)** | RapidOCR ONNX (`rapidocr`, profile `rapidocr`, port 8220, CPU) |
| **In repo (OnnxTR)** | OnnxTR (`onnxtr`, profile `onnxtr`, port 8230, CPU) |
| **In repo (EasyOCR)** | EasyOCR (`easyocr`, profile `easyocr`, port 8240, PyTorch CPU image) |
| **In repo (docTR)** | docTR (`doctr`, profile `doctr`, port 8250, PyTorch CPU image) |
| **In repo (PaddleOCR)** | PaddleOCR PP-OCR (`paddleocr`, profile `paddleocr`, port 8260, PaddlePaddle CPU image) |
| **In repo (PaddleOCR-VL VLM)** | PaddleOCR-VL (`PaddlePaddle/PaddleOCR-VL`, vLLM `vllm-paddleocr-vl`, profile `paddleocr-vl`, port 8107) — distinct from CPU PP-OCR sidecar |
| **In repo (Dots.MOCR)** | Dots.MOCR (`rednote-hilab/dots.mocr`, vLLM `vllm-dotsmocr`, profile `dotsmocr`, port 8108) |
| **In repo (Phi-4-multimodal)** | Phi-4-multimodal (`microsoft/Phi-4-multimodal-instruct`, vLLM `vllm-phi4-mm`, profile `phi4mm`, port 8109) |
| **In repo (RolmOCR)** | RolmOCR (`reducto/RolmOCR`, vLLM `vllm-rolmocr`, profile `rolmocr`, port 8110) |
| **In repo (NuMarkdown)** | NuMarkdown (`numind/NuMarkdown-8B-Thinking`, vLLM `vllm-numarkdown`, profile `numarkdown`, port 8111) |
| **In repo (Qwen3-Omni)** | Qwen3-Omni (`Qwen/Qwen3-Omni-30B-A3B-*`, vLLM-Omni `vllm-qwen3-omni`, profile `qwen3omni`, port 8112) |
| **In repo (Smol Docling)** | Smol Docling (`docling-project/SmolDocling-256M-preview`, vLLM `vllm-smoldocling`, profile `smoldocling`, port 8113; DocTags → markdown via `docling-core`) |
| **In repo (Nemotron OCR v2)** | Nemotron OCR v2 multilingual (`nemotron-ocr-v2`, profile `nemotron`, port 8210) |
| **Planned (Medium four)** | — (LiteParse shipped) |
| **In repo (LiteParse)** | LiteParse (`litparse`, local `lit` CLI, PDF + multi-format) |
| **In repo (Chandra)** | Chandra OCR 2 (`vllm-chandra`) |
| **In repo (Medium four)** | LightOnOCR (`vllm-lighton`); MinerU-Diffusion (`mineru-diffusion`, profile `mineru`) |
| **Article rejected (out of scope)** | Marker, Surya, MinerU 2.5 AGPL, PaddleOCR-only, GOT-OCR2, Docling, GLM cloud API |

---

## Ollama vs vLLM (same weights)

For the **same model**, Ollama is typically **~1.2–1.5× slower** than vLLM, with extra RAM/context quirks.

| Model | vLLM (repo) | Ollama | Relative |
|-------|-------------|--------|----------|
| DeepSeek-OCR | Yes | `deepseek-ocr:latest` | vLLM faster |
| GLM-OCR | Yes | `glm-ocr:latest` | vLLM faster |
| PaddleOCR-VL | Yes (profile `paddleocr-vl`) | Broken | vLLM: `PaddlePaddle/PaddleOCR-VL`; Ollama: see [paddleocr-vl-ollama-load-failure.md](../issues/paddleocr-vl-ollama-load-failure.md) |
| Qwen3-VL Instruct | Yes (profile `qwen3vl`) | — | Optional vLLM multimodal OCR |
| Hunyuan OCR | Yes (profile `hunyuanocr`) | — | `tencent/HunyuanOCR` dedicated OCR VLM |
| Dots.MOCR | Yes (profile `dotsmocr`) | — | `rednote-hilab/dots.mocr` via vLLM ≥ 0.11 |
| Phi-4-multimodal | Yes (profile `phi4mm`) | — | `microsoft/Phi-4-multimodal-instruct`; MS license — see HF card |
| RolmOCR | Yes (profile `rolmocr`) | — | `reducto/RolmOCR`; Apache 2.0 — see HF card |
| NuMarkdown | Yes (profile `numarkdown`) | — | `numind/NuMarkdown-8B-Thinking`; MIT — see HF card |
| Qwen3-Omni | Yes (profile `qwen3omni`) | — | `Qwen/Qwen3-Omni-30B-A3B-Instruct` default; **vLLM-Omni** (`vllm serve --omni`); Qwen license — see HF card |

---

## Suggested `speed_tier` metadata (`ocr_engines.json`)

| `speed_tier` | Engines |
|--------------|---------|
| `instant` | LiteParse (workload A only) |
| `fast` | Tesseract (browser + native), TrOCR, LightOnOCR, Nemotron OCR v2 (sidecar), RapidOCR (`rapidocr`), OnnxTR (`onnxtr`), docTR (`doctr`), Hunyuan OCR (vLLM), **PaddleOCR-VL** (vLLM) |
| `medium` | EasyOCR (`easyocr`, CPU PyTorch sidecar), PaddleOCR (`paddleocr`, CPU Paddle sidecar), **Dots.MOCR** (`rednote-hilab/dots.mocr`, optional vLLM `dotsmocr`), DeepSeek-OCR, GLM-OCR, MinerU-Diffusion (batched) |
| `slow` | MinerU (sequential), Chandra vLLM, **RolmOCR** vLLM (`rolmocr`), PaliGemma (browser) |
| `very_slow` | Chandra HF, Gemma 4 vLLM, Qwen3-VL vLLM, **Qwen3-Omni** vLLM-Omni (`qwen3omni`), **Phi-4-multimodal** vLLM (`phi4mm`), **NuMarkdown** vLLM (`numarkdown`), Qwen/Mistral OCR (Ollama), hybrid pipelines |

---

## Pick by speed goal

| Goal | Engine |
|------|--------|
| Fastest on digital PDF | LiteParse |
| Fastest on scanned page (GPU) | LightOnOCR |
| Fastest offline in browser | Tesseract |
| Best speed/quality in repo **today** | LightOnOCR (vLLM) when `vllm-lighton` is up |
| Need block coordinates | MinerU-Diffusion (slower than LightOn alone) |
| Avoid for production scans | Chandra HF local; general Ollama VLMs |

---

## Caveats

- Arena comparisons require the same **input mode** (image vs PDF), **preprocess** (200 DPI / 1540px), and **one heavy model per GPU**.
- Dense table pages can move LightOnOCR from ~4 s to ~25 s — tiers reflect **typical** latency, not worst case.
- Re-measure on target hardware before UI badges or SLA claims.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-15 | Initial speed ladders and categorization |
| 2026-05-16 | MinerU-Diffusion in repo (`mineru-diffusion` nano_dvlm sidecar) |
| 2026-05-16 | LiteParse in repo (`litparse`, `lit` CLI in backend, PDF uploads) |
| 2026-05-16 | Gemma 4 optional vLLM endpoint (`google/gemma-4-E4B-it`, profile `gemma4`, port 8104) |
| 2026-05-16 | OnnxTR ONNX CPU sidecar (`onnxtr`, profile `onnxtr`, port 8230) |
| 2026-05-16 | EasyOCR PyTorch CPU sidecar (`easyocr`, profile `easyocr`, port 8240) |
| 2026-05-16 | docTR PyTorch CPU sidecar (`doctr`, profile `doctr`, port 8250) |
| 2026-05-16 | PaddleOCR-VL vLLM optional endpoint (`PaddlePaddle/PaddleOCR-VL`, profile `paddleocr-vl`, port 8107) |
| 2026-05-16 | Dots.MOCR optional vLLM endpoint (`rednote-hilab/dots.mocr`, profile `dotsmocr`, port 8108) |
| 2026-05-16 | RolmOCR optional vLLM endpoint (`reducto/RolmOCR`, profile `rolmocr`, port 8110) |
| 2026-05-16 | Phi-4-multimodal optional vLLM endpoint (`microsoft/Phi-4-multimodal-instruct`, profile `phi4mm`, port 8109) |
| 2026-05-16 | Granite Docling 258M browser ONNX on `/scan` (`granite`, `onnx-community/granite-docling-258M-ONNX`) |
