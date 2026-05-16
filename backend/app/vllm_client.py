from __future__ import annotations

import asyncio
import base64
import os
import re
import time
from typing import Any

import httpx

from app.config import MODEL_LIST_HTTP_TIMEOUT, VLLM_MAX_TOKENS, VLLM_TIMEOUT, VLLM_XARGS
from app.vllm_registry import (
    all_configured_models,
    host_for_endpoint,
    load_endpoints,
    model_entry,
    resolve_host_for_model,
)

_DEEPSEEK_OCR_RE = re.compile(r"deepseek-ocr", re.IGNORECASE)
_CHANDRA_RE = re.compile(r"chandra", re.IGNORECASE)
_GEMMA4_RE = re.compile(r"gemma-4", re.IGNORECASE)
_QWEN3_VL_RE = re.compile(r"qwen.*3.*vl|qwen3-vl", re.IGNORECASE)
_HUNYUAN_OCR_RE = re.compile(r"hunyuanocr", re.IGNORECASE)
_PADDLEOCR_VL_RE = re.compile(r"paddleocr-vl", re.IGNORECASE)
_DOTS_MOCR_RE = re.compile(r"dots\.mocr|dotsmocr", re.IGNORECASE)
_PHI4_MM_RE = re.compile(r"phi-4-multimodal", re.IGNORECASE)
_ROLMOCR_RE = re.compile(r"rolmocr", re.IGNORECASE)
_NUMARKDOWN_RE = re.compile(r"numarkdown|nu\s*markdown", re.IGNORECASE)
_QWEN3_OMNI_RE = re.compile(r"qwen3-omni|qwen.*3.*omni", re.IGNORECASE)


