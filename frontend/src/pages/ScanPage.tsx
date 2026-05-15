import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { saveBrowserScan } from "../api/client";
import { checkChromeAiCapabilities, isChromeAiAvailable } from "../browser-ocr/chromeAi";
import type { EngineId, ScanExtraction } from "../browser-ocr/types";
import { ImageCapture } from "../components/ImageCapture";
import { useImage } from "../context/ImageContext";
import { useBrowserOcr, useChromeAiPreference } from "../hooks/useBrowserOcr";
import type { BrowserScanResult } from "../types";

const ENGINE_OPTIONS: { id: EngineId; label: string; hint: string }[] = [
  { id: "auto", label: "Auto", hint: "TrOCR on capable devices, else Tesseract" },
  { id: "trocr", label: "TrOCR", hint: "Transformers.js handwritten OCR (~100MB)" },
  { id: "paligemma", label: "PaliGemma (slow)", hint: "High quality VLM (~1–2GB download)" },
  { id: "tesseract", label: "Fast scan", hint: "Tesseract.js for high-contrast text" },
];

export function ScanPage() {
  const { file } = useImage();
  const [engine, setEngine] = useState<EngineId>(
    () => (localStorage.getItem("browser-ocr-engine") as EngineId) || "auto"
  );
  const [chromeAi, setChromeAi] = useChromeAiPreference();
  const [chromeAiAvailable, setChromeAiAvailable] = useState(false);
  const [result, setResult] = useState<ScanExtraction | null>(null);
  const [saved, setSaved] = useState<BrowserScanResult | null>(null);
  const [saving, setSaving] = useState(false);
  const [durationMs, setDurationMs] = useState(0);

  const { ready, loading, running, progress, error, resolvedEngine, runScan, setError } =
    useBrowserOcr(engine);

  useEffect(() => {
    void checkChromeAiCapabilities().then(setChromeAiAvailable);
  }, []);

  const onEngineChange = (id: EngineId) => {
    setEngine(id);
    localStorage.setItem("browser-ocr-engine", id);
    setResult(null);
    setSaved(null);
  };

  const scan = async () => {
    if (!file) return;
    setResult(null);
    setSaved(null);
    try {
      const { extraction, durationMs: ms } = await runScan(file, chromeAi && chromeAiAvailable);
      setResult(extraction);
      setDurationMs(ms);
      setSaving(true);
      try {
        const record = await saveBrowserScan(file, extraction, ms);
        setSaved(record);
      } catch (e) {
        setError(
          (e instanceof Error ? e.message : "Save failed") +
            " — scan completed locally; retry save from History."
        );
      } finally {
        setSaving(false);
      }
    } catch {
      /* error set in hook */
    }
  };

  const progressPct =
    progress?.status === "run"
      ? progress.progress
      : progress?.status === "download" || progress?.status === "load"
        ? progress.progress
        : loading
          ? 5
          : ready
            ? 100
            : 0;

  return (
    <>
      <section className="card">
        <h2>Browser scan (offline OCR)</h2>
        <p className="muted">
          Runs entirely in your browser via Web Workers and WASM. Models download from Hugging Face on
          first use and are cached locally. Saving sends the image and results to the server history.
        </p>
      </section>
      <ImageCapture />
      <section className="card">
        <h2>Engine</h2>
        <select
          value={engine}
          onChange={(e) => onEngineChange(e.target.value as EngineId)}
          style={{ width: "100%" }}
          disabled={loading || running}
        >
          {ENGINE_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
        <p className="muted" style={{ marginTop: "0.35rem" }}>
          {ENGINE_OPTIONS.find((o) => o.id === engine)?.hint}
          {resolvedEngine && ` · Active: ${resolvedEngine}`}
        </p>
        {(loading || !ready) && (
          <div className="progress-wrap" style={{ marginTop: "0.75rem" }}>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${Math.min(100, progressPct)}%` }} />
            </div>
            <span className="muted" style={{ fontSize: "0.85rem", marginTop: "0.25rem", display: "block" }}>
              {progress?.file ? `${progress.file} — ` : ""}
              {loading ? "Loading model…" : "Ready"}
              {progress?.progress != null && progress.progress > 0 ? ` (${progress.progress}%)` : ""}
            </span>
          </div>
        )}
        {isChromeAiAvailable() && (
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.75rem" }}>
            <input
              type="checkbox"
              checked={chromeAi}
              onChange={(e) => setChromeAi(e.target.checked)}
              disabled={running}
            />
            <span className="muted">Refine with Chrome built-in AI (text only, not the image)</span>
          </label>
        )}
      </section>
      {error && <div className="error-banner">{error}</div>}
      <div className="row">
        <button
          type="button"
          className="primary"
          disabled={!file || !ready || running || saving}
          onClick={() => void scan()}
        >
          {running ? (
            <>
              <span className="spinner" /> Scanning…
            </>
          ) : saving ? (
            "Saving…"
          ) : (
            "Run scan"
          )}
        </button>
        {saved && <Link to={`/history?id=${saved.id}`}>View in history →</Link>}
      </div>
      {result && (
        <section className="card">
          <h2>
            Extraction{" "}
            <span className="muted">
              ({result.engine} · {Math.round(result.confidence * 100)}% · {durationMs} ms)
            </span>
          </h2>
          <dl className="scan-fields">
            <dt>SKU / Product</dt>
            <dd>{result.sku}</dd>
            <dt>Expiry date</dt>
            <dd>{result.expiry_date ?? "—"}</dd>
          </dl>
          {result.raw_text && (
            <>
              <p className="muted" style={{ marginTop: "0.75rem" }}>
                Raw OCR
              </p>
              <pre className="ocr-text">{result.raw_text}</pre>
            </>
          )}
          {saved && (
            <p className="health-ok" style={{ marginTop: "0.5rem" }}>
              Saved to server history.
            </p>
          )}
        </section>
      )}
    </>
  );
}
