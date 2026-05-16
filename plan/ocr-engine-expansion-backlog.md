# OCR engine expansion backlog

**Date:** 2026-05-16  
**Status:** Draft  
**`next` / `n`:** This file is the **canonical queue** for the [AGENTS.md](../AGENTS.md) **Next engine** workflow — pick the next unimplemented candidate by **Suggested waves** (and workload hints from [ocr-engines.md](./ocr-engines.md) when needed).  
**Related:** [ocr-engines.md](./ocr-engines.md) (speed ladder + in-repo truth), [medium-four-ocr-models.md](./medium-four-ocr-models.md) (registry / adapter patterns), [browser-ocr-pipeline.md](./browser-ocr-pipeline.md), [AGENTS.md](../AGENTS.md) (architecture rules)

## Goals

1. Maintain a **single ordered backlog** of third-party OCR / document models the user asked to integrate, aligned with this repo’s patterns (**FastAPI gateway**, **no browser → heavy inference**, **uv-only backend**, optional **sidecar** or **vLLM** services).
2. For each candidate, record **integration class** (vLLM, custom HTTP sidecar, subprocess/CLI, Transformers.js/browser, external API), **license / compliance note**, and **relation to what is already shipped**.
3. Drive implementation as **small vertical slices** (registry entry → adapter → compose or docs → Run/Arena/History → `issues/*` when non-trivial), not as one giant PR.

## Non-goals (for this document)

- Replacing [ocr-engines.md](./ocr-engines.md) as the **speed ranking** source of truth (update that file when an engine lands and is benchmarked).
- Committing to every name on the list: some rows are **placeholders** (vague product names, unreleased weights, or X-only announcements) and stay **Research** until there is an HF repo, Docker image, or crisp API.

## Architecture constraints (recap)

| Rule | Implication |
|------|-------------|
| Browser never calls vLLM/Ollama/engine hosts | New engines need a **server** adapter (`/api/ocr`, `/api/arena`) or **browser worker** + `POST /api/scan` for browser-tier only. |
| Production path via nginx | Sidecars bind on Docker network; hosts via `*_HOST` env / settings. |
| Arena sequential | Each new server engine must tolerate **queue-style** calls; document VRAM if exclusive. |

**Reuse:** `backend/config/ocr_engines.json`, `engine_registry.py`, `inference/factory.py`, per-engine client modules (see `mineru_client.py`, `vllm_client.py` patterns), optional compose profile + GPU page controls.

---

## Already in repo (do not re-implement from scratch)

Treat these as **done** unless adding a second checkpoint or fixing gaps.

| Engine / capability | Where | Notes |
|---------------------|-------|--------|
| DeepSeek-OCR | vLLM (`vllm-deepseek`) | Baseline GPU OCR. |
| GLM-OCR | vLLM (`vllm-glm`) | Baseline GPU OCR. |
| LightOnOCR | vLLM (`vllm-lighton`) | User list: “Light Ono OCR” / LightOnOCR-1B-1025 / blog — **already routed**. Optional: second catalog row for `2-1B` / bbox variant. |
| Chandra OCR 2 | vLLM (`vllm-chandra`, profile `chandra`) | User list: “Chandra OCR”. |
| MinerU-Diffusion (`nano_dvlm`) | Sidecar `mineru-diffusion` | User list: “Miner U” — **this repo ships the Diffusion decoder**, not full MinerU 2.x parser stack. |
| LiteParse | `litparse` engine | User list: “LiteParse”. |
| Nemotron OCR v2 | Sidecar `nemotron` | User list partially overlaps “Nemotron-Parse” naming. |
| **RapidOCR** | Sidecar `rapidocr` | ONNX (**CPU**), Apache 2.0; model id **`rapidocr`**, profile **`rapidocr`**. |
| Gemma 4 | Optional vLLM (`gemma4` profile) | User list: “Gemma 4 OCR”. |
| Qwen3-VL | Optional vLLM (`qwen3vl`) | Related to “Qwen 3 … VL OCR”. |
| TrOCR | Browser `/scan` | User asked to **keep as example only** for server path — OK to leave browser-only. |
| Tesseract | Browser Tesseract.js | User list: native Tesseract — **server wrapper** would be a *new* integration class if desired. |

---

