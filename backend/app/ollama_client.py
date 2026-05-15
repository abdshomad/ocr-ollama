from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any

import httpx

from app.config import OCR_NUM_CTX, OLLAMA_TIMEOUT
from app.inference.classify import (
    ModelTier,
    classify_ollama_model,
    is_ocr_capable,
)
from app.settings_store import get_ollama_host

_DEBUG_LOG = Path(__file__).resolve().parents[2] / ".cursor" / "debug-cebe92.log"


def _agent_log(location: str, message: str, data: dict, hypothesis_id: str) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "cebe92",
            "timestamp": int(time.time() * 1000),
            "location": location,
            "message": message,
            "data": data,
            "hypothesisId": hypothesis_id,
        }
        _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _DEBUG_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except OSError:
        pass
    # #endregion


def classify_model(name: str, show: dict[str, Any]) -> ModelTier:
    return classify_ollama_model(name, show)


def has_parent_blob(show: dict[str, Any]) -> bool:
    parent = (show.get("details") or {}).get("parent_model") or ""
    return bool(str(parent).strip())


def format_ollama_error(status_code: int, detail: Any, model: str) -> str:
    err_msg = ""
    if isinstance(detail, dict):
        err_msg = str(detail.get("error", detail))
    else:
        err_msg = str(detail)
    lower = err_msg.lower()
    if "unknown model architecture" in lower or "unknown model architecture" in str(detail).lower():
        return (
            f"Ollama on the host does not support model '{model}' yet (unsupported architecture). "
            f"Upgrade Ollama to a build that includes this architecture, or pick another OCR model "
            f"(e.g. deepseek-ocr, glm-ocr). Detail: {err_msg}"
        )
    if "unable to load model" in lower or "model failed to load" in lower:
        if "paddleocr" in model.lower():
            return (
                f"Ollama could not load model '{model}'. "
                f"This model uses the paddleocr architecture, which is not supported on Ollama "
                f"0.23.x yet (check server logs for 'unknown model architecture'). "
                f"Upgrade Ollama when available, or use deepseek-ocr / glm-ocr. Detail: {err_msg}"
            )
        if "glm-ocr" in model.lower():
            return (
                f"Ollama could not load model '{model}' on GPU with the default context window "
                f"(131k ctx can trigger a CUDA ggml INT_MAX bug on Ollama 0.23.x — see server logs). "
                f"Rebuild/restart the app so OCR requests pass num_ctx={OCR_NUM_CTX}, use deepseek-ocr, "
                f"or set OCR_NUM_CTX lower in the backend env. Detail: {err_msg}"
            )
        return (
            f"Ollama could not load model '{model}' (unsupported architecture, GPU/context limits, "
            f"or missing files). Try: ollama pull {model!r} — check `journalctl -u ollama` for details, "
            f"or pick another model. Detail: {err_msg}"
        )
    return f"Ollama error ({status_code}): {err_msg}"


async def fetch_tags(client: httpx.AsyncClient, host: str | None = None) -> list[dict[str, Any]]:
    base = host or get_ollama_host()
    r = await client.get(f"{base}/api/tags")
    r.raise_for_status()
    return r.json().get("models", [])


async def fetch_show(client: httpx.AsyncClient, name: str, host: str | None = None) -> dict[str, Any]:
    base = host or get_ollama_host()
    r = await client.post(f"{base}/api/show", json={"name": name})
    r.raise_for_status()
    return r.json()


async def list_models_with_classification() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        tags = await fetch_tags(client)
        result = []
        for m in tags:
            name = m.get("name", "")
            try:
                show = await fetch_show(client, name)
            except httpx.HTTPError:
                show = {}
            tier = classify_model(name, show)
            result.append(
                {
                    "name": name,
                    "size": m.get("size"),
                    "modified_at": m.get("modified_at"),
                    "tier": tier.value,
                    "ocr_capable": is_ocr_capable(tier),
                    "has_parent_blob": has_parent_blob(show),
                    "capabilities": show.get("capabilities", []),
                    "families": (show.get("details") or {}).get("families", []),
                }
            )
        # #region agent log
        ocr_count = sum(1 for m in result if m.get("ocr_capable"))
        _agent_log(
            "ollama_client.py:list_models_with_classification",
            "models classified",
            {"total": len(result), "ocr_capable": ocr_count},
            "D",
        )
        # #endregion
        return result


async def check_health() -> dict[str, Any]:
    host = get_ollama_host()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tags = await fetch_tags(client, host)
            # #region agent log
            _agent_log(
                "ollama_client.py:check_health",
                "ollama reachable",
                {"host": host, "model_count": len(tags)},
                "A",
            )
            # #endregion
            return {
                "inference_reachable": True,
                "inference_host": host,
                "ollama_reachable": True,
                "ollama_host": host,
                "model_count": len(tags),
            }
    except Exception as e:
        # #region agent log
        _agent_log(
            "ollama_client.py:check_health",
            "ollama unreachable",
            {"host": host, "error": str(e), "error_type": type(e).__name__},
            "A",
        )
        # #endregion
        return {
            "inference_reachable": False,
            "inference_host": host,
            "ollama_reachable": False,
            "ollama_host": host,
            "model_count": 0,
            "error": str(e),
        }


async def ocr_chat(model: str, prompt: str, image_bytes: bytes) -> tuple[str, dict[str, Any], int]:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [b64],
            }
        ],
        "stream": False,
        "options": {"num_ctx": OCR_NUM_CTX},
    }
    host = get_ollama_host()
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        r = await client.post(f"{host}/api/chat", json=payload)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if r.status_code >= 400:
            detail: Any = r.text
            try:
                detail = r.json()
            except Exception:
                pass
            # #region agent log
            _agent_log(
                "ollama_client.py:ocr_chat",
                "ollama chat failed",
                {
                    "model": model,
                    "status": r.status_code,
                    "detail": detail if isinstance(detail, (dict, str)) else str(detail),
                },
                "E",
            )
            # #endregion
            raise httpx.HTTPStatusError(
                format_ollama_error(r.status_code, detail, model),
                request=r.request,
                response=r,
            )
        data = r.json()
    text = (data.get("message") or {}).get("content", "")
    meta = {
        "eval_count": data.get("eval_count"),
        "eval_duration": data.get("eval_duration"),
        "total_duration": data.get("total_duration"),
    }
    return text, meta, duration_ms
