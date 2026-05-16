"""Static OCR model catalog from config — no network I/O."""

from __future__ import annotations

from typing import Any

from app.engine_registry import (
    all_docling_models,
    all_doctr_models,
    all_easyocr_models,
    all_lanyocr_models,
    all_litparse_models,
    all_mineru_models,
    all_nemotron_models,
    all_onnxtr_models,
    all_paddleocr_models,
    all_rapidocr_models,
    all_tesseract_models,
    model_entry,
)
from app.settings_store import get_inference_backend
from app.vllm_registry import all_configured_models, model_entry as vllm_model_entry


def _catalog_from_pairs(
    pairs: list[tuple[dict[str, Any], str]],
    *,
    engine_type: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ep, model_id in pairs:
        speed = ep.get("speed_tier")
        modes = ep.get("input_modes")
        im = [str(x) for x in modes] if isinstance(modes, list) else None
        out.append(
            model_entry(
                model_id,
                available=None,
                endpoint_id=str(ep.get("id", "")),
                endpoint_label=str(ep.get("label") or ep.get("id") or ""),
                engine_type=engine_type,
                speed_tier=str(speed) if speed else None,
                input_modes=im,
            )
        )
    return out


def _vllm_catalog() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ep, model_id in all_configured_models():
        speed = ep.get("speed_tier")
        out.append(
            vllm_model_entry(
                model_id,
                available=None,
                endpoint_id=str(ep.get("id", "")),
                endpoint_label=str(ep.get("label") or ep.get("id") or ""),
                speed_tier=str(speed) if speed else None,
            )
        )
    return out


def _sidecar_catalog_vllm() -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    parts.extend(_catalog_from_pairs(all_mineru_models(), engine_type="nano_dvlm"))
    parts.extend(_catalog_from_pairs(all_nemotron_models(), engine_type="nemotron"))
    parts.extend(_catalog_from_pairs(all_rapidocr_models(), engine_type="rapidocr"))
    parts.extend(_catalog_from_pairs(all_onnxtr_models(), engine_type="onnxtr"))
    parts.extend(_catalog_from_pairs(all_easyocr_models(), engine_type="easyocr"))
    parts.extend(_catalog_from_pairs(all_doctr_models(), engine_type="doctr"))
    parts.extend(_catalog_from_pairs(all_paddleocr_models(), engine_type="paddleocr"))
    parts.extend(_catalog_from_pairs(all_docling_models(), engine_type="docling"))
    parts.extend(_catalog_from_pairs(all_lanyocr_models(), engine_type="lanyocr"))
    parts.extend(_catalog_from_pairs(all_litparse_models(), engine_type="litparse"))
    parts.extend(_catalog_from_pairs(all_tesseract_models(), engine_type="tesseract"))
    return parts


def _sidecar_catalog_ollama() -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    parts.extend(_catalog_from_pairs(all_rapidocr_models(), engine_type="rapidocr"))
    parts.extend(_catalog_from_pairs(all_onnxtr_models(), engine_type="onnxtr"))
    parts.extend(_catalog_from_pairs(all_easyocr_models(), engine_type="easyocr"))
    parts.extend(_catalog_from_pairs(all_doctr_models(), engine_type="doctr"))
    parts.extend(_catalog_from_pairs(all_paddleocr_models(), engine_type="paddleocr"))
    parts.extend(_catalog_from_pairs(all_docling_models(), engine_type="docling"))
    parts.extend(_catalog_from_pairs(all_lanyocr_models(), engine_type="lanyocr"))
    parts.extend(_catalog_from_pairs(all_litparse_models(), engine_type="litparse"))
    parts.extend(_catalog_from_pairs(all_tesseract_models(), engine_type="tesseract"))
    return parts


def list_models_catalog(*, backend: str | None = None) -> list[dict[str, Any]]:
    """All configured OCR models; ``available`` is None until probed."""
    b = (backend or get_inference_backend()).strip().lower()
    if b == "ollama":
        return _sidecar_catalog_ollama()
    return [*_vllm_catalog(), *_sidecar_catalog_vllm()]
