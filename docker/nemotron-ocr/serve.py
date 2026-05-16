#!/usr/bin/env python3
"""HTTP sidecar for NVIDIA Nemotron OCR v2 (PyTorch pipeline, not vLLM)."""

from __future__ import annotations

import os
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

_port = int(os.getenv("NEMOTRON_PORT", "8210"))
_repo_root = os.getenv("NEMOTRON_REPO_ROOT", "/opt/nemotron-ocr-v2").rstrip("/")
_variant = os.getenv("NEMOTRON_VARIANT", "multilingual").strip().lower()
_model_id = os.getenv("NEMOTRON_MODEL_ID", "nvidia/nemotron-ocr-v2").strip()
_merge_default = os.getenv("NEMOTRON_MERGE_LEVEL", "paragraph").strip().lower()
_skip_rel = os.getenv("NEMOTRON_SKIP_RELATIONAL", "0").lower() in ("1", "true", "yes")

_ocr = None  # type: ignore[assignment]


def _model_dir() -> Path:
    if _variant in ("en", "english"):
        sub = "v2_english"
    else:
        sub = "v2_multilingual"
    p = Path(_repo_root) / sub
    if not p.is_dir():
        raise RuntimeError(f"Checkpoint directory missing: {p}")
    return p.resolve()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _ocr
    from nemotron_ocr.inference.pipeline_v2 import NemotronOCRV2

    kwargs: dict = {"model_dir": str(_model_dir())}
    if _skip_rel:
        kwargs["skip_relational"] = True
    _ocr = NemotronOCRV2(**kwargs)
    yield


app = FastAPI(title="Nemotron OCR v2", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _ocr is not None, "model_id": _model_id}


@app.get("/v1/models")
async def list_models():
    return {"data": [{"id": _model_id, "object": "model"}]}


def _normalize_merge(level: str) -> str:
    v = (level or "").strip().lower()
    if v in ("word", "sentence", "paragraph"):
        return v
    if _merge_default in ("word", "sentence", "paragraph"):
        return _merge_default
    return "paragraph"


@app.post("/v1/ocr")
async def ocr(
    image: UploadFile = File(...),
    prompt: str = Form(default=""),
    model: str = Form(default=""),
    merge_level: str = Form(default=""),
):
    if model and model.strip() and model.strip() != _model_id:
        raise HTTPException(status_code=400, detail=f"Unknown model '{model}'")
    if _ocr is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image")

    ml = _normalize_merge(merge_level or prompt)
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
        preds = _ocr(tmp_path, merge_level=ml)  # type: ignore[operator]
        lines: list[str] = []
        for pred in preds:
            t = pred.get("text")
            if isinstance(t, str) and t.strip():
                lines.append(t.strip())
        text = "\n".join(lines)
        duration_ms = int((time.perf_counter() - start) * 1000)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    return {"text": text, "duration_ms": duration_ms, "model": _model_id, "merge_level": ml}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=_port, log_level="info")
