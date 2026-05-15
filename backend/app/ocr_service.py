from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, UploadFile

from app.config import ALLOWED_CONTENT_TYPES, MAX_IMAGE_BYTES, UPLOAD_DIR
from app.history import new_timestamp, save_result
from app.inference.factory import ocr_chat
from app.prompts import resolve_prompt
from app.settings_store import get_inference_backend

EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


async def read_and_validate_image(file: UploadFile) -> tuple[bytes, str]:
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {content_type}. Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail=f"Image exceeds {MAX_IMAGE_BYTES} bytes")
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty image file")
    ext = EXT_BY_TYPE.get(content_type, ".bin")
    return data, ext


def save_upload(image_bytes: bytes, ext: str) -> str:
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext}"
    path = UPLOAD_DIR / filename
    path.write_bytes(image_bytes)
    return f"upload/{filename}"


async def run_ocr(
    image_bytes: bytes,
    ext: str,
    model: str,
    prompt_override: str | None = None,
    *,
    reuse_image_path: str | None = None,
) -> dict[str, Any]:
    image_path = reuse_image_path or save_upload(image_bytes, ext)
    prompt = resolve_prompt(model, prompt_override)
    run_id = str(uuid.uuid4())

    try:
        text, meta, duration_ms = await ocr_chat(model, prompt, image_bytes)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}") from e

    record = {
        "id": run_id,
        "kind": "single",
        "timestamp": new_timestamp(),
        "model": model,
        "prompt": prompt,
        "image_path": image_path,
        "text": text,
        "duration_ms": duration_ms,
        "ollama_meta": meta,
    }
    save_result(record)
    return record


async def run_arena(
    image_bytes: bytes,
    ext: str,
    models: list[str],
    prompt_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    if len(models) < 2:
        raise HTTPException(status_code=400, detail="Arena requires at least 2 models")

    image_path = save_upload(image_bytes, ext)
    arena_id = str(uuid.uuid4())
    overrides = prompt_overrides or {}
    results: list[dict[str, Any]] = []

    for model in models:
        override = overrides.get(model)
        prompt = resolve_prompt(model, override)
        entry: dict[str, Any] = {"model": model, "prompt": prompt}
        try:
            text, meta, duration_ms = await ocr_chat(model, prompt, image_bytes)
            entry["text"] = text
            entry["duration_ms"] = duration_ms
            entry["inference_meta"] = meta
            entry["ollama_meta"] = meta
        except httpx.HTTPError as e:
            entry["error"] = str(e)
            entry["text"] = ""
            entry["duration_ms"] = 0
        results.append(entry)

    record = {
        "id": arena_id,
        "kind": "arena",
        "timestamp": new_timestamp(),
        "image_path": image_path,
        "results": results,
    }
    save_result(record)
    return record


def safe_upload_filename(filename: str) -> Path:
    name = Path(filename).name
    if not name or name != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = UPLOAD_DIR / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return path
