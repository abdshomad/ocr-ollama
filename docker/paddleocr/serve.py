#!/usr/bin/env python3
"""HTTP sidecar for PaddleOCR (PaddlePaddle CPU by default in Docker image)."""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

_port = int(os.getenv("PADDLEOCR_PORT", "8260"))
_model_id = os.getenv("PADDLEOCR_MODEL_ID", "paddleocr").strip()

_ocr = None  # type: ignore[assignment]


def _text_from_paddle_result(result: object) -> str:
    """Normalize PaddleOCR `ocr.ocr()` output to plain text."""
    if not result:
        return ""
    lines: list[str] = []
    # Single image: list of detected lines or None
    pages = result if isinstance(result, list) else []
    for page in pages:
        if page is None:
            continue
        if not isinstance(page, list):
            continue
        for item in page:
            if not item or len(item) < 2:
                continue
            tup = item[1]
            if isinstance(tup, (list, tuple)) and len(tup) >= 1:
                lines.append(str(tup[0]))
            elif isinstance(tup, str):
                lines.append(tup)
    return "\n".join(lines).strip()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _ocr
    os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")

    from paddleocr import PaddleOCR

    lang = os.getenv("PADDLEOCR_LANG", "en").strip() or "en"
    use_gpu = os.getenv("PADDLEOCR_USE_GPU", "").strip() == "1"
    kwargs: dict[str, object] = {
        "use_angle_cls": True,
        "lang": lang,
        "show_log": False,
    }
    # PaddleOCR 2.x accepts use_gpu; newer builds may ignore or alias it.
    try:
        _ocr = PaddleOCR(use_gpu=use_gpu, **kwargs)  # type: ignore[arg-type]
    except TypeError:
        _ocr = PaddleOCR(**kwargs)  # type: ignore[misc]
    yield


app = FastAPI(title="PaddleOCR", version="1.0.0", lifespan=lifespan)


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

        def run_ocr():
            return _ocr.ocr(tmp_path, cls=True)

        raw = await asyncio.to_thread(run_ocr)
        text = _text_from_paddle_result(raw)
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
