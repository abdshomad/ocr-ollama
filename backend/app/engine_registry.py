from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.inference.classify import classify_model_by_name, is_ocr_capable
from app.vllm_registry import load_endpoints as load_vllm_endpoints

_OCR_ENGINES_PATH = Path(__file__).resolve().parents[1] / "config" / "ocr_engines.json"


@lru_cache(maxsize=1)
def load_ocr_engines() -> list[dict[str, Any]]:
    if not _OCR_ENGINES_PATH.is_file():
        return []
    data = json.loads(_OCR_ENGINES_PATH.read_text(encoding="utf-8"))
    return list(data.get("engines") or [])


def load_all_endpoints() -> list[dict[str, Any]]:
    """vLLM endpoints plus custom OCR engine services (GPU page, health)."""
    return [*load_vllm_endpoints(), *load_ocr_engines()]


def host_for_engine(ep: dict[str, Any]) -> str:
    env_key = ep.get("host_env") or ""
    env_val = os.getenv(env_key, "").strip().rstrip("/") if env_key else ""
    if env_val:
        return env_val
    return str(ep.get("default_host", "")).rstrip("/")


def ocr_engine_for_model(model: str) -> dict[str, Any] | None:
    model_stripped = model.strip()
    for ep in load_ocr_engines():
        if model_stripped in (ep.get("models") or []):
            return ep
    return None


def is_mineru_model(model: str) -> bool:
    ep = ocr_engine_for_model(model)
    return ep is not None and str(ep.get("type")) == "nano_dvlm"


def is_litparse_model(model: str) -> bool:
    ep = ocr_engine_for_model(model)
    return ep is not None and str(ep.get("type")) == "litparse"


def is_nemotron_model(model: str) -> bool:
    ep = ocr_engine_for_model(model)
    return ep is not None and str(ep.get("type")) == "nemotron"


def is_rapidocr_model(model: str) -> bool:
    ep = ocr_engine_for_model(model)
    return ep is not None and str(ep.get("type")) == "rapidocr"


def is_onnxtr_model(model: str) -> bool:
    ep = ocr_engine_for_model(model)
    return ep is not None and str(ep.get("type")) == "onnxtr"


def is_tesseract_model(model: str) -> bool:
    ep = ocr_engine_for_model(model)
    return ep is not None and str(ep.get("type")) == "tesseract"


def all_mineru_models() -> list[tuple[dict[str, Any], str]]:
    out: list[tuple[dict[str, Any], str]] = []
    for ep in load_ocr_engines():
        if str(ep.get("type")) != "nano_dvlm":
            continue
        for name in ep.get("models") or []:
            out.append((ep, str(name)))
    return out


def all_litparse_models() -> list[tuple[dict[str, Any], str]]:
    out: list[tuple[dict[str, Any], str]] = []
    for ep in load_ocr_engines():
        if str(ep.get("type")) != "litparse":
            continue
        for name in ep.get("models") or []:
            out.append((ep, str(name)))
    return out


def all_nemotron_models() -> list[tuple[dict[str, Any], str]]:
    out: list[tuple[dict[str, Any], str]] = []
    for ep in load_ocr_engines():
        if str(ep.get("type")) != "nemotron":
            continue
        for name in ep.get("models") or []:
            out.append((ep, str(name)))
    return out


def all_rapidocr_models() -> list[tuple[dict[str, Any], str]]:
    out: list[tuple[dict[str, Any], str]] = []
    for ep in load_ocr_engines():
        if str(ep.get("type")) != "rapidocr":
            continue
        for name in ep.get("models") or []:
            out.append((ep, str(name)))
    return out


def all_onnxtr_models() -> list[tuple[dict[str, Any], str]]:
    out: list[tuple[dict[str, Any], str]] = []
    for ep in load_ocr_engines():
        if str(ep.get("type")) != "onnxtr":
            continue
        for name in ep.get("models") or []:
            out.append((ep, str(name)))
    return out


def all_tesseract_models() -> list[tuple[dict[str, Any], str]]:
    out: list[tuple[dict[str, Any], str]] = []
    for ep in load_ocr_engines():
        if str(ep.get("type")) != "tesseract":
            continue
        for name in ep.get("models") or []:
            out.append((ep, str(name)))
    return out


def model_entry(
    name: str,
    *,
    available: bool,
    endpoint_id: str,
    endpoint_label: str,
    engine_type: str,
    speed_tier: str | None = None,
    input_modes: list[str] | None = None,
) -> dict[str, Any]:
    tier = classify_model_by_name(name)
    entry: dict[str, Any] = {
        "name": name,
        "size": None,
        "modified_at": None,
        "tier": tier.value,
        "ocr_capable": is_ocr_capable(tier),
        "has_parent_blob": False,
        "capabilities": [],
        "families": [],
        "available": available,
        "engine_type": engine_type,
        "engine_label": endpoint_label,
        "vllm_endpoint": endpoint_id,
        "vllm_endpoint_label": endpoint_label,
    }
    if speed_tier:
        entry["speed_tier"] = speed_tier
    if input_modes:
        entry["input_modes"] = input_modes
    return entry
