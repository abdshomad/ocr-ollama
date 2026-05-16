from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx

from app import gpu_device_assignments_store
from app.engine_registry import host_for_engine, load_all_endpoints
from app.vllm_registry import host_for_endpoint

_DOCKER = "docker"
_SOCKET = Path("/var/run/docker.sock")
_COMPOSE_TIMEOUT = 180.0
# Repo bind-mount inside backend (host paths from env are not visible in this container).
_WORKSPACE_COMPOSE = Path("/workspace/docker-compose.yml")


def docker_socket_available() -> bool:
    return _SOCKET.is_socket()


def compose_manage_enabled() -> bool:
    if not docker_socket_available():
        return False
    if not _project_dir():
        return False
    # docker compose uses host paths; validate repo via /workspace mount, not COMPOSE_FILE on disk here.
    if _WORKSPACE_COMPOSE.is_file():
        return True
    compose_file = _compose_file()
    return bool(compose_file and Path(compose_file).is_file())


def _infer_host_workspace_mount() -> str:
    """Host repo path when backend sees the repo at /workspace (GPU page compose)."""
    try:
        for line in Path("/proc/mounts").read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "/workspace":
                host_src = parts[0]
                if host_src and host_src != "overlay" and Path(host_src).is_dir():
                    return host_src
    except OSError:
        pass
    return ""


def _project_dir() -> str:
    host = os.getenv("COMPOSE_HOST_PROJECT_DIR", "").strip()
    if host:
        return host
    env = os.getenv("COMPOSE_PROJECT_DIR", "").strip()
    if env in ("", "/workspace"):
        inferred = _infer_host_workspace_mount()
        if inferred:
            return inferred
    return env


def _compose_file() -> str:
    root = _project_dir()
    if root:
        host_compose = Path(root) / "docker-compose.yml"
        if host_compose.is_file():
            return str(host_compose)
    explicit = os.getenv("COMPOSE_FILE", "").strip()
    if explicit and Path(explicit).is_file():
        return explicit
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
    for ep in load_all_endpoints():
        if str(ep.get("id")) == service_id:
            return ep
    return None


_CUDA_DEVICE_ENV_FOR_ENDPOINT_ID: dict[str, str] = {
    "deepseek": "VLLM_DEEPSEEK_CUDA_DEVICE",
    "deepseek-ocr2": "VLLM_DEEPSEEK_OCR2_CUDA_DEVICE",
    "glm": "VLLM_GLM_CUDA_DEVICE",
    "lighton": "VLLM_LIGHTON_CUDA_DEVICE",
    "chandra": "VLLM_CHANDRA_CUDA_DEVICE",
    "gemma4": "VLLM_GEMMA4_CUDA_DEVICE",
    "qwen3vl": "VLLM_QWEN3_VL_CUDA_DEVICE",
    "hunyuanocr": "VLLM_HUNYUAN_OCR_CUDA_DEVICE",
    "paddleocr-vl": "VLLM_PADDLEOCR_VL_CUDA_DEVICE",
    "dotsmocr": "VLLM_DOTS_MOCR_CUDA_DEVICE",
    "phi4multimodal": "VLLM_PHI4_MM_CUDA_DEVICE",
    "rolmocr": "VLLM_ROLMOCR_CUDA_DEVICE",
    "numarkdown": "VLLM_NUMARKDOWN_CUDA_DEVICE",
    "qwen3omni": "VLLM_QWEN3_OMNI_CUDA_DEVICE",
    "smoldocling": "VLLM_SMOLDOCLING_CUDA_DEVICE",
    "mineru-diffusion": "MINERU_DIFFUSION_CUDA_DEVICE",
    "nemotron-ocr-v2": "NEMOTRON_OCR_CUDA_DEVICE",
    "easyocr": "EASYOCR_CUDA_DEVICE",
    "doctr": "DOCTR_CUDA_DEVICE",
    "paddleocr": "PADDLEOCR_CUDA_DEVICE",
    "docling": "DOCLING_CUDA_DEVICE",
    "lanyocr": "LANYOCR_CUDA_DEVICE",
}


