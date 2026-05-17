import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  deleteHistoryItem,
  getHistory,
  getHistoryItem,
  uploadImageUrl,
} from "../api/client";
import { ArenaGrid } from "../components/ArenaGrid";
import { StructuredComparePanel } from "../components/StructuredComparePanel";
import type {
  ArenaResult,
  BrowserScanResult,
  HistorySummary,
  ProductScanResult,
  RunResult,
  SingleResult,
} from "../types";
import {
  historySummaryHasStructuredCompare,
  structuredFieldsFromRun,
} from "../utils/structuredCompare";

function listKindLabel(kind: HistorySummary["kind"]): string {
  switch (kind) {
    case "arena":
      return "Arena";
    case "browser_scan":
      return "Browser scan";
    case "product_scan":
      return "Product scan";
    default:
      return "Single";
  }
}

function detailKindLabel(run: RunResult): string {
  switch (run.kind) {
    case "arena":
      return "Arena";
    case "browser_scan":
      return "Browser scan";
    case "product_scan":
      return "Product scan";
    default:
      return "Single";
  }
}

export function HistoryPage() {
  const [params] = useSearchParams();
  const focusId = params.get("id");
  const [items, setItems] = useState<HistorySummary[]>([]);
  const [detail, setDetail] = useState<RunResult | null>(null);
  const [compareRuns, setCompareRuns] = useState<RunResult[] | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareLoading, setCompareLoading] = useState(false);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadList = () => {
    getHistory()
      .then((r) => setItems(r.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load history"));
  };

  useEffect(() => {
    loadList();
  }, []);

  useEffect(() => {
    if (focusId) openDetail(focusId);
  }, [focusId]);

  const openDetail = (id: string) => {
    setCompareRuns(null);
    getHistoryItem(id)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "Not found"));
  };

  const toggleCompareId = (id: string, checked: boolean) => {
    setCompareIds((prev) => {
      if (checked) return prev.includes(id) ? prev : [...prev, id];
      return prev.filter((x) => x !== id);
    });
  };

  const runStructuredCompare = async () => {
    if (compareIds.length < 2) return;
    setCompareLoading(true);
    setError(null);
    try {
      const runs = await Promise.all(compareIds.map((id) => getHistoryItem(id)));
      const withStruct = runs.filter((r) => structuredFieldsFromRun(r) !== null);
      if (withStruct.length < 2) {
        setError(
          "Need at least two runs with structured fields (product extraction, browser scan, product arena, or single run with JSON sku).",
        );
        setCompareRuns(null);
        return;
      }
      setCompareRuns(withStruct);
      setDetail(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compare failed");
      setCompareRuns(null);
    } finally {
      setCompareLoading(false);
    }
  };

  const onDelete = async (id: string) => {
    await deleteHistoryItem(id);
    setCompareIds((prev) => prev.filter((x) => x !== id));
    if (detail?.id === id) setDetail(null);
    if (compareRuns?.some((r) => r.id === id)) setCompareRuns(null);
    loadList();
  };

  const filtered = filter
    ? items.filter((i) => i.models.some((m) => m.toLowerCase().includes(filter.toLowerCase())))
    : items;

  const imageUrl = (filename: string) => (filename ? uploadImageUrl(filename) : "");

  const comparableSelected = compareIds.filter((id) => {
    const row = items.find((i) => i.id === id);
    return row && historySummaryHasStructuredCompare(row);
  }).length;

  const splitPane = Boolean(detail || compareRuns);

  return (
    <div className={`history-layout${splitPane ? " history-layout--split" : ""}`}>
      <section className="card history-pane-list">
        <h2>History</h2>
        <input
          type="search"
          placeholder="Filter by model name…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ width: "100%", maxWidth: 320 }}
        />
        <div className="row" style={{ marginTop: "0.75rem" }}>
          <button
            type="button"
            disabled={comparableSelected < 2 || compareLoading}
            onClick={() => void runStructuredCompare()}
          >
            {compareLoading ? "Loading…" : "Compare structured fields"}
          </button>
          {compareIds.length > 0 && (
            <button
              type="button"
              className="muted"
              onClick={() => {
                setCompareIds([]);
                setCompareRuns(null);
              }}
            >
              Clear selection ({compareIds.length})
            </button>
          )}
        </div>
        <p className="muted" style={{ marginTop: "0.35rem", fontSize: "0.85rem" }}>
          Select two or more runs that include extracted product fields (checkbox on eligible rows), then compare.
        </p>
        {error && <div className="error-banner">{error}</div>}
        <ul className="history-list" style={{ marginTop: "1rem" }}>
          {filtered.map((item) => {
            const selected = detail?.id === item.id;
            const canCompare = historySummaryHasStructuredCompare(item);
            return (
              <li
                key={item.id}
                className={`history-item${selected ? " history-item--selected" : ""}`}
                role="button"
                tabIndex={0}
                onClick={() => openDetail(item.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openDetail(item.id);
                  }
                }}
              >
                <div className="history-item-compare" style={{ flex: 1, minWidth: 0 }}>
                  {canCompare && (
                    <label
                      className="muted"
                      style={{ cursor: "pointer" }}
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={compareIds.includes(item.id)}
                        onChange={(e) => toggleCompareId(item.id, e.target.checked)}
                        aria-label={`Select ${item.id.slice(0, 8)} for structured compare`}
                      />
                    </label>
                  )}
                  <div style={{ minWidth: 0 }}>
                    <strong>{listKindLabel(item.kind)}</strong>
                    <span className="muted"> — {new Date(item.timestamp).toLocaleString()}</span>
                    <br />
                    <span className="muted">{item.models.join(", ")}</span>
                    <p className="muted" style={{ margin: "0.25rem 0 0" }}>
                      {item.preview || "(no text)"}
                    </p>
                  </div>
                </div>
                <div className="row">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      void onDelete(item.id);
                    }}
                  >
                    Delete
                  </button>
                </div>
              </li>
            );
          })}
          {filtered.length === 0 && <p className="muted">No history yet.</p>}
        </ul>
      </section>
      {compareRuns && compareRuns.length >= 2 && (
        <section className="card history-pane-detail">
          <StructuredComparePanel runs={compareRuns} onClose={() => setCompareRuns(null)} />
        </section>
      )}
      {detail && !compareRuns && (
        <section className="card history-pane-detail">
          <h2>
            {detailKindLabel(detail)} — {detail.id.slice(0, 8)}…
          </h2>
          {detail.image_path && (
            <img
              src={imageUrl(detail.image_path.split("/").pop() ?? "")}
              alt="Source"
              className="preview-img"
            />
          )}
          {detail.kind === "browser_scan" ? (
            <>
              <p className="muted">
                {(detail as BrowserScanResult).engine} · {(detail as BrowserScanResult).duration_ms} ms
                {" · "}
                {Math.round((detail as BrowserScanResult).confidence * 100)}% confidence
              </p>
              <dl className="scan-fields">
                <dt>SKU / Product</dt>
                <dd>{(detail as BrowserScanResult).sku}</dd>
                <dt>Expiry date</dt>
                <dd>{(detail as BrowserScanResult).expiry_date ?? "—"}</dd>
              </dl>
              {(detail as BrowserScanResult).raw_text && (
                <pre className="ocr-text" style={{ marginTop: "0.75rem" }}>
                  {(detail as BrowserScanResult).raw_text}
                </pre>
              )}
            </>
          ) : detail.kind === "product_scan" ? (
            <>
              <p className="muted">
                {(detail as ProductScanResult).model} · {(detail as ProductScanResult).pipeline} ·{" "}
                {(detail as ProductScanResult).duration_ms} ms
              </p>
              <dl className="scan-fields">
                <dt>SKU / Product</dt>
                <dd>{(detail as ProductScanResult).sku}</dd>
                <dt>Expiry date</dt>
                <dd>{(detail as ProductScanResult).expiry_date ?? "—"}</dd>
                {(detail as ProductScanResult).ocr_model && (
                  <>
                    <dt>OCR model</dt>
                    <dd>{(detail as ProductScanResult).ocr_model}</dd>
                  </>
                )}
              </dl>
              {(detail as ProductScanResult).raw_text && (
                <pre className="ocr-text" style={{ marginTop: "0.75rem" }}>
                  {(detail as ProductScanResult).raw_text}
                </pre>
              )}
            </>
          ) : detail.kind === "single" ? (
            <>
              <p className="muted">
                {(detail as SingleResult).model} · {(detail as SingleResult).duration_ms} ms
              </p>
              <pre className="ocr-text">{(detail as SingleResult).text}</pre>
            </>
          ) : (
            <ArenaGrid
              results={(detail as ArenaResult).results}
              extractionMode={(detail as ArenaResult).extraction_mode}
            />
          )}
          <button type="button" style={{ marginTop: "0.5rem" }} onClick={() => setDetail(null)}>
            Close
          </button>
        </section>
      )}
    </div>
  );
}
