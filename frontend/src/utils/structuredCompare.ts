import type {
  ArenaResult,
  BrowserScanResult,
  HistorySummary,
  ProductScanResult,
  RunResult,
  SingleResult,
} from "../types";

export type FlatStructured = Record<string, string>;

function formatExpiry(v: unknown): string {
  if (v == null || v === "") return "—";
  return String(v);
}

function tryParseProductLikeJson(text: string): { sku: string; expiry_date?: string | null } | null {
  const t = text.trim();
  if (!t.startsWith("{")) return null;
  try {
    const obj = JSON.parse(t) as Record<string, unknown>;
    const sku = obj.sku;
    if (typeof sku !== "string" || !sku.trim()) return null;
    const exp = obj.expiry_date;
    if (exp === undefined || exp === null) return { sku: sku.trim(), expiry_date: null };
    return { sku: sku.trim(), expiry_date: String(exp) };
  } catch {
    return null;
  }
}

/** Flatten structured key/value pairs from a saved run, if any. */
export function structuredFieldsFromRun(run: RunResult): FlatStructured | null {
  if (run.kind === "product_scan") {
    const r = run as ProductScanResult;
    return {
      "SKU / Product": r.sku,
      "Expiry date": formatExpiry(r.expiry_date),
      Model: r.model,
      Pipeline: r.pipeline,
    };
  }
  if (run.kind === "browser_scan") {
    const r = run as BrowserScanResult;
    return {
      "SKU / Product": r.sku,
      "Expiry date": formatExpiry(r.expiry_date),
      Engine: r.engine,
      Confidence: `${Math.round(r.confidence * 100)}%`,
    };
  }
  if (run.kind === "arena" && run.extraction_mode === "product") {
    const r = run as ArenaResult;
    const out: FlatStructured = {};
    for (const e of r.results) {
      const label = e.model;
      if (e.error) {
        out[`${label} · status`] = `Error: ${e.error}`;
        continue;
      }
      out[`${label} · SKU`] = e.sku ?? "—";
      out[`${label} · Expiry`] = formatExpiry(e.expiry_date);
    }
    return Object.keys(out).length ? out : null;
  }
  if (run.kind === "single") {
    const r = run as SingleResult;
    const parsed = tryParseProductLikeJson(r.text);
    if (parsed) {
      return {
        "SKU / Product": parsed.sku,
        "Expiry date": formatExpiry(parsed.expiry_date),
      };
    }
  }
  return null;
}

export function unionStructuredKeys(runs: RunResult[]): string[] {
  const keys = new Set<string>();
  for (const run of runs) {
    const flat = structuredFieldsFromRun(run);
    if (!flat) continue;
    for (const k of Object.keys(flat)) keys.add(k);
  }
  return Array.from(keys).sort((a, b) => a.localeCompare(b));
}

/** Highlight cells whose trimmed value differs from the first column (reference run). */
export function diffFromFirstColumn(values: string[]): boolean[] {
  const base = (values[0] ?? "—").trim();
  return values.map((v) => (v ?? "—").trim() !== base);
}

export function historySummaryHasStructuredCompare(item: HistorySummary): boolean {
  if (item.kind === "product_scan" || item.kind === "browser_scan") return true;
  return item.kind === "arena" && item.extraction_mode === "product";
}
