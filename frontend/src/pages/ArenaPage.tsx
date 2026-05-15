import { useEffect, useState } from "react";
import { getModels, runArena } from "../api/client";
import { ArenaGrid } from "../components/ArenaGrid";
import { ImageCapture } from "../components/ImageCapture";
import { ModelPicker } from "../components/ModelPicker";
import { useImage } from "../context/ImageContext";
import type { ArenaResult, OllamaModel } from "../types";
import { pickDefaultOcrModel } from "../utils/models";

export function ArenaPage() {
  const { file } = useImage();
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ArenaResult | null>(null);

  useEffect(() => {
    getModels()
      .then((r) => {
        setModels(r.models);
        const ocrNames = r.models.filter((m) => m.ocr_capable && !m.has_parent_blob).map((m) => m.name);
        const preferred = ocrNames.filter((n) =>
          ["deepseek-ocr:latest", "glm-ocr:latest", "qwen3.6:latest"].includes(n)
        );
        if (preferred.length >= 2) setSelected(preferred.slice(0, 3));
        else if (ocrNames.length >= 2) setSelected(ocrNames.slice(0, 2));
        else {
          const fallback = pickDefaultOcrModel(r.models);
          if (fallback) setSelected([fallback]);
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load models"));
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
