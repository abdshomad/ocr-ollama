# OCR engine expansion backlog

**Date:** 2026-05-16  
**Status:** Draft  
**`next` / `n`:** This file is the **canonical queue** for the [AGENTS.md](../AGENTS.md) **Next engine** workflow — pick the next **Ship-ready** unimplemented candidate by **Suggested waves** (and workload hints from [ocr-engines.md](./ocr-engines.md) when needed). **`next` does not mean “research-only” rows** — use **[§ Next research triage queue](#next-research-triage-queue)** for the ordered **Research → Spike** backlog.  
**Related:** [ocr-engines.md](./ocr-engines.md) (speed ladder + in-repo truth), [medium-four-ocr-models.md](./medium-four-ocr-models.md) (registry / adapter patterns), [browser-ocr-pipeline.md](./browser-ocr-pipeline.md), [AGENTS.md](../AGENTS.md) (architecture rules)

## Goals

1. Maintain a **single ordered backlog** of third-party OCR / document models the user asked to integrate, aligned with this repo’s patterns (**FastAPI gateway**, **no browser → heavy inference**, **uv-only backend**, optional **sidecar** or **vLLM** services).
2. For each candidate, record **integration class** (vLLM, custom HTTP sidecar, subprocess/CLI, Transformers.js/browser, external API), **license / compliance note**, and **relation to what is already shipped**.
3. Drive implementation as **small vertical slices** (registry entry → adapter → compose or docs → Run/Arena/History → `issues/*` when non-trivial), not as one giant PR.

## Non-goals (for this document)

- Replacing [ocr-engines.md](./ocr-engines.md) as the **speed ranking** source of truth (update that file when an engine lands and is benchmarked).
- Committing to every name on the list: some rows are **placeholders** (vague product names, unreleased weights, or X-only announcements) and stay **Research** until there is an HF repo, Docker image, or crisp API.
- **GPL-licensed OCR engines** (e.g. **GPL-3.0**): **out of backlog scope** — no Ship waves, no promotion from Research/Spike ([§ Excluded engines (GPL)](#excluded-engines-gpl)).

## Architecture constraints (recap)

| Rule | Implication |
|------|-------------|
| Browser never calls vLLM/Ollama/engine hosts | New engines need a **server** adapter (`/api/ocr`, `/api/arena`) or **browser worker** + `POST /api/scan` for browser-tier only. |
| Production path via nginx | Sidecars bind on Docker network; hosts via `*_HOST` env / settings. |
| Arena sequential | Each new server engine must tolerate **queue-style** calls; document VRAM if exclusive. |

**Reuse:** `backend/config/ocr_engines.json`, `engine_registry.py`, `inference/factory.py`, per-engine client modules (see `mineru_client.py`, `vllm_client.py` patterns), optional compose profile + GPU page controls.

---

## Excluded engines (GPL)

**Policy:** Engines whose distribution terms are **GNU General Public License v3** (**GPL-3.0**) — and other **GPL-family** OCR stacks treated the same by policy — are **not integration targets** for this repo’s backlog (sidecar, subprocess, or browser worker). Do **not** route them through **`next` / `n`**, waves, or research triage toward Ship.

| Engine / link | License | Notes |
|---------------|---------|--------|
| [Surya](https://github.com/VikParuchuri/surya) | GPL-3.0 | Was formerly listed under a GPL wave; **permanently excluded** here. |

*Note:* **AGPL** (e.g. optional **full MinerU** stack row elsewhere in this doc) is **not** GPLv3 but remains a **separate license gate** — unchanged by this GPL exclusion.

---

## Next research triage queue

**Purpose:** When **Ship-ready** wave candidates are exhausted (or for dedicated research time), **triage this list next**. Each item lacks a concrete **HF model id**, **weights**, **vendor/OSS clarity**, or **open inference surface** — clarify those before scheduling implementation. **GPL-3.0 engines are never promoted** — see [§ Excluded engines (GPL)](#excluded-engines-gpl). This queue is **not** the [AGENTS.md](../AGENTS.md) **`next` / `n`** ship workflow (that builds **one** engine end-to-end); use this list to promote rows **Research → Spike → Ship**. **As of 2026-05-16**, items **#1–#8** are **triaged** — append new rows for fresh Research topics; ships still require Spikes that meet **exit criteria** below.

**Suggested triage order** (reorder when upstream publishes artifacts):

| # | Candidate | Gate before design / Ship |
|---|-----------|---------------------------|
| 1 | **Doc OWL** | **Triaged 2026-05-16** — pinned lineage: **`mPLUG/DocOwl2`** (primary), DocOwl1.5 variants; **Apache-2.0**; **no stock vLLM path** found — Ship needs **custom GPU sidecar** (Transformers) or future vLLM support. See [issues/doc-owl-wave-r-triage.md](../issues/doc-owl-wave-r-triage.md). |
| 2 | **Aya Vision OCR** | **Triaged 2026-05-16** — **`CohereLabs/aya-vision-8b`** (+ **`CohereLabs/aya-vision-32B`**); **CC-BY-NC 4.0** + Cohere AUP; **HF gated** (`HF_TOKEN`); **vLLM:** `vllm serve CohereLabs/aya-vision-8b` (architecture in vLLM supported models). **Ollama:** no official library pin found. See [issues/aya-vision-ocr-wave-r-triage.md](../issues/aya-vision-ocr-wave-r-triage.md). |
| 3 | **Dolphin** | **Triaged 2026-05-16** — **ByteDance** line: **`ByteDance/Dolphin`** (v1, **MIT**); **`ByteDance/Dolphin-v2`** (**Qwen RESEARCH LICENSE**, NC). vLLM one-liner **unverified**; Transformers + [bytedance/Dolphin](https://github.com/bytedance/Dolphin) demos. See [issues/dolphin-wave-r-triage.md](../issues/dolphin-wave-r-triage.md). |
| 4 | **owlOCR / OCR Flux / Monkey OCR / Nanonets** | **Triaged 2026-05-16** — disambiguation: **OlmOCR** `allenai/olmOCR-*` (Apache-2.0) vs Mac **OwlOCR**; **ChatDOC/OCRFlux-3B** (**Qwen Research LICENSE**, NC); **echo840/MonkeyOCR** (non-commercial per card); **nanonets/Nanonets-OCR-s** (HF license unclear; Qwen derivative). See [issues/marketing-ocr-names-wave-r-triage.md](../issues/marketing-ocr-names-wave-r-triage.md). |
| 5 | **DocParse / OCR Docker / OpenPage / OCRbro / DocuMagnet / OCR Studio** | **Triaged 2026-05-16** — bundle is **mostly commercial / SDK / workflow glue** (e.g. Aryn DocParse, DocuMagnet, OCR Studio); **no** shared open HF weight for gateway Ship — **still deferred**. See [issues/vendor-ocr-products-wave-r-triage.md](../issues/vendor-ocr-products-wave-r-triage.md). |
| 6 | **Gemma 3 OCR / Falcon OCR / Youtu-VL / ExaOCR / Col Pali / Pixl** | **Triaged 2026-05-16** — **Gemma 3** `google/gemma-3-*-it` (vLLM **Gemma3** MM); **Falcon-OCR** `tiiuae/Falcon-OCR`; **Youtu-VL** `tencent/Youtu-VL-4B-Instruct`; **ExaOCR** pipeline repo; **ColPali** = retrieval not Run OCR; **Pixl** = commercial API. See [issues/wave-r-6-vlm-doc-models-triage.md](../issues/wave-r-6-vlm-doc-models-triage.md). |
| 7 | **Pike PDF** | **Triaged 2026-05-16** — **[pikepdf](https://github.com/pikepdf/pikepdf)** Python PDF library (**QPDF**); **not** an OCR model / **no** `vllm serve`. **MPL-2.0.** See [issues/pikepdf-wave-r-triage.md](../issues/pikepdf-wave-r-triage.md). |
| 8 | **DeepSeek OCR 2 / Paddle OCR VL 1.5 / MinerU 2.5 / Dolphin v2 / Light On OCR 2** | **Triaged 2026-05-16** — **DeepSeek-OCR-2** + **PaddleOCR-VL-1.5** have public HF weights; **Spike** vLLM/serve on this repo’s images. **MinerU** AGPL; **Dolphin-v2** Qwen NC; **LightOnOCR-2-1B** **already in repo**. [issues/wave-r-8-upstream-watchlist-triage.md](../issues/wave-r-8-upstream-watchlist-triage.md). |

**Exit criteria (promote to Spike):** HF repo or pinned container tag, license reference (**must not be GPL-3.0** per [§ Excluded engines (GPL)](#excluded-engines-gpl)), minimal serve command (vLLM/sidecar), and sample I/O suitable for `fixtures/ocr/`.

---

## Already in repo (do not re-implement from scratch)

Treat these as **done** unless adding a second checkpoint or fixing gaps.

| Engine / capability | Where | Notes |
|---------------------|-------|--------|
| DeepSeek-OCR | vLLM (`vllm-deepseek`) | Baseline GPU OCR. |
| DeepSeek-OCR-2 | vLLM (`vllm-deepseek-ocr2`, profile `deepseek-ocr2`, port 8114) | Optional; ~3.4B VLM (`deepseek-ai/DeepSeek-OCR-2`). |
| GLM-OCR | vLLM (`vllm-glm`) | Baseline GPU OCR. |
| LightOnOCR | vLLM (`vllm-lighton`) | User list: “Light Ono OCR” / LightOnOCR-1B-1025 / blog — **already routed**. Optional: second catalog row for `2-1B` / bbox variant. |
| Chandra OCR 2 | vLLM (`vllm-chandra`, profile `chandra`) | User list: “Chandra OCR”. |
| MinerU-Diffusion (`nano_dvlm`) | Sidecar `mineru-diffusion` | User list: “Miner U” — **this repo ships the Diffusion decoder**, not full MinerU 2.x parser stack. |
| LiteParse | `litparse` engine | User list: “LiteParse”. |
| Nemotron OCR v2 | Sidecar `nemotron` | User list partially overlaps “Nemotron-Parse” naming. |
| **RapidOCR** | Sidecar `rapidocr` | ONNX (**CPU**), Apache 2.0; model id **`rapidocr`**, profile **`rapidocr`**. |
| **OnnxTR** | Sidecar `onnxtr` | ONNX (**CPU**), Apache 2.0; model id **`onnxtr`**, profile **`onnxtr`**. |
| **EasyOCR** | Sidecar `easyocr` | Apache 2.0; PyTorch **CPU** image in repo; model id **`easyocr`**, profile **`easyocr`**. |
| **docTR** | Sidecar `doctr` | Apache 2.0; PyTorch **CPU**; model id **`doctr`**, profile **`doctr`**, port 8250. |
| **PaddleOCR** (PP-OCR) | Sidecar `paddleocr` | Apache 2.0; PaddlePaddle **CPU**; model id **`paddleocr`**, profile **`paddleocr`**, port 8260 (distinct from **PaddleOCR-VL** on vLLM). |
| **Docling** | Sidecar `docling` | MIT; layout + OCR **CPU**; model id **`docling`**, profile **`docling`**, port 8270. |
| **LanyOCR** | Sidecar `lanyocr` | MIT; ONNX line-merge OCR (**EasyOCR/Paddle-style** blend); model id **`lanyocr`**, profile **`lanyocr`**, port 8280. |
| **PaddleOCR-VL** | vLLM (`vllm-paddleocr-vl`) | Apache 2.0; model id **`PaddlePaddle/PaddleOCR-VL`**, profile **`paddleocr-vl`**, port 8107; **1.5:** **`PaddlePaddle/PaddleOCR-VL-1.5`**, **`vllm-paddleocr-vl-15`**, profile **`paddleocr-vl-15`**, port 8115 — [paddleocr-vl-vllm-integration.md](../issues/paddleocr-vl-vllm-integration.md), [paddleocr-vl-15-vllm-integration.md](../issues/paddleocr-vl-15-vllm-integration.md); Ollama path still broken — [paddleocr-vl-ollama-load-failure.md](../issues/paddleocr-vl-ollama-load-failure.md). |
| **Dots.MOCR** | vLLM (`vllm-dotsmocr`, profile `dotsmocr`) | MIT; layout OCR VLM **`rednote-hilab/dots.mocr`**, port 8108 — [dots-mocr-vllm-integration.md](../issues/dots-mocr-vllm-integration.md). |
| **Phi-4-multimodal** | vLLM (`vllm-phi4-mm`, profile `phi4mm`) | MS license; **`microsoft/Phi-4-multimodal-instruct`**, port 8109 — [phi4-multimodal-vllm-integration.md](../issues/phi4-multimodal-vllm-integration.md). |
| **RolmOCR** | vLLM (`vllm-rolmocr`, profile `rolmocr`) | Apache 2.0; **`reducto/RolmOCR`**, port 8110 — [rolmocr-vllm-integration.md](../issues/rolmocr-vllm-integration.md). |
| **NuMarkdown** | vLLM (`vllm-numarkdown`, profile `numarkdown`) | MIT; **`numind/NuMarkdown-8B-Thinking`**, port 8111 — [numarkdown-vllm-integration.md](../issues/numarkdown-vllm-integration.md). |
| **Qwen3-Omni** | vLLM-Omni (`vllm-qwen3-omni`, profile `qwen3omni`) | Qwen license; **`Qwen/Qwen3-Omni-30B-A3B-*`**, port 8112 (`vllm serve --omni`) — [qwen3-omni-vllm-integration.md](../issues/qwen3-omni-vllm-integration.md). |
| **Smol Docling** | vLLM (`vllm-smoldocling`, profile `smoldocling`) | CDLA-Permissive-2.0; **`docling-project/SmolDocling-256M-preview`**, port 8113; DocTags → markdown in gateway — [smol-docling-vllm-integration.md](../issues/smol-docling-vllm-integration.md). |
| Gemma 4 | Optional vLLM (`gemma4` profile) | User list: “Gemma 4 OCR”. |
| **Hunyuan OCR** | vLLM (`vllm-hunyuanocr`, profile `hunyuanocr`) | `tencent/HunyuanOCR` ~1B VLM; Tencent license — see HF card. |
| Qwen3-VL | Optional vLLM (`qwen3vl`) | Related to “Qwen 3 … VL OCR”. |
| TrOCR | Browser `/scan` | User asked to **keep as example only** for server path — OK to leave browser-only. |
| **Granite Docling 258M** | Browser `/scan` (`granite`) | Apache 2.0; ONNX `onnx-community/granite-docling-258M-ONNX` via Transformers.js — [plan/granite-docling-browser.md](./granite-docling-browser.md), [issues/granite-docling-browser.md](../issues/granite-docling-browser.md). |
| **Tesseract (native)** | Subprocess (`tesseract_client.py`) | **In repo** — wraps `tesseract` binary as a subprocess engine. |

---

## Backlog inventory (user list + integration class)

**Legend:** `vLLM` = OpenAI-compatible multimodal chat; `Sidecar` = dedicated HTTP service in Compose; `Subproc` = Python/CLI in backend container or host; `Browser` = worker + `/api/scan`; `API` = external hosted; `Research` = unclear artifact or license. **GPLv3 OCR engines** are **not** backlog candidates — [§ Excluded engines (GPL)](#excluded-engines-gpl).

| Name / link | Class | License / gate | Notes |
|-------------|-------|----------------|--------|
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Subproc or Sidecar | Apache 2.0 | Heavy deps; consider **sidecar** image with PP-OCRv4/v5 + HTTP shim. |
| [RapidOCR](https://github.com/RapidAI/RapidOCR) | Subproc / Sidecar | Apache 2.0 | ONNX-friendly; good candidate for **small sidecar** or bundled ONNX runtime. |
| [MinerU](https://github.com/opendatalab/MinerU) (full stack) | Sidecar | **MinerU 2.5+ AGPL** (verify per release) | Repo previously marked AGPL concern; **Diffusion** path already MIT. Full MinerU needs **explicit license approval** before default compose. |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | Subproc / Sidecar | Apache 2.0 | PyTorch; VRAM; prefer sidecar. |
| [docTR](https://github.com/mindee/doctr) | Subproc / Sidecar | Apache 2.0 | **In repo** — CPU PyTorch sidecar (`doctr`, profile `doctr`, port 8250). |
| [Lany OCR](https://github.com/JC1DA/lanyocr) | Sidecar | MIT | **In repo** — CPU sidecar `lanyocr`, port 8280; upstream quiet since ~2023. |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) (native) | Subproc | Apache 2.0 | Wrap `tesseract` binary or `pytesseract`; useful for **CPU baseline** and PDF raster fallback. |
| [Docling](https://github.com/DS4SD/docling) | Sidecar | MIT (verify sub-deps) | Layout + OCR pipeline; **in repo** — CPU sidecar `docling`, profile **`docling`**, port 8270. |
| [OnnxTR](https://github.com/felixdittrich92/OnnxTR) | Subproc / Sidecar | Apache 2.0 | ONNX — **in repo** as CPU sidecar (`onnxtr`, profile `onnxtr`, port 8230). |
| [TrOCR](https://huggingface.co/docs/transformers/en/model_doc/trocr) | Browser / Example | Apache 2.0 | **Example / research** on server; browser path exists. |
| [LightOnOCR](https://huggingface.co/blog/lightonai/lightonocr) | vLLM | Apache 2.0 | **In repo**; track “Light On OCR 2 1B” as **model ID / prompt** updates only. |
| Doc OWL (mPLUG-DocOwl) | Spike → **Blocked (vLLM)** / sidecar candidate | Apache-2.0 (`mPLUG/DocOwl2`) | **#1 triaged** — collection [DocOwl Series](https://huggingface.co/collections/mPLUG/docowl-series); primary id **`mPLUG/DocOwl2`** (~9B, `custom_code` + Transformers); **not** in stock vLLM supported list → **optional Transformers GPU sidecar** to Ship. [doc-owl-wave-r-triage.md](../issues/doc-owl-wave-r-triage.md). |
| [Phi-4-multimodal](https://huggingface.co/microsoft/Phi-4-multimodal-instruct) | vLLM | MS license | **In repo** — optional vLLM `vllm-phi4-mm` (`microsoft/Phi-4-multimodal-instruct`, profile `phi4mm`, port 8109) — [phi4-multimodal-vllm-integration.md](../issues/phi4-multimodal-vllm-integration.md). |
| Smol Docling | vLLM | CDLA Permissive v2 (**verify** HF card) | **In repo** — optional `vllm-smoldocling` (`docling-project/SmolDocling-256M-preview`, profile `smoldocling`, port **8113**) — [smol-docling-vllm-integration.md](../issues/smol-docling-vllm-integration.md). Successor **`ibm-granite/granite-docling-258M`** tracked separately if added later. |
| [RolmOCR](https://huggingface.co/reducto/RolmOCR) | vLLM | Apache 2.0 | **In repo** — optional vLLM `vllm-rolmocr` (`reducto/RolmOCR`, profile `rolmocr`, port 8110) — [rolmocr-vllm-integration.md](../issues/rolmocr-vllm-integration.md). |
| [IBM Granite Docling WebGPU](https://huggingface.co/spaces/ibm-granite/granite-docling-258M-WebGPU) | Browser (WASM / ONNX) | Apache 2.0 | **In repo** — **`/scan`** worker engine **`granite`**, HF ONNX community build `onnx-community/granite-docling-258M-ONNX` (see [plan/granite-docling-browser.md](./granite-docling-browser.md)). |
| Aya Vision OCR | vLLM (Ollama unverified) | **CC-BY-NC 4.0** + Cohere AUP; HF **gated** | **#2 triaged** — `CohereLabs/aya-vision-8b` / `aya-vision-32B`; **vLLM** `AyaVisionForConditionalGeneration`; Ship needs **org NC approval** + optional compose profile. [aya-vision-ocr-wave-r-triage.md](../issues/aya-vision-ocr-wave-r-triage.md). |
| Mistral OCR / “Mistral OCR 3” | API / vLLM | **Often API-only** | If closed API, add `engine.type: http_proxy` pattern or document “out of self-host”. |
| Dolphin (ByteDance) | Transformers / vLLM spike | **MIT** (`ByteDance/Dolphin`); **Qwen Research** (`ByteDance/Dolphin-v2` **NC**) | **#3 triaged** — document parsing VLMs; v1 permissive; v2 stronger + Qwen license. [dolphin-wave-r-triage.md](../issues/dolphin-wave-r-triage.md). |
| [Dots.OCR](https://github.com/rednote-hilab/dots.ocr) | vLLM (primary) | MIT | **In repo** as **`rednote-hilab/dots.mocr`** on optional vLLM (`dotsmocr` profile). Newer **`dots.mocr`** line; weights on HF. |
| [Qwen3-Omni](https://github.com/QwenLM/Qwen3-Omni) | vLLM-Omni | Qwen license | **In repo** — optional **`vllm-qwen3-omni`** (`vllm serve --omni`, default `Qwen/Qwen3-Omni-30B-A3B-Instruct`, profile **`qwen3omni`**, port **8112**) — [qwen3-omni-vllm-integration.md](../issues/qwen3-omni-vllm-integration.md). |
| owlOCR / OCR Flux / Monkey OCR / Nanonets | Mixed — see triage | **Varies** — OlmOCR Apache-2.0; OCRFlux Qwen Research NC; Monkey academic NC; Nanonets verify | **#4 triaged** — [marketing-ocr-names-wave-r-triage.md](../issues/marketing-ocr-names-wave-r-triage.md). |
| [NuMarkdown](https://github.com/numindai/NuMarkdown) / [NuMarkdown-8B](https://huggingface.co/numind/NuMarkdown-8B-Thinking) | vLLM | MIT | **In repo** — optional vLLM `vllm-numarkdown` (`numind/NuMarkdown-8B-Thinking`, profile `numarkdown`, port 8111) — [numarkdown-vllm-integration.md](../issues/numarkdown-vllm-integration.md). |
| DocParse / OCR Docker / OpenPage / OCRbro / DocuMagnet / OCR Studio | Vendor / ambiguous | **Commercial or N/A** | **#5 triaged** — [vendor-ocr-products-wave-r-triage.md](../issues/vendor-ocr-products-wave-r-triage.md); **Ship still deferred** (no open inference artifact for bundle). |
| Gemma 3 OCR / Falcon OCR / Youtu-VL / ~~Hunyuan OCR~~ / ExaOCR / Col Pali / Pixl | vLLM / pipeline / API / retrieval | **Varies** (Gemma ToU; Tencent; TII verify; Pixl commercial) | **#6 triaged** — [wave-r-6-vlm-doc-models-triage.md](../issues/wave-r-6-vlm-doc-models-triage.md). **Hunyuan:** in repo. **ColPali:** retrieval. |
| Pike PDF (pikepdf) | Library (not OCR) | **MPL-2.0** | **#7 triaged** — Python PDF I/O, optional plumbing only. [pikepdf-wave-r-triage.md](../issues/pikepdf-wave-r-triage.md). |
| DeepSeek OCR 2 / PaddleOCR-VL-1.5 / MinerU 2.5+ / Dolphin v2 / LightOnOCR “2” | vLLM / AGPL / NC / **done** | Apache / Qwen NC / AGPL / Apache | **#8 triaged** — **DeepSeek-OCR-2** + **PaddleOCR-VL-1.5** shipped (`vllm-deepseek-ocr2`, `vllm-paddleocr-vl-15`; [plan/deepseek-ocr-2-vllm-integration.md](./deepseek-ocr-2-vllm-integration.md), [plan/paddleocr-vl-15-vllm-integration.md](./paddleocr-vl-15-vllm-integration.md)); **LightOnOCR-2-1B** already shipped (`vllm-lighton`). [wave-r-8-upstream-watchlist-triage.md](../issues/wave-r-8-upstream-watchlist-triage.md). |
| Gemini 3.0 | API | Google ToS | Only via **user API key** pattern if ever; out of default self-host stack. |
| iFlyTek AI NOTE 2 | API / closed | Commercial | Likely **out of scope** for self-host unless legal + SDK. |

---

## Suggested waves (priority order)

Order balances **license safety**, **engineering clarity**, and **distinct capability** vs what is already shipped.

### Wave 0 — Hygiene (ongoing)

- Keep `ocr_engines.json` as the **catalog**; merge duplicate conceptual entries (e.g. multiple “MinerU” rows) into **one service + variants**.
- For each new engine: **model id**, **prompt policy**, **input modes** (`image` / `pdf`), **`speed_tier`**, **`issues/<slug>.md`** if Docker or VRAM non-trivial.

### Wave R — Research triage (**next** when nothing is Ship-ready)

**Candidates:** Ordered list in **[§ Next research triage queue](#next-research-triage-queue)** (Doc OWL → … → upstream-tracking row).

**Approach:** Spike only: HF id / license / serve command / sample output. Promote a row to **Ship** and a numbered wave only after exit criteria there are met — **do not** count Wave R as satisfying [AGENTS.md](../AGENTS.md) **`next` / `n`** until triage completes.

**Progress (Wave R):** **#1** [issues/doc-owl-wave-r-triage.md](../issues/doc-owl-wave-r-triage.md). **#2** [issues/aya-vision-ocr-wave-r-triage.md](../issues/aya-vision-ocr-wave-r-triage.md). **#3** [issues/dolphin-wave-r-triage.md](../issues/dolphin-wave-r-triage.md). **#4** [issues/marketing-ocr-names-wave-r-triage.md](../issues/marketing-ocr-names-wave-r-triage.md). **#5** [issues/vendor-ocr-products-wave-r-triage.md](../issues/vendor-ocr-products-wave-r-triage.md). **#6** [issues/wave-r-6-vlm-doc-models-triage.md](../issues/wave-r-6-vlm-doc-models-triage.md). **#7** [issues/pikepdf-wave-r-triage.md](../issues/pikepdf-wave-r-triage.md). **#8** [issues/wave-r-8-upstream-watchlist-triage.md](../issues/wave-r-8-upstream-watchlist-triage.md). **Ordered queue complete** — add new rows above when fresh Research topics appear.

### Wave 1 — Classical / ONNX cluster (CPU-friendly sidecars)

**Candidates:** ~~RapidOCR~~ (**in repo**), ~~OnnxTR~~ (**in repo**), ~~optional native **Tesseract** wrapper~~ (**in repo**), ~~docTR~~ (**in repo**).

**Approach:** Thin FastAPI sidecar in `docker/` + small adapter in `backend/app/`. Prefer **one multi-model sidecar** only if deps align; else separate images to avoid dependency hell.

### Wave 2 — PyTorch “OCR libraries” (GPU sidecars)

**Candidates:** ~~PaddleOCR~~ (**in repo** — CPU Paddle sidecar `paddleocr`), ~~EasyOCR~~ (**in repo** as CPU PyTorch sidecar), ~~Lany OCR~~ (**in repo** — CPU sidecar `lanyocr`, upstream maintenance limited).

**Approach:** Dedicated Dockerfiles, **one model family per container**, strict timeouts, return plain text + optional boxes in JSON for Arena parity.

### Wave 3 — Layout / document AI (heavier sidecars)

**Candidates:** ~~Docling~~ (**in repo** — CPU sidecar `docling`), ~~Dots.OCR / Dots.MOCR~~ (**in repo** — vLLM `vllm-dotsmocr`, profile `dotsmocr`, `rednote-hilab/dots.mocr`), (optional) full MinerU **after license sign-off**.

**Approach:** Reuse MinerU-Diffusion lessons: internal HTTP, batching flags, strong error messages when OOM.

### Wave 4 — New VLMs on vLLM (when distinct from existing)

**Candidates:** ~~Phi-4-multimodal~~ (**in repo** — vLLM `vllm-phi4-mm`, profile `phi4mm`, port 8109), ~~RolmOCR~~ (**in repo** — vLLM `vllm-rolmocr`, profile `rolmocr`, port 8110), ~~NuMarkdown~~ (**in repo** — vLLM `vllm-numarkdown`, profile `numarkdown`, port 8111), ~~Qwen3-Omni~~ (**in repo** — vLLM-Omni `vllm-qwen3-omni`, profile `qwen3omni`, port 8112), ~~Smol Docling~~ (**in repo** — vLLM `vllm-smoldocling`, profile `smoldocling`, port 8113).

**Approach:** Compose profile + serve recipe: stock vLLM models use `vllm-entrypoint.sh`; **Qwen3-Omni** uses **`vllm/vllm-omni`** + `vllm-omni-entrypoint.sh` (`--omni`). Set `prompts.json` and `VLLM_*` limits per model family.

### Wave 5 — Browser / WebGPU demos

**Candidates:** ~~IBM Granite Docling (`granite`, ONNX in Transformers.js)~~ (**in repo**), other WASM-friendly small models.

**Approach:** Extend **browser worker** pipeline; results via `POST /api/scan`; label latency in UI.

### Wave 6 — External APIs (optional product direction)

**Candidates:** Mistral OCR, Gemini, iFlyTek, Nanonets-hosted.

**Approach:** Separate `engine.type` (e.g. `cloud_http`) with **API key from env**, never committed; default off.

---

## Tasks (master checklist)

Use this as a **program tracker**; implementation tickets can reference wave + row.

- [ ] **Triage:** Mark each backlog row **Ship / Spike / Blocked** with owner and license reference.
- [ ] **Spike template:** For each Spike: serve command, VRAM, latency smoke, output format (text vs markdown vs HTML).
- [ ] **Adapter contract:** Standardize return shape: `{ "text": "...", "meta": { "engine": "...", "latency_ms": N, "boxes": ... } }` for Arena/History.
- [ ] **GPU page:** Generalize start/stop beyond vLLM for **all `compose_service` engines** (pattern exists for vLLM + MinerU + Nemotron).
- [ ] **Docs:** `.env.example` + `AGENTS.md` table row per **supported** engine; never document closed credentials.
- [ ] **Browser parity:** For browser-tier engines, verify `/scan` + model picker + worker load path.
- [ ] **Update ladders:** After each ship, edit [ocr-engines.md](./ocr-engines.md) **In repo** column and tiers from measured data.

---

## Risk register

| Risk | Mitigation |
|------|------------|
| Dependency / image size explosion | Prefer **one concern per Dockerfile**; share base stages where safe. |
| **GPL-3.0 OCR engines** | **Excluded** from backlog — no Ship path ([§ Excluded engines (GPL)](#excluded-engines-gpl)). |
| AGPL (e.g. optional full MinerU stack) | Keep behind **explicit profiles** + organizational approval; never default compose — distinct from GPLv3 exclusion above. |
| “Name-only” models | Require HF ID or container tag before scheduling work. |
| Mistral / Google **API-only** | Do not pretend self-hosted; use cloud adapter or defer. |
| Arena fairness | Shared preprocess (`normalize_page_image`) for raster inputs; PDF engines compared only on PDF-capable rows. |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-16 | **Wave R #8** upstream bundle (DeepSeek-OCR-2, PaddleOCR-VL-1.5, MinerU, Dolphin-v2, LightOnOCR-2) — [issues/wave-r-8-upstream-watchlist-triage.md](../issues/wave-r-8-upstream-watchlist-triage.md); **ordered research queue complete** |
| 2026-05-16 | **Wave R #7 Pike PDF** — [pikepdf](https://github.com/pikepdf/pikepdf) library (**MPL-2.0**), not an OCR engine — [issues/pikepdf-wave-r-triage.md](../issues/pikepdf-wave-r-triage.md) |
| 2026-05-16 | **Wave R #6** Gemma3/Falcon-OCR/Youtu-VL/ExaOCR/ColPali/Pixl — [issues/wave-r-6-vlm-doc-models-triage.md](../issues/wave-r-6-vlm-doc-models-triage.md) |
| 2026-05-16 | **Wave R #5** vendor DocParse/OCR Docker/OpenPage/OCRbro/DocuMagnet/OCR Studio — [issues/vendor-ocr-products-wave-r-triage.md](../issues/vendor-ocr-products-wave-r-triage.md); **Ship deferred** |
| 2026-05-16 | **Wave R #4** owlOCR/OCR Flux/Monkey/Nanonets — [issues/marketing-ocr-names-wave-r-triage.md](../issues/marketing-ocr-names-wave-r-triage.md) |
| 2026-05-16 | **Wave R #3 Dolphin** — [issues/dolphin-wave-r-triage.md](../issues/dolphin-wave-r-triage.md); **`ByteDance/Dolphin`** (MIT), **`ByteDance/Dolphin-v2`** (Qwen Research / NC); vLLM serve **unverified** |
| 2026-05-16 | **Wave R #2 Aya Vision OCR** — [issues/aya-vision-ocr-wave-r-triage.md](../issues/aya-vision-ocr-wave-r-triage.md); **`CohereLabs/aya-vision-8b`** / 32B; **CC-BY-NC** + HF gate; **vLLM** serve recipe pinned |
| 2026-05-16 | **Wave R #1 Doc OWL** — triage [issues/doc-owl-wave-r-triage.md](../issues/doc-owl-wave-r-triage.md); pinned **`mPLUG/DocOwl2`** |
| 2026-05-16 | **GPL exclusion** — [§ Excluded engines (GPL)](#excluded-engines-gpl); Surya removed from inventory table; former GPL wave dropped; waves **5→6** renumbered to **4→6**; risk register split GPLv3 vs AGPL |
| 2026-05-16 | **Next research triage queue** — ordered Research candidates (Doc OWL … upstream-tracking row); **Wave R**; clarified **`next` / `n`** vs research-only rows |
| 2026-05-16 | **Granite Docling 258M (browser)** — `/scan` engine `granite`, `onnx-community/granite-docling-258M-ONNX`; nginx image must be rebuilt to refresh static assets |
| 2026-05-16 | **Smol Docling** — optional vLLM `vllm-smoldocling` (`docling-project/SmolDocling-256M-preview`, profile `smoldocling`, port 8113) |
| 2026-05-16 | **Qwen3-Omni** — optional vLLM-Omni `vllm-qwen3-omni` (`Qwen/Qwen3-Omni-30B-A3B-Instruct` default, profile `qwen3omni`, port 8112) |
| 2026-05-16 | **NuMarkdown** — optional vLLM `vllm-numarkdown` (`numind/NuMarkdown-8B-Thinking`, profile `numarkdown`, port 8111) |
| 2026-05-16 | **RolmOCR** — optional vLLM `vllm-rolmocr` (`reducto/RolmOCR`, profile `rolmocr`, port 8110) |
| 2026-05-16 | **Phi-4-multimodal** — optional vLLM `vllm-phi4-mm` (`microsoft/Phi-4-multimodal-instruct`, profile `phi4mm`, port 8109) |
| 2026-05-16 | **Dots.MOCR** — optional vLLM `vllm-dotsmocr` (`rednote-hilab/dots.mocr`, profile `dotsmocr`, port 8108) |
| 2026-05-16 | **Docling** — CPU sidecar (`docling`, profile `docling`, port 8270), model id `docling` |
| 2026-05-16 | **LanyOCR** — CPU sidecar (`lanyocr`, profile `lanyocr`, port 8280), model id `lanyocr` |
| 2026-05-16 | **Hunyuan OCR** — `tencent/HunyuanOCR`, vLLM optional profile `hunyuanocr`, port 8106 |
| 2026-05-16 | OnnxTR CPU sidecar (`onnxtr`, profile `onnxtr`, port 8230) |
| 2026-05-16 | **EasyOCR** — CPU PyTorch sidecar (`easyocr`, profile `easyocr`, port 8240) |
| 2026-05-16 | **PaddleOCR-VL** — vLLM optional `vllm-paddleocr-vl` (`PaddlePaddle/PaddleOCR-VL`, profile `paddleocr-vl`, port 8107); Ollama remains unsupported — [paddleocr-vl-ollama-load-failure.md](../issues/paddleocr-vl-ollama-load-failure.md) |
