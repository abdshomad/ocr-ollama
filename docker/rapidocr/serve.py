#!/usr/bin/env python3
"""HTTP sidecar for RapidOCR (rapidocr-onnxruntime, CPU)."""

from __future__ import annotations

import os
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

_port = int(os.getenv("RAPIDOCR_PORT", "8220"))
_model_id = os.getenv("RAPIDOCR_MODEL_ID", "rapidocr").strip()

_ocr = None  # type: ignore[assignment]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _ocr
    from rapidocr_onnxruntime import RapidOCR

    _ocr = RapidOCR()
    yield


app = FastAPI(title="RapidOCR", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _ocr is not None, "model_id": _model_id}


@app.get("/v1/models")
async def list_models():
    return {"data": [{"id": _model_id, "object": "model"}]}


def _lines_from_result(result: object) -> list[str]:
    lines: list[str] = []
    if not result:
        return lines
    if not isinstance(result, (list, tuple)):
        return lines
    for row in result:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        txt_box = row[1]
        if isinstance(txt_box, (list, tuple)) and txt_box:
            t = txt_box[0]
        elif isinstance(txt_box, str):
            t = txt_box
        else:
            continue
        if isinstance(t, str) and t.strip():
            lines.append(t.strip())
    return lines


@app.post("/v1/ocr")
async def ocr(
    image: UploadFile = File(...),
    prompt: str = Form(default=""),
    model: str = Form(default=""),
    merge_level: str = Form(default=""),
):
    _ = (prompt, merge_level)  # API parity with other sidecars; unused for classical OCR
    if model and model.strip() and model.strip() != _model_id:
        raise HTTPException(status_code=400, detail=f"Unknown model '{model}'")
    if _ocr is None:
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
        result, _elapse = _ocr(tmp_path)  # type: ignore[operator]
        lines = _lines_from_result(result)
        text = "\n".join(lines)
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
