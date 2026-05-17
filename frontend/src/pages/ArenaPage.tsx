import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { getModels, runArenaStream } from "../api/client";
import { ArenaGrid } from "../components/ArenaGrid";
import { ArenaProgressTimeline, type ArenaTimelineStep } from "../components/ArenaProgressTimeline";
import { ImageCapture } from "../components/ImageCapture";
import { ModelPicker } from "../components/ModelPicker";
import { useImage } from "../context/ImageContext";
import type { ArenaResult, ArenaSseEvent, OllamaModel } from "../types";
import { pickDefaultArenaModels } from "../utils/models";

function applyArenaStreamEvent(
  prev: ArenaTimelineStep[],
  e: ArenaSseEvent
): ArenaTimelineStep[] {
  if (e.type === "arena_model") {
    const next = prev.map((s) => ({ ...s }));
    const idx = next.findIndex((s) => s.model === e.model);
    if (idx < 0) return prev;
    if (e.phase === "running") {
      next[idx] = { ...next[idx], state: "running" };
    } else if (e.phase === "finished" && e.entry) {
      next[idx] = {
        ...next[idx],
        state: e.entry.error ? "error" : "done",
        entry: e.entry,
      };
    }
    return next;
  }
  if (e.type === "arena_cancelled") {
    return prev.map((s, i) => {
      const p = e.partial_results[i];
      if (p) {
        return { model: s.model, state: p.error ? "error" : "done", entry: p };
      }
      if (i >= e.next_index) {
        return { ...s, state: "skipped" };
      }
      return s;
    });
  }
  if (e.type === "arena_complete") {
    return e.record.results.map((entry, i) => ({
      model: prev[i]?.model ?? entry.model,
      state: entry.error ? "error" : "done",
      entry,
    }));
  }
  return prev;
}

export function ArenaPage() {
  const { file } = useImage();
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [timeline, setTimeline] = useState<ArenaTimelineStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ArenaResult | null>(null);
  const [productMode, setProductMode] = useState(false);
  const arenaAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      arenaAbortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    const load = () => {
      getModels()
        .then((r) => {
          setModels(r.models);
          setSelected((prev) => {
            const valid = prev.filter((id) =>
              r.models.some((m) => m.name === id && m.available === true)
            );
            if (valid.length >= 2) return valid;
            return pickDefaultArenaModels(r.models);
          });
        })
        .catch((e) => setError(e instanceof Error ? e.message : "Failed to load models"));
    };
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  const run = async () => {
    if (!file || selected.length < 2) return;
    arenaAbortRef.current?.abort();
    const ac = new AbortController();
    arenaAbortRef.current = ac;

    setLoading(true);
    setError(null);
    setResult(null);
    setTimeline(selected.map((m) => ({ model: m, state: "queued" as const })));

    const serverCancelledRef = { current: false };

    try {
      const res = await runArenaStream(file, selected, {
        extractionMode: productMode ? "product" : "text",
        signal: ac.signal,
        onEvent: (e) => {
          if (e.type === "arena_cancelled") {
            serverCancelledRef.current = true;
          }
          setTimeline((prev) => applyArenaStreamEvent(prev, e));
        },
      });
      if (res) {
        setResult(res);
      } else if (serverCancelledRef.current) {
        /* timeline already reflects partial + skipped */
      } else if (ac.signal.aborted) {
        setTimeline((prev) =>
          prev.map((s) =>
            s.state === "queued" || s.state === "running"
              ? { ...s, state: s.state === "running" ? "cancelled" : "skipped" }
              : s
          )
        );
      } else {
        setError("Arena stream ended before completion.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Arena failed");
    } finally {
      setLoading(false);
      if (arenaAbortRef.current === ac) {
        arenaAbortRef.current = null;
      }
    }
  };

  return (
    <>
      <p className="muted">
        Run the same image through multiple OCR-capable models side by side (sequential on
        server to avoid GPU OOM).
      </p>
      <ImageCapture />
      <section className="card">
        <label className="row" style={{ alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
          <input
            type="checkbox"
            checked={productMode}
            onChange={(e) => setProductMode(e.target.checked)}
          />
          <span>Extract SKU and expiry date (structured, Pydantic-validated)</span>
        </label>
        <h2>Models (2+)</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          All configured OCR models appear below. Offline entries (e.g. LightOnOCR) can be started on the{" "}
          <Link to="/gpu">GPU</Link> page; this list refreshes every 5s.
        </p>
        <ModelPicker
          models={models}
          selected={selected}
          onChange={setSelected}
          multiple
          ocrOnly
        />
      </section>
      {error && <div className="error-banner">{error}</div>}
      <ArenaProgressTimeline steps={timeline} />
      <div className="row" style={{ flexWrap: "wrap", gap: "0.5rem" }}>
        <button
          type="button"
          className="primary"
          disabled={!file || selected.length < 2 || loading}
          onClick={run}
        >
          {loading ? (
            <>
              <span className="spinner" /> Running arena…
            </>
          ) : (
            `Run arena (${selected.length} models)`
          )}
        </button>
        <button
          type="button"
          disabled={!loading}
          onClick={() => arenaAbortRef.current?.abort()}
          aria-label="Cancel arena run"
        >
          Cancel
        </button>
      </div>
      {result && (
        <section className="card">
          <h2>Arena results</h2>
          <ArenaGrid results={result.results} extractionMode={result.extraction_mode} />
        </section>
      )}
    </>
  );
}
