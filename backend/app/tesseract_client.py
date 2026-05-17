from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
import time
from typing import Any

def tesseract_bin() -> str:
    return (os.getenv("TESSERACT_BIN") or "tesseract").strip() or "tesseract"


def tesseract_lang() -> str:
    return (os.getenv("TESSERACT_LANG") or "eng").strip() or "eng"


def tesseract_psm() -> int:
    v = (os.getenv("TESSERACT_PSM") or "3").strip()
    try:
        return max(0, min(13, int(v)))
    except ValueError:
        return 3


def tesseract_cli_available() -> bool:
    exe = tesseract_bin()
    found = shutil.which(exe)
    return found is not None


def _suffix_for_bytes(data: bytes) -> str:
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".png"


def _run_tesseract(file_path: str, timeout: float) -> str:
    cmd = [
        tesseract_bin(),
        file_path,
        "stdout",
        "-l",
        tesseract_lang(),
        "--psm",
        str(tesseract_psm()),
    ]
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=os.environ.copy(),
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip() or f"exit {r.returncode}"
        raise RuntimeError(f"tesseract failed: {err}")
    return (r.stdout or "").strip()


async def list_models_with_classification() -> list[dict[str, Any]]:
    from app.engine_registry import all_tesseract_models, feature_tags_from_ocr_engine, model_entry

    ready = tesseract_cli_available()
    out: list[dict[str, Any]] = []
    for ep, model_id in all_tesseract_models():
        modes = ep.get("input_modes")
        imodes = [str(x) for x in modes] if isinstance(modes, list) else None
        out.append(
            model_entry(
                model_id,
                available=ready,
                endpoint_id=str(ep.get("id", "tesseract")),
                endpoint_label=str(ep.get("label") or "Tesseract"),
                engine_type=str(ep.get("type", "tesseract")),
                speed_tier=str(ep["speed_tier"]) if ep.get("speed_tier") else None,
                input_modes=imodes,
                feature_tags=feature_tags_from_ocr_engine(ep),
            )
        )
    return out


async def check_health_slice() -> tuple[list[dict[str, Any]], bool, list[str]]:
    from app.engine_registry import all_tesseract_models

    endpoint_status: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        ready = await asyncio.to_thread(tesseract_cli_available)
    except Exception as e:
        ready = False
        errors.append(f"tesseract: {e}")
    for ep, _mid in all_tesseract_models():
        endpoint_status.append(
            {
                "id": str(ep.get("id", "tesseract")),
                "label": ep.get("label"),
                "reachable": ready,
                "host": tesseract_bin(),
                "model_count": len(ep.get("models") or []) if ready else 0,
                "engine_type": "tesseract",
            }
        )
    return endpoint_status, ready, errors


async def ocr_chat(model: str, prompt: str, image_bytes: bytes) -> tuple[str, dict[str, Any], int]:
    from app.engine_registry import ocr_engine_for_model

    ep = ocr_engine_for_model(model)
    if not ep or str(ep.get("type")) != "tesseract":
        raise RuntimeError(f"No Tesseract engine for model '{model}'")

    if not tesseract_cli_available():
        raise RuntimeError("tesseract binary not found; install tesseract-ocr on the backend host")

    suffix = _suffix_for_bytes(image_bytes)
    start = time.perf_counter()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name
    try:
        text = await asyncio.to_thread(_run_tesseract, tmp_path, 120.0)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    duration_ms = int((time.perf_counter() - start) * 1000)
    meta: dict[str, Any] = {
        "engine_type": "tesseract",
        "engine_label": str(ep.get("label") or "Tesseract"),
        "tesseract_binary": tesseract_bin(),
        "tesseract_lang": tesseract_lang(),
        "tesseract_psm": tesseract_psm(),
    }
    return text, meta, duration_ms
