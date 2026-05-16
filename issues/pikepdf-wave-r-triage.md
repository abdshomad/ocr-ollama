# “Pike PDF” / pikepdf — Wave R research triage

**Date:** 2026-05-16  
**Backlog:** [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) — **Next research triage #7 (Pike PDF)**

## Summary

The backlog name **“Pike PDF”** maps to **[pikepdf](https://github.com/pikepdf/pikepdf)** — a **Python library** for reading and writing PDFs, built on **[QPDF](https://qpdf.sourceforge.io/)**. It is **not** a Hugging Face vision model, **not** an OCR neural net, and **not** something you `vllm serve`. “Model” in pikepdf docs means **PDF object / structure types**, not ML weights.

**License:** GitHub API lists the repo as **MPL-2.0** ([`pikepdf/pikepdf`](https://github.com/pikepdf/pikepdf)) — **not** GPL-3.0.

## Relation to this app

- **No new `ocr_engines.json` entry** for “Pike PDF” as an OCR engine.
- **Optional future use:** PDF plumbing (merge/split/metadata, saner rasterization hooks) alongside **LiteParse**, **native Tesseract**, **MinerU-Diffusion**, or other PDF-capable paths — only if a concrete feature needs it; add `uv add pikepdf` (or equivalent) at that time.

## Resolution

- **Research closed:** clarified **library vs model** — **library only**; no inference artifact to Ship as OCR.

## Repo impact

- Documentation / backlog only (this file + `plan/ocr-engine-expansion-backlog.md`).
