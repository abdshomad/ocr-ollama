"""Background availability probes with instant catalog responses."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.model_catalog import list_models_catalog
from app.settings_store import get_inference_backend

_AVAILABILITY_BY_NAME: dict[str, bool] = {}
_EXTRA_MODELS: dict[str, dict[str, Any]] = {}
_REFRESH_LOCK = asyncio.Lock()
_REFRESHING = False
_LAST_REFRESH_MONO: float = 0.0

_GPU_API_BY_ID: dict[str, dict[str, Any]] = {}
_GPU_REFRESHING = False

# Do not stack probes on every /api/models poll (frontend uses 5s interval).
_MIN_REFRESH_INTERVAL_S = 4.0


def get_models_for_api() -> list[dict[str, Any]]:
    catalog = list_models_catalog()
    by_name: dict[str, dict[str, Any]] = {m["name"]: dict(m) for m in catalog}

    for name, probed in _EXTRA_MODELS.items():
        if name not in by_name:
            by_name[name] = dict(probed)

    out: list[dict[str, Any]] = []
    for name, row in by_name.items():
        if name in _AVAILABILITY_BY_NAME:
            row = {**row, "available": _AVAILABILITY_BY_NAME[name]}
        out.append(row)
    return out


def availability_pending() -> bool:
    if _REFRESHING:
        return True
    if not _AVAILABILITY_BY_NAME and not _EXTRA_MODELS:
        return True
    return False


def merge_gpu_services(fast_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in fast_rows:
        sid = str(row.get("id", ""))
        cached = _GPU_API_BY_ID.get(sid)
        if cached:
            merged = {**row, **cached}
            if "gpu_device" in row:
                merged["gpu_device"] = row["gpu_device"]
        else:
            merged = dict(row)
        out.append(merged)
    return out


def schedule_availability_refresh(background_tasks: Any | None = None) -> None:
    if background_tasks is not None:
        background_tasks.add_task(refresh_models_availability)
    else:
        asyncio.create_task(refresh_models_availability())


def schedule_gpu_api_refresh(background_tasks: Any | None = None) -> None:
    if background_tasks is not None:
        background_tasks.add_task(refresh_gpu_api_status)
    else:
        asyncio.create_task(refresh_gpu_api_status())


async def refresh_models_availability() -> None:
    global _REFRESHING, _LAST_REFRESH_MONO

    if _REFRESHING:
        return
    now = time.monotonic()
    if _LAST_REFRESH_MONO and (now - _LAST_REFRESH_MONO) < _MIN_REFRESH_INTERVAL_S:
        return

    async with _REFRESH_LOCK:
        if _REFRESHING:
            return
        now = time.monotonic()
        if _LAST_REFRESH_MONO and (now - _LAST_REFRESH_MONO) < _MIN_REFRESH_INTERVAL_S:
            return
        _REFRESHING = True

    try:
        from app.inference.factory import probe_models_availability

        probed = await probe_models_availability()
        catalog_names = {m["name"] for m in list_models_catalog()}
        by_name: dict[str, bool] = {}
        extra: dict[str, dict[str, Any]] = {}
        for m in probed:
            name = str(m.get("name", ""))
            if not name:
                continue
            avail = bool(m.get("available"))
            by_name[name] = avail
            if name not in catalog_names:
                extra[name] = m
        _AVAILABILITY_BY_NAME.clear()
        _AVAILABILITY_BY_NAME.update(by_name)
        _EXTRA_MODELS.clear()
        _EXTRA_MODELS.update(extra)
        _LAST_REFRESH_MONO = time.monotonic()
    finally:
        _REFRESHING = False


async def refresh_gpu_api_status() -> None:
    global _GPU_REFRESHING

    if _GPU_REFRESHING:
        return
    _GPU_REFRESHING = True
    try:
        from app.vllm_compose import list_service_statuses_probed

        rows = await list_service_statuses_probed()
        _GPU_API_BY_ID.clear()
        for row in rows:
            sid = str(row.get("id", ""))
            if sid:
                _GPU_API_BY_ID[sid] = {
                    "api_ready": row.get("api_ready"),
                    "models": row.get("models"),
                }
    finally:
        _GPU_REFRESHING = False
