import type { HistorySummary } from "../types";

const STORAGE_KEY = "ocr-run-duration-hints-v1";
const MAX_SAMPLES = 6;
/** Cap how many history rows contribute per model when seeding (newest-first lists). */
const HISTORY_SEED_PER_MODEL = 4;

export type DurationHintStore = {
  models: Record<string, number[]>;
};

export function loadDurationHintStore(): DurationHintStore {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { models: {} };
    const o = JSON.parse(raw) as unknown;
    if (!o || typeof o !== "object" || !("models" in o)) return { models: {} };
    const models = (o as { models: unknown }).models;
    if (!models || typeof models !== "object") return { models: {} };
    return { models: models as Record<string, number[]> };
  } catch {
    return { models: {} };
  }
}

export function saveDurationHintStore(store: DurationHintStore): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    /* quota / private mode */
  }
}

export function pushModelDuration(store: DurationHintStore, model: string, ms: number): DurationHintStore {
  if (!model || !Number.isFinite(ms) || ms <= 0) return store;
  const next = [...(store.models[model] ?? []), Math.round(ms)].slice(-MAX_SAMPLES);
  return { models: { ...store.models, [model]: next } };
}

export function avgMs(samples: number[] | undefined): number | null {
  if (!samples?.length) return null;
  return Math.round(samples.reduce((a, b) => a + b, 0) / samples.length);
}

/** Seed rolling hints from recent history summaries (duration fields come from stored JSON). */
export function seedHintsFromHistory(store: DurationHintStore, items: HistorySummary[]): DurationHintStore {
  const seededPerModel: Record<string, number> = {};
  let models = { ...store.models };

  const bump = (model: string, ms: number) => {
    if (!model || !Number.isFinite(ms) || ms <= 0) return;
    const n = (seededPerModel[model] ?? 0) + 1;
    if (n > HISTORY_SEED_PER_MODEL) return;
    seededPerModel[model] = n;
    const arr = [...(models[model] ?? []), Math.round(ms)].slice(-MAX_SAMPLES);
    models = { ...models, [model]: arr };
  };

  for (const item of items) {
    if (item.kind === "single" && item.duration_ms != null && item.duration_ms > 0 && item.models[0]) {
      bump(item.models[0], item.duration_ms);
    } else if (item.kind === "product_scan" && item.duration_ms != null && item.duration_ms > 0 && item.models[0]) {
      bump(item.models[0], item.duration_ms);
    } else if (item.kind === "arena" && item.model_duration_ms) {
      for (const [name, ms] of Object.entries(item.model_duration_ms)) {
        bump(name, ms);
      }
    }
  }

  return { models };
}
