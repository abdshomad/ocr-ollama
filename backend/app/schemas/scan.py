from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")


class ProductScanExtraction(BaseModel):
    sku: str = Field(min_length=1, max_length=500)
    expiry_date: date | None = None

    @field_validator("sku")
    @classmethod
    def strip_sku(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("sku must not be empty")
        return s


def extract_json_str(raw: str) -> str:
    text = raw.strip()
    if text.startswith("{"):
        return text
    match = _JSON_OBJECT_RE.search(text)
    if not match:
        raise ValueError("No JSON object in model response")
    return match.group(0)


def parse_extraction(raw: str) -> ProductScanExtraction:
    return ProductScanExtraction.model_validate_json(extract_json_str(raw))


class BrowserScanSubmit(BaseModel):
    sku: str = Field(min_length=1, max_length=500)
    expiry_date: date | None = None
    confidence: float = Field(ge=0, le=1)
    engine: str = Field(min_length=1, max_length=64)
    duration_ms: int = Field(ge=0)
    raw_text: str = ""

    @field_validator("sku", "engine")
    @classmethod
    def strip_required_str(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be empty")
        return s

    @field_validator("expiry_date", mode="before")
    @classmethod
    def parse_expiry(cls, v: object) -> date | None:
        if v is None:
            return None
        if isinstance(v, date):
            return v
        s = str(v).strip()
        if not s:
            return None
        return date.fromisoformat(s)

    @field_validator("raw_text", mode="before")
    @classmethod
    def normalize_raw_text(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v).strip()


class BrowserScanRecord(BrowserScanSubmit):
    id: str
    kind: Literal["browser_scan"] = "browser_scan"
    timestamp: str
    image_path: str


class ProductScanResponse(ProductScanExtraction):
    id: str
    kind: Literal["product_scan"] = "product_scan"
    timestamp: str
    image_path: str
    model: str
    pipeline: Literal["vision", "ocr_then_text"]
    duration_ms: int
    ocr_model: str | None = None
    raw_text: str | None = None
    inference_backend: str
