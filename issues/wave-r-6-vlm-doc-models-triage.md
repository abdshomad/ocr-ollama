# Gemma 3 OCR / Falcon OCR / Youtu-VL / ExaOCR / Col Pali / Pixl — Wave R research triage

**Date:** 2026-05-16  
**Backlog:** [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) — **Next research triage #6**

## Summary

Six partially overlapping names: some are **shippable VLMs / OCR specialists** with Hugging Face weights; one is a **CPU pipeline repo**; one is **retrieval-first** (not Run/Arena OCR without a RAG/index layer); one is a **commercial API brand**. **Hunyuan OCR** in the same inventory row is **already in repo** — unchanged here.

## Per-name disposition

| Name | Pinned artifact(s) | OCR / doc angle | vLLM / gateway notes | License / gate |
|------|-------------------|-----------------|----------------------|----------------|
| **Gemma 3 OCR** | Multimodal instruct checkpoints, e.g. **`google/gemma-3-4b-it`**, **`google/gemma-3-12b-it`**, **`google/gemma-3-27b-it`** (see [Gemma 3 model card](https://ai.google.dev/gemma/docs/core/model_card_3), [HF blog](https://huggingface.co/blog/gemma3)) | Vision-capable **VLM** (SigLip + pan-and-scan); can be prompted for transcription like other VLMs | **vLLM** documents **`Gemma3ForConditionalGeneration`** with examples such as `google/gemma-3-4b-it` (multimodal). **Distinct** from **Gemma 4** already optional in this repo (`google/gemma-4-E4B-it`, profile `gemma4`) — Gemma **3** would be a **separate** endpoint row if shipped | **Gemma Terms of Use** (Google) — same family compliance as other Gemma weights |
| **Falcon OCR** | **`tiiuae/Falcon-OCR`** (~300M **early-fusion** image-to-text OCR VLM; [HF](https://huggingface.co/tiiuae/Falcon-OCR), [Falcon Perception blog](https://huggingface.co/blog/tiiuae/falcon-perception)) | Purpose-built **document OCR** (text / LaTeX / HTML modes); optional two-stage layout with **PP-DocLayoutV3** per card | **Not** listed under **`Falcon-OCR`** in the vLLM **0.21** supported-models table reviewed during triage — treat **`vllm serve tiiuae/Falcon-OCR`** as a **GPU spike** (card cites **FlexAttention** / **PyTorch 2.5+** and throughput claims with vLLM in marketing material). **Transformers** path is primary on HF | **Verify** `LICENSE` / HF metadata before Ship (TII repos often Apache-2.0; confirm on card) |
| **Youtu-VL** | **`tencent/Youtu-VL-4B-Instruct`** (+ **GGUF** variant), [GitHub TencentCloudADP/youtu-vl](https://github.com/TencentCloudADP/youtu-vl) | General **VLM**; paper/card list **OCR** among tasks | **Not** confirmed in vLLM supported-models snippet for this triage — **spike** alongside other Tencent stacks (**compare `tencent/HunyuanOCR`** already integrated) | **Tencent** model license — same **org policy** class as Hunyuan; read HF card |
| **ExaOCR** | GitHub [**ikantkode/exaOCR**](https://github.com/ikantkode/exaOCR) | **Pipeline** (e.g. PyMuPDF / OCRmyPDF / Tesseract-style paths), FastAPI + Streamlit — **not** a single multimodal **weight id** for `vllm serve` | Fits **sidecar** or **tooling** integration, not a drop-in next to DeepSeek-OCR **without** new Docker + HTTP contract | Check repo **LICENSE** (not triaged to clause level here) |
| **Col Pali** | **`vidore/colpali`**, **`vidore/colpali-v1.3`**, **`vidore/colpali-v1.3-hf`** ([paper](https://arxiv.org/abs/2407.01449)) | **Visual document retrieval** — **ColBERT-style multi-vector** page embeddings; **not** full-page markdown OCR generation | **Out of scope** for standard **Run → plain text** OCR unless the product adds a **retrieval / index** path (different UX and contract) | HF model license — **verify** per checkpoint; **task mismatch** is the main blocker |
| **Pixl** | **[pixl.ai](https://products.pixl.ai/)** | Commercial **invoice / ID / receipt** extraction **APIs** (and on-prem positioning per vendor site) | **Wave 6** **cloud_http** / vendor SDK — not a public HF engine row for default compose | **Commercial** terms |

## Exit criteria (backlog)

| Criterion | Status |
|-----------|--------|
| HF + license for a **single** promoted Ship candidate | **Partial** — **Falcon-OCR** and **Gemma 3** are the strongest **self-host** follow-ups; **ColPali** fails task fit; **Pixl** is vendor; **ExaOCR** is a pipeline |
| Minimal **`vllm serve`** | **Unverified** for **Falcon-OCR** and **Youtu-VL** in this pass; **Gemma 3** has documented **Gemma3** multimodal support in vLLM docs |

**Conclusion:** Wave R **#6 triaged**. To **Ship** next: (1) optional **Gemma 3** profile mirroring **Gemma 4** if desired; (2) **Falcon-OCR** GPU spike (Transformers and/or vLLM); (3) **Youtu-VL** only with Tencent license review + serve proof; (4) treat **ColPali** as retrieval backlog; **Pixl** as API; **ExaOCR** as separate pipeline/sidecar design.

## Repo impact

- Documentation only: backlog + [issues/README.md](README.md).
