import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { getHealth, getHistory, getModels, getPrompts, runOcr } from "../api/client";
import { ImageCapture } from "../components/ImageCapture";
import { ModelPicker } from "../components/ModelPicker";
import { RunIdleHints } from "../components/RunIdleHints";
import { useImage } from "../context/ImageContext";
import type { InferenceBackend, OllamaModel, SingleResult } from "../types";
import { pickDefaultOcrModel } from "../utils/models";
import {
  loadDurationHintStore,
  pushModelDuration,
  saveDurationHintStore,
  seedHintsFromHistory,
} from "../utils/runDurationHints";

const WARM_AVAIL_MSG =
  "Inference availability changed — engines may be warming up or reloading. Expect noisy timings until probes settle.";

export function HomePage() {
  const { file } = useImage();
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const selectedRef = useRef(selected);
  selectedRef.current = selected;
  const [promptOverride, setPromptOverride] = useState("");
  const [resolvedPrompt, setResolvedPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SingleResult | null>(null);
  const [hintStore, setHintStore] = useState(loadDurationHintStore);
  const [warmNotice, setWarmNotice] = useState<string | null>(null);
  const [vllmMaxOutputTokens, setVllmMaxOutputTokens] = useState<number | null>(null);
  const [inferenceBackend, setInferenceBackend] = useState<InferenceBackend>("vllm");
  const [availabilityPending, setAvailabilityPending] = useState(false);
  const [inferenceReachable, setInferenceReachable] = useState(true);
  const prevHealthReachable = useRef<boolean | undefined>(undefined);
  const prevAvailRef = useRef<Map<string, boolean | null>>(new Map());

  useEffect(() => {
    let cancelled = false;
    getHistory(0, 80)
      .then(({ items }) => {
        if (cancelled) return;
        const seeded = seedHintsFromHistory(loadDurationHintStore(), items);
        saveDurationHintStore(seeded);
        setHintStore(seeded);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const tick = async () => {
      try {
        const mr = await getModels();
        setError(null);
        setModels(mr.models);
        setInferenceBackend(mr.inference_backend);
        setVllmMaxOutputTokens(mr.vllm_max_output_tokens ?? null);
        setAvailabilityPending(Boolean(mr.availability_pending));

        const defaultModel = pickDefaultOcrModel(mr.models);
        if (defaultModel) {
          setSelected((prev) => {
            if (prev.length === 0) return [defaultModel];
            const cur = prev[0];
            if (mr.models.some((m) => m.name === cur && m.available === true)) return prev;
            return [defaultModel];
          });
        }

        let health: Awaited<ReturnType<typeof getHealth>> | null = null;
        try {
          health = await getHealth();
          setInferenceReachable(health.inference_reachable);
        } catch {
          /* keep last inferenceReachable; models still refresh */
        }

        let flipHealth = false;
        if (health) {
          const ph = prevHealthReachable.current;
          if (ph === true && health.inference_reachable === false) flipHealth = true;
          prevHealthReachable.current = health.inference_reachable;
        }

        let flipModel = false;
        const sel = selectedRef.current[0];
        for (const m of mr.models) {
          const p = prevAvailRef.current.get(m.name);
          const c = m.available ?? null;
          if (sel && m.name === sel && p === true && c !== true) flipModel = true;
          prevAvailRef.current.set(m.name, c);
        }

        if (flipHealth || flipModel) setWarmNotice(WARM_AVAIL_MSG);
        else if (
          health?.inference_reachable &&
          sel &&
          mr.models.some((x) => x.name === sel && x.available === true)
        ) {
          setWarmNotice(null);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load models");
      }
    };
    void tick();
    const t = setInterval(() => void tick(), 5000);
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
      setHintStore((prev) => {
        const next = pushModelDuration(prev, selected[0], res.duration_ms);
        saveDurationHintStore(next);
        return next;
      });
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
        <RunIdleHints
          selectedModel={selected[0]}
          catalogModels={models}
          hintStore={hintStore}
          inferenceBackend={inferenceBackend}
          vllmMaxOutputTokens={vllmMaxOutputTokens}
          warmNotice={warmNotice}
          inferenceReachable={inferenceReachable}
          availabilityPending={availabilityPending}
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
