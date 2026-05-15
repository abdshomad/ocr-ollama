import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getModels, runArena } from "../api/client";
import { ArenaGrid } from "../components/ArenaGrid";
import { ImageCapture } from "../components/ImageCapture";
import { ModelPicker } from "../components/ModelPicker";
import { useImage } from "../context/ImageContext";
import type { ArenaResult, OllamaModel } from "../types";
import { pickDefaultArenaModels } from "../utils/models";

export function ArenaPage() {
  const { file } = useImage();
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ArenaResult | null>(null);

  useEffect(() => {
    const load = () => {
      getModels()
        .then((r) => {
          setModels(r.models);
          setSelected((prev) => {
            const valid = prev.filter((id) =>
              r.models.some((m) => m.name === id && m.available !== false)
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
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(`Running 0 / ${selected.length}…`);
    try {
      const res = await runArena(file, selected);
      setResult(res);
      setProgress(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Arena failed");
      setProgress(null);
    } finally {
      setLoading(false);
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
      {progress && <p className="muted">{progress}</p>}
      <div className="row">
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
      </div>
      {result && (
        <section className="card">
          <h2>Arena results</h2>
          <ArenaGrid results={result.results} />
        </section>
      )}
    </>
  );
}
