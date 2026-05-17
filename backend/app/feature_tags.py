from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_RULES_PATH = Path(__file__).resolve().parents[1] / "config" / "ollama_model_tags.json"


def normalized_feature_tags(obj: dict[str, Any]) -> list[str]:
    raw = obj.get("feature_tags")
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for x in raw:
        s = str(x).strip()
        if s:
            out.append(s)
    return sorted(set(out))


@lru_cache(maxsize=1)
def _ollama_patterns() -> list[tuple[str, list[str]]]:
    if not _RULES_PATH.is_file():
        return []
    try:
        data = json.loads(_RULES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rules = data.get("patterns")
    if not isinstance(rules, list):
        return []
    out: list[tuple[str, list[str]]] = []
    for r in rules:
        if not isinstance(r, dict):
            continue
        sub = str(r.get("substring", "")).strip().lower()
        tags = r.get("tags")
        if not sub or not isinstance(tags, list):
            continue
        norm = sorted({str(t).strip() for t in tags if str(t).strip()})
        if norm:
            out.append((sub, norm))
    return out


def ollama_feature_tags_for_name(model_name: str) -> list[str]:
    n = model_name.lower()
    acc: set[str] = set()
    for sub, tags in _ollama_patterns():
        if sub in n:
            acc.update(tags)
    return sorted(acc)
