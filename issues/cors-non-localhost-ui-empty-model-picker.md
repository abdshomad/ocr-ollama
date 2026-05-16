# CORS — hosted UI (`*.demoin.id` etc.) shows “No models match filter”

**Date:** 2026-05-16  
**Status:** Fixed in repo (configurable CORS)

## Summary

When the React UI is loaded from a **non-localhost** origin (for example `https://something.demoin.id`) and the browser calls the FastAPI API **cross-origin** (different scheme, host, or port), the backend’s `CORSMiddleware` rejected those requests because `allow_origins` was hard-coded to `http://localhost:5173` and `http://127.0.0.1:5173` only. Fetches to `/api/models` failed, the frontend kept an empty `models` array, and **Run** and **Arena** showed **“No models match filter.”** The fix is environment-driven: `CORS_ALLOW_ORIGINS` and `CORS_ALLOW_ORIGIN_REGEX` in `backend/app/config.py`, wired in `backend/app/main.py`.

## Symptoms

- Model list: **No models match filter.** on `/` and `/arena`
- Browser DevTools → Network: failed `/api/*` requests, often with CORS errors in the console when the UI origin is not allowed
- Same deployment works when opening the app from localhost (5173 or same-origin nginx)

## Analysis / evidence

- `ModelPicker` shows “No models match filter.” when `models.length === 0` after `ocrOnly` filter ([`frontend/src/components/ModelPicker.tsx`](../frontend/src/components/ModelPicker.tsx)).
- `HomePage` / `ArenaPage` load models via `fetch("/api/models", …)` relative to the page origin; if the static app and API are on different origins, the browser enforces CORS on the response.
- Prior `CORSMiddleware` configuration allowed only Vite dev origins, not arbitrary production or tunnel domains.

## Resolution

1. **Set CORS on the backend** (restart required):

   **Wildcard subdomain pattern (typical for `*.demoin.id`):**

   ```bash
   CORS_ALLOW_ORIGIN_REGEX=https://.*\.demoin\.id(:[0-9]+)?$
   ```

   Adjust for `http` or omit the port group if you always use default ports.

   **Explicit list** (include Vite if you still dev locally):

   ```bash
   CORS_ALLOW_ORIGINS=https://your-host.demoin.id,http://localhost:5173,http://127.0.0.1:5173
   ```

   If `CORS_ALLOW_ORIGINS` is set, **only** those origins are used (defaults are not merged). Leave it unset to keep the previous localhost-only defaults.

2. **Docker Compose:** ensure the `backend` service receives these variables (e.g. under `environment:` or `env_file`); `.env` alone does not pass arbitrary keys unless substituted into compose.

3. **Same-origin hosting:** if nginx serves both the SPA and `/api/` on one host (e.g. only `https://app.demoin.id`), normal navigation does not trigger CORS for same-origin `/api` calls; if you still see empty models, inspect `/api/models` response body and backend inference reachability separately.

## Repo impact

- [`backend/app/config.py`](../backend/app/config.py): `cors_allow_origins()`, `cors_allow_origin_regex()`
- [`backend/app/main.py`](../backend/app/main.py): `CORSMiddleware(allow_origins=…, allow_origin_regex=…)`
- [`.env.example`](../.env.example): documents `CORS_ALLOW_ORIGINS` / `CORS_ALLOW_ORIGIN_REGEX`
