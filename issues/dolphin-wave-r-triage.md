# Dolphin (ByteDance document parsing) — Wave R research triage

**Date:** 2026-05-16  
**Backlog:** [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) — **Next research triage #3 (Dolphin)**

## Summary

The vague backlog row **“Dolphin (X link)”** resolves to **ByteDance’s Dolphin** document image parsing models on Hugging Face — **not** unrelated chat LLMs that happen to use the name “Dolphin.” There are **two public checkpoints** with **different licenses**:

| Model id | Role | License (as triaged) |
|----------|------|----------------------|
| [`ByteDance/Dolphin`](https://huggingface.co/ByteDance/Dolphin) | **v1** — Swin + mBART-style vision–encoder–decoder; two-stage layout + parallel element parsing | **MIT** (HF tag `license:mit`; model card states MIT) |
| [`ByteDance/Dolphin-v2`](https://huggingface.co/ByteDance/Dolphin-v2) | **v2** — Qwen2.5-VL-3B-class backbone; stronger layout/table/formula/code coverage | **Qwen RESEARCH LICENSE** (repo `LICENSE` text — **non-commercial / research**; commercial use requires separate permission from Alibaba Cloud per that agreement) |

**GPL:** Neither variant is GPLv3; **v2 is license-gated** similarly to other **Qwen research** stacks (compare backlog notes on Qwen family terms).

**Upstream code / recipes:** [github.com/bytedance/Dolphin](https://github.com/bytedance/Dolphin) — includes HF-oriented demos (e.g. page-wise / element-wise parsing scripts referenced from the v1 model card).

## Pinned artifacts

- **Primary (permissive):** `ByteDance/Dolphin` — **not gated** on HF; **Transformers** `VisionEncoderDecoderModel` / `AutoModelForImageTextToText` per card.
- **Newer capability / stricter terms:** `ByteDance/Dolphin-v2` — **not gated** on HF for download in metadata reviewed here; **`LICENSE`** is **Qwen RESEARCH LICENSE** (NC research grant); backbone attribution to **Qwen2.5-VL**.

## Inference / serve paths

### Transformers (verified story on HF cards)

- Both models expose **`AutoModelForImageTextToText`** + processor/tokenizer patterns suitable for **Python inference** and wrapping in a **small HTTP sidecar** (this repo’s Nemotron / MinerU-diffusion pattern).
- **v1** card points to GitHub `demo_page_hf.py` / `demo_element_hf.py` for **page-level** vs **crop-level** flows.

### vLLM / OpenAI-compatible `vllm serve`

- **v0.21.0 “Supported models”** table checked during triage does **not** list **`ByteDance/Dolphin`** or **`ByteDance/Dolphin-v2`** by name.
- vLLM has surfaced **Dolphin-oriented** examples/discussions (e.g. offline inference docs / issues in the vLLM tracker). Treat **one-command `vllm serve ByteDance/Dolphin-v2`** as **unverified** until smoke-tested on the **same vLLM image** you ship; **v2** may still behave like a **Qwen2.5-VL** derivative for serving — that needs a **GPU spike**, not desk research alone.

**Practical recommendation for Ship:** plan **either** (a) **GPU sidecar** + Transformers using the official GitHub demo flow, **or** (b) a **pinned vLLM version** spike after confirming OpenAI multimodal chat compatibility for Dolphin-v2.

### Ollama

- No **first-party** `ollama.com/library` slug established here; HF lists **community quantizations** that may advertise Ollama — **not** the canonical integration path for this repo.

## Symptoms / user-facing gap

- None (research only). No `dolphin` engine in the app today.

## Resolution (triage outcome)

| Exit criterion ([backlog](../plan/ocr-engine-expansion-backlog.md)) | Status |
|---------------------------------------------------------------------|--------|
| HF weights + clear naming | **Met** — `ByteDance/Dolphin`, `ByteDance/Dolphin-v2`. |
| License reference (not GPL-3.0) | **Met** — **MIT (v1)**; **Qwen Research License (v2)** (**NC** — org must accept before default Ship). |
| Minimal **vLLM** `serve` one-liner | **Not verified** in this triage — needs **GPU spike** or **sidecar** path. |

**Conclusion:** Wave R **#3 is triaged** with **pinned HF ids** and **license split (v1 vs v2)**. **Default “open” Ship candidate** for permissive stacks is **`ByteDance/Dolphin` (MIT)**. **`ByteDance/Dolphin-v2`** is **research/Qwen-license** — use only with **explicit compliance**, like other NC- or vendor-gated models.

**Next step (implementation):** If shipping: add **`plan/dolphin-integration.md`**, pick **v1 (MIT)** vs **v2 (Qwen NC)**, then sidecar or vLLM spike + `ocr_engines.json` / `factory.py` wiring.

## Repo impact

- Documentation only for this Wave R step: backlog + [issues/README.md](README.md).
