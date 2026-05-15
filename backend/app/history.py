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
    if kind == "browser_scan":
        engine = data.get("engine", "unknown")
        models = [f"browser:{engine}"]
        sku = data.get("sku", "")
        expiry = data.get("expiry_date") or "—"
        preview = f"SKU: {sku} | Exp: {expiry}"[:120]
    elif kind == "product_scan":
        models = [data.get("model", "unknown")]
        sku = data.get("sku", "")
        expiry = data.get("expiry_date") or "—"
        preview = f"SKU: {sku} | Exp: {expiry}"[:120]
    elif kind == "arena":
        models = [r.get("model") for r in data.get("results", [])]
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
    image_path = data.get("image_path", "")
    filename = Path(image_path).name if image_path else ""
    return {
        "id": data.get("id"),
        "kind": kind,
        "timestamp": data.get("timestamp"),
        "models": [m for m in models if m],
        "image_filename": filename,
        "preview": preview,
    }


def new_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
