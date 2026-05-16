# DocParse / OCR Docker / OpenPage / OCRbro / DocuMagnet / OCR Studio — Wave R research triage

**Date:** 2026-05-16  
**Backlog:** [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) — **Next research triage #5**

## Summary

These names mostly denote **vendor products**, **add-ins**, or **ambiguous labels** — not a single stack with **public model weights + reproducible self-host recipe** like the engines already integrated in this repo. **Ship remains deferred** per the backlog gate: no default **`vllm serve` / sidecar / `ocr_engines.json`** target without a **pinned open artifact** and license review.

Triage below records **what each name usually is**, so future backlog edits can split rows or drop placeholders.

## Name-by-name disposition

| Name | Typical referent | Open inference surface? | Notes |
|------|------------------|---------------------------|--------|
| **DocParse** | **Aryn DocParse** ([aryn.ai](https://www.aryn.ai/docparse), [docs.aryn.ai](https://docs.aryn.ai/docparse/introduction)) — document parsing / OCR SaaS; **on-prem / private cloud** positioning | **Commercial** — REST/SDK under vendor terms; **not** a Hugging Face weight drop for generic gateway integration | Unrelated: **DocParse Arena** ([DocParse_Arena](https://github.com/Bae-ChangHyun/DocParse_Arena)) is an **MIT** *comparison harness* for parsing models, not a replacement OCR engine product. |
| **OCR Docker** | **Not one canonical OSS product** — many small repos (e.g. Flask + Tesseract wrappers) use similar wording | **N/A** — treat as **pattern** (“OCR in Docker”) unless the user supplies a **URL** | If the intent was **containerized Tesseract**, this repo already has **native Tesseract** and browser/worker paths. |
| **OpenPage** | **No dominant OSS** “OpenPage OCR” located in search | **Defer** — likely **wrong name** or niche product; could be confused with **OpenPages** (other domains), **Open-Capture**, etc. | Need a link from the requester to pin. |
| **OCRbro** | **n8n community node** ([blankarrayy/ocrbro](https://github.com/blankarrayy/ocrbro) cited in ecosystem) — **Tesseract.js** + PDF text extraction, local | **Integration class ≠ ocr-ollama server engine** — workflow node, not a distinct multimodal OCR **model id** | Could overlap conceptually with **browser/worker Tesseract** work; **not** a Wave 1–4 **Ship** without an explicit new requirement. |
| **DocuMagnet** | **DocuMagnet** ([documagnet.com](https://www.documagnet.com/)) — **financial** document extraction (Sheets/Excel add-ins, marketplace SaaS) | **No** — commercial product / API behind accounts | Out of scope for default self-host OCR model list. |
| **OCR Studio** | **OCR Studio** ([ocrstudio.ai](https://ocrstudio.ai/)) — **commercial SDK** / on-device stack for **ID / MRZ** and related capture; GitHub org [OCR-Studio](https://github.com/OCR-Studio) hosts **SDK samples** | **No** open **general document OCR** checkpoint comparable to repo VLMs; **SDK licensing** is vendor-driven | Suitable only under a future **commercial SDK** or **Wave 6 cloud** policy, not default compose. |

## Exit criteria (backlog)

| Criterion | Status |
|-----------|--------|
| HF repo or pinned container + usable license | **Not met** for this bundle as **one** Ship candidate |
| Minimal vLLM / sidecar command | **N/A** |
| Sample I/O | **N/A** |

**Conclusion:** Wave R **#5 triaged** — identities documented; **status remains defer / blocked for Ship** until a specific product publishes **open weights** or a **stable self-host HTTP API** with terms compatible with this repo (and the user pins **one URL + model/API id**).

## Repo impact

- Documentation only: backlog + [issues/README.md](README.md).
