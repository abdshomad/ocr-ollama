import { useCallback, useEffect, useState } from "react";
import {
  deleteModelPrompt,
  getHealth,
  getModels,
  getPrompts,
  getSettings,
  updatePrompts,
  updateSettings,
} from "../api/client";
import type { InferenceBackend, OllamaModel, PromptsConfig } from "../types";
import { clearBrowserModelCache, getCacheClearedAt } from "../browser-ocr/modelCache";
import { pickDefaultOcrModel } from "../utils/models";

const HOST_PLACEHOLDER: Record<InferenceBackend, string> = {
  vllm: "http://localhost:8100",
  ollama: "http://localhost:11434",
};

export function SettingsPage() {
  const [backend, setBackend] = useState<InferenceBackend>("vllm");
  const [host, setHost] = useState("");
  const [vllmHost, setVllmHost] = useState("");
  const [ollamaHost, setOllamaHost] = useState("");
  const [health, setHealth] = useState<string>("");
  const [hostSaving, setHostSaving] = useState(false);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [prompts, setPrompts] = useState<PromptsConfig>({ general: "", per_model: {} });
  const [editModel, setEditModel] = useState("");
  const [modelPrompt, setModelPrompt] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cacheClearedAt, setCacheClearedAt] = useState<string | null>(() => getCacheClearedAt());
  const [cacheClearing, setCacheClearing] = useState(false);

  const formatHealth = (h: { inference_reachable?: boolean; model_count?: number; error?: string }) =>
    h.inference_reachable
      ? `Connected — ${h.model_count ?? 0} models`
      : `Unreachable: ${h.error ?? "unknown error"}`;

  const refreshHealth = useCallback(async () => {
    const h = await getHealth();
    setHealth(formatHealth(h));
    return h;
  }, []);

  const loadModels = useCallback(async () => {
    const m = await getModels();
    setModels(m.models);
    return m;
  }, []);

  useEffect(() => {
    Promise.all([getSettings(), refreshHealth(), loadModels(), getPrompts()])
      .then(([s, , m, p]) => {
        setBackend(s.inference_backend);
        setVllmHost(s.vllm_host);
        setOllamaHost(s.ollama_host);
        setHost(s.inference_host);
        setPrompts(p);
        const first = pickDefaultOcrModel(m.models) ?? m.models[0]?.name ?? "";
        setEditModel(first);
        setModelPrompt(p.per_model[first] ?? "");
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [refreshHealth, loadModels]);

  useEffect(() => {
    setModelPrompt(prompts.per_model[editModel] ?? "");
  }, [editModel, prompts]);

  const saveHost = async () => {
    setHostSaving(true);
    setError(null);
    try {
      const res = await updateSettings(backend, host.trim());
      setBackend(res.inference_backend);
      setVllmHost(res.vllm_host);
      setOllamaHost(res.ollama_host);
      setHost(res.inference_host);
      setHealth(formatHealth(res));
      await loadModels();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save settings");
    } finally {
      setHostSaving(false);
    }
  };

  const testConnection = async () => {
    setHostSaving(true);
    setError(null);
    try {
      await saveHost();
    } finally {
      setHostSaving(false);
    }
  };

  const saveGeneral = async () => {
    const next = await updatePrompts({ general: prompts.general });
    setPrompts(next);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const saveModel = async () => {
    const next = await updatePrompts({
      per_model: { [editModel]: modelPrompt },
    });
    setPrompts(next);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const resetModel = async () => {
    const next = await deleteModelPrompt(editModel);
    setPrompts(next);
    setModelPrompt("");
  };

  return (
    <>
      <section className="card">
        <h2>Inference server</h2>
        <p className="muted">
          OCR runs through the backend against vLLM (OpenAI API) or Ollama. Saved in{" "}
          <code>backend/config/settings.json</code>; env vars override loopback URLs in Docker.
        </p>
        <label className="muted" htmlFor="inference-backend">
          Backend
        </label>
        <select
          id="inference-backend"
          value={backend}
          onChange={(e) => {
            const next = e.target.value as InferenceBackend;
            setBackend(next);
            setHost(next === "vllm" ? vllmHost : ollamaHost);
          }}
          style={{ width: "100%", marginTop: "0.35rem" }}
        >
          <option value="vllm">vLLM</option>
          <option value="ollama">Ollama</option>
        </select>
        <label className="muted" htmlFor="inference-host" style={{ display: "block", marginTop: "0.75rem" }}>
          {backend === "vllm" ? "VLLM_HOST" : "OLLAMA_HOST"}
        </label>
        <input
          id="inference-host"
          type="url"
          value={host}
          onChange={(e) => setHost(e.target.value)}
          placeholder={HOST_PLACEHOLDER[backend]}
          style={{ width: "100%", marginTop: "0.35rem" }}
        />
        <p className={health.startsWith("Connected") ? "health-ok" : "health-bad"} style={{ marginTop: "0.75rem" }}>
          {health || "—"}
        </p>
        <div className="row" style={{ marginTop: "0.5rem" }}>
          <button type="button" className="primary" disabled={hostSaving || !host.trim()} onClick={saveHost}>
            {hostSaving ? "Saving…" : "Save"}
          </button>
          <button type="button" disabled={hostSaving || !host.trim()} onClick={testConnection}>
            Save & test
          </button>
        </div>
      </section>
      <section className="card">
        <h2>Browser OCR models</h2>
        <p className="muted">
          Offline scan models are cached in the browser (Cache API / IndexedDB). Clear if downloads are
          corrupt or you need disk space.
        </p>
        {cacheClearedAt && (
          <p className="muted" style={{ marginTop: "0.5rem" }}>
            Last cleared: {new Date(cacheClearedAt).toLocaleString()}
          </p>
        )}
        <button
          type="button"
          style={{ marginTop: "0.5rem" }}
          disabled={cacheClearing}
          onClick={async () => {
            setCacheClearing(true);
            setError(null);
            try {
              await clearBrowserModelCache();
              setCacheClearedAt(getCacheClearedAt());
              setSaved(true);
              setTimeout(() => setSaved(false), 2000);
            } catch (e) {
              setError(e instanceof Error ? e.message : "Failed to clear cache");
            } finally {
              setCacheClearing(false);
            }
          }}
        >
          {cacheClearing ? "Clearing…" : "Clear browser model cache"}
        </button>
      </section>
      <section className="card">
        <h2>General prompt</h2>
        <textarea
          value={prompts.general}
          onChange={(e) => setPrompts({ ...prompts, general: e.target.value })}
          style={{ width: "100%" }}
          rows={5}
        />
        <button type="button" className="primary" style={{ marginTop: "0.5rem" }} onClick={saveGeneral}>
          Save general
        </button>
      </section>
      <section className="card">
        <h2>Per-model prompt</h2>
        <select value={editModel} onChange={(e) => setEditModel(e.target.value)} style={{ width: "100%" }}>
          {models.map((m) => (
            <option key={m.name} value={m.name}>
              {m.name}
            </option>
          ))}
        </select>
        <textarea
          value={modelPrompt}
          onChange={(e) => setModelPrompt(e.target.value)}
          placeholder="Empty uses general prompt"
          style={{ width: "100%", marginTop: "0.5rem" }}
          rows={5}
        />
        <div className="row" style={{ marginTop: "0.5rem" }}>
          <button type="button" className="primary" onClick={saveModel}>
            Save for model
          </button>
          <button type="button" onClick={resetModel}>
            Reset to general
          </button>
        </div>
      </section>
      {saved && <p className="health-ok">Saved.</p>}
      {error && <div className="error-banner">{error}</div>}
    </>
  );
}
