from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import HTTPException, UploadFile

from app.history import new_timestamp, save_result
from app.ocr_service import read_and_validate_image, save_upload

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


async def run_browser_scan(
    image: UploadFile,
    sku: str,
    expiry_date: str | None,
    confidence: float,
    raw_text: str | None,
    engine: str,
    duration_ms: int,
) -> dict[str, Any]:
    if not sku.strip():
        raise HTTPException(status_code=400, detail="sku is required")
    if confidence < 0 or confidence > 1:
        raise HTTPException(status_code=400, detail="confidence must be between 0 and 1")
    if duration_ms < 0:
        raise HTTPException(status_code=400, detail="duration_ms must be non-negative")

    expiry: str | None = None
    if expiry_date is not None and expiry_date.strip():
        expiry = expiry_date.strip()
        if not _ISO_DATE.match(expiry):
            raise HTTPException(status_code=400, detail="expiry_date must be YYYY-MM-DD")

    image_bytes, ext = await read_and_validate_image(image)
    image_path = save_upload(image_bytes, ext)
    run_id = str(uuid.uuid4())

    record: dict[str, Any] = {
        "id": run_id,
        "kind": "browser_scan",
        "timestamp": new_timestamp(),
        "image_path": image_path,
        "sku": sku.strip(),
        "expiry_date": expiry,
        "confidence": round(confidence, 4),
        "raw_text": (raw_text or "").strip(),
        "engine": engine.strip() or "unknown",
        "duration_ms": duration_ms,
    }
    save_result(record)
    return record
