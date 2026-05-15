# OCR engines — speed ranking and categorization

**Date:** 2026-05-15  
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
| 2 | **DeepSeek-OCR** (`deepseek-ai/DeepSeek-OCR`) | **~5–15 s** | Estimated | Yes (vLLM) |
| 3 | **GLM-OCR** (`zai-org/GLM-OCR`) | **~6–20 s** | Estimated | Yes (vLLM) |
| 4 | **MinerU-Diffusion** (batched, `nano_dvlm`) | **~10.5 s/page** avg | Measured | Yes (`mineru-diffusion` sidecar) |
| 5 | **MinerU-Diffusion** (sequential / no batch) | **~15.6 s/page** | Measured | Same service (single-page requests) |
| 6 | **Chandra** (vLLM / `chandra_vllm`) | **~20–40 s** | Partial (article) | Yes (`vllm-chandra`, profile `chandra`) |
| 7 | **Chandra** (HuggingFace local) | **~66 s/page** | Measured | Fallback only |
| 8 | **General VLMs** (Qwen, Mistral, etc. via Ollama) | **~30–120+ s** | Estimated | Prompts only |
| 9 | **Hybrid** MinerU layout → LightOn text | **~15–35 s+** | Sum of stages | Optional (Phase 5) |

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
| 3 | **PaliGemma 2** (`onnx-community/paligemma2-3b-pt-224`) | **~15–60+ s** | Yes (“slow”) |
| 4 | **Chrome Built-in AI** refine | **+2–20 s** on top | Yes (optional) |

Server GPU models are usually faster and better than browser VLMs for full pages but require a GPU host.

---

## Category: by mechanism

| Category | Engines | Speed profile | Best for |
|----------|---------|---------------|----------|
| **Text extraction** | LiteParse | Fastest on **A**; poor on raw scans | Digital PDFs, embedded text |
| **Classical OCR** | Tesseract.js | Fast, limited | Labels, high contrast, offline |
| **Seq2seq OCR (small)** | TrOCR | Fast–medium | Short text, handwriting-ish crops |
| **Autoregressive VLM (small)** | LightOnOCR ~1B | Fastest GPU OCR in article | Scanned docs, markdown/tables |
| **Autoregressive VLM (medium)** | DeepSeek-OCR, GLM-OCR | Medium | General OCR + tables (repo baselines) |
| **Diffusion decoder** | MinerU-Diffusion | Medium–slow; custom engine | Layout + coordinates |
| **Layout VLM (large)** | Chandra ~3–4B | Slow (HF path very slow) | Layout HTML/MD + bboxes |
| **General-purpose VLM** | Qwen, Mistral (Ollama) | Slowest server path | “Can OCR” but not specialized |
| **Browser VLM** | PaliGemma 2 | Slow in WASM | Offline quality on crops |
| **Pipeline** | MinerU → LightOn | Slowest useful stack | Coordinates + clean text |

---

## Category: by runtime / integration

| Category | Engines | Planned `engine.type` |
|----------|---------|------------------------|
| **vLLM OpenAI** | DeepSeek, GLM, LightOn, Chandra | `vllm` |
| **Custom GPU sidecar** | MinerU (`nano_dvlm`) | `nano_dvlm` |
| **Subprocess (Node)** | LiteParse | `litparse` |
| **Ollama** | `deepseek-ocr`, `glm-ocr`, PaddleOCR-VL, Qwen, Mistral | `ollama` (global backend) |
| **Browser worker** | TrOCR, Tesseract, PaliGemma | N/A (`POST /api/scan` only) |

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
| **In repo today** | DeepSeek-OCR, GLM-OCR (vLLM); TrOCR, Tesseract, PaliGemma (browser); Ollama catalog |
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
| PaddleOCR-VL | — | Broken | See [paddleocr-vl-ollama-load-failure.md](../issues/paddleocr-vl-ollama-load-failure.md) |
| Qwen / Mistral | — | General VLM | Slowest server path |

---

## Suggested `speed_tier` metadata (`ocr_engines.json`)

| `speed_tier` | Engines |
|--------------|---------|
| `instant` | LiteParse (workload A only) |
| `fast` | Tesseract, TrOCR, LightOnOCR |
| `medium` | DeepSeek-OCR, GLM-OCR, MinerU-Diffusion (batched) |
| `slow` | MinerU (sequential), Chandra vLLM, PaliGemma (browser) |
| `very_slow` | Chandra HF, Qwen/Mistral OCR, hybrid pipelines |

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
