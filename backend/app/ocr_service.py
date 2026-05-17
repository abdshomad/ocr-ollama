from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, UploadFile

from app.config import ALLOWED_CONTENT_TYPES, ALLOWED_OCR_UPLOAD_TYPES, MAX_IMAGE_BYTES, UPLOAD_DIR
from app.engine_registry import is_litparse_model
from app.history import new_timestamp, save_result
from app.inference.factory import list_models_with_classification, ocr_chat
from app.prompts import resolve_prompt
from app.settings_store import get_inference_backend


async def _ensure_model_available(model: str) -> None:
    models = await list_models_with_classification()
    entry = next((m for m in models if m.get("name") == model), None)
    if entry is not None and entry.get("available") is False:
        label = (
            entry.get("vllm_endpoint_label")
            or entry.get("engine_label")
            or entry.get("vllm_endpoint")
            or "inference"
        )
        raise HTTPException(
            status_code=503,
            detail=f"Model '{model}' is offline ({label} server not ready). Check docker compose logs.",
        )

EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "application/pdf": ".pdf",
}


def _validate_ocr_content_type(model: str, content_type: str) -> None:
    if content_type == "application/pdf":
        if not is_litparse_model(model):
            raise HTTPException(
                status_code=400,
                detail="PDF uploads require model litparse.",
            )
        return
    if is_litparse_model(model) and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="LiteParse requires a PDF or a supported image type (JPEG, PNG, WebP, GIF).",
        )


async def read_and_validate_ocr_upload(file: UploadFile) -> tuple[bytes, str, str]:
    content_type = file.content_type or ""
    if content_type not in ALLOWED_OCR_UPLOAD_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: "
            f"{', '.join(sorted(ALLOWED_OCR_UPLOAD_TYPES))}",
        )
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_IMAGE_BYTES} bytes")
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    ext = EXT_BY_TYPE.get(content_type, ".bin")
    return data, ext, content_type


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
    content_type: str,
    reuse_image_path: str | None = None,
) -> dict[str, Any]:
    _validate_ocr_content_type(model, content_type)
    image_path = reuse_image_path or save_upload(image_bytes, ext)
    prompt = resolve_prompt(model, prompt_override)
    run_id = str(uuid.uuid4())

    await _ensure_model_available(model)
    try:
        text, meta, duration_ms = await ocr_chat(model, prompt, image_bytes)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except httpx.HTTPError as e:
        backend = get_inference_backend()
        raise HTTPException(status_code=503, detail=f"{backend} unreachable: {e}") from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    record = {
        "id": run_id,
        "kind": "single",
        "timestamp": new_timestamp(),
        "model": model,
        "prompt": prompt,
        "image_path": image_path,
        "text": text,
        "duration_ms": duration_ms,
        "inference_backend": get_inference_backend(),
        "inference_meta": meta,
        "ollama_meta": meta,
    }
    save_result(record)
    return record


def _validate_arena_inputs(
    models: list[str],
    *,
    content_type: str,
    extraction_mode: str,
) -> None:
    if len(models) < 2:
        raise HTTPException(status_code=400, detail="Arena requires at least 2 models")
    if extraction_mode not in ("text", "product"):
        raise HTTPException(status_code=400, detail="extraction_mode must be 'text' or 'product'")
    for m in models:
        _validate_ocr_content_type(m, content_type)


async def _arena_run_one_model(
    model: str,
    image_bytes: bytes,
    *,
    extraction_mode: str,
    overrides: dict[str, str],
) -> dict[str, Any]:
    if extraction_mode == "product":
        from app.product_scan import arena_product_entry

        return await arena_product_entry(model, image_bytes)

    override = overrides.get(model)
    prompt = resolve_prompt(model, override)
    entry: dict[str, Any] = {"model": model, "prompt": prompt}
    try:
        await _ensure_model_available(model)
        text, meta, duration_ms = await ocr_chat(model, prompt, image_bytes)
        entry["text"] = text
        entry["duration_ms"] = duration_ms
        entry["inference_meta"] = meta
        entry["ollama_meta"] = meta
    except HTTPException as e:
        entry["error"] = str(e.detail)
        entry["text"] = ""
        entry["duration_ms"] = 0
    except httpx.HTTPError as e:
        entry["error"] = str(e)
        entry["text"] = ""
        entry["duration_ms"] = 0
    except RuntimeError as e:
        entry["error"] = str(e)
        entry["text"] = ""
        entry["duration_ms"] = 0
    return entry


async def run_arena(
    image_bytes: bytes,
    ext: str,
    models: list[str],
    prompt_overrides: dict[str, str] | None = None,
    *,
    content_type: str,
    extraction_mode: str = "text",
) -> dict[str, Any]:
    _validate_arena_inputs(models, content_type=content_type, extraction_mode=extraction_mode)

    image_path = save_upload(image_bytes, ext)
    arena_id = str(uuid.uuid4())
    overrides = prompt_overrides or {}
    results: list[dict[str, Any]] = []
    for m in models:
        results.append(
            await _arena_run_one_model(m, image_bytes, extraction_mode=extraction_mode, overrides=overrides)
        )

    record = {
        "id": arena_id,
        "kind": "arena",
        "extraction_mode": extraction_mode,
        "timestamp": new_timestamp(),
        "image_path": image_path,
        "results": results,
    }
    save_result(record)
    return record


async def iter_arena_sse_events(
    disconnect_check: Callable[[], Awaitable[bool]] | None,
    image_bytes: bytes,
    ext: str,
    models: list[str],
    prompt_overrides: dict[str, str] | None,
    *,
    content_type: str,
    extraction_mode: str,
) -> AsyncIterator[dict[str, Any]]:
    """Yield arena progress dicts for SSE. Persists to history only after all models finish."""
    _validate_arena_inputs(models, content_type=content_type, extraction_mode=extraction_mode)

    async def disconnected() -> bool:
        if disconnect_check is None:
            return False
        return await disconnect_check()

    image_path = save_upload(image_bytes, ext)
    arena_id = str(uuid.uuid4())
    overrides = prompt_overrides or {}
    results: list[dict[str, Any]] = []

    for model in models:
        if await disconnected():
            yield {
                "type": "arena_cancelled",
                "next_index": len(results),
                "partial_results": results,
            }
            return
        yield {"type": "arena_model", "model": model, "phase": "running"}
        entry = await _arena_run_one_model(
            model, image_bytes, extraction_mode=extraction_mode, overrides=overrides
        )
        results.append(entry)
        yield {"type": "arena_model", "model": model, "phase": "finished", "entry": entry}

    record = {
        "id": arena_id,
        "kind": "arena",
        "extraction_mode": extraction_mode,
        "timestamp": new_timestamp(),
        "image_path": image_path,
        "results": results,
    }
    save_result(record)
    yield {"type": "arena_complete", "record": record}


def safe_upload_filename(filename: str) -> Path:
    name = Path(filename).name
    if not name or name != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = UPLOAD_DIR / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return path
