# Doc OWL (mPLUG-DocOwl) — Wave R research triage

**Date:** 2026-05-16  
**Backlog:** [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) — **Next research triage #1 (Doc OWL)**

## Summary

“Doc OWL” in the user backlog maps cleanly to Alibaba’s **mPLUG-DocOwl** line on Hugging Face. The current generation checkpoint **`mPLUG/DocOwl2`** is public, **Apache-2.0**, document-oriented multimodal (OCR-free QA / multi-page understanding), loaded via **Transformers** with **`trust_remote_code=True`** (`custom_code`). **Stock vLLM does not list mPLUG/DocOwl** in its supported-models catalog (checked v0.21.0 docs mirror in workspace research), so this repo’s default **optional GPU pattern (`vllm serve` + OpenAI adapter)** is **not** available without upstream vLLM support or a **custom GPU sidecar** (Transformers + small HTTP shim), analogous to Nemotron / MinerU-Diffusion.

## Pinned Hugging Face lineage

| Priority | Model id | Params (HF) | License (HF tags) | Role |
|----------|-----------|-------------|-------------------|------|
| **Primary** | [`mPLUG/DocOwl2`](https://huggingface.co/mPLUG/DocOwl2) | ~9B (BF16 ~8.6GB) | **Apache-2.0** | Multi-page doc MLLM; DocCompressor → **324 image tokens/page** (card quickstart). |
| Legacy | [`mPLUG/DocOwl1.5`](https://huggingface.co/mPLUG/DocOwl1.5) | 8B | Apache-2.0 (verify card) | Prior single/multi-image line. |
| Variants | [`mPLUG/DocOwl1.5-Omni`](https://huggingface.co/mPLUG/DocOwl1.5-Omni), [`mPLUG/DocOwl1.5-Chat`](https://huggingface.co/mPLUG/DocOwl1.5-Chat), [`mPLUG/DocOwl1.5-stage1`](https://huggingface.co/mPLUG/DocOwl1.5-stage1) | 8B | Apache-2.0 (verify each) | Stages / chat / omni splits. |

**Collection (source of truth for series):** [DocOwl Series — mPLUG](https://huggingface.co/collections/mPLUG/docowl-series).

**Upstream code:** [X-PLUG/mPLUG-DocOwl](https://github.com/X-PLUG/mPLUG-DocOwl) (paper: [arXiv:2409.03420](https://arxiv.org/abs/2409.03420)).

**GPL:** Not applicable — Apache-2.0 on the pinned DocOwl2 card; align with [AGENTS.md](../AGENTS.md) non-GPL policy.

## Symptoms / user-facing gap

- None (research only). The app has no `docowl` engine today; this note is the **gate** before design.

## Analysis / evidence

### Inference surface today

- **Hugging Face card** documents **Python Transformers** inference: `AutoTokenizer`, `AutoModel.from_pretrained(..., trust_remote_code=True)`, `model.init_processor(...)`, **`model.chat(messages=..., images=..., tokenizer=...)`**. Message format uses `<|image|>` repeats per page + user text query.
- **HF Inference API:** DocOwl2 is **not** deployed on HF Inference Providers (card message as of triage).
- **vLLM:** No **DocOwl** / **mplug_docowl** entry in vLLM **Supported Models** documentation reviewed during this spike — **do not assume** `vllm serve mPLUG/DocOwl2` works like DeepSeek-OCR / GLM-OCR without an explicit upstream recipe.

### Fit for ocr-ollama

- **Workload:** Strong for **document understanding** and **multi-page** contexts; for **single-page “OCR text dump”** the gateway would pass one image and a prompt such as “Transcribe all visible text, preserve reading order.”
- **Architecture constraint:** Browser must not call the engine host; any integration must be **`POST /api/ocr`** via backend (sidecar or future vLLM).
- **VRAM:** ~9B BF16 class — plan for **one dedicated GPU** service, similar footprint to other 7–9B multimodal stacks.

## Resolution (triage outcome)

| Exit criterion ([backlog § exit criteria](../plan/ocr-engine-expansion-backlog.md)) | Status |
|----------------------------------------------------------------------------------|--------|
| HF repo / weights | **Met** — `mPLUG/DocOwl2` (+ 1.5 family above). |
| License not GPL-3.0 | **Met** — Apache-2.0 on DocOwl2. |
| Minimal **vLLM** serve command | **Not met** — no verified stock vLLM path in docs reviewed. |
| Sample I/O for `fixtures/ocr/` | **Deferred** until a concrete **Ship** integration exists. |

**Conclusion:** Wave R item **Doc OWL** is **triaged**: family and primary **`model_id` are pinned**. Status: **Research → Spike complete**; **Ship** remains **blocked on vLLM** unless we **choose a non-vLLM path** (recommended **optional GPU sidecar**: FastAPI + `transformers` + CUDA, single-model container).

**Next implementation step (separate task / not Wave R):** If product wants DocOwl in-app, open a **`plan/docowl-sidecar-integration.md`** (or vLLM spike if vLLM adds official support) and add `engine.type` + compose profile + client module following [plan/medium-four-ocr-models.md](../plan/medium-four-ocr-models.md).

## Repo impact

- This triage updates [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) and [issues/README.md](README.md). **No runtime code** in this change set unless a follow-up Ship task is approved.
