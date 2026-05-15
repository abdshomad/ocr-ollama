from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

from app.config import DEFAULT_OLLAMA_HOST, DEFAULT_VLLM_HOST, INFERENCE_BACKEND

SETTINGS_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.json"
_DEBUG_LOG = Path(__file__).resolve().parents[2] / ".cursor" / "debug-cebe92.log"
_VALID_BACKENDS = frozenset({"ollama", "vllm"})


def _agent_log(location: str, message: str, data: dict, hypothesis_id: str) -> None:
    # #region agent log
    try:
        payload = {
            "sessionId": "cebe92",
            "timestamp": int(time.time() * 1000),
            "location": location,
            "message": message,
            "data": data,
            "hypothesisId": hypothesis_id,
        }
        _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _DEBUG_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except OSError:
        pass
    # #endregion


def _is_loopback_url(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host in ("localhost", "127.0.0.1", "::1")


def _normalize_host(url: str, *, label: str = "Inference") -> str:
    url = url.strip().rstrip("/")
    if not url:
        raise ValueError(f"{label} host URL is required")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"{label} host must be a valid http or https URL (e.g. http://localhost:8100)")
    if parsed.path not in ("", "/"):
        raise ValueError(f"{label} host URL must not include a path")
    return url


def _normalize_backend(value: str) -> str:
    backend = value.strip().lower()
    if backend not in _VALID_BACKENDS:
        raise ValueError(f"inference_backend must be one of: {', '.join(sorted(_VALID_BACKENDS))}")
    return backend


def _load_settings_file() -> dict[str, str]:
    if not SETTINGS_PATH.is_file():
        return {}
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        return {k: str(v).strip() for k, v in data.items() if v is not None}
    except json.JSONDecodeError:
        return {}


def _resolve_host(
    *,
    settings_key: str,
    env_var: str,
    default: str,
) -> str:
    file_data = _load_settings_file()
    settings_host: str | None = None
    raw = (file_data.get(settings_key) or "").strip()
    if raw:
        settings_host = _normalize_host(raw)

    env_host = os.getenv(env_var, "").strip().rstrip("/")
    resolved = default
    if settings_host:
        if _is_loopback_url(settings_host) and env_host and not _is_loopback_url(env_host):
            resolved = _normalize_host(env_host)
        else:
            resolved = settings_host
    elif env_host:
        resolved = _normalize_host(env_host)
    return resolved


def get_inference_backend() -> str:
    file_data = _load_settings_file()
    raw = (file_data.get("inference_backend") or "").strip().lower()
    if raw in _VALID_BACKENDS:
        return raw
    env = os.getenv("INFERENCE_BACKEND", INFERENCE_BACKEND).strip().lower()
    if env in _VALID_BACKENDS:
        return env
    return "vllm"


def get_vllm_host() -> str:
    return _resolve_host(
        settings_key="vllm_host",
        env_var="VLLM_HOST",
        default=DEFAULT_VLLM_HOST,
    )


def get_vllm_deepseek_host() -> str:
    return os.getenv("VLLM_DEEPSEEK_HOST", "http://vllm-deepseek:8100").strip().rstrip("/")


def get_vllm_glm_host() -> str:
    return os.getenv("VLLM_GLM_HOST", "http://vllm-glm:8101").strip().rstrip("/")


def get_ollama_host() -> str:
    return _resolve_host(
        settings_key="ollama_host",
        env_var="OLLAMA_HOST",
        default=DEFAULT_OLLAMA_HOST,
    )


def get_inference_host() -> str:
    if get_inference_backend() == "ollama":
        return get_ollama_host()
    return get_vllm_host()


def get_settings() -> dict[str, str]:
    backend = get_inference_backend()
    return {
        "inference_backend": backend,
        "inference_host": get_inference_host(),
        "vllm_host": get_vllm_host(),
        "vllm_deepseek_host": get_vllm_deepseek_host(),
        "vllm_glm_host": get_vllm_glm_host(),
        "ollama_host": get_ollama_host(),
    }


def update_settings(
    inference_host: str,
    *,
    inference_backend: str | None = None,
) -> dict[str, str]:
    backend = _normalize_backend(inference_backend or get_inference_backend())
    normalized = _normalize_host(inference_host)
    payload: dict[str, str] = {"inference_backend": backend}
    if backend == "ollama":
        payload["ollama_host"] = normalized
    else:
        payload["vllm_host"] = normalized
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_settings_file()
    existing.update(payload)
    SETTINGS_PATH.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return get_settings()
