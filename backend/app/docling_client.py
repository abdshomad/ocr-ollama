from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from app.config import MODEL_LIST_HTTP_TIMEOUT, VLLM_TIMEOUT
from app.engine_registry import all_docling_models, feature_tags_from_ocr_engine, host_for_engine, model_entry


def format_docling_error(status_code: int, detail: Any, model: str) -> str:
    if isinstance(detail, dict):
        err_msg = str(detail.get("detail") or detail)
    else:
        err_msg = str(detail)
    return f"Docling error ({status_code}) for model '{model}': {err_msg}"


async def _service_ready(client: httpx.AsyncClient, host: str) -> bool:
    if not host:
        return False
    try:
        r = await client.get(f"{host.rstrip('/')}/health")
        if r.status_code != 200:
            return False
        body = r.json()
        return bool(body.get("model_loaded"))
    except httpx.HTTPError:
        return False


async def list_models_with_classification() -> list[dict[str, Any]]:
    pairs = all_docling_models()
    hosts_ordered: list[str] = []
    seen: set[str] = set()
    for ep, _mid in pairs:
        h = host_for_engine(ep)
        if h and h not in seen:
            seen.add(h)
            hosts_ordered.append(h)

    async with httpx.AsyncClient(timeout=MODEL_LIST_HTTP_TIMEOUT) as client:
        host_ready_list = await asyncio.gather(*[_service_ready(client, h) for h in hosts_ordered])
        ready_by_host = dict(zip(hosts_ordered, host_ready_list, strict=True))

    result: list[dict[str, Any]] = []
    for ep, model_id in pairs:
        host = host_for_engine(ep)
        available = ready_by_host.get(host, False) if host else False
        speed = ep.get("speed_tier")
        modes = ep.get("input_modes")
        im = list(modes) if isinstance(modes, list) else None
        entry = model_entry(
            model_id,
            available=available,
            endpoint_id=str(ep.get("id", "")),
            endpoint_label=str(ep.get("label") or ep.get("id") or ""),
            engine_type=str(ep.get("type", "docling")),
            speed_tier=str(speed) if speed else None,
            input_modes=im,
            feature_tags=feature_tags_from_ocr_engine(ep),
        )
        result.append(entry)
    return result


async def check_health_slice() -> tuple[list[dict[str, Any]], bool, list[str]]:
    from app.engine_registry import load_ocr_engines

    endpoint_status: list[dict[str, Any]] = []
    any_up = False
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for ep in load_ocr_engines():
            if str(ep.get("type")) != "docling":
                continue
            ep_id = str(ep.get("id", ""))
            host = host_for_engine(ep)
            if not host:
                endpoint_status.append(
                    {"id": ep_id, "label": ep.get("label"), "reachable": False, "error": "no host configured"}
                )
                continue
            try:
                ready = await _service_ready(client, host)
                if ready:
                    any_up = True
                endpoint_status.append(
                    {
                        "id": ep_id,
                        "label": ep.get("label"),
                        "reachable": ready,
                        "host": host,
                        "model_count": len(ep.get("models") or []) if ready else 0,
                    }
                )
            except Exception as e:
                errors.append(f"{ep_id}: {e}")
                endpoint_status.append(
                    {
                        "id": ep_id,
                        "label": ep.get("label"),
                        "reachable": False,
                        "host": host,
                        "error": str(e),
                    }
                )
    return endpoint_status, any_up, errors


async def ocr_chat(model: str, prompt: str, image_bytes: bytes) -> tuple[str, dict[str, Any], int]:
    from app.engine_registry import ocr_engine_for_model

    ep = ocr_engine_for_model(model)
    if not ep:
        raise httpx.HTTPError(f"No Docling engine configured for model '{model}'")
    host = host_for_engine(ep)
    if not host:
        raise httpx.HTTPError(f"No Docling host configured for model '{model}'")

    files = {"image": ("image.png", image_bytes, "application/octet-stream")}
    data = {"prompt": prompt, "model": model}

    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=VLLM_TIMEOUT) as client:
        r = await client.post(f"{host.rstrip('/')}/v1/ocr", files=files, data=data)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if r.status_code >= 400:
            detail: Any = r.text
            try:
                detail = r.json()
            except Exception:
                pass
            raise httpx.HTTPStatusError(
                format_docling_error(r.status_code, detail, model),
                request=r.request,
                response=r,
            )
        body = r.json()

    text = str(body.get("text") or "")
    meta = {
        "engine_type": "docling",
        "engine_label": str(ep.get("label") or "Docling"),
        "docling_host": host,
        "duration_ms": body.get("duration_ms"),
    }
    return text, meta, duration_ms
