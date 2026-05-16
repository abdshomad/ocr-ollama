# owlOCR / OCR Flux / Monkey OCR / Nanonets — Wave R research triage

**Date:** 2026-05-16  
**Backlog:** [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) — **Next research triage #4**

## Summary

The backlog bundles **four ambiguous names**. Triage pins **concrete artifacts** where they exist and separates **vendor products** from **research weights**. None of these replace a single “Ship tomorrow” row without a follow-up **license check** (several are **Qwen-derived** or **non-commercial**).

## Disambiguation table

| Backlog name | What it usually points to | Pinned artifact(s) | License / compliance (triaged) |
|--------------|---------------------------|--------------------|--------------------------------|
| **owlOCR** | Often **homophone confusion** with **OlmOCR** (Allen AI), or the **Mac app** “OwlOCR” | **Typo / confusion:** [**allenai/olmOCR-7B-0725**](https://huggingface.co/allenai/olmOCR-7B-0725), [**allenai/olmOCR-2-7B-1025-FP8**](https://huggingface.co/allenai/olmOCR-2-7B-1025-FP8), toolkit [**github.com/allenai/olmocr**](https://github.com/allenai/olmocr) — **Apache-2.0** (per HF / project). **Different product:** [owlocr.com](https://www.owlocr.com/) — **commercial Mac OCR**, not an HF checkpoint for this gateway. |
| **OCR Flux** | **ChatDOC OCRFlux** (document parsing VLM) | [**ChatDOC/OCRFlux-3B**](https://huggingface.co/ChatDOC/OCRFlux-3B), code [**github.com/chatdoc-com/OCRFlux**](https://github.com/chatdoc-com/OCRFlux) | Repo **`LICENSE`** file is the [**Qwen RESEARCH LICENSE AGREEMENT**](https://huggingface.co/ChatDOC/OCRFlux-3B/raw/main/LICENSE) (**non-commercial / research**; commercial use needs separate permission from Alibaba Cloud per that text). **Do not** assume “Apache 2.0” from third-party blog copy — **verify `LICENSE` in the HF repo**. |
| **Monkey OCR** | **MonkeyOCR** (SRR document parsing) | HF [**echo840/MonkeyOCR**](https://huggingface.co/echo840/MonkeyOCR), upstream [**github.com/Yuliang-Liu/MonkeyOCR**](http://www.github.com/Yuliang-Liu/MonkeyOCR) | Model card **Copyright** section: intended for **academic research and non-commercial use**; commercial contact per institutional emails on card. **Not** a default permissive OSS license for all uses. |
| **Nanonets** | Company + open **small** weights + hosted API | Weights [**nanonets/Nanonets-OCR-s**](https://huggingface.co/nanonets/Nanonets-OCR-s) (Qwen2.5-VL-3B-class fine-tune per HF metadata); **hosted** OCR/API and **on-prem enterprise** per [Nanonets docs](https://docs.nanonets.com/docs/on-prem-offerings) | **HF:** no **`LICENSE`** file at repo root found in this triage (**404** on `.../raw/main/LICENSE`); **follow** HF discussions on **License** (#2, #19, etc.) and Nanonets legal terms for redistribution. **Self-host integration** likely inherits **Qwen** usage constraints from base model — treat as **license spike** before Ship. **Cloud-only** path belongs in **Wave 6** (`cloud_http` + API key), not default compose. |

## Inference surface (high level)

- **OlmOCR:** Mature **Apache-2.0** story; PDF-focused pipeline in `allenai/olmocr` — best **permissive** candidate if the user meant “owlOCR.”
- **OCRFlux-3B / Nanonets-OCR-s:** **`AutoModelForImageTextToText`** + processor; **vLLM** may apply to Qwen2.5-VL derivatives (HF discussions mention vLLM issues for Nanonets-OCR-s) — **GPU validation** required before documenting a one-liner.
- **MonkeyOCR:** Project-specific inference / demo stack on GitHub — **not** assumed identical to stock `vllm serve` without spike.

## Symptoms / user-facing gap

- None (research only).

## Resolution (triage outcome)

| Exit criterion | Status |
|----------------|--------|
| Concrete HF or product id per name | **Met** (with **owlOCR → OlmOCR** + OwlOCR Mac product called out). |
| License reference (not GPL-3.0) | **Partially met** — **OCRFlux = Qwen Research (NC)**; **MonkeyOCR = non-commercial (card)**; **Nanonets = verify** (no root `LICENSE`); **OlmOCR = Apache-2.0**. |
| Minimal vLLM / sidecar serve command | **Not met** in this doc — **per-model GPU spike**. |

**Conclusion:** Wave R **#4 triaged**. For a **permissive default** integration target from this list, prefer **Allen AI OlmOCR** if the user meant “owlOCR.” **OCRFlux** and **Nanonets-OCR-s** need **Qwen / vendor license** review before Ship. **MonkeyOCR** needs **non-commercial / academic** acceptance. **Nanonets SaaS** remains **Wave 6** API territory.

## Repo impact

- Documentation only: backlog + [issues/README.md](README.md).
