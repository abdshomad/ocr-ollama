# Wave R #8 — upstream watchlist (DeepSeek OCR 2, PaddleOCR-VL-1.5, MinerU, Dolphin v2, LightOnOCR 2)

**Date:** 2026-05-16  
**Backlog:** [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) — **Next research triage #8**

## Summary

This row bundled **several “2.x / 1.5” follow-ons**. Triage outcome: **two are now pin-ready on Hugging Face** (ship still needs **this-repo** vLLM or sidecar spikes), **two are license / product gates**, and **one is already shipped** here.

| Name | HF / upstream pin | License (HF tags / repo as triaged) | Status vs this repo |
|------|-------------------|-------------------------------------|---------------------|
| **DeepSeek-OCR 2** | [`deepseek-ai/DeepSeek-OCR-2`](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2) | **Apache-2.0** (`license:apache-2.0`); **custom_code** | **Weights public.** Default stack still targets **DeepSeek-OCR (v1)** on `vllm-deepseek`. **v2** = separate multimodal OCR model (~3.4B params); upstream README points to GitHub for **vLLM** acceleration — **Spike** `vllm serve` + prompt policy on our **`Dockerfile.vllm-ocr`** image before adding a second catalog entry. |
| **PaddleOCR-VL-1.5** | [`PaddlePaddle/PaddleOCR-VL-1.5`](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5) | Verify on HF card per release (expect similar to Paddle family) | **Weights public** (0.9B-class doc VLM). We already ship **`PaddlePaddle/PaddleOCR-VL`** on optional `vllm-paddleocr-vl` — **1.5** is a **new checkpoint**, not automatic. **Spike:** same service pattern, new model id + endpoint routing + smoke on Arena. |
| **MinerU 2.5+** | [MinerU](https://github.com/opendatalab/MinerU) | **AGPL** concern for full stack (verify per release) | **Unchanged:** full MinerU needs org license approval for default compose. **MIT** [MinerU-Diffusion / nano path](mineru-diffusion-nano-dvlm-integration.md) already integrated separately. |
| **Dolphin v2** | [`ByteDance/Dolphin-v2`](https://huggingface.co/ByteDance/Dolphin-v2) | **Qwen RESEARCH LICENSE** (non-commercial / research) | **Weights public;** terms stricter than v1. See [dolphin-wave-r-triage.md](dolphin-wave-r-triage.md). Ship only with explicit NC/commercial approval. |
| **Light On OCR 2** | [`lightonai/LightOnOCR-2-1B`](https://huggingface.co/lightonai/LightOnOCR-2-1B) | Apache-2.0 (per backlog / existing integration doc) | **Already in repo** — optional **`vllm-lighton`**, profile `lighton`. No extra Wave R work unless the catalog splits a **bbox** variant ([lightonocr-vllm-integration.md](lightonocr-vllm-integration.md)). |

## Practical recommendation

- **Promote to implementation queue (separate `plan/` + Ship slice):** **DeepSeek-OCR-2** and/or **PaddleOCR-VL-1.5** when GPU time is available — after a **single-GPU smoke** on the same vLLM baseline you run for other `custom_code` VLMs.
- **Keep as license watch:** **MinerU** (AGPL), **Dolphin-v2** (Qwen NC).
- **Remove from “missing artifact” anxiety:** **LightOnOCR-2-1B** is done.

## Repo impact

- Documentation / backlog only unless a follow-up Ship plan is opened.
