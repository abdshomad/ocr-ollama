#!/usr/bin/env python3
"""HTTP sidecar for LanyOCR (ONNX + OpenCV, CPU in Docker by default)."""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

_port = int(os.getenv("LANYOCR_PORT", "8280"))
_model_id = os.getenv("LANYOCR_MODEL_ID", "lanyocr").strip()

_ocr = None  # type: ignore[assignment]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return default


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _ocr
    from lanyocr import LanyOcr

    use_gpu = _env_bool("LANYOCR_USE_GPU", False)
    merge_rotated = _env_bool("LANYOCR_MERGE_ROTATED", True)
    merge_vertical = _env_bool("LANYOCR_MERGE_VERTICAL", True)
    merge_boxes_inference = _env_bool("LANYOCR_MERGE_BOXES_INFERENCE", True)
    recognizer = os.getenv("LANYOCR_RECOGNIZER_NAME", "").strip() or "paddleocr_en_ppocr_v3"
    detector = os.getenv("LANYOCR_DETECTOR_NAME", "").strip() or "paddleocr_en_ppocr_v3"
    _ocr = LanyOcr(
        detector_name=detector,
        recognizer_name=recognizer,
        merge_rotated_boxes=merge_rotated,
        merge_vertical_boxes=merge_vertical,
        merge_boxes_inference=merge_boxes_inference,
        use_gpu=use_gpu,
    )
    yield


app = FastAPI(title="LanyOCR", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _ocr is not None, "model_id": _model_id}


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

        def run_infer():
            results = _ocr.infer_from_file(tmp_path)
            return "\n".join(str(getattr(r, "text", "") or "") for r in results).strip()

        text = await asyncio.to_thread(run_infer)
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
