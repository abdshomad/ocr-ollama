import type { InferenceBackend, ModelTier, OllamaModel } from "../types";
import { avgMs, type DurationHintStore } from "../utils/runDurationHints";

function formatLatency(ms: number): string {
  if (!Number.isFinite(ms) || ms <= 0) return "—";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

function tierLabel(tier: ModelTier): string {
  if (tier === "dedicated_ocr") return "OCR-dedicated";
  if (tier === "vision") return "Vision";
  return "Text-only";
}

function avgForTier(models: OllamaModel[], tier: ModelTier, store: DurationHintStore): number | null {
  const rows = models.filter((m) => m.tier === tier);
  const vals: number[] = [];
  for (const m of rows) {
    const a = avgMs(store.models[m.name]);
    if (a != null) vals.push(a);
  }
  if (vals.length === 0) return null;
  return Math.round(vals.reduce((x, y) => x + y, 0) / vals.length);
}

type Props = {
  selectedModel: string | undefined;
  catalogModels: OllamaModel[];
  hintStore: DurationHintStore;
  inferenceBackend: InferenceBackend;
  vllmMaxOutputTokens: number | null | undefined;
  warmNotice: string | null;
  inferenceReachable: boolean;
  availabilityPending: boolean;
};

export function RunIdleHints({
  selectedModel,
  catalogModels,
  hintStore,
  inferenceBackend,
  vllmMaxOutputTokens,
  warmNotice,
  inferenceReachable,
  availabilityPending,
}: Props) {
  const meta = selectedModel ? catalogModels.find((m) => m.name === selectedModel) : undefined;
  const samples = selectedModel ? hintStore.models[selectedModel] : undefined;
  const lastMs = samples?.length ? samples[samples.length - 1] : null;
  const avgModel = avgMs(samples);
  const tierAvg =
    meta && catalogModels.length > 0 ? avgForTier(catalogModels, meta.tier, hintStore) : null;

  const tokenTitle =
    inferenceBackend === "vllm"
      ? vllmMaxOutputTokens != null
        ? `Server OCR requests cap output at ${vllmMaxOutputTokens.toLocaleString()} tokens (VLLM_MAX_TOKENS). Long pages may truncate.`
        : "Output token cap is set on the backend (VLLM_MAX_TOKENS)."
      : undefined;

  const degraded =
    !inferenceReachable &&
    (inferenceBackend === "vllm"
      ? "Inference endpoint unreachable — check Settings / GPU services."
      : "Ollama unreachable — check Settings and that the server is running.");

  return (
    <div className="run-idle-hints">
      {warmNotice ? (
        <div className="run-idle-hints-warm" role="status">
          <span className="run-idle-hints-warm-label">Warming up</span>
          {warmNotice}
        </div>
      ) : null}
      {availabilityPending ? (
        <p className="muted run-idle-hints-line" role="status">
          Checking which engines are online…
        </p>
      ) : null}
      {degraded ? <p className="muted run-idle-hints-line run-idle-hints-warn">{degraded}</p> : null}
      {selectedModel ? (
        <p className="muted run-idle-hints-line">
          {avgModel != null ? (
            <>
              <span title="Rolling average from this browser tab (session), seeded from recent History when you open Run.">
                Typical latency ({selectedModel})
              </span>
              : avg {formatLatency(avgModel)}
              {samples && samples.length > 1 ? ` · ${samples.length} samples in tab` : ""}
              {lastMs != null ? ` · last ${formatLatency(lastMs)}` : ""}
            </>
          ) : (
            <>
              No timing samples for <strong>{selectedModel}</strong> in this tab yet — first run calibrates,
              or open History after runs to seed hints.
            </>
          )}
        </p>
      ) : null}
      {meta && tierAvg != null && tierAvg !== avgModel ? (
        <p className="muted run-idle-hints-line">
          {tierLabel(meta.tier)} tier avg (cached models in tab): ~{formatLatency(tierAvg)}
        </p>
      ) : null}
      {inferenceBackend === "vllm" ? (
        <p className="muted run-idle-hints-line">
          <abbr title={tokenTitle} style={{ cursor: "help", textDecoration: "underline dotted" }}>
            Max output tokens
          </abbr>
          {vllmMaxOutputTokens != null ? `: ${vllmMaxOutputTokens.toLocaleString()} (cap)` : ""}
        </p>
      ) : (
        <p className="muted run-idle-hints-line">
          Output length follows your Ollama server / model defaults (no fixed token cap in this UI).
        </p>
      )}
    </div>
  );
}
