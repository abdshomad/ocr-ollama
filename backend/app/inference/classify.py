from __future__ import annotations

import re
from enum import Enum
from typing import Any


class ModelTier(str, Enum):
    DEDICATED_OCR = "dedicated_ocr"
    VISION = "vision"
    TEXT_ONLY = "text_only"


_OCR_NAME_RE = re.compile(r"ocr|paddleocr|glm-ocr|lighton|mineru|litparse|chandra|nemotron", re.IGNORECASE)
_GEMMA4_RE = re.compile(r"gemma-4", re.IGNORECASE)
_QWEN_VL_RE = re.compile(r"qwen.*vl", re.IGNORECASE)


def classify_model_by_name(name: str) -> ModelTier:
    if _OCR_NAME_RE.search(name):
        return ModelTier.DEDICATED_OCR
    if _GEMMA4_RE.search(name) or _QWEN_VL_RE.search(name):
        return ModelTier.VISION
    return ModelTier.TEXT_ONLY


def classify_ollama_model(name: str, show: dict[str, Any]) -> ModelTier:
    caps = show.get("capabilities") or []
    details = show.get("details") or {}
    families = details.get("families") or []
    family = details.get("family") or ""
    name_lower = name.lower()
    family_str = " ".join(str(f) for f in families).lower() + " " + str(family).lower()

    if "ocr" in name_lower or "paddleocr" in name_lower or "ocr" in family_str or "paddleocr" in family_str:
        return ModelTier.DEDICATED_OCR
    if "vision" in caps:
        return ModelTier.VISION
    return ModelTier.TEXT_ONLY


def is_ocr_capable(tier: ModelTier) -> bool:
    return tier in (ModelTier.DEDICATED_OCR, ModelTier.VISION)


def is_vision_tier(tier: ModelTier) -> bool:
    return tier in (ModelTier.DEDICATED_OCR, ModelTier.VISION)
