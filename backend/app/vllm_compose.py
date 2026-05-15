from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx

from app.vllm_registry import host_for_endpoint, load_endpoints

_DOCKER = "docker"
_SOCKET = Path("/var/run/docker.sock")
_COMPOSE_TIMEOUT = 180.0


def docker_socket_available() -> bool:
    return _SOCKET.is_socket()


def compose_manage_enabled() -> bool:
    project_dir = _project_dir()
    compose_file = _compose_file()
    return docker_socket_available() and bool(project_dir and compose_file and Path(compose_file).is_file())


def _project_dir() -> str:
    return os.getenv("COMPOSE_PROJECT_DIR", "").strip()


def _compose_file() -> str:
    explicit = os.getenv("COMPOSE_FILE", "").strip()
    if explicit:
        return explicit
    root = _project_dir()
    if root:
        return str(Path(root) / "docker-compose.yml")
    return ""


def _compose_base_cmd() -> list[str]:
    compose_file = _compose_file()
    project_dir = _project_dir()
    cmd = [_DOCKER, "compose", "-f", compose_file, "--project-directory", project_dir]
    project_name = os.getenv("COMPOSE_PROJECT_NAME", "").strip()
    if project_name:
        cmd.extend(["-p", project_name])
    return cmd


def endpoint_by_id(service_id: str) -> dict[str, Any] | None:
    for ep in load_endpoints():
        if str(ep.get("id")) == service_id:
            return ep
    return None


def gpu_device_for_endpoint(ep: dict[str, Any]) -> int:
    ep_id = str(ep.get("id", ""))
    if ep_id == "deepseek":
        return int(os.getenv("VLLM_DEEPSEEK_CUDA_DEVICE", str(ep.get("gpu_device", 0))))
    if ep_id == "glm":
        return int(os.getenv("VLLM_GLM_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    return int(ep.get("gpu_device", 0))


async def run_docker(args: list[str], *, timeout: float = 60.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        _DOCKER,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    return (
        proc.returncode or 0,
        stdout_b.decode(errors="replace"),
        stderr_b.decode(errors="replace"),
    )


async def _run_compose(*args: str, timeout: float = _COMPOSE_TIMEOUT) -> tuple[int, str, str]:
    if not compose_manage_enabled():
        raise RuntimeError("Docker Compose management is not configured")
    cmd = [*_compose_base_cmd(), *args]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise TimeoutError(f"docker compose {' '.join(args)} timed out") from None
    return (
        proc.returncode or 0,
        stdout_b.decode(errors="replace"),
        stderr_b.decode(errors="replace"),
    )


async def _compose_ps_map() -> dict[str, dict[str, str]]:
    try:
        code, out, _ = await _run_compose("ps", "-a", "--format", "json", timeout=30.0)
    except (RuntimeError, TimeoutError, FileNotFoundError):
        return {}
    if code != 0 or not out.strip():
        return {}
    by_service: dict[str, dict[str, str]] = {}
    for line in out.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        service = str(row.get("Service") or row.get("Name") or "")
        if service:
            by_service[service] = row
    return by_service


async def _api_ready(host: str) -> bool:
    if not host:
        return False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{host.rstrip('/')}/v1/models")
            return r.status_code == 200
    except httpx.HTTPError:
        return False


async def list_service_statuses() -> list[dict[str, Any]]:
    ps_map = await _compose_ps_map()
    out: list[dict[str, Any]] = []
    for ep in load_endpoints():
        service = str(ep.get("compose_service") or "")
        row = ps_map.get(service, {})
        state = str(row.get("State") or "not_created").lower()
        health = str(row.get("Health") or "")
        host = host_for_endpoint(ep)
        api_ready = await _api_ready(host) if state == "running" else False
        docker_state = state
        if state == "running" and health and health.lower() not in ("healthy", ""):
            if not api_ready:
                docker_state = "starting"
        out.append(
            {
                "id": str(ep.get("id", "")),
                "label": str(ep.get("label") or ep.get("id") or ""),
                "compose_service": service,
                "gpu_device": gpu_device_for_endpoint(ep),
                "port": int(ep.get("port") or 0),
                "models": list(ep.get("models") or []),
                "docker_state": docker_state,
                "health": health or None,
                "api_ready": api_ready,
                "container_id": (str(row.get("ID") or row.get("Id") or "")) or None,
            }
        )
    return out


async def start_service(service_id: str) -> dict[str, Any]:
    ep = endpoint_by_id(service_id)
    if not ep:
        raise ValueError(f"Unknown service: {service_id}")
    compose_name = str(ep.get("compose_service") or "")
    if not compose_name:
        raise ValueError(f"No compose service for {service_id}")

    code, out, err = await _run_compose("up", "-d", compose_name)
    if code != 0:
        raise RuntimeError((err or out or "docker compose up failed").strip())

    statuses = await list_service_statuses()
    match = next((s for s in statuses if s["id"] == service_id), None)
    return {
        "ok": True,
        "action": "start",
        "service_id": service_id,
        "message": f"Started {compose_name}",
        "service": match,
    }


async def stop_service(service_id: str) -> dict[str, Any]:
    ep = endpoint_by_id(service_id)
    if not ep:
        raise ValueError(f"Unknown service: {service_id}")
    compose_name = str(ep.get("compose_service") or "")
    if not compose_name:
        raise ValueError(f"No compose service for {service_id}")

    code, out, err = await _run_compose("stop", compose_name, timeout=120.0)
    if code != 0:
        raise RuntimeError((err or out or "docker compose stop failed").strip())

    statuses = await list_service_statuses()
    match = next((s for s in statuses if s["id"] == service_id), None)
    return {
        "ok": True,
        "action": "stop",
        "service_id": service_id,
        "message": f"Stopped {compose_name} (GPU memory released)",
        "service": match,
    }


async def gpu_dashboard() -> dict[str, Any]:
    from app.gpu_stats import query_gpus

    manage = compose_manage_enabled()
    message = None
    if not manage:
        if not docker_socket_available():
            message = "Mount /var/run/docker.sock and set COMPOSE_PROJECT_DIR to manage models from the UI."
        else:
            message = "Set COMPOSE_PROJECT_DIR to the repo root (see docker-compose.yml backend service)."

    gpus, gpu_err = await query_gpus() if manage else ([], None)
    services = await list_service_statuses() if manage else await _services_without_compose()

    return {
        "manage_enabled": manage,
        "manage_message": message,
        "gpus": gpus,
        "gpu_query_error": gpu_err,
        "services": services,
        "gpu_memory_utilization": float(os.getenv("VLLM_GPU_MEMORY_UTILIZATION", "0.92")),
    }


async def _services_without_compose() -> list[dict[str, Any]]:
    """Status from HTTP only when compose control is unavailable."""
    out: list[dict[str, Any]] = []
    for ep in load_endpoints():
        host = host_for_endpoint(ep)
        api_ready = await _api_ready(host)
        out.append(
            {
                "id": str(ep.get("id", "")),
                "label": str(ep.get("label") or ep.get("id") or ""),
                "compose_service": str(ep.get("compose_service") or ""),
                "gpu_device": gpu_device_for_endpoint(ep),
                "port": int(ep.get("port") or 0),
                "models": list(ep.get("models") or []),
                "docker_state": "running" if api_ready else "unknown",
                "health": None,
                "api_ready": api_ready,
                "container_id": None,
            }
        )
    return out
