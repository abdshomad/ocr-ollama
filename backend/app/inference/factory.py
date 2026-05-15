from __future__ import annotations

from typing import Any

from app import ollama_client, vllm_client
from app.settings_store import get_inference_backend

Backend = str


def _backend() -> Backend:
    return get_inference_backend()


async def list_models_with_classification() -> list[dict[str, Any]]:
    if _backend() == "ollama":
        return await ollama_client.list_models_with_classification()
    return await vllm_client.list_models_with_classification()


async def check_health() -> dict[str, Any]:
    if _backend() == "ollama":
        raw = await ollama_client.check_health()
        return _normalize_health(raw, "ollama")
    raw = await vllm_client.check_health()
    return _normalize_health(raw, "vllm")


async def ocr_chat(model: str, prompt: str, image_bytes: bytes) -> tuple[str, dict[str, Any], int]:
    if _backend() == "ollama":
        return await ollama_client.ocr_chat(model, prompt, image_bytes)
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
