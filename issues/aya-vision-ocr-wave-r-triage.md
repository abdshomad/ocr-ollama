# Aya Vision OCR — Wave R research triage

**Date:** 2026-05-16  
**Backlog:** [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) — **Next research triage #2 (Aya Vision OCR)**

## Summary

“Aya Vision OCR” maps to **Cohere Labs Aya Vision** — multilingual vision–language checkpoints on Hugging Face under **`CohereLabs/`**. The **8B** variant is the practical default for integration spikes; **32B** exists for heavier GPUs. The model card explicitly lists **OCR** among use cases (with captioning, VQA, etc.).

**License (gate):** Weights are under **[CC-BY-NC 4.0](https://huggingface.co/CohereLabs/aya-vision-8b)** (HF tag `license:cc-by-nc-4.0`) plus [Cohere Labs CC-BY-NC license text](https://cohere.com/cohere-labs-cc-by-nc-license) and [Acceptable Use Policy](https://docs.cohere.com/docs/cohere-labs-acceptable-use-policy). **Non-commercial** terms — treat like a **license gate** before **default** Compose (cf. full MinerU AGPL note in backlog): optional profile + org approval, not assumed shipping terms for all users.

**Access:** Repos are **`gated: auto`** on HF — downloading weights requires a logged-in Hugging Face account and accepting the form (contact info / license acknowledgment). Use **`HF_TOKEN`** (or `huggingface-cli login`) in any serve environment.

## Pinned Hugging Face IDs

| Tier | Model id | Notes |
|------|-----------|--------|
| **Default spike** | [`CohereLabs/aya-vision-8b`](https://huggingface.co/CohereLabs/aya-vision-8b) | ~8.3B params (F16 ~8.6GB tensor payload per HF metadata); **16K** context; SigLIP2 + Command-family VL stack. |
| Heavier | [`CohereLabs/aya-vision-32B`](https://huggingface.co/CohereLabs/aya-vision-32B) | 32B variant linked from 8B model card; same license/gating pattern (verify card before pin in compose). |

**Aliases:** Some links use `CohereForAI/…` — canonical repo paths used above match the HF model cards and **vLLM** docs.

**GPL:** Not applicable — CC-BY-NC, not GPLv3.

## Reproducible serve recipes

### vLLM (preferred for this repo’s gateway)

vLLM **Supported Models** documents **`AyaVisionForConditionalGeneration`** with examples **`CohereLabs/aya-vision-8b`**, **`CohereLabs/aya-vision-32b`** (multimodal **T + I+**). See [vLLM supported models — Aya Vision](https://docs.vllm.ai/en/latest/models/supported_models/) (table row “Aya Vision”).

**Minimal smoke (host with GPU, after HF gating satisfied):**

```bash
export HF_TOKEN=…   # HF token with access to the gated repo
vllm serve CohereLabs/aya-vision-8b --host 0.0.0.0 --port 8100
```

Tune **`--max-model-len`**, **`--gpu-memory-utilization`**, and multimodal limits per GPU (follow vLLM multimodal docs if you hit image-token or OOM issues). Pin the **vLLM image version** in Compose to match the docs you validated.

**OpenAI-compatible** chat with image parts is then usable through this repo’s existing **`vllm_client`** path once the model id is registered in `vllm_endpoints.json` (Ship task — not done in Wave R).

### Transformers (reference / fallback)

The model card documents **`AutoProcessor`** + **`AutoModelForImageTextToText`** and a **`processor.apply_chat_template`** + **`model.generate`** flow. It recommends installing Transformers from a branch that includes Aya Vision support (see card — historically `v4.49.0-AyaVision`; **newer Transformers 5.x** also documents **Aya Vision** in the official model doc). Use this path if building a **non–vLLM sidecar** (not required if vLLM suffices).

### Ollama

**First-party** `ollama.com/library/…` entry for **Cohere Aya Vision** was **not confirmed** during this triage (no stable official library slug documented like other Cohere text models). Community GGUF/quantizations may appear on HF under “Apps → Ollama”; treat as **best-effort**, not the canonical recipe. **vLLM + HF weights** remains the reproducible self-host path for ocr-ollama–style integration.

## Symptoms / user-facing gap

- None (research only). No `aya-vision` engine in the app today.

## Resolution (triage outcome)

| Exit criterion ([backlog § exit criteria](../plan/ocr-engine-expansion-backlog.md)) | Status |
|-------------------------------------------------------------------------------------|--------|
| HF repo / weights | **Met** — `CohereLabs/aya-vision-8b` (+ 32B sibling). |
| License reference (not GPL-3.0) | **Met** — **CC-BY-NC 4.0** + Cohere Labs terms (**commercial use restricted**). |
| Minimal serve command (vLLM / sidecar) | **Met (vLLM)** — `vllm serve CohereLabs/aya-vision-8b` per supported-arch table; **Ollama** not pinned. |
| Sample I/O for `fixtures/ocr/` | **Deferred** until Ship. |

**Conclusion:** Wave R **#2 is triaged**. **Ship** is **technically feasible** on **vLLM** like other VLMs in this repo, but **product/legal** must explicitly accept **CC-BY-NC** + **HF gating** before adding to default stacks.

**Next implementation step (separate task):** Optional compose service + `vllm_endpoints.json` entry + `vllm-entrypoint.sh` branch if special flags are required after GPU smoke; **`plan/aya-vision-vllm.md`** + **`issues/aya-vision-vllm-integration.md`** after first successful run.

## Repo impact

- This triage updates [plan/ocr-engine-expansion-backlog.md](../plan/ocr-engine-expansion-backlog.md) and [issues/README.md](README.md). No runtime code in this Wave R step.
