from __future__ import annotations

import json
from pathlib import Path

_STORE_PATH = Path(__file__).resolve().parents[1] / "config" / "gpu_device_assignments.json"


def assignment_path() -> Path:
    return _STORE_PATH


def load_assignments() -> dict[str, int]:
    """UI-persisted GPU index per endpoint/service id."""
    if not _STORE_PATH.is_file():
        return {}
    try:
        data = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    raw = data.get("assignments") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for sid, val in raw.items():
        key = str(sid).strip()
        if not key:
            continue
        try:
            out[key] = int(val)
        except (TypeError, ValueError):
            continue
    return out


def save_assignments(assignments: dict[str, int]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"assignments": assignments}
    _STORE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def merge_assignments(updates: dict[str, int | None]) -> dict[str, int]:
    """Merge keyed updates into the persisted map. ``None`` removes an override."""
    current = dict(load_assignments())
    for raw_key, val in updates.items():
        key = str(raw_key).strip()
        if not key:
            continue
        if val is None:
            current.pop(key, None)
            continue
        current[key] = int(val)
    save_assignments(current)
    return current


def assignment_for(endpoint_id: str) -> int | None:
    return load_assignments().get(str(endpoint_id).strip())

