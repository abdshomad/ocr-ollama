# vLLM LightOn — restart loop after GPU page start (`entrypoint.sh: Is a directory`)

**Date:** 2026-05-15  
**Status:** Fixed in repo  
**Related:** [lightonocr-vllm-integration.md](lightonocr-vllm-integration.md), [vllm-deepseek-ocr-integration.md](vllm-deepseek-ocr-integration.md)

## Summary

Starting **`vllm-lighton`** from the **GPU** page showed “Started vllm-lighton”, but the container stayed in **Restarting** forever. Logs repeated `/docker/vllm-entrypoint.sh: Is a directory` with exit code **126**. The root cause was **`docker compose` run from the backend container** using project directory **`/workspace`** on the host: Docker created `/workspace/docker/vllm-entrypoint.sh` as an empty **directory** instead of binding the real script under the repo. DeepSeek/GLM were unaffected when started from the host shell with the correct repo path.

## Symptoms

- GPU page: “Started vllm-lighton” then **LightOnOCR (GPU 1)** stuck **restarting** / **Loading…** indefinitely
- `docker ps`: `Restarting (126)` for `ocr-ollama-vllm-lighton-1`
- Logs (every few seconds):

```text
/docker/vllm-entrypoint.sh: /docker/vllm-entrypoint.sh: Is a directory
```

- `GET /api/models`: `lightonai/LightOnOCR-2-1B` with `"available": false`
- Arena/Run: LightOn listed under **Offline** (not selectable)
- Working services (started from host): DeepSeek/GLM mounts show host path  
  `/home/.../ocr-ollama/docker/vllm-entrypoint.sh` (file)

## Analysis / evidence

### How GPU start differs from `docker compose up` on the host

The backend container runs Compose via the Docker socket:

```text
docker compose -f …/docker-compose.yml --project-directory <dir> up -d vllm-lighton
```

`docker-compose.yml` had:

```yaml
COMPOSE_PROJECT_DIR: /workspace
```

`/workspace` is the **in-container** mount of the repo (`.:./workspace:ro`), **not** the host path `/home/aiserver/LABS/CPI/ocr-ollama`.

Relative volume in the vLLM service anchor:

```yaml
- ./docker/vllm-entrypoint.sh:/docker/vllm-entrypoint.sh:ro
```

Compose resolved that to the **host** path `/workspace/docker/vllm-entrypoint.sh`. That path did not exist as a file, so the engine created an empty **directory** at that location.

### Inspect (broken lighton container)

```bash
docker inspect ocr-ollama-vllm-lighton-1 --format '{{json .Mounts}}'
# bind Source: "/workspace/docker/vllm-entrypoint.sh" → Destination: "/docker/vllm-entrypoint.sh"

ls -la /workspace/docker/vllm-entrypoint.sh   # on host: directory, not a file
file /home/aiserver/LABS/CPI/ocr-ollama/docker/vllm-entrypoint.sh   # real script in repo
```

Exit **126**: entrypoint `["/bin/bash", "/docker/vllm-entrypoint.sh"]` cannot execute a directory.

### Why DeepSeek/GLM still worked

Those containers were created with `docker compose up` from the **host** repo directory, so the bind source was the real script file.

## Resolution

### 1. Host project path for GPU Compose (required)

Set in `.env` (absolute path to this repo on the **host**):

```env
COMPOSE_HOST_PROJECT_DIR=/home/aiserver/LABS/CPI/ocr-ollama
```

`docker-compose.yml` backend service now passes this to `COMPOSE_PROJECT_DIR` / `COMPOSE_FILE` so Compose bind mounts resolve on the host tree.

`backend/app/vllm_compose.py` also infers the host path from `/proc/mounts` when the backend sees the repo at `/workspace` and `COMPOSE_HOST_PROJECT_DIR` is unset.

### 2. Bake entrypoint into `vllm-lighton` image

`docker/Dockerfile.vllm-ocr` copies `docker/vllm-entrypoint.sh` into the image. The `vllm-lighton` service overrides volumes to **only** the Hugging Face cache (no entrypoint bind), so a bad host path cannot break LightOn even if Compose project dir is wrong again.

### 3. One-time host cleanup

Remove the erroneous directory Docker created:

```bash
sudo rm -rf /workspace/docker/vllm-entrypoint.sh
# optional if empty: sudo rm -rf /workspace/docker
```

### 4. Recreate the service

```bash
docker compose build backend vllm-lighton
docker compose up -d backend
docker compose --profile lighton up -d --force-recreate vllm-lighton
docker compose --profile lighton logs -f vllm-lighton
```

Healthy logs show vLLM loading `lightonai/LightOnOCR-2-1B` (not “Is a directory”).

### Operator notes

- **VRAM:** LightOn defaults to **GPU 1** (`VLLM_LIGHTON_CUDA_DEVICE=1`). Stop **GLM-OCR** on the same GPU before starting LightOn if memory is tight.
- **First start:** Weights download can take 15–30+ minutes; GPU page refreshes every 5s until `api_ready`.

## Repo impact

| File | Change |
|------|--------|
| `backend/app/vllm_compose.py` | `_infer_host_workspace_mount()`, `COMPOSE_HOST_PROJECT_DIR`, compose file path from host root; `compose_manage_enabled()` checks `/workspace/docker-compose.yml` (host paths are not visible inside backend) |
| `docker-compose.yml` | `COMPOSE_HOST_PROJECT_DIR` for backend; `vllm-lighton` volumes without entrypoint bind |
| `docker/Dockerfile.vllm-ocr` | `COPY` + `chmod` entrypoint script |
| `.env.example` | Document `COMPOSE_HOST_PROJECT_DIR` |
| `issues/lightonocr-vllm-integration.md` | Cross-link to this issue |

## Changelog

| Date | Change |
|------|--------|
| 2026-05-15 | Initial write-up after GPU-page restart loop diagnosis |
