# OCR engine verification — browser-first matrix

**Date:** 2026-05-17  
**Status:** Active procedure  
**Goal:** Prove **each OCR-capable engine** returns **non-empty, plausible text** through the real UI, using **Cursor IDE browser MCP** (or equivalent automation). When a run fails, **diagnose, fix in-repo, document in `issues/`**, and re-run until it passes for that engine on this host.

**Related:** [AGENTS.md](../AGENTS.md) (`test` / `t` workflow), [ocr-engines.md](./ocr-engines.md), [browser-ocr-pipeline.md](./browser-ocr-pipeline.md), config sources [`backend/config/vllm_endpoints.json`](../backend/config/vllm_endpoints.json), [`backend/config/ocr_engines.json`](../backend/config/ocr_engines.json).

---

## 1. Definitions

| Term | Meaning |
|------|--------|
| **Server OCR engine** | Any model selectable on **Run** (`/`) — listed by `GET /api/models`, executed via `POST /api/ocr` (browser never talks to vLLM/Ollama directly). |
| **Browser scan engine** | Worker engines on **Scan** (`/scan`) — TrOCR, Tesseract.js, Granite Docling, PaliGemma, optional Chrome Built-in AI (see [browser-ocr-pipeline.md](./browser-ocr-pipeline.md)). |
| **Pass** | After **Run OCR** (or **Scan**), the result panel shows **non-empty** output that **matches visible text** in the sample (allow normal OCR noise; reject blank, error-only, or obvious garbage). |

**Scope note:** Optional **Arena** compare is *not* required for sign-off; use it only if it helps debug a specific model interaction.

---

## 2. Preconditions

1. **App URL:** `http://127.0.0.1:${PORT}` — read `PORT` from [.env](../.env) (default **3036** per [.env.example](../.env.example)).
2. **Health:** `curl -sS "http://127.0.0.1:${PORT}/api/health"` returns OK before UI testing.
3. **Canonical model list (server):**  
   `curl -sS "http://127.0.0.1:${PORT}/api/models" | jq '.models[] | select(.ocr_capable==true) | {name, available, tier, vllm_endpoint_label}'`  
   Treat **`available: true`** as “runnable on this stack right now.” **`false`** means start the matching Compose service/profile (see AGENTS.md Common tasks) **before** expecting a browser pass.
4. **Fixtures / samples:**
   - **Images for Run:** Prefer **built-in samples** from `GET /api/samples` (files live under `backend/SAMPLES/IMAGES` unless `SAMPLE_IMAGES_DIR` overrides). Use UI or upload the same files manually.
   - **Extra local files:** Documentation often cites `fixtures/ocr/`; **create or symlink** that tree if missing, with at least one **clear PNG/JPEG** (printed text) and, for **LiteParse (`litparse`)**, a **small digital PDF** with embedded text (not scan-only).
5. **Browser MCP:** Follow **cursor-ide-browser** rules: `browser_navigate` → `browser_lock` → `browser_snapshot` before interactions → one action → fresh snapshot → unlock when finished.

---

## 3. Standard browser procedure (Run — one engine)

Repeat **per model** (or per distinct model name in `/api/models`).

| Step | Action | Verify |
|------|--------|--------|
| 1 | Open **`/`** (Run). | Page loads; model picker visible. |
| 2 | In Settings (if needed), set **inference backend** and hosts so the target engine can reach vLLM/Ollama/sidecars. | `/api/models` shows target with `available: true`. |
| 3 | Select **exactly one** model matching the engine under test. | Radio/checkbox state matches snapshot. |
| 4 | Attach sample: use **sample picker** if present, else **file upload** with a readable image (or PDF only where the model accepts PDF). | File name or preview shows in UI. |
| 5 | Submit **Run OCR** / primary action. | Loading completes without blocking error toast. |
| 6 | Read **result panel** text. | **Pass:** substantive OCR text. **Fail:** empty, timeout, 502-style message, or irrelevant output → go to §5. |
| 7 | Capture evidence | Save **browser_snapshot** YAML (and optional screenshot) in chat or attach to issue notes. |

**LiteParse:** Run with **digital PDF** (and any image types the backend accepts for that model). Expect **extracted embedded text**, not a blank panel.

**Multi-variant vLLM endpoints:** If `/api/models` returns several names for one endpoint (e.g. multiple Qwen3-VL sizes), test **each name** you intend to support, or document that only a subset is in use.

---

## 4. Browser procedure (Scan — one engine)

On **`/scan`**, for each selectable engine mode (e.g. default TrOCR, Fast/Tesseract, Granite Docling, PaliGemma):

| Step | Action | Verify |
|------|--------|--------|
| 1 | Open **`/scan`**, choose engine tier. | Worker loads (first run may download ONNX; wait per snapshot). |
| 2 | Provide a **crop or image** with legible text (product label or typed sample). | Preview OK. |
| 3 | Run scan. | **SKU/expiry** or **raw text** path shows non-empty sensible content where applicable. |
| 4 | Optional | Confirm history or network `POST /api/scan` succeeds if testing persistence. |

**Chrome Built-in AI:** Mark as **environment-dependent** (browser support + user gesture). If unavailable, record **N/A** with reason; do not block shipping other engines.

---

## 5. Failure loop (fix until succeeded)

1. **Reproduce** with the same sample and model; note HTTP status from browser **network** tools if the UI hides detail.
2. **Split cause:**
   - **Unavailable service** → start correct Compose profile / GPU service; confirm sidecar health (see relevant `issues/*.md`).
   - **Backend routing** → wrong host in `settings.json` vs Docker network; fix settings or env documented in AGENTS.md.
   - **Upload validation** → MIME/size; adjust sample or backend limits only if justified.
   - **Model/prompt** → check [`backend/config/prompts.json`](../backend/config/prompts.json) and model-specific notes in `issues/`.
