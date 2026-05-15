from __future__ import annotations

import json
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.history import delete_result, list_history, load_result
from app.inference.factory import check_health, list_models_with_classification
from app.ocr_service import (
    read_and_validate_image,
    read_and_validate_ocr_upload,
    run_arena,
    run_ocr,
    safe_upload_filename,
)
from app.product_scan import run_product_ocr
from app.samples import list_sample_images, resolve_sample_path, sample_file_response
from app.scan_service import run_browser_scan
from app.prompts import get_prompts, remove_model_prompt, update_prompts
from app.settings_store import get_inference_backend, get_inference_host, get_settings, update_settings
from app.vllm_compose import (
    compose_manage_enabled,
    gpu_dashboard,
    start_service,
    stop_service,
)

app = FastAPI(title="OCR Inference API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptsUpdate(BaseModel):
    general: str | None = None
    per_model: dict[str, str] | None = None


class SettingsUpdate(BaseModel):
    inference_backend: Literal["ollama", "vllm"] = "vllm"
    inference_host: str


class ArenaRequest(BaseModel):
    models: list[str] = Field(..., min_length=2)
    prompt_overrides: dict[str, str] | None = None


@app.get("/api/health")
async def health():
    h = await check_health()
    return {**h, "status": "ok" if h.get("inference_reachable") else "degraded"}


@app.get("/api/settings")
async def settings_get():
    return get_settings()


@app.put("/api/settings")
async def settings_put(body: SettingsUpdate):
    try:
        data = update_settings(body.inference_host, inference_backend=body.inference_backend)
        h = await check_health()
        return {**data, **h, "status": "ok" if h.get("inference_reachable") else "degraded"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/gpu")
async def gpu_get():
    return await gpu_dashboard()


@app.post("/api/vllm/services/{service_id}/start")
async def vllm_service_start(service_id: str):
    if not compose_manage_enabled():
        raise HTTPException(
            status_code=503,
            detail="GPU management requires Docker socket and COMPOSE_PROJECT_DIR on the backend container.",
        )
    try:
        return await start_service(service_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (RuntimeError, TimeoutError) as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@app.post("/api/vllm/services/{service_id}/stop")
async def vllm_service_stop(service_id: str):
    if not compose_manage_enabled():
        raise HTTPException(
            status_code=503,
            detail="GPU management requires Docker socket and COMPOSE_PROJECT_DIR on the backend container.",
        )
    try:
        return await stop_service(service_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (RuntimeError, TimeoutError) as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@app.get("/api/samples")
async def samples_list():
    return {"samples": list_sample_images()}


@app.get("/api/samples/{filename}")
async def samples_get(filename: str):
    path = resolve_sample_path(filename)
    return sample_file_response(path)


@app.get("/api/models")
async def models():
    try:
        return {
            "models": await list_models_with_classification(),
            "inference_backend": get_inference_backend(),
            "inference_host": get_inference_host(),
            "ollama_host": get_inference_host(),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.get("/api/prompts")
async def prompts_get():
    return get_prompts()


@app.put("/api/prompts")
async def prompts_put(body: PromptsUpdate):
    return update_prompts(body.general, body.per_model)


@app.delete("/api/prompts/{model_name:path}")
async def prompts_delete_model(model_name: str):
    return remove_model_prompt(model_name)


@app.post("/api/ocr")
async def ocr_endpoint(
    image: UploadFile = File(...),
    model: str = Form(...),
    prompt: str | None = Form(None),
):
    image_bytes, ext, content_type = await read_and_validate_ocr_upload(image)
    return await run_ocr(image_bytes, ext, model, prompt, content_type=content_type)


@app.post("/api/ocr/product")
async def ocr_product_endpoint(
    image: UploadFile = File(...),
    model: str = Form(...),
):
    image_bytes, ext = await read_and_validate_image(image)
    return await run_product_ocr(image_bytes, ext, model)


@app.post("/api/scan")
async def scan_endpoint(
    image: UploadFile = File(...),
    sku: str = Form(...),
    expiry_date: str | None = Form(None),
    confidence: float = Form(...),
    raw_text: str | None = Form(None),
    engine: str = Form(...),
    duration_ms: int = Form(...),
):
    return await run_browser_scan(
        image, sku, expiry_date, confidence, raw_text, engine, duration_ms
    )


@app.post("/api/arena")
async def arena_endpoint(
    image: UploadFile = File(...),
    models: str = Form(...),
    prompt_overrides: str | None = Form(None),
    extraction_mode: str = Form("text"),
):
    image_bytes, ext, content_type = await read_and_validate_ocr_upload(image)
    try:
        model_list = json.loads(models)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="models must be a JSON array of strings") from e
    if not isinstance(model_list, list):
        raise HTTPException(status_code=400, detail="models must be a JSON array")
    overrides = None
    if prompt_overrides:
        try:
            overrides = json.loads(prompt_overrides)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail="prompt_overrides must be JSON object") from e
    return await run_arena(
        image_bytes,
        ext,
        model_list,
        overrides,
        content_type=content_type,
        extraction_mode=extraction_mode.strip().lower(),
    )


@app.get("/api/history")
async def history_list(offset: int = 0, limit: int = 50):
    items, total = list_history(offset, limit)
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@app.get("/api/history/{run_id}")
async def history_get(run_id: str):
    record = load_result(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@app.delete("/api/history/{run_id}")
async def history_delete(run_id: str):
    if not delete_result(run_id):
        raise HTTPException(status_code=404, detail="Run not found")
    return {"deleted": run_id}


@app.get("/api/files/upload/{filename}")
async def serve_upload(filename: str):
    path = safe_upload_filename(filename)
    return FileResponse(path)
