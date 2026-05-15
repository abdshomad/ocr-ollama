from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import DEFAULT_OCR_MODEL
from app.history import new_timestamp, save_result
from app.inference.classify import ModelTier, classify_model_by_name, is_vision_tier
from app.inference.factory import list_models_with_classification, ocr_chat
from app.inference.structured import structured_extract_from_image, structured_extract_from_text
from app.ocr_service import _ensure_model_available, save_upload
from app.prompts import resolve_prompt
from app.schemas.scan import ProductScanExtraction, ProductScanResponse
from app.settings_store import get_inference_backend


@dataclass
class ProductExtractionRun:
    extraction: ProductScanExtraction
    pipeline: Literal["vision", "ocr_then_text"]
    duration_ms: int
    ocr_model: str | None = None
    raw_text: str | None = None


async def resolve_model_tier(model: str) -> ModelTier:
    models = await list_models_with_classification()
    entry = next((m for m in models if m.get("name") == model), None)
    if entry and entry.get("tier"):
        return ModelTier(entry["tier"])
    return classify_model_by_name(model)


async def resolve_default_ocr_model() -> str:
    if DEFAULT_OCR_MODEL:
        return DEFAULT_OCR_MODEL
    models = await list_models_with_classification()
    for prefer_available in (True, False):
        for m in models:
            if m.get("tier") != ModelTier.DEDICATED_OCR.value:
                continue
            if prefer_available and m.get("available") is False:
                continue
            name = m.get("name")
            if name:
                return str(name)
    raise HTTPException(
        status_code=503,
        detail="No dedicated OCR model configured for text-only product extraction. Set DEFAULT_OCR_MODEL.",
    )


async def extract_product_fields(model: str, image_bytes: bytes) -> ProductExtractionRun:
    await _ensure_model_available(model)
    tier = await resolve_model_tier(model)
    ocr_model: str | None = None
    raw_text: str | None = None
    total_ms = 0

    if is_vision_tier(tier):
        pipeline: Literal["vision", "ocr_then_text"] = "vision"
        extraction, _meta, duration_ms = await structured_extract_from_image(model, image_bytes)
        total_ms = duration_ms
    else:
        pipeline = "ocr_then_text"
        ocr_model = await resolve_default_ocr_model()
        await _ensure_model_available(ocr_model)
        ocr_prompt = resolve_prompt(ocr_model, None)
        raw_text, _ocr_meta, ocr_ms = await ocr_chat(ocr_model, ocr_prompt, image_bytes)
        extraction, _meta, extract_ms = await structured_extract_from_text(model, raw_text)
        total_ms = ocr_ms + extract_ms

    return ProductExtractionRun(
        extraction=extraction,
        pipeline=pipeline,
        duration_ms=total_ms,
        ocr_model=ocr_model,
        raw_text=raw_text,
    )


def product_extraction_to_entry(model: str, run: ProductExtractionRun) -> dict[str, Any]:
    expiry: date | None = run.extraction.expiry_date
    return {
        "model": model,
        "sku": run.extraction.sku,
        "expiry_date": expiry.isoformat() if expiry else None,
        "pipeline": run.pipeline,
        "duration_ms": run.duration_ms,
        "ocr_model": run.ocr_model,
        "raw_text": run.raw_text,
    }


async def arena_product_entry(model: str, image_bytes: bytes) -> dict[str, Any]:
    entry: dict[str, Any] = {"model": model}
    try:
        run = await extract_product_fields(model, image_bytes)
        entry.update(product_extraction_to_entry(model, run))
    except ValidationError as e:
        entry["error"] = str(e.errors())
        entry["duration_ms"] = 0
    except HTTPException as e:
        entry["error"] = str(e.detail)
        entry["duration_ms"] = 0
    except ValueError as e:
        entry["error"] = str(e)
        entry["duration_ms"] = 0
    except httpx.HTTPStatusError as e:
        entry["error"] = str(e)
        entry["duration_ms"] = 0
    except httpx.HTTPError as e:
        entry["error"] = str(e)
        entry["duration_ms"] = 0
    return entry


async def run_product_ocr(
    image_bytes: bytes,
    ext: str,
    model: str,
) -> dict[str, Any]:
    image_path = save_upload(image_bytes, ext)
    run_id = str(uuid.uuid4())

    try:
        extraction_run = await extract_product_fields(model, image_bytes)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except httpx.HTTPError as e:
        backend = get_inference_backend()
        raise HTTPException(status_code=503, detail=f"{backend} unreachable: {e}") from e

    record = ProductScanResponse(
        id=run_id,
        timestamp=new_timestamp(),
        image_path=image_path,
        model=model,
        pipeline=extraction_run.pipeline,
        duration_ms=extraction_run.duration_ms,
        ocr_model=extraction_run.ocr_model,
        raw_text=extraction_run.raw_text,
        inference_backend=get_inference_backend(),
        sku=extraction_run.extraction.sku,
        expiry_date=extraction_run.extraction.expiry_date,
    )
    save_result(record.model_dump(mode="json"))
    return record.model_dump(mode="json")
