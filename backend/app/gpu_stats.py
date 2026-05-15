from __future__ import annotations

import asyncio
import time
from typing import Any

from app.vllm_compose import docker_socket_available, run_docker

_NVIDIA_SMI_IMAGE = "nvidia/cuda:12.6.0-base-ubuntu24.04"
_CACHE_TTL_SEC = 5.0
_cache: tuple[float, list[dict[str, Any]] | None, str | None] = (0.0, None, None)


async def query_gpus() -> tuple[list[dict[str, Any]], str | None]:
    """Host GPU stats via a short-lived Docker container (requires socket)."""
    global _cache
    now = time.monotonic()
    if now - _cache[0] < _CACHE_TTL_SEC and _cache[1] is not None:
        return _cache[1], _cache[2]

    if not docker_socket_available():
        return [], "Docker socket not available"

    cmd = [
        "run",
        "--rm",
        "--gpus",
        "all",
        _NVIDIA_SMI_IMAGE,
        "nvidia-smi",
        "--query-gpu=index,name,memory.used,memory.total,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        code, out, err = await run_docker(cmd, timeout=90.0)
    except TimeoutError:
        return [], "nvidia-smi query timed out"
    except FileNotFoundError as e:
        return [], str(e)

    if code != 0:
        msg = (err or out or "nvidia-smi failed").strip()
        _cache = (now, [], msg)
        return [], msg

    gpus: list[dict[str, Any]] = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        try:
            idx = int(parts[0])
            used = int(float(parts[2]))
            total = int(float(parts[3]))
            util = int(float(parts[4])) if len(parts) > 4 and parts[4] not in ("", "[N/A]") else None
        except ValueError:
            continue
        gpus.append(
            {
                "index": idx,
                "name": parts[1],
                "memory_used_mib": used,
                "memory_total_mib": total,
                "utilization_pct": util,
            }
        )

    _cache = (now, gpus, None)
    return gpus, None
