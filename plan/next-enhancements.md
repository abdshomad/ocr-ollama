# Next enhancements queue

Canonical queue for **`next`** / **`n`** work. Each item uses **Idea**, **Description**, and **Status** (`pending`, `Draft`, or `completed`).

---

## Run (single OCR `/`)

### 1 — Advanced OCR pre-processing pipeline control

**Idea:** User-controlled preprocessing before inference.

**Description:** Allow optional steps (rotation, deskew, grayscale/binarization, contrast) exposed as a compact control strip on Run, applied client-side or via a small `/api/` helper, with the processed bytes sent as the OCR input. Align limits with existing `ALLOWED_CONTENT_TYPES` / size caps; persist which pipeline was used in `result/` metadata for reproducibility.

**Status:** Draft

### 2 — Run session snapshot (image + prompt + model chips)

**Idea:** One-click “snapshot” banner of the active run configuration.

**Description:** Above the results panel, show pinned chips for selected model(s), resolved prompt label (default vs override), inference backend indicator, and image source (upload vs camera, filename/thumbnail). Optionally “Copy run summary” to clipboard as Markdown for bugs and comparisons without opening History.

**Status:** pending

### 3 — Idle-cost guardrails & token/timer hints for server models

**Idea:** Surface expected cost/latency context before hitting Run.

**Description:** After model list loads, show non-blocking hints: last-seen **`duration_ms`** or a rolling average per model tier (from History or lightweight client cache keyed by session), optional **max_tokens** tooltip from backend settings, and a clear “warming up” label when **`/api/health`** or model availability flips during GPU load/unload. Reduces accidental long runs without adding new persistence requirements beyond existing history payloads.

**Status:** completed

---

## Arena (`/arena`)

### 4 — Diff-first compare mode for OCR text

**Idea:** Side-by-side or unified diff of model outputs within Arena.

**Description:** After an arena completes, toggle “Compare text” that normalizes line breaks (and optional Markdown strip) then shows a gutter diff (e.g. word-level highlighting) plus per-model character counts and common-prefix length. Keeps parity with sequential backend behavior; pure frontend over existing arena JSON payload.

**Status:** pending

### 5 — Arena presets (named model bundles)

**Idea:** Save and reload favorite multi-model lineups.

**Description:** Persist named presets locally (e.g. `localStorage`) or via new optional `GET/PUT /api/arena-presets` JSON in `backend/config/` if cross-device consistency is desired. Presets restore checkbox selection, optional per-model prompt overrides map, and show a badge when the current Arena selection matches an existing preset exactly.

**Status:** pending

### 6 — Arena progress timeline & cancel affordance

**Idea:** Per-model progress and graceful cancel while sequential runs execute.

**Description:** Extend the Arena UI with a stepped timeline (Queued → Running → Done/Error per modelName) wired to streamed or polled status if feasible; minimally, client-side placeholders between sequential `fetch` completions. Surface **AbortController** cancellation for the outstanding request batch when the user navigates away or clicks Cancel, matching backend sequential semantics without parallelizing inference.

**Status:** completed

---

## History (`/history`)

### 7 — Structured result comparison in History

**Idea:** Side-by-side comparison of structured JSON across runs.

**Description:** When viewing historical results, compare detected structured segments (tables, KV blocks, headings) across two selected runs with field-level discrepancy highlighting.

**Status:** completed

### 8 — Bulk history actions (multi-select export/delete)

**Idea:** Operate on many history rows without repeat clicks.

**Description:** Checkbox selection column, toolbar actions Export selected (.zip of JSON + optional image paths), Delete selected (`DELETE` calls with confirmation), and “Open in Arena” preload by carrying the uploaded image identifier when still available under `upload/`. Respect existing delete semantics that remove JSON only unless extended deliberately.

**Status:** pending

### 9 — History facets and full-text-ish search over OCR text

**Idea:** Find past runs faster than paging.

**Description:** Lightweight client filter bar: substring search over `ocr_text`/primary text field returned in history summaries if present; facets for date range (from `created`), model filter, inference backend (`vllm` vs `ollama`), and tier. If payloads are truncated in list view, degrade to fetch-on-expand for snippets.

**Status:** pending

### 10 — Replay run from History

**Idea:** Rehydrate Run page from a historical record.

**Description:** Each history detail view gains “Open on Run”: restore image preview (existing file serve URL), prompt, and model picker selection into `ImageContext` / router state, without auto-submitting OCR until the user presses Run — useful for debugging regressions across engine upgrades.

**Status:** pending

---

## Reference — model picker tagging (completed)

**Idea:** Model feature tagging and filtering.

**Description:** Model picker enriched with capability tags beyond `tier`/`ocr_capable`, with filter chips for handwriting, tables, latency, etc.

**Status:** completed
