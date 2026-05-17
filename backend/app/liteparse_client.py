from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from app.engine_registry import all_litparse_models, feature_tags_from_ocr_engine, model_entry


def liteparse_bin() -> str:
    return (os.getenv("LITEPARSE_BIN") or "lit").strip() or "lit"


def liteparse_timeout() -> float:
    return float(os.getenv("LITEPARSE_TIMEOUT", "600"))


def liteparse_dpi() -> str:
    """Render DPI before OCR. Default 300 — LiteParse CLI default 150 is too low for scans vs GPU OCR."""
    v = (os.getenv("LITEPARSE_DPI") or "300").strip()
    return v or "300"


def liteparse_output_format() -> str:
    """json (default): join pages[].text; text: raw CLI stdout."""
    f = (os.getenv("LITEPARSE_FORMAT") or "json").strip().lower()
    return "text" if f == "text" else "json"


def liteparse_ocr_language() -> str | None:
    v = (os.getenv("LITEPARSE_OCR_LANGUAGE") or "").strip()
    return v or None


def liteparse_ocr_server_url() -> str | None:
    v = (os.getenv("LITEPARSE_OCR_SERVER_URL") or "").strip()
    return v or None


def _env_flag(name: str, default_true: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default_true
    return raw.strip().lower() not in ("0", "false", "no", "off")


def liteparse_preserve_small_text() -> bool:
    """Helps faint / small glyphs; on by default (disable with LITEPARSE_PRESERVE_SMALL_TEXT=0)."""
    return _env_flag("LITEPARSE_PRESERVE_SMALL_TEXT", True)


_LIT_NODE_OPTIONS_STRIP = frozenset(
    {
        "--warnings-as-errors",
        "--throw-deprecation",
    }
)


def _lit_subprocess_env() -> dict[str, str]:
    """Env for `lit` subprocess.

    LiteParse pulls deps that may emit Node ExperimentalWarning (JSON imports). Inherited
    NODE_OPTIONS such as --warnings-as-errors (common in CI) turns those into exit code 1
    and surfaces as 502. Silence process warnings and drop strict warning flags.
    """
    env = os.environ.copy()
    env["NODE_NO_WARNINGS"] = "1"
    opts_raw = (env.get("NODE_OPTIONS") or "").strip()
    if not opts_raw:
        return env
    parts = [p for p in opts_raw.split() if p not in _LIT_NODE_OPTIONS_STRIP]
    if parts:
        env["NODE_OPTIONS"] = " ".join(parts)
    else:
        env.pop("NODE_OPTIONS", None)
    return env


def lit_cli_available() -> bool:
    exe = liteparse_bin()
    path = Path(exe)
    if path.is_file():
        candidates = [str(path)]
    else:
        found = shutil.which(exe)
        if not found:
            return False
        candidates = [found]
    try:
        r = subprocess.run(
            [*candidates, "--version"],
            capture_output=True,
            text=True,
            timeout=8.0,
            env=_lit_subprocess_env(),
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _suffix_for_bytes(data: bytes) -> str:
    if len(data) >= 4 and data[:4] == b"%PDF":
        return ".pdf"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".bin"


def _lit_parse_command(file_path: Path) -> list[str]:
    cmd: list[str] = [
        liteparse_bin(),
        "parse",
        str(file_path),
        "-q",
        "--format",
        liteparse_output_format(),
        "--dpi",
        liteparse_dpi(),
    ]
    if liteparse_preserve_small_text():
        cmd.append("--preserve-small-text")
    lang = liteparse_ocr_language()
    if lang:
        cmd.extend(["--ocr-language", lang])
    ocr_url = liteparse_ocr_server_url()
    if ocr_url:
        cmd.extend(["--ocr-server-url", ocr_url])
    return cmd


def _strip_node_stdout_noise(stdout: str) -> str:
    """Remove leading Node warning lines if they leak onto stdout (unlikely but defensive)."""
    lines = (stdout or "").splitlines()
    while lines:
        l = lines[0].strip()
        if (
            l.startswith("(node:")
            or "ExperimentalWarning" in lines[0]
            or l.startswith("Warning:")
        ):
            lines.pop(0)
            continue
        break
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines)


def _normalized_lit_stdout(stdout: str) -> str:
    raw = _strip_node_stdout_noise((stdout or "").strip())
    if not raw or liteparse_output_format() == "text":
        return raw
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    pages = data.get("pages")
    if not isinstance(pages, list):
        return raw
    parts: list[str] = []
    for p in pages:
        if isinstance(p, dict):
            t = str(p.get("text") or "").strip()
            if t:
                parts.append(t)
    return "\n\n".join(parts).strip()


def _run_lit_parse(file_path: Path, timeout: float) -> str:
    cmd = _lit_parse_command(file_path)
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_lit_subprocess_env(),
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip() or f"exit {r.returncode}"
        raise RuntimeError(f"lit parse failed: {err}")
    return _normalized_lit_stdout(r.stdout or "")


async def list_models_with_classification() -> list[dict[str, Any]]:
    ready = await asyncio.to_thread(lit_cli_available)
    out: list[dict[str, Any]] = []
    for ep, model_id in all_litparse_models():
        modes = ep.get("input_modes")
        imodes = [str(x) for x in modes] if isinstance(modes, list) else None
        out.append(
            model_entry(
                model_id,
                available=ready,
                endpoint_id=str(ep.get("id", "litparse")),
                endpoint_label=str(ep.get("label") or "LiteParse"),
                engine_type=str(ep.get("type", "litparse")),
                speed_tier=str(ep["speed_tier"]) if ep.get("speed_tier") else None,
                input_modes=imodes,
                feature_tags=feature_tags_from_ocr_engine(ep),
            )
        )
    return out


async def check_health_slice() -> tuple[list[dict[str, Any]], bool, list[str]]:
    endpoint_status: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        ready = await asyncio.to_thread(lit_cli_available)
    except Exception as e:
        ready = False
        errors.append(f"litparse: {e}")
    for ep, _mid in all_litparse_models():
        endpoint_status.append(
            {
                "id": str(ep.get("id", "litparse")),
                "label": ep.get("label"),
                "reachable": ready,
                "host": liteparse_bin(),
                "model_count": len(ep.get("models") or []) if ready else 0,
                "engine_type": "litparse",
            }
        )
    return endpoint_status, ready, errors


async def ocr_chat(model: str, prompt: str, image_bytes: bytes) -> tuple[str, dict[str, Any], int]:
    from app.engine_registry import ocr_engine_for_model

    ep = ocr_engine_for_model(model)
    if not ep or str(ep.get("type")) != "litparse":
        raise RuntimeError(f"No LiteParse engine for model '{model}'")

    if not await asyncio.to_thread(lit_cli_available):
        raise RuntimeError("lit CLI not found; set LITEPARSE_BIN or install @llamaindex/liteparse")

    suffix = _suffix_for_bytes(image_bytes)
    start = time.perf_counter()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = Path(tmp.name)
    try:
        text = await asyncio.to_thread(_run_lit_parse, tmp_path, liteparse_timeout())
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

    duration_ms = int((time.perf_counter() - start) * 1000)
    meta: dict[str, Any] = {
        "engine_type": "litparse",
        "engine_label": str(ep.get("label") or "LiteParse"),
        "lit_binary": liteparse_bin(),
        "litparse_dpi": liteparse_dpi(),
        "litparse_format": liteparse_output_format(),
    }
    return text, meta, duration_ms
