#!/usr/bin/env python3
"""HTTP sidecar for Docling (layout + OCR pipeline, CPU)."""

from __future__ import annotations

import os
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

_port = int(os.getenv("DOCLING_PORT", "8270"))
_model_id = os.getenv("DOCLING_MODEL_ID", "docling").strip()

_converter = None  # type: ignore[assignment]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _converter
    from docling.document_converter import DocumentConverter

    _converter = DocumentConverter()
    yield


app = FastAPI(title="Docling", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _converter is not None, "model_id": _model_id}


@app.get("/v1/models")
async def list_models():
    return {"data": [{"id": _model_id, "object": "model"}]}


@app.post("/v1/ocr")
async def ocr(
    image: UploadFile = File(...),
    prompt: str = Form(default=""),
    model: str = Form(default=""),
    merge_level: str = Form(default=""),
):
    _ = (prompt, merge_level)
    if model and model.strip() and model.strip() != _model_id:
        raise HTTPException(status_code=400, detail=f"Unknown model '{model}'")
    if _converter is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image")

    suffix = ".png"
    lower = (image.filename or "").lower()
    if lower.endswith((".jpg", ".jpeg")):
        suffix = ".jpg"
    elif lower.endswith(".webp"):
        suffix = ".webp"

    tmp_path = ""
    start = time.perf_counter()
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        result = _converter.convert(tmp_path)
        doc = result.document
        try:
            text = doc.export_to_markdown(strict_text=True).strip()
        except TypeError:
            text = doc.export_to_markdown().strip()
        duration_ms = int((time.perf_counter() - start) * 1000)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    return {"text": text, "duration_ms": duration_ms, "model": _model_id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=_port, log_level="info")