def _strip_numarkdown_answer(text: str) -> str:
    """NuMarkdown emits thinking + `<answer>` blocks; return markdown inside `<answer>` when present."""
    m = re.search(r"<answer>([\s\S]*?)</answer>", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.strip()


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


def _max_tokens_for_model(model: str) -> int:
    if _CHANDRA_RE.search(model):
        return int(os.getenv("VLLM_CHANDRA_MAX_TOKENS", "4096"))
    if _GEMMA4_RE.search(model):
        return int(os.getenv("VLLM_GEMMA4_MAX_TOKENS", "4096"))
    if _QWEN3_VL_RE.search(model):
        return int(os.getenv("VLLM_QWEN3_VL_MAX_TOKENS", "4096"))
    if _HUNYUAN_OCR_RE.search(model):
        return int(os.getenv("VLLM_HUNYUAN_OCR_MAX_TOKENS", "2048"))
    if _PADDLEOCR_VL_RE.search(model):
        return int(os.getenv("VLLM_PADDLEOCR_VL_MAX_TOKENS", "4096"))
    if _DOTS_MOCR_RE.search(model):
        return int(os.getenv("VLLM_DOTS_MOCR_MAX_TOKENS", "8192"))
    if _PHI4_MM_RE.search(model):
        return int(os.getenv("VLLM_PHI4_MM_MAX_TOKENS", "4096"))
    if _ROLMOCR_RE.search(model):
        return int(os.getenv("VLLM_ROLMOCR_MAX_TOKENS", "4096"))
    if _NUMARKDOWN_RE.search(model):
        return int(os.getenv("VLLM_NUMARKDOWN_MAX_TOKENS", "8192"))
    if _QWEN3_OMNI_RE.search(model):
        return int(os.getenv("VLLM_QWEN3_OMNI_MAX_TOKENS", "4096"))
    return VLLM_MAX_TOKENS


def _sampling_for_model(model: str) -> dict[str, float]:
    if _CHANDRA_RE.search(model):
        return {"top_p": float(os.getenv("VLLM_CHANDRA_TOP_P", "0.1"))}
    if _ROLMOCR_RE.search(model):
        return {"temperature": float(os.getenv("VLLM_ROLMOCR_TEMPERATURE", "0.2"))}
    if _NUMARKDOWN_RE.search(model):
        return {"temperature": float(os.getenv("VLLM_NUMARKDOWN_TEMPERATURE", "0.4"))}
    return {}


def _qwen3_omni_chat_extras(model: str) -> dict[str, Any]:
    """vLLM-Omni chat completions: request text-only output for OCR runs."""
    if not _QWEN3_OMNI_RE.search(model):
        return {}
    return {"modalities": ["text"]}


def _hunyuan_ocr_extras(model: str) -> dict[str, Any]:
    """Recipe-aligned sampling flags for OpenAI-compatible vLLM body."""
    if not _HUNYUAN_OCR_RE.search(model):
        return {}
    return {
        "top_k": int(os.getenv("VLLM_HUNYUAN_OCR_TOP_K", "1")),
        "repetition_penalty": float(os.getenv("VLLM_HUNYUAN_OCR_REPETITION_PENALTY", "1.0")),
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


async def fetch_models(client: httpx.AsyncClient, host: str) -> list[dict[str, Any]]:
    r = await client.get(f"{_v1_base(host)}/models")
    r.raise_for_status()
    return r.json().get("data", [])


async def list_models_with_classification() -> list[dict[str, Any]]:
    rows = all_configured_models()
    hosts_ordered: list[str] = []
    seen_hosts: set[str] = set()
    for ep, _mid in rows:
        h = host_for_endpoint(ep)
        if h and h not in seen_hosts:
            seen_hosts.add(h)
            hosts_ordered.append(h)

    async def _live_ids(client: httpx.AsyncClient, host: str) -> set[str]:
        try:
            live = await fetch_models(client, host)
            return {str(m.get("id", "")) for m in live}
        except httpx.HTTPError:
            return set()

    host_live: dict[str, set[str]]
    async with httpx.AsyncClient(timeout=MODEL_LIST_HTTP_TIMEOUT) as client:
        fetched = await asyncio.gather(*[_live_ids(client, h) for h in hosts_ordered])
        host_live = dict(zip(hosts_ordered, fetched, strict=True))

    result: list[dict[str, Any]] = []
    for ep, model_id in rows:
        host = host_for_endpoint(ep)
        live = host_live.get(host, set())
        if _DOTS_MOCR_RE.search(model_id):
            alias = os.getenv("VLLM_DOTS_MOCR_CHAT_MODEL", "").strip()
            available = bool(host) and (model_id in live or bool(alias and alias in live))
        elif _PHI4_MM_RE.search(model_id):
            alias = os.getenv("VLLM_PHI4_MM_CHAT_MODEL", "").strip()
            available = bool(host) and (model_id in live or bool(alias and alias in live))
        elif _ROLMOCR_RE.search(model_id):
            alias = os.getenv("VLLM_ROLMOCR_CHAT_MODEL", "").strip()
            available = bool(host) and (model_id in live or bool(alias and alias in live))
        elif _NUMARKDOWN_RE.search(model_id):
            alias = os.getenv("VLLM_NUMARKDOWN_CHAT_MODEL", "").strip()
            available = bool(host) and (model_id in live or bool(alias and alias in live))
        elif _QWEN3_OMNI_RE.search(model_id):
            alias = os.getenv("VLLM_QWEN3_OMNI_CHAT_MODEL", "").strip()
            available = bool(host) and (model_id in live or bool(alias and alias in live))
        else:
            available = bool(host) and model_id in live
        speed = ep.get("speed_tier")
        result.append(
            model_entry(
                model_id,
                available=available,
                endpoint_id=str(ep.get("id", "")),
                endpoint_label=str(ep.get("label") or ep.get("id") or ""),
                speed_tier=str(speed) if speed else None,
            )
        )
    return result


async def check_health() -> dict[str, Any]:
    async def _probe_one(client: httpx.AsyncClient, ep: dict[str, Any]) -> tuple[dict[str, Any], str | None, int]:
        ep_id = str(ep.get("id", ""))
        host = host_for_endpoint(ep)
        if not host:
            return (
                {"id": ep_id, "label": ep.get("label"), "reachable": False, "error": "no host configured"},
                None,
                0,
            )
        try:
            models = await fetch_models(client, host)
            count = len(models)
            return (
                {
                    "id": ep_id,
                    "label": ep.get("label"),
                    "reachable": True,
                    "host": host,
                    "model_count": count,
                },
                None,
                count,
            )
        except Exception as e:
            return (
                {
                    "id": ep_id,
                    "label": ep.get("label"),
                    "reachable": False,
                    "host": host,
                    "error": str(e),
                },
                f"{ep_id}: {e}",
                0,
            )

    async with httpx.AsyncClient(timeout=10.0) as client:
        parts = await asyncio.gather(*[_probe_one(client, ep) for ep in load_endpoints()])

    endpoint_status = [p[0] for p in parts]
    errors = [p[1] for p in parts if p[1]]
    total = sum(p[2] for p in parts)
    any_up = any(p[0].get("reachable") for p in parts)

    primary_host = host_for_endpoint(load_endpoints()[0]) if load_endpoints() else ""
    return {
        "inference_reachable": any_up,
        "inference_host": primary_host,
        "vllm_reachable": any_up,
        "vllm_host": primary_host,
        "model_count": total,
        "vllm_endpoints": endpoint_status,
        "error": "; ".join(errors) if errors and not any_up else None,
    }


def _chat_model_id(model: str) -> str:
    """OpenAI `model` field; optional override when vLLM uses --served-model-name."""
    if _DOTS_MOCR_RE.search(model):
        override = os.getenv("VLLM_DOTS_MOCR_CHAT_MODEL", "").strip()
        if override:
            return override
    if _PHI4_MM_RE.search(model):
        override = os.getenv("VLLM_PHI4_MM_CHAT_MODEL", "").strip()
        if override:
            return override
    if _ROLMOCR_RE.search(model):
        override = os.getenv("VLLM_ROLMOCR_CHAT_MODEL", "").strip()
        if override:
            return override
    if _NUMARKDOWN_RE.search(model):
        override = os.getenv("VLLM_NUMARKDOWN_CHAT_MODEL", "").strip()
        if override:
            return override
    if _QWEN3_OMNI_RE.search(model):
        override = os.getenv("VLLM_QWEN3_OMNI_CHAT_MODEL", "").strip()
        if override:
            return override
    return model


async def ocr_chat(model: str, prompt: str, image_bytes: bytes) -> tuple[str, dict[str, Any], int]:
    host = resolve_host_for_model(model)
    if not host:
        raise httpx.HTTPError(f"No vLLM endpoint configured for model '{model}'")

    mime = _mime_for_image(image_bytes)
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    chat_model = _chat_model_id(model)
    payload: dict[str, Any] = {
        "model": chat_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "max_tokens": _max_tokens_for_model(model),
        "temperature": 0.0,
        "stream": False,
    }
    payload.update(_sampling_for_model(model))
    payload.update(_hunyuan_ocr_extras(model))
    payload.update(_qwen3_omni_chat_extras(model))
    extra = _deepseek_extra_body(model)
    if extra:
        payload.update(extra)

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
    if _NUMARKDOWN_RE.search(model):
        text = _strip_numarkdown_answer(text)
    elif _QWEN3_OMNI_RE.search(model) and "thinking" in model.lower():
        text = _strip_numarkdown_answer(text)
    usage = data.get("usage") or {}
    meta = {
        "completion_tokens": usage.get("completion_tokens"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "vllm_host": host,
    }
    return text, meta, duration_ms


async def text_chat(model: str, prompt: str) -> tuple[str, dict[str, Any], int]:
    host = resolve_host_for_model(model)
    if not host:
        raise httpx.HTTPError(f"No vLLM endpoint configured for model '{model}'")

    payload: dict[str, Any] = {
        "model": _chat_model_id(model),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": VLLM_MAX_TOKENS,
        "temperature": 0.0,
        "stream": False,
    }
    extra = _deepseek_extra_body(model)
    if extra:
        payload.update(extra)

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
        "vllm_host": host,
    }
    return text, meta, duration_ms