def _compose_cuda_assignment_env_for_subprocess() -> dict[str, str]:
    """Inject UI-persisted device indices so compose substitutions override host .env defaults."""
    out: dict[str, str] = {}
    for sid, gpu_i in gpu_device_assignments_store.load_assignments().items():
        env_key = _CUDA_DEVICE_ENV_FOR_ENDPOINT_ID.get(str(sid).strip())
        if env_key:
            out[env_key] = str(int(gpu_i))
    return out


def _profiles_for_endpoint(ep: dict[str, Any]) -> list[str]:
    raw = ep.get("compose_profile")
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(p) for p in raw if p]
    return [str(raw)]


def _compose_profile_args(*, endpoints: list[dict[str, Any]] | None = None) -> list[str]:
    profiles: set[str] = set()
    for ep in endpoints if endpoints is not None else load_all_endpoints():
        profiles.update(_profiles_for_endpoint(ep))
    args: list[str] = []
    for name in sorted(profiles):
        args.extend(["--profile", name])
    return args


def gpu_device_for_endpoint(ep: dict[str, Any]) -> int:
    ep_id = str(ep.get("id", ""))
    if ep_id == "deepseek":
        return int(os.getenv("VLLM_DEEPSEEK_CUDA_DEVICE", str(ep.get("gpu_device", 0))))
    if ep_id == "deepseek-ocr2":
        return int(os.getenv("VLLM_DEEPSEEK_OCR2_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "glm":
        return int(os.getenv("VLLM_GLM_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "lighton":
        return int(os.getenv("VLLM_LIGHTON_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "chandra":
        return int(os.getenv("VLLM_CHANDRA_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "gemma4":
        return int(os.getenv("VLLM_GEMMA4_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "qwen3vl":
        return int(os.getenv("VLLM_QWEN3_VL_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "hunyuanocr":
        return int(os.getenv("VLLM_HUNYUAN_OCR_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "paddleocr-vl":
        return int(os.getenv("VLLM_PADDLEOCR_VL_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "dotsmocr":
        return int(os.getenv("VLLM_DOTS_MOCR_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "phi4multimodal":
        return int(os.getenv("VLLM_PHI4_MM_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "rolmocr":
        return int(os.getenv("VLLM_ROLMOCR_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "numarkdown":
        return int(os.getenv("VLLM_NUMARKDOWN_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "qwen3omni":
        return int(os.getenv("VLLM_QWEN3_OMNI_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "smoldocling":
        return int(os.getenv("VLLM_SMOLDOCLING_CUDA_DEVICE", str(ep.get("gpu_device", 1))))
    if ep_id == "mineru-diffusion":
        return int(os.getenv("MINERU_DIFFUSION_CUDA_DEVICE", str(ep.get("gpu_device", 0))))
    if ep_id == "nemotron-ocr-v2":
        return int(os.getenv("NEMOTRON_OCR_CUDA_DEVICE", str(ep.get("gpu_device", 0))))
    if ep_id == "easyocr":
        return int(os.getenv("EASYOCR_CUDA_DEVICE", str(ep.get("gpu_device", -1))))
    if ep_id == "doctr":
        return int(os.getenv("DOCTR_CUDA_DEVICE", str(ep.get("gpu_device", -1))))
    if ep_id == "paddleocr":
        return int(os.getenv("PADDLEOCR_CUDA_DEVICE", str(ep.get("gpu_device", -1))))
    if ep_id == "docling":
        return int(os.getenv("DOCLING_CUDA_DEVICE", str(ep.get("gpu_device", -1))))
    if ep_id == "lanyocr":
        return int(os.getenv("LANYOCR_CUDA_DEVICE", str(ep.get("gpu_device", -1))))
    return int(ep.get("gpu_device", 0))


def cuda_device_env_var_for_endpoint_id(endpoint_id: str) -> str | None:
    return _CUDA_DEVICE_ENV_FOR_ENDPOINT_ID.get(str(endpoint_id).strip()) or None


def resolved_gpu_device_for_endpoint(ep: dict[str, Any]) -> int:
    sid = str(ep.get("id", "")).strip()
    if sid:
        assigned = gpu_device_assignments_store.assignment_for(sid)
        if assigned is not None:
            return int(assigned)
    return gpu_device_for_endpoint(ep)


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


async def _run_compose(
    *args: str,
    timeout: float = _COMPOSE_TIMEOUT,
    profile_args: list[str] | None = None,
) -> tuple[int, str, str]:
    if not compose_manage_enabled():
        raise RuntimeError("Docker Compose management is not configured")
    profiles = profile_args if profile_args is not None else _compose_profile_args()
    cmd = [*_compose_base_cmd(), *profiles, *args]
    env = {**os.environ, **_compose_cuda_assignment_env_for_subprocess()}
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
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


async def _probe_runtime(host: str, *, engine_type: str | None = None) -> tuple[bool, list[str]]:
    """HTTP reachability plus model IDs reported by the running service (vLLM or /health)."""
    if not host:
        return False, []
    base = host.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            if engine_type in (
                "nano_dvlm",
                "nemotron",
                "rapidocr",
                "onnxtr",
                "easyocr",
                "doctr",
                "paddleocr",
                "docling",
                "lanyocr",
            ):
                r = await client.get(f"{base}/health")
                if r.status_code != 200:
                    return False, []
                body = r.json()
                ready = bool(body.get("model_loaded"))
                mid = body.get("model_id")
                models = [str(mid)] if mid else []
                return ready, models
            r = await client.get(f"{base}/v1/models")
            if r.status_code != 200:
                return False, []
            body = r.json()
            models = [str(x["id"]) for x in (body.get("data") or []) if x.get("id")]
            return True, models
    except httpx.HTTPError:
        return False, []


def _host_for_service(ep: dict[str, Any]) -> str:
    if ep.get("type") in (
        "nano_dvlm",
        "nemotron",
        "rapidocr",
        "onnxtr",
        "easyocr",
        "doctr",
        "paddleocr",
        "docling",
        "lanyocr",
    ):
        return host_for_engine(ep)
    return host_for_endpoint(ep)


async def _endpoint_dashboard_row(
    ep: dict[str, Any],
    *,
    ps_map: dict[str, dict[str, str]] | None,
    probe: bool,
) -> dict[str, Any]:
    from app import liteparse_client

    if str(ep.get("type") or "") == "litparse":
        ready: bool | None
        if probe:
            ready = await asyncio.to_thread(liteparse_client.lit_cli_available)
        else:
            ready = None
        return {
            "id": str(ep.get("id", "")),
            "label": str(ep.get("label") or ep.get("id") or ""),
            "compose_service": "",
            "gpu_device": resolved_gpu_device_for_endpoint(ep),
            "gpu_assignment_supported": False,
            "port": int(ep.get("port") or 0),
            "models": list(ep.get("models") or []),
            "docker_state": "local_cli",
            "health": None,
            "api_ready": ready,
            "container_id": None,
        }

    host = _host_for_service(ep)
    cfg_models = list(ep.get("models") or [])

    if ps_map is not None:
        service = str(ep.get("compose_service") or "")
        row = ps_map.get(service, {})
        state = str(row.get("State") or "not_created").lower()
        health = str(row.get("Health") or "")
        api_ready: bool | None = False
        live_models: list[str] = []
        if state == "running":
            if probe:
                probed_ready, live_models = await _probe_runtime(host, engine_type=str(ep.get("type") or ""))
                api_ready = probed_ready
            else:
                api_ready = None
        models_out = live_models if live_models else cfg_models
        docker_state = state
        if probe and state == "running" and health and health.lower() not in ("healthy", ""):
            if not api_ready:
                docker_state = "starting"
        elif not probe and state == "running" and health and health.lower() not in ("healthy", ""):
            docker_state = "starting"
        return {
            "id": str(ep.get("id", "")),
            "label": str(ep.get("label") or ep.get("id") or ""),
            "compose_service": service,
            "gpu_device": resolved_gpu_device_for_endpoint(ep),
            "gpu_assignment_supported": cuda_device_env_var_for_endpoint_id(str(ep.get("id", ""))) is not None,
            "port": int(ep.get("port") or 0),
            "models": models_out,
            "docker_state": docker_state,
            "health": health or None,
            "api_ready": api_ready,
            "container_id": (str(row.get("ID") or row.get("Id") or "")) or None,
        }

    api_ready = None
    live_models: list[str] = []
    if probe:
        probed_ready, live_models = await _probe_runtime(host, engine_type=str(ep.get("type") or ""))
        api_ready = probed_ready
    models_out = live_models if live_models else cfg_models
    return {
        "id": str(ep.get("id", "")),
        "label": str(ep.get("label") or ep.get("id") or ""),
        "compose_service": str(ep.get("compose_service") or ""),
        "gpu_device": resolved_gpu_device_for_endpoint(ep),
        "gpu_assignment_supported": cuda_device_env_var_for_endpoint_id(str(ep.get("id", ""))) is not None,
        "port": int(ep.get("port") or 0),
        "models": models_out,
        "docker_state": "running" if api_ready else "unknown",
        "health": None,
        "api_ready": api_ready,
        "container_id": None,
    }


async def list_service_statuses_fast() -> list[dict[str, Any]]:
    ps_map = await _compose_ps_map()
    endpoints = load_all_endpoints()
    return list(
        await asyncio.gather(
            *[_endpoint_dashboard_row(ep, ps_map=ps_map, probe=False) for ep in endpoints]
        )
    )


async def list_service_statuses_probed() -> list[dict[str, Any]]:
    ps_map = await _compose_ps_map()
    endpoints = load_all_endpoints()
    return list(
        await asyncio.gather(
            *[_endpoint_dashboard_row(ep, ps_map=ps_map, probe=True) for ep in endpoints]
        )
    )


async def list_service_statuses() -> list[dict[str, Any]]:
    return await list_service_statuses_probed()


async def start_service(service_id: str) -> dict[str, Any]:
    ep = endpoint_by_id(service_id)
    if not ep:
        raise ValueError(f"Unknown service: {service_id}")
    compose_name = str(ep.get("compose_service") or "")
    if not compose_name:
        raise ValueError(f"No compose service for {service_id}")

    profile_args = _compose_profile_args(endpoints=[ep])
    code, out, err = await _run_compose("up", "-d", compose_name, profile_args=profile_args)
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


async def recycle_service(service_id: str) -> dict[str, Any]:
    await stop_service(service_id)
    inner = await start_service(service_id)
    return {
        **inner,
        "action": "recycle",
        "message": f"Stopped and restarted {service_id} (GPU remap applied)",
    }


async def stop_all_running_services() -> dict[str, Any]:
    """Unload every compose-managed service that Docker reports running or starting."""
    from app.model_availability import merge_gpu_services

    fast = await list_service_statuses_fast()
    statuses = merge_gpu_services(fast)
    stopping = []
    errors: list[dict[str, str]] = []
    for st in statuses:
        sid = str(st.get("id") or "")
        if not sid or not str(st.get("compose_service") or "").strip():
            continue
        state = str(st.get("docker_state") or "").lower()
        if state not in {"running", "starting"}:
            continue
        try:
            await stop_service(sid)
            stopping.append(sid)
        except (ValueError, RuntimeError, TimeoutError) as e:
            errors.append({"service_id": sid, "detail": str(e)})
    return {
        "ok": len(errors) == 0,
        "action": "stop_all",
        "stopped_service_ids": stopping,
        "errors": errors or None,
        "message": f"Stopped {len(stopping)} service(s)" + (f" ({len(errors)} errors)" if errors else ""),
    }


async def stop_running_services_on_gpu(gpu_index: int) -> dict[str, Any]:
    from app.model_availability import merge_gpu_services

    fast = await list_service_statuses_fast()
    statuses = merge_gpu_services(fast)
    stopping = []
    errors: list[dict[str, str]] = []
    for st in statuses:
        sid = str(st.get("id") or "")
        if not sid or not str(st.get("compose_service") or "").strip():
            continue
        if int(st.get("gpu_device", -999)) != gpu_index:
            continue
        state = str(st.get("docker_state") or "").lower()
        if state not in {"running", "starting"}:
            continue
        try:
            await stop_service(sid)
            stopping.append(sid)
        except (ValueError, RuntimeError, TimeoutError) as e:
            errors.append({"service_id": sid, "detail": str(e)})
    return {
        "ok": len(errors) == 0,
        "action": "stop_gpu",
        "gpu_index": gpu_index,
        "stopped_service_ids": stopping,
        "errors": errors or None,
        "message": f"Stopped {len(stopping)} service(s) on GPU {gpu_index}"
        + (f" ({len(errors)} errors)" if errors else ""),
    }


async def stop_service(service_id: str) -> dict[str, Any]:
    ep = endpoint_by_id(service_id)
    if not ep:
        raise ValueError(f"Unknown service: {service_id}")
    compose_name = str(ep.get("compose_service") or "")
    if not compose_name:
        raise ValueError(f"No compose service for {service_id}")

    profile_args = _compose_profile_args(endpoints=[ep])
    code, out, err = await _run_compose("stop", compose_name, timeout=120.0, profile_args=profile_args)
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


async def gpu_dashboard(*, background_tasks: Any | None = None) -> dict[str, Any]:
    from app.gpu_stats import query_gpus
    from app.model_availability import merge_gpu_services, schedule_gpu_api_refresh

    manage = compose_manage_enabled()
    message = None
    if not manage:
        if not docker_socket_available():
            message = (
                "Mount /var/run/docker.sock and set COMPOSE_HOST_PROJECT_DIR in .env "
                "to manage models from the UI."
            )
        elif not _project_dir():
            message = (
                "Set COMPOSE_HOST_PROJECT_DIR in .env to the host repo root "
                "(absolute path, e.g. /home/you/ocr-ollama), then recreate the backend container."
            )
        else:
            message = "Repo mount missing at /workspace — rebuild stack from this repository."

    gpus, gpu_err = await query_gpus() if manage else ([], None)
    if manage:
        fast = await list_service_statuses_fast()
        services = merge_gpu_services(fast)
    else:
        fast = await _services_without_compose_fast()
        services = merge_gpu_services(fast)

    schedule_gpu_api_refresh(background_tasks)

    return {
        "manage_enabled": manage,
        "manage_message": message,
        "gpus": gpus,
        "gpu_query_error": gpu_err,
        "services": services,
        "gpu_memory_utilization": float(os.getenv("VLLM_GPU_MEMORY_UTILIZATION", "0.92")),
        "gpu_device_assignments": gpu_device_assignments_store.load_assignments(),
    }


async def _services_without_compose_fast() -> list[dict[str, Any]]:
    endpoints = load_all_endpoints()
    return list(
        await asyncio.gather(
            *[_endpoint_dashboard_row(ep, ps_map=None, probe=False) for ep in endpoints]
        )
    )


async def _services_without_compose() -> list[dict[str, Any]]:
    endpoints = load_all_endpoints()
    return list(
        await asyncio.gather(
            *[_endpoint_dashboard_row(ep, ps_map=None, probe=True) for ep in endpoints]
        )
    )
