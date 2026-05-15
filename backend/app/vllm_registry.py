from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.inference.classify import ModelTier, classify_model_by_name, is_ocr_capable

_ENDPOINTS_PATH = Path(__file__).resolve().parents[1] / "config" / "vllm_endpoints.json"


@lru_cache(maxsize=1)
def load_endpoints() -> list[dict[str, Any]]:
    data = json.loads(_ENDPOINTS_PATH.read_text(encoding="utf-8"))
    return list(data.get("endpoints") or [])


def host_for_endpoint(ep: dict[str, Any]) -> str:
    env_key = ep.get("host_env") or ""
    env_val = os.getenv(env_key, "").strip().rstrip("/") if env_key else ""
    if env_val:
        return env_val
    return str(ep.get("default_host", "")).rstrip("/")


def resolve_host_for_model(model: str) -> str:
    model_stripped = model.strip()
    for ep in load_endpoints():
        models = ep.get("models") or []
        if model_stripped in models:
            host = host_for_endpoint(ep)
            if host:
                return host
    # Fallback: single-host dev (VLLM_HOST / settings)
    from app.settings_store import get_vllm_host

    return get_vllm_host()


def endpoint_for_model(model: str) -> dict[str, Any] | None:
    model_stripped = model.strip()
    for ep in load_endpoints():
        if model_stripped in (ep.get("models") or []):
            return ep
    return None


def all_configured_models() -> list[tuple[dict[str, Any], str]]:
    """(endpoint, model_id) for every catalog entry."""
    out: list[tuple[dict[str, Any], str]] = []
    for ep in load_endpoints():
        for name in ep.get("models") or []:
            out.append((ep, str(name)))
    return out


def model_entry(
    name: str,
    *,
    available: bool,
    endpoint_id: str,
    endpoint_label: str,
    speed_tier: str | None = None,
) -> dict[str, Any]:
    tier = classify_model_by_name(name)
    entry: dict[str, Any] = {
        "name": name,
        "size": None,
        "modified_at": None,
        "tier": tier.value,
        "ocr_capable": is_ocr_capable(tier),
        "has_parent_blob": False,
        "capabilities": [],
        "families": [],
        "available": available,
        "vllm_endpoint": endpoint_id,
        "vllm_endpoint_label": endpoint_label,
    }
    if speed_tier:
        entry["speed_tier"] = speed_tier
    return entry