## Backlog inventory (user list + integration class)

**Legend:** `vLLM` = OpenAI-compatible multimodal chat; `Sidecar` = dedicated HTTP service in Compose; `Subproc` = Python/CLI in backend container or host; `Browser` = worker + `/api/scan`; `API` = external hosted; `Research` = unclear artifact or license.

| Name / link | Class | License / gate | Notes |
|-------------|-------|----------------|--------|
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Subproc or Sidecar | Apache 2.0 | Heavy deps; consider **sidecar** image with PP-OCRv4/v5 + HTTP shim. |
| [RapidOCR](https://github.com/RapidAI/RapidOCR) | Subproc / Sidecar | Apache 2.0 | ONNX-friendly; good candidate for **small sidecar** or bundled ONNX runtime. |
| [MinerU](https://github.com/opendatalab/MinerU) (full stack) | Sidecar | **MinerU 2.5+ AGPL** (verify per release) | Repo previously marked AGPL concern; **Diffusion** path already MIT. Full MinerU needs **explicit license approval** before default compose. |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | Subproc / Sidecar | Apache 2.0 | PyTorch; VRAM; prefer sidecar. |
| [docTR](https://github.com/mindee/doctr) | Subproc / Sidecar | Apache 2.0 | Good “classical + learned” middle ground. |
| [Lany OCR](https://github.com/JC1DA/lanyocr) | Research / Subproc | Check repo license | Confirm maintenance and model weights distribution. |
| [Surya](https://github.com/VikParuchuri/surya) | Sidecar / Subproc | GPL-3.0 | **Conflicts with prior “out of scope”** in medium plan; only integrate if project **accepts GPL** in sidecar boundary. |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) (native) | Subproc | Apache 2.0 | Wrap `tesseract` binary or `pytesseract`; useful for **CPU baseline** and PDF raster fallback. |
| [Docling](https://github.com/DS4SD/docling) | Sidecar | MIT (verify sub-deps) | Layout + OCR pipeline; likely **heavy**; good sidecar candidate. |
| [OnnxTR](https://github.com/felixdittrich92/OnnxTR) | Subproc / Sidecar | Check LICENSE | ONNX — fits **RapidOCR / Onnx** cluster. |
| [TrOCR](https://huggingface.co/docs/transformers/en/model_doc/trocr) | Browser / Example | Apache 2.0 | **Example / research** on server; browser path exists. |
| [LightOnOCR](https://huggingface.co/blog/lightonai/lightonocr) | vLLM | Apache 2.0 | **In repo**; track “Light On OCR 2 1B” as **model ID / prompt** updates only. |
| Doc OWL | Research | — | Specify HF model id (e.g. DocOwl family) before design. |
| [Phi-4-multimodal](https://huggingface.co/microsoft/Phi-4-multimodal-instruct) | vLLM | MS license | VLM OCR via chat template; **vLLM spike** + VRAM plan. |
| Smol Docling | Research | — | Pin exact HF artifact; likely vLLM or Transformers sidecar. |
| [RolmOCR](https://huggingface.co/reducto/RolmOCR) | vLLM | Check license | Reducto weights; vLLM if architecture supported. |
| [IBM Granite Docling WebGPU](https://huggingface.co/spaces/ibm-granite/granite-docling-258M-WebGPU) | Browser (WASM) | Apache 2.0 | Likely **browser tier** only unless IBM ships server ONNX; compare to existing PaliGemma worker cost. |
| Aya Vision OCR | vLLM / Ollama | Check license | Blog comparisons only until a **single serve command** is chosen. |
| Mistral OCR / “Mistral OCR 3” | API / vLLM | **Often API-only** | If closed API, add `engine.type: http_proxy` pattern or document “out of self-host”. |
| Dolphin (X link) | Research | — | Wait for open weights + license. |
| [Dots.OCR](https://github.com/rednote-hilab/dots.ocr) | Sidecar / vLLM | Check LICENSE | Newer layout OCR — spike vLLM vs custom. |
| [Qwen3-Omni](https://github.com/QwenLM/Qwen3-Omni) | vLLM | Qwen license | Large multimodal; **optional profile** like Qwen3-VL. |
| owlOCR / OCR Flux / Monkey OCR / Nanonets | Research | — | Clarify vendor vs OSS; many are **marketing names**. |
| [NuMarkdown](https://github.com/numindai/NuMarkdown) / [NuMarkdown-8B](https://huggingface.co/numind/NumMarkdown-8B-Thinking) | vLLM | Check license | “Markdown thinking” VLM — may overlap OCR with **long reasoning**; high VRAM. |
| DocParse / OCR Docker / OpenPage / OCRbro / DocuMagnet / OCR Studio | Research | — | Could be products; **do not implement** until open inference surface exists. |
| Gemma 3 OCR / Falcon OCR / Youtu-VL / Hunyuan OCR / ExaOCR / Col Pali / Pixl | Research | — | Pin HF ids; **ColPali** is retrieval — different task unless scoped to “OCR-like”. |
| Pike PDF | Research | — | Clarify if library vs model. |
| DeepSeek OCR 2 / Paddle OCR VL 1.5 / MinerU 2.5 / Dolphin v2 / Light On OCR 2 | Research | — | Track upstream releases; integrate when **public weights + serve recipe** stabilizes. |
| Gemini 3.0 | API | Google ToS | Only via **user API key** pattern if ever; out of default self-host stack. |
| iFlyTek AI NOTE 2 | API / closed | Commercial | Likely **out of scope** for self-host unless legal + SDK. |

---

## Suggested waves (priority order)

Order balances **license safety**, **engineering clarity**, and **distinct capability** vs what is already shipped.

### Wave 0 — Hygiene (ongoing)

- Keep `ocr_engines.json` as the **catalog**; merge duplicate conceptual entries (e.g. multiple “MinerU” rows) into **one service + variants**.
- For each new engine: **model id**, **prompt policy**, **input modes** (`image` / `pdf`), **`speed_tier`**, **`issues/<slug>.md`** if Docker or VRAM non-trivial.

### Wave 1 — Classical / ONNX cluster (CPU-friendly sidecars)

**Candidates:** ~~RapidOCR~~ (**in repo**), OnnxTR, optional native **Tesseract** wrapper, docTR (if smaller variant fits CPU).

**Approach:** Thin FastAPI sidecar in `docker/` + small adapter in `backend/app/`. Prefer **one multi-model sidecar** only if deps align; else separate images to avoid dependency hell.

### Wave 2 — PyTorch “OCR libraries” (GPU sidecars)

**Candidates:** PaddleOCR, EasyOCR, Lany OCR (if active).

**Approach:** Dedicated Dockerfiles, **one model family per container**, strict timeouts, return plain text + optional boxes in JSON for Arena parity.

### Wave 3 — Layout / document AI (heavier sidecars)

**Candidates:** Docling, Dots.OCR, (optional) full MinerU **after license sign-off**.

**Approach:** Reuse MinerU-Diffusion lessons: internal HTTP, batching flags, strong error messages when OOM.

### Wave 4 — GPL / policy decision engines

**Candidates:** Surya, any GPL stack.

**Approach:** **Project decision**: either (a) keep GPL strictly inside optional **optional profile** container with SPDX + docs, or (b) drop. Do not silently bundle.

### Wave 5 — New VLMs on vLLM (when distinct from existing)

**Candidates:** Phi-4-multimodal, RolmOCR, Qwen3-Omni, Smol Docling (if servable), NuMarkdown-class models.

**Approach:** Same as LightOn/Chandra: `docker-compose` profile, `vllm-entrypoint.sh` branch, `prompts.json`, `VLLM_*` limits.

### Wave 6 — Browser / WebGPU demos

**Candidates:** IBM Granite Docling WebGPU, other WASM-friendly small models.

**Approach:** Extend **browser worker** pipeline; results via `POST /api/scan`; label latency in UI.

### Wave 7 — External APIs (optional product direction)

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
| AGPL / GPL in default compose | Keep AGPL/GPL images behind **explicit profiles**; document in plan + README. |
| “Name-only” models | Require HF ID or container tag before scheduling work. |
| Mistral / Google **API-only** | Do not pretend self-hosted; use cloud adapter or defer. |
| Arena fairness | Shared preprocess (`normalize_page_image`) for raster inputs; PDF engines compared only on PDF-capable rows. |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-16 | RapidOCR CPU sidecar (`rapidocr`, profile `rapidocr`, port 8220) |
