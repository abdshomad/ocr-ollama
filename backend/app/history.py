from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import RESULT_DIR


def _result_path(run_id: str) -> Path:
    return RESULT_DIR / f"{run_id}.json"


def save_result(record: dict[str, Any]) -> dict[str, Any]:
    run_id = record["id"]
    path = _result_path(run_id)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def load_result(run_id: str) -> dict[str, Any] | None:
    path = _result_path(run_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def delete_result(run_id: str) -> bool:
    path = _result_path(run_id)
    if path.is_file():
        path.unlink()
        return True
    return False


def list_history(offset: int = 0, limit: int = 50) -> tuple[list[dict[str, Any]], int]:
    files = sorted(RESULT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    total = len(files)
    items: list[dict[str, Any]] = []
    for path in files[offset : offset + limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        summary = _to_summary(data)
        items.append(summary)
    return items, total


def _to_summary(data: dict[str, Any]) -> dict[str, Any]:
    kind = data.get("kind", "single")
    duration_ms: int | None = None
    model_duration_ms: dict[str, int] | None = None

    if kind == "browser_scan":
        engine = data.get("engine", "unknown")
        models = [f"browser:{engine}"]
        sku = data.get("sku", "")
        expiry = data.get("expiry_date") or "—"
        preview = f"SKU: {sku} | Exp: {expiry}"[:120]
        raw_d = data.get("duration_ms")
        if isinstance(raw_d, (int, float)) and raw_d > 0:
            duration_ms = int(raw_d)
    elif kind == "product_scan":
        models = [data.get("model", "unknown")]
        sku = data.get("sku", "")
        expiry = data.get("expiry_date") or "—"
        preview = f"SKU: {sku} | Exp: {expiry}"[:120]
        raw_d = data.get("duration_ms")
        if isinstance(raw_d, (int, float)) and raw_d > 0:
            duration_ms = int(raw_d)
    elif kind == "arena":
        models = [r.get("model") for r in data.get("results", [])]
        per_model: dict[str, int] = {}
        for r in data.get("results", []) or []:
            m = r.get("model")
            raw_d = r.get("duration_ms")
            if not m or not isinstance(raw_d, (int, float)) or raw_d <= 0:
                continue
            d = int(raw_d)
            per_model[m] = max(per_model.get(m, 0), d)
        if per_model:
            model_duration_ms = per_model
        if data.get("extraction_mode") == "product":
            first = next((r for r in data.get("results", []) if r.get("sku")), {})
            sku = first.get("sku", "")
            expiry = first.get("expiry_date") or "—"
            preview = f"SKU: {sku} | Exp: {expiry}"[:120]
        else:
            preview = next((r.get("text", "")[:120] for r in data.get("results", []) if r.get("text")), "")
    else:
        models = [data.get("model")]
        preview = (data.get("text") or "")[:120]
        raw_d = data.get("duration_ms")
        if isinstance(raw_d, (int, float)) and raw_d > 0:
            duration_ms = int(raw_d)
    image_path = data.get("image_path", "")
    filename = Path(image_path).name if image_path else ""
    summary: dict[str, Any] = {
        "id": data.get("id"),
        "kind": kind,
        "timestamp": data.get("timestamp"),
        "models": [m for m in models if m],
        "image_filename": filename,
        "preview": preview,
    }
    if kind == "arena":
        summary["extraction_mode"] = data.get("extraction_mode")
        if model_duration_ms is not None:
            summary["model_duration_ms"] = model_duration_ms
    elif duration_ms is not None:
        summary["duration_ms"] = duration_ms
    return summary


def new_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
