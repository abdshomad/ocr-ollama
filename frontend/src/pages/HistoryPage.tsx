import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  deleteHistoryItem,
  getHistory,
  getHistoryItem,
  uploadImageUrl,
} from "../api/client";
import { ArenaGrid } from "../components/ArenaGrid";
import type { ArenaResult, BrowserScanResult, HistorySummary, RunResult, SingleResult } from "../types";

export function HistoryPage() {
  const [params] = useSearchParams();
  const focusId = params.get("id");
  const [items, setItems] = useState<HistorySummary[]>([]);
  const [detail, setDetail] = useState<RunResult | null>(null);
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
    getHistoryItem(id)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "Not found"));
  };

  const onDelete = async (id: string) => {
    await deleteHistoryItem(id);
    if (detail?.id === id) setDetail(null);
    loadList();
  };

  const filtered = filter
    ? items.filter((i) => i.models.some((m) => m.toLowerCase().includes(filter.toLowerCase())))
    : items;

  const imageUrl = (filename: string) => (filename ? uploadImageUrl(filename) : "");

  return (
    <div className={`history-layout${detail ? " history-layout--split" : ""}`}>
      <section className="card history-pane-list">
        <h2>History</h2>
        <input
          type="search"
          placeholder="Filter by model name…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ width: "100%", maxWidth: 320 }}
        />
        {error && <div className="error-banner">{error}</div>}
        <ul className="history-list" style={{ marginTop: "1rem" }}>
          {filtered.map((item) => {
            const selected = detail?.id === item.id;
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
                <div>
                  <strong>
                    {item.kind === "arena" ? "Arena" : item.kind === "browser_scan" ? "Browser scan" : "Single"}
                  </strong>
                  <span className="muted"> — {new Date(item.timestamp).toLocaleString()}</span>
                  <br />
                  <span className="muted">{item.models.join(", ")}</span>
                  <p className="muted" style={{ margin: "0.25rem 0 0" }}>
                    {item.preview || "(no text)"}
                  </p>
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
      {detail && (
        <section className="card history-pane-detail">
          <h2>
            {detail.kind === "arena"
              ? "Arena"
              : detail.kind === "browser_scan"
                ? "Browser scan"
                : "Single"}{" "}
            — {detail.id.slice(0, 8)}…
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
