from __future__ import annotations

import json
from typing import Any

from app.config import PROMPTS_PATH


def _load() -> dict[str, Any]:
    if not PROMPTS_PATH.exists():
        return {"general": "", "per_model": {}}
    return json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))


def _save(data: dict[str, Any]) -> None:
    PROMPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROMPTS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_prompts() -> dict[str, Any]:
    return _load()


def update_prompts(general: str | None = None, per_model: dict[str, str] | None = None) -> dict[str, Any]:
    data = _load()
    if general is not None:
        data["general"] = general
    if per_model is not None:
        existing = data.get("per_model") or {}
        existing.update(per_model)
        data["per_model"] = existing
    _save(data)
    return data


def resolve_prompt(model: str, override: str | None = None) -> str:
    if override and override.strip():
        return override.strip()
    data = _load()
    per = (data.get("per_model") or {}).get(model)
    if per and str(per).strip():
        return str(per).strip()
    return str(data.get("general", "")).strip()


def remove_model_prompt(model: str) -> dict[str, Any]:
    data = _load()
    per = data.get("per_model") or {}
    per.pop(model, None)
    data["per_model"] = per
    _save(data)
    return data
