from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

_CATALOG_PATH = Path(__file__).resolve().parents[1] / "config" / "model_vram_estimates.json"

# Compose default env keys → catalog model id (when endpoint lists multiple weights).
_ENDPOINT_DEFAULT_ENV: dict[str, tuple[str, str]] = {
    "qwen3vl": ("VLLM_QWEN3_VL_MODEL", "Qwen/Qwen3-VL-8B-Instruct"),
    "qwen3omni": ("VLLM_QWEN3_OMNI_MODEL", "Qwen/Qwen3-Omni-30B-A3B-Instruct"),
    "deepseek-ocr2": ("VLLM_DEEPSEEK_OCR2_MODEL", "deepseek-ai/DeepSeek-OCR-2"),
    "paddleocr-vl": ("VLLM_PADDLEOCR_VL_MODEL", "PaddlePaddle/PaddleOCR-VL"),
    "paddleocr-vl-15": ("VLLM_PADDLEOCR_VL_15_MODEL", "PaddlePaddle/PaddleOCR-VL-1.5"),
    "dotsmocr": ("VLLM_DOTS_MOCR_MODEL", "rednote-hilab/dots.mocr"),
    "phi4multimodal": ("VLLM_PHI4_MM_MODEL", "microsoft/Phi-4-multimodal-instruct"),
    "rolmocr": ("VLLM_ROLMOCR_MODEL", "reducto/RolmOCR"),
    "numarkdown": ("VLLM_NUMARKDOWN_MODEL", "numind/NuMarkdown-8B-Thinking"),
    "hunyuanocr": ("VLLM_HUNYUAN_OCR_MODEL", "tencent/HunyuanOCR"),
    "smoldocling": ("VLLM_SMOLDOCLING_MODEL", "docling-project/SmolDocling-256M-preview"),
}


@lru_cache(maxsize=1)
def _catalog() -> dict[str, Any]:
    if not _CATALOG_PATH.is_file():
        return {"models": {}, "endpoint_defaults": {}}
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def lookup_model_vram(model_id: str) -> dict[str, Any] | None:
    entry = (_catalog().get("models") or {}).get(model_id.strip())
    if not entry:
        return None
    out: dict[str, Any] = {"id": model_id}
    if entry.get("params_b") is not None:
        out["params_b"] = float(entry["params_b"])
    if entry.get("vram_gib") is not None:
        out["vram_gib"] = float(entry["vram_gib"])
    if entry.get("ram_gib") is not None:
        out["ram_gib"] = float(entry["ram_gib"])
    if entry.get("note"):
        out["note"] = str(entry["note"])
    return out


def default_model_for_endpoint(endpoint_id: str) -> str | None:
    ep_id = endpoint_id.strip()
    pair = _ENDPOINT_DEFAULT_ENV.get(ep_id)
    if pair:
        env_key, fallback = pair
        return os.getenv(env_key, fallback).strip() or fallback
    defaults = _catalog().get("endpoint_defaults") or {}
    val = defaults.get(ep_id)
    return str(val) if val else None


def models_for_size_estimate(
    *,
    endpoint_id: str,
    configured_models: list[str],
    live_models: list[str],
) -> list[str]:
    """Prefer live IDs; else single default for multi-model endpoints; else all configured."""
    if live_models:
        return live_models
    if len(configured_models) == 1:
        return configured_models
    default_id = default_model_for_endpoint(endpoint_id)
    if default_id and default_id in configured_models:
        return [default_id]
    return configured_models


def model_details_for_service(
    *,
    endpoint_id: str,
    configured_models: list[str],
    live_models: list[str],
) -> list[dict[str, Any]]:
    ids = models_for_size_estimate(
        endpoint_id=endpoint_id,
        configured_models=configured_models,
        live_models=live_models,
    )
    details: list[dict[str, Any]] = []
    for mid in ids:
        info = lookup_model_vram(mid)
        if info:
            details.append(info)
        else:
            details.append({"id": mid})
    return details


def service_vram_summary(details: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate estimates for the service row (max when several variants listed)."""
    vram = [float(d["vram_gib"]) for d in details if d.get("vram_gib") is not None]
    ram = [float(d["ram_gib"]) for d in details if d.get("ram_gib") is not None]
    out: dict[str, Any] = {}
    if vram:
        out["vram_estimate_gib"] = max(vram)
        if len(vram) > 1:
            out["vram_estimate_gib_min"] = min(vram)
    if ram:
        out["ram_estimate_gib"] = max(ram)
    return out
