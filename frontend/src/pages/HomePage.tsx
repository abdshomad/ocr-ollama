import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getModels, getPrompts, runOcr } from "../api/client";
import { ImageCapture } from "../components/ImageCapture";
import { ModelPicker } from "../components/ModelPicker";
import { useImage } from "../context/ImageContext";
import type { OllamaModel, SingleResult } from "../types";
import { pickDefaultOcrModel } from "../utils/models";

export function HomePage() {
  const { file } = useImage();
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [promptOverride, setPromptOverride] = useState("");
  const [resolvedPrompt, setResolvedPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SingleResult | null>(null);

  useEffect(() => {
    const load = () => {
      getModels()
        .then((r) => {
          setModels(r.models);
          const defaultModel = pickDefaultOcrModel(r.models);
          if (defaultModel) {
            setSelected((prev) => {
              if (prev.length === 0) return [defaultModel];
              const cur = prev[0];
              if (r.models.some((m) => m.name === cur && m.available === true)) return prev;
              return [defaultModel];
            });
          }
        })
        .catch((e) => setError(e instanceof Error ? e.message : "Failed to load models"));
    };
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const model = selected[0];
    if (!model) return;
    getPrompts().then((p) => {
      const per = p.per_model[model];
      setResolvedPrompt(per?.trim() ? per : p.general);
    });
  }, [selected]);

  const run = async () => {
    if (!file || !selected[0]) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await runOcr(
        file,
        selected[0],
        promptOverride.trim() || undefined
      );
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "OCR failed");
    } finally {
      setLoading(false);
    }
  };

  const exportTxt = () => {
    if (!result?.text) return;
    const blob = new Blob([result.text], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `ocr-${result.id}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <>
      <ImageCapture />
      <section className="card">
        <h2>Model</h2>
        <ModelPicker
          models={models}
          selected={selected}
          onChange={setSelected}
          ocrOnly
        />
      </section>
      <section className="card">
        <h2>Prompt</h2>
        <p className="muted">Active prompt (per-model or general):</p>
        <pre className="ocr-text" style={{ maxHeight: 100 }}>
          {resolvedPrompt}
        </pre>
        <label className="muted">Override for this run (optional)</label>
        <textarea
          value={promptOverride}
          onChange={(e) => setPromptOverride(e.target.value)}
          placeholder="Leave empty to use saved prompt"
          style={{ width: "100%", marginTop: "0.35rem" }}
        />
      </section>
      {error && <div className="error-banner">{error}</div>}
      <div className="row">
        <button
          type="button"
          className="primary"
          disabled={!file || !selected[0] || loading}
          onClick={run}
        >
          {loading ? (
            <>
              <span className="spinner" /> Running…
            </>
          ) : (
            "Run OCR"
          )}
        </button>
        <Link to="/arena">Compare in Arena →</Link>
      </div>
      {result && (
        <section className="card">
          <h2>
            Result — {result.model}{" "}
            <span className="muted">({result.duration_ms} ms)</span>
          </h2>
          <pre className="ocr-text">{result.text}</pre>
          <div className="row" style={{ marginTop: "0.5rem" }}>
            <button type="button" onClick={() => void navigator.clipboard.writeText(result.text)}>
              Copy
            </button>
            <button type="button" onClick={exportTxt}>
              Export .txt
            </button>
            <Link to={`/history?id=${result.id}`}>View in history</Link>
          </div>
        </section>
      )}
    </>
  );
}
