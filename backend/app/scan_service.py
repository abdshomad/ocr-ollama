from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, UploadFile
from pydantic import ValidationError

from app.history import new_timestamp, save_result
from app.ocr_service import read_and_validate_image, save_upload
from app.schemas.scan import BrowserScanRecord, BrowserScanSubmit


async def run_browser_scan(
    image: UploadFile,
    sku: str,
    expiry_date: str | None,
    confidence: float,
    raw_text: str | None,
    engine: str,
    duration_ms: int,
) -> dict[str, Any]:
    try:
        fields = BrowserScanSubmit(
            sku=sku,
            expiry_date=expiry_date,
            confidence=confidence,
            raw_text=raw_text,
            engine=engine,
            duration_ms=duration_ms,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors()) from e

    image_bytes, ext = await read_and_validate_image(image)
    image_path = save_upload(image_bytes, ext)
    run_id = str(uuid.uuid4())

    record = BrowserScanRecord(
        id=run_id,
        timestamp=new_timestamp(),
        image_path=image_path,
        sku=fields.sku,
        expiry_date=fields.expiry_date,
        confidence=round(fields.confidence, 4),
        raw_text=fields.raw_text,
        engine=fields.engine,
        duration_ms=fields.duration_ms,
    )
    payload = record.model_dump(mode="json")
    save_result(payload)
    return payload
