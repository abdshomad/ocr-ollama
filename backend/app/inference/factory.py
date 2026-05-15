from __future__ import annotations

from typing import Any

from app import liteparse_client, mineru_client, ollama_client, vllm_client
from app.engine_registry import is_litparse_model, is_mineru_model
from app.settings_store import get_inference_backend

Backend = str


def _backend() -> Backend:
    return get_inference_backend()


async def list_models_with_classification() -> list[dict[str, Any]]:
    if _backend() == "ollama":
        ollama_models = await ollama_client.list_models_with_classification()
        litparse_models = await liteparse_client.list_models_with_classification()
        return [*ollama_models, *litparse_models]
    vllm_models = await vllm_client.list_models_with_classification()
    mineru_models = await mineru_client.list_models_with_classification()
    litparse_models = await liteparse_client.list_models_with_classification()
    return [*vllm_models, *mineru_models, *litparse_models]


async def check_health() -> dict[str, Any]:
    if _backend() == "ollama":
        raw = await ollama_client.check_health()
        litparse_status, litparse_up, litparse_errors = await liteparse_client.check_health_slice()
        raw["vllm_endpoints"] = [*list(raw.get("vllm_endpoints") or []), *litparse_status]
        if litparse_up:
            raw["inference_reachable"] = True
            raw.pop("error", None)
        if litparse_errors and not raw.get("inference_reachable"):
            raw["error"] = "; ".join(litparse_errors)
        return _normalize_health(raw, "ollama")
    raw = await vllm_client.check_health()
    mineru_status, mineru_up, mineru_errors = await mineru_client.check_health_slice()
    litparse_status, litparse_up, litparse_errors = await liteparse_client.check_health_slice()
    endpoints = list(raw.get("vllm_endpoints") or [])
    endpoints.extend(mineru_status)
    endpoints.extend(litparse_status)
    raw["vllm_endpoints"] = endpoints
    if mineru_up or litparse_up:
        raw["inference_reachable"] = True
        raw["vllm_reachable"] = True
        raw.pop("error", None)
    errs = [*mineru_errors, *litparse_errors]
    if errs and not raw.get("inference_reachable"):
        raw["error"] = "; ".join(errs)
    return _normalize_health(raw, "vllm")


async def ocr_chat(model: str, prompt: str, image_bytes: bytes) -> tuple[str, dict[str, Any], int]:
    if _backend() == "ollama":
        if is_litparse_model(model):
            return await liteparse_client.ocr_chat(model, prompt, image_bytes)
        return await ollama_client.ocr_chat(model, prompt, image_bytes)
    if is_litparse_model(model):
        return await liteparse_client.ocr_chat(model, prompt, image_bytes)
    if is_mineru_model(model):
        return await mineru_client.ocr_chat(model, prompt, image_bytes)
    return await vllm_client.ocr_chat(model, prompt, image_bytes)


async def text_chat(model: str, prompt: str) -> tuple[str, dict[str, Any], int]:
    if _backend() == "ollama":
        return await ollama_client.text_chat(model, prompt)
    return await vllm_client.text_chat(model, prompt)


def _normalize_health(raw: dict[str, Any], backend: str) -> dict[str, Any]:
    reachable = bool(raw.get("inference_reachable") or raw.get("ollama_reachable") or raw.get("vllm_reachable"))
    host = raw.get("inference_host") or raw.get("ollama_host") or raw.get("vllm_host") or ""
    out: dict[str, Any] = {
        "inference_backend": backend,
        "inference_reachable": reachable,
        "inference_host": host,
        "model_count": raw.get("model_count", 0),
        "error": raw.get("error"),
        "ollama_reachable": reachable if backend == "ollama" else False,
        "ollama_host": host if backend == "ollama" else "",
        "vllm_reachable": reachable if backend == "vllm" else False,
        "vllm_host": host if backend == "vllm" else "",
    }
    if raw.get("vllm_endpoints") is not None:
        out["vllm_endpoints"] = raw["vllm_endpoints"]
    return out
