from __future__ import annotations

from typing import Any

from app import (
    doctr_client,
    easyocr_client,
    liteparse_client,
    mineru_client,
    nemotron_client,
    ollama_client,
    onnxtr_client,
    rapidocr_client,
    tesseract_client,
    vllm_client,
)
from app.engine_registry import (
    is_doctr_model,
    is_easyocr_model,
    is_litparse_model,
    is_mineru_model,
    is_nemotron_model,
    is_onnxtr_model,
    is_rapidocr_model,
    is_tesseract_model,
)
from app.settings_store import get_inference_backend

Backend = str


def _backend() -> Backend:
    return get_inference_backend()


async def list_models_with_classification() -> list[dict[str, Any]]:
    tesseract_models = await tesseract_client.list_models_with_classification()
    if _backend() == "ollama":
        ollama_models = await ollama_client.list_models_with_classification()
        rapidocr_models = await rapidocr_client.list_models_with_classification()
        onnxtr_models = await onnxtr_client.list_models_with_classification()
        easyocr_models = await easyocr_client.list_models_with_classification()
        doctr_models = await doctr_client.list_models_with_classification()
        litparse_models = await liteparse_client.list_models_with_classification()
        return [
            *ollama_models,
            *rapidocr_models,
            *onnxtr_models,
            *easyocr_models,
            *doctr_models,
            *litparse_models,
            *tesseract_models,
        ]
    vllm_models = await vllm_client.list_models_with_classification()
    mineru_models = await mineru_client.list_models_with_classification()
    nemotron_models = await nemotron_client.list_models_with_classification()
    rapidocr_models = await rapidocr_client.list_models_with_classification()
    onnxtr_models = await onnxtr_client.list_models_with_classification()
    easyocr_models = await easyocr_client.list_models_with_classification()
    doctr_models = await doctr_client.list_models_with_classification()
    litparse_models = await liteparse_client.list_models_with_classification()
    return [
        *vllm_models,
        *mineru_models,
        *nemotron_models,
        *rapidocr_models,
        *onnxtr_models,
        *easyocr_models,
        *doctr_models,
        *litparse_models,
        *tesseract_models,
    ]


async def check_health() -> dict[str, Any]:
    tesseract_status, tesseract_up, tesseract_errors = await tesseract_client.check_health_slice()
    if _backend() == "ollama":
        raw = await ollama_client.check_health()
        rapidocr_status, rapidocr_up, rapidocr_errors = await rapidocr_client.check_health_slice()
        onnxtr_status, onnxtr_up, onnxtr_errors = await onnxtr_client.check_health_slice()
        easyocr_status, easyocr_up, easyocr_errors = await easyocr_client.check_health_slice()
        doctr_status, doctr_up, doctr_errors = await doctr_client.check_health_slice()
        litparse_status, litparse_up, litparse_errors = await liteparse_client.check_health_slice()
        raw["vllm_endpoints"] = [
            *list(raw.get("vllm_endpoints") or []),
            *rapidocr_status,
            *onnxtr_status,
            *easyocr_status,
            *doctr_status,
            *litparse_status,
            *tesseract_status,
        ]
        if rapidocr_up or onnxtr_up or easyocr_up or doctr_up or litparse_up or tesseract_up:
            raw["inference_reachable"] = True
            raw.pop("error", None)
        errs = [
            *rapidocr_errors,
            *onnxtr_errors,
            *easyocr_errors,
            *doctr_errors,
            *litparse_errors,
            *tesseract_errors,
        ]
        if errs and not raw.get("inference_reachable"):
            raw["error"] = "; ".join(errs)
        return _normalize_health(raw, "ollama")
    raw = await vllm_client.check_health()
    mineru_status, mineru_up, mineru_errors = await mineru_client.check_health_slice()
    nemotron_status, nemotron_up, nemotron_errors = await nemotron_client.check_health_slice()
    rapidocr_status, rapidocr_up, rapidocr_errors = await rapidocr_client.check_health_slice()
    onnxtr_status, onnxtr_up, onnxtr_errors = await onnxtr_client.check_health_slice()
    easyocr_status, easyocr_up, easyocr_errors = await easyocr_client.check_health_slice()
    doctr_status, doctr_up, doctr_errors = await doctr_client.check_health_slice()
    litparse_status, litparse_up, litparse_errors = await liteparse_client.check_health_slice()
    endpoints = list(raw.get("vllm_endpoints") or [])
    endpoints.extend(mineru_status)
    endpoints.extend(nemotron_status)
    endpoints.extend(rapidocr_status)
    endpoints.extend(onnxtr_status)
    endpoints.extend(easyocr_status)
    endpoints.extend(doctr_status)
    endpoints.extend(litparse_status)
    endpoints.extend(tesseract_status)
    raw["vllm_endpoints"] = endpoints
    if (
        mineru_up
        or nemotron_up
        or rapidocr_up
        or onnxtr_up
        or easyocr_up
        or doctr_up
        or litparse_up
        or tesseract_up
    ):
        raw["inference_reachable"] = True
        raw["vllm_reachable"] = True
        raw.pop("error", None)
    errs = [
        *mineru_errors,
        *nemotron_errors,
        *rapidocr_errors,
        *onnxtr_errors,
        *easyocr_errors,
        *doctr_errors,
        *litparse_errors,
        *tesseract_errors,
    ]
    if errs and not raw.get("inference_reachable"):
        raw["error"] = "; ".join(errs)
    return _normalize_health(raw, "vllm")


async def ocr_chat(model: str, prompt: str, image_bytes: bytes) -> tuple[str, dict[str, Any], int]:
    if is_tesseract_model(model):
        return await tesseract_client.ocr_chat(model, prompt, image_bytes)
    if _backend() == "ollama":
        if is_litparse_model(model):
            return await liteparse_client.ocr_chat(model, prompt, image_bytes)
        if is_rapidocr_model(model):
            return await rapidocr_client.ocr_chat(model, prompt, image_bytes)
        if is_onnxtr_model(model):
            return await onnxtr_client.ocr_chat(model, prompt, image_bytes)
        if is_easyocr_model(model):
            return await easyocr_client.ocr_chat(model, prompt, image_bytes)
        if is_doctr_model(model):
            return await doctr_client.ocr_chat(model, prompt, image_bytes)
        return await ollama_client.ocr_chat(model, prompt, image_bytes)
    if is_litparse_model(model):
        return await liteparse_client.ocr_chat(model, prompt, image_bytes)
    if is_mineru_model(model):
        return await mineru_client.ocr_chat(model, prompt, image_bytes)
    if is_nemotron_model(model):
        return await nemotron_client.ocr_chat(model, prompt, image_bytes)
    if is_rapidocr_model(model):
        return await rapidocr_client.ocr_chat(model, prompt, image_bytes)
    if is_onnxtr_model(model):
        return await onnxtr_client.ocr_chat(model, prompt, image_bytes)
    if is_easyocr_model(model):
        return await easyocr_client.ocr_chat(model, prompt, image_bytes)
    if is_doctr_model(model):
        return await doctr_client.ocr_chat(model, prompt, image_bytes)
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
