from __future__ import annotations

import base64
import re
import time
from typing import Any

import httpx

from app.config import VLLM_MAX_TOKENS, VLLM_TIMEOUT, VLLM_XARGS
from app.inference.classify import ModelTier, classify_model_by_name, is_ocr_capable
from app.settings_store import get_vllm_host

_DEEPSEEK_OCR_RE = re.compile(r"deepseek-ocr", re.IGNORECASE)


def _mime_for_image(image_bytes: bytes) -> str:
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if len(image_bytes) >= 12 and image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _v1_base(host: str) -> str:
    return f"{host.rstrip('/')}/v1"


def _deepseek_extra_body(model: str) -> dict[str, Any] | None:
    if not _DEEPSEEK_OCR_RE.search(model):
        return None
    return {
        "skip_special_tokens": False,
        "vllm_xargs": dict(VLLM_XARGS),
    }


def format_vllm_error(status_code: int, detail: Any, model: str) -> str:
    err_msg = ""
    if isinstance(detail, dict):
        err = detail.get("error")
        if isinstance(err, dict):
            err_msg = str(err.get("message", err))
        else:
            err_msg = str(err or detail)
    else:
        err_msg = str(detail)
    return f"vLLM error ({status_code}) for model '{model}': {err_msg}"


async def fetch_models(client: httpx.AsyncClient, host: str | None = None) -> list[dict[str, Any]]:
    base = _v1_base(host or get_vllm_host())
    r = await client.get(f"{base}/models")
    r.raise_for_status()
    return r.json().get("data", [])


async def list_models_with_classification() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        entries = await fetch_models(client)
        result = []
        for m in entries:
            name = m.get("id", "")
            tier = classify_model_by_name(name)
            result.append(
                {
                    "name": name,
                    "size": None,
                    "modified_at": None,
                    "tier": tier.value,
                    "ocr_capable": is_ocr_capable(tier),
                    "has_parent_blob": False,
                    "capabilities": [],
                    "families": [],
                }
            )
        return result


async def check_health() -> dict[str, Any]:
    host = get_vllm_host()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            models = await fetch_models(client, host)
            return {
                "inference_reachable": True,
                "inference_host": host,
                "vllm_reachable": True,
                "vllm_host": host,
                "model_count": len(models),
            }
    except Exception as e:
        return {
            "inference_reachable": False,
            "inference_host": host,
            "vllm_reachable": False,
            "vllm_host": host,
            "model_count": 0,
            "error": str(e),
        }


async def ocr_chat(model: str, prompt: str, image_bytes: bytes) -> tuple[str, dict[str, Any], int]:
    mime = _mime_for_image(image_bytes)
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "max_tokens": VLLM_MAX_TOKENS,
        "temperature": 0.0,
        "stream": False,
    }
    extra = _deepseek_extra_body(model)
    if extra:
        payload.update(extra)

    host = get_vllm_host()
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=VLLM_TIMEOUT) as client:
        r = await client.post(f"{_v1_base(host)}/chat/completions", json=payload)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if r.status_code >= 400:
            detail: Any = r.text
            try:
                detail = r.json()
            except Exception:
                pass
            raise httpx.HTTPStatusError(
                format_vllm_error(r.status_code, detail, model),
                request=r.request,
                response=r,
            )
        data = r.json()

    choice = (data.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content", "") or ""
    usage = data.get("usage") or {}
    meta = {
        "completion_tokens": usage.get("completion_tokens"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }
    return text, meta, duration_ms