3. **Implement minimal fix** in app code or Compose/docs — **no unrelated refactors.**
4. **Document** non-trivial problems and resolutions in **`issues/<slug>.md`** (Summary, Symptoms, Analysis, Resolution, Repo impact). Update [`issues/README.md`](../issues/README.md) if adding a new primary doc.
5. **Re-run** §3 or §4 for that engine until **Pass**.

---

## 6. Master checklist (server OCR)

Use `/api/models` as the live source. The tables below match **registry defaults** in-repo; **skip** rows your stack does not deploy, but **document** “not run on this host” vs “broken.”

### 6.1 Always-on or CPU (typical)

| Engine / model id | Compose / notes | Browser test (Run) |
|---------------------|-----------------|-------------------|
| `tesseract` | Native in backend image | [x] |
| `litparse` | PDF + image modes | [x] (use digital PDF + image) |
| `rapidocr` | profile `rapidocr` | [x] |
| `onnxtr` | profile `onnxtr` | [x] |
| `easyocr` | profile `easyocr` | [x] |
| `doctr` | profile `doctr` | [x] |
| `paddleocr` | profile `paddleocr` | [x] |
| `docling` | profile `docling` | [x] |
| `lanyocr` | profile `lanyocr` | [x] |

### 6.2 GPU sidecars (optional)

| Engine / model id | Profile (see AGENTS.md) | [ ] |
|-------------------|-------------------------|-----|
| `opendatalab/MinerU-Diffusion-V1-0320-2.5B` | `mineru` | [ ] |
| `nvidia/nemotron-ocr-v2` | `nemotron` | [x] |

### 6.3 vLLM endpoints (optional — each `models[]` entry)

Check off **each model name** your deployment exposes as `available`.

| Endpoint id / label | Model id(s) in config | [ ] |
|---------------------|------------------------|-----|
| `deepseek` | `deepseek-ai/DeepSeek-OCR` | [x] |
| `deepseek-ocr2` | `deepseek-ai/DeepSeek-OCR-2` | [x] |
| `glm` | `zai-org/GLM-OCR` | [ ] |
| `lighton` | `lightonai/LightOnOCR-2-1B` | [ ] |
| `chandra` | `datalab-to/chandra-ocr-2` | [ ] |
| `gemma4` | `google/gemma-4-E4B-it` | [ ] |
| `qwen3vl` | `Qwen/Qwen3-VL-*` (each size in use) | [ ] |
| `hunyuanocr` | `tencent/HunyuanOCR` | [x] |
| `paddleocr-vl` | `PaddlePaddle/PaddleOCR-VL` | [ ] |
| `paddleocr-vl-15` | `PaddlePaddle/PaddleOCR-VL-1.5` | [ ] |
| `dotsmocr` | `rednote-hilab/dots.mocr` | [x] |
| `phi4multimodal` | `microsoft/Phi-4-multimodal-instruct` | [ ] |
| `rolmocr` | `reducto/RolmOCR` | [ ] |
| `numarkdown` | `numind/NuMarkdown-8B-Thinking` | [ ] |
| `qwen3omni` | `Qwen/Qwen3-Omni-30B-A3B-*` (each in use) | [ ] |
| `smoldocling` | `docling-project/SmolDocling-256M-preview` | [x] |

### 6.4 Ollama backend

When `INFERENCE_BACKEND=ollama`, repeat §3 for **each** `ocr_capable` model returned by `/api/models` **after** pulling the model on that host. Checklist is **dynamic** — export names from `jq` and tick manually.

---

## 7. Master checklist (browser Scan)

| Mode / engine | [ ] |
|---------------|-----|
| Default (TrOCR / auto path) | [ ] |
| Tesseract.js (“Fast” / fallback path) | [x] |
| Granite Docling (`granite`) | [ ] |
| PaliGemma 2 (“High quality”) | [ ] |
| Chrome Built-in AI refine (if supported) | [ ] N/A: ___ |

---

## 8. Completion criteria

- **Server OCR:** Every **deployed** engine you intend to support has **[ ] → [x]** on §6 with snapshot evidence once.
- **Browser Scan:** §7 modes exercised; N/A documented with reason where environment blocks testing.
- **Issues:** Any fix touching behavior has a matching **`issues/*.md`** resolution trail.
- **Regression:** After broad changes, re-run `/api/health`, spot-check **default Run model** + **one** optional engine you rely on.

---

## 9. Quick reference commands

```bash
# Models (server)
curl -sS "http://127.0.0.1:${PORT}/api/models" | jq .

# Samples list (images)
curl -sS "http://127.0.0.1:${PORT}/api/samples" | jq .

# Optional direct OCR (for debugging without browser)
curl -sS -X POST "http://127.0.0.1:${PORT}/api/ocr" \
  -F "image=@/path/to/sample.png;type=image/png" \
  -F "model=MODEL_ID_HERE" | jq .
```

---

## 10. Maintenance

When adding an engine:

1. Update [`backend/config/ocr_engines.json`](../backend/config/ocr_engines.json) or [`backend/config/vllm_endpoints.json`](../backend/config/vllm_endpoints.json).
2. Add a row to §6 (or note “dynamic Ollama”).
3. Add integration notes under **`issues/`** if non-trivial.
4. Run §3 once against **Run** (and `/scan` only if browser-tier).
