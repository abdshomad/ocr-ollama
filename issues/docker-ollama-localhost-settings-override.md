# Docker — “Ollama offline” when Ollama works on the host

**Date:** 2026-05-15  
**Status:** Fixed in repo (host resolution + operator config)

## Summary

The app at `http://localhost:3036/` showed **Ollama offline**, **No models match filter**, and **`All connection attempts failed`**, while `http://localhost:11434/api/tags` on the **host** returned models normally. The backend was reaching **`http://localhost:11434` inside the Docker container** (no Ollama there), because `backend/config/settings.json` stored a loopback URL that overrode Compose’s `OLLAMA_HOST`.

## Symptoms

- UI header: `Ollama offline`
- Home model list: `No models match filter.`
- Error string (from `/api/health`): `All connection attempts failed`
- `/api/health` before fix:

```json
{
  "ollama_reachable": false,
  "ollama_host": "http://localhost:11434",
  "model_count": 0,
  "error": "All connection attempts failed",
  "status": "degraded"
}
```

- Host Ollama healthy: `curl http://localhost:11434/api/tags` → model list OK

## Analysis / evidence

### Resolution order

Documented order: `settings.json` → `OLLAMA_HOST` env → default. A saved UI/host value of `http://localhost:11434` in `settings.json` wins over `.env`:

```env
OLLAMA_HOST=http://host.docker.internal:11434
```

### Why localhost fails in Compose

| Where `localhost:11434` points | Ollama present? |
|--------------------------------|-----------------|
| Host browser / shell           | Yes             |
| `backend` container            | No              |

`docker-compose.yml` sets `OLLAMA_HOST` and `extra_hosts: host.docker.internal:host-gateway` so the backend should use `http://host.docker.internal:11434`.

### Repro (from host)

```bash
curl -s http://127.0.0.1:3036/api/health
curl -s http://127.0.0.1:3036/api/settings
# Both showed ollama_host: http://localhost:11434 while unreachable
```

### Fix verification

After code change + rebuild, with `settings.json` still containing `localhost`:

```json
{
  "ollama_reachable": true,
  "ollama_host": "http://host.docker.internal:11434",
  "model_count": 13,
  "status": "ok"
}
```

Debug log (container): `"used_env_override": true` when `settings_host` is loopback and `env_host` is `host.docker.internal`.

## Resolution

### Operator (immediate)

1. Set **Settings → Ollama host** to `http://host.docker.internal:11434` when running via Docker, **or**
2. Rely on repo fix below when `settings.json` still says `localhost` but `.env` sets `OLLAMA_HOST` to a non-loopback URL.

### Repo fix

`backend/app/settings_store.py` — `get_ollama_host()`:

- If `settings.json` has a **loopback** URL (`localhost`, `127.0.0.1`, `::1`) **and** `OLLAMA_HOST` is set to a **non-loopback** URL, use the env value (Docker-friendly).
- Otherwise keep UI-saved settings as the source of truth.

## Repo impact

| Area | Change |
|------|--------|
| `backend/app/settings_store.py` | Loopback + env override in `get_ollama_host()` |
| `backend/config/settings.json` | Gitignored; often created by Settings UI with `localhost` |
| `.env` / `.env.example` | `OLLAMA_HOST=http://host.docker.internal:11434` for Compose |

## Related

- [AGENTS.md](../AGENTS.md) — Docker + `OLLAMA_HOST`
- [issues/paddleocr-vl-ollama-load-failure.md](paddleocr-vl-ollama-load-failure.md) — separate issue after connectivity works
