import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { OllamaModel } from "../types";

function TierBadge({ tier }: { tier: OllamaModel["tier"] }) {
  if (tier === "dedicated_ocr") return <span className="badge badge-ocr">OCR</span>;
  if (tier === "vision") return <span className="badge badge-vision">Vision</span>;
  return <span className="badge badge-text">Text</span>;
}

function SpeedBadge({ tier }: { tier?: string }) {
  if (!tier) return null;
  return <span className="badge badge-text">{tier}</span>;
}

function formatModelSize(n?: number): string | null {
  if (n == null || !Number.isFinite(n)) return null;
  const b = n;
  if (b >= 1e12) return `${(b / 1e12).toFixed(1)} TB`;
  if (b >= 1e9) return `${(b / 1e9).toFixed(1)} GB`;
  if (b >= 1e6) return `${(b / 1e6).toFixed(1)} MB`;
  if (b >= 1e3) return `${(b / 1e3).toFixed(0)} KB`;
  return `${b} B`;
}

function rowTitle(m: OllamaModel, up: boolean): string | undefined {
  if (!up) {
    if (m.engine_type === "litparse") {
      return "Install the lit CLI (npm i -g @llamaindex/liteparse) or set LITEPARSE_BIN on the backend host.";
    }
    if (m.engine_type === "nemotron") {
      return "Start the nemotron-ocr-v2 service (compose profile nemotron), then refresh.";
    }
    if (m.engine_type === "rapidocr") {
      return "Start the rapidocr service (compose profile rapidocr), then refresh.";
    }
    if (m.engine_type === "onnxtr") {
      return "Start the onnxtr service (compose profile onnxtr), then refresh.";
    }
    if (m.engine_type === "easyocr") {
      return "Start the easyocr service (compose profile easyocr), then refresh.";
    }
    if (m.engine_type === "doctr") {
      return "Start the doctr service (compose profile doctr), then refresh.";
    }
    if (m.engine_type === "paddleocr") {
      return "Start the paddleocr service (compose profile paddleocr), then refresh.";
    }
    return undefined;
  }
  if (m.input_modes?.length) {
    return `Supported inputs: ${m.input_modes.join(", ")}`;
  }
  return undefined;
}

export function isModelAvailable(m: OllamaModel): boolean {
  return m.available !== false;
}

function sortModels(a: OllamaModel, b: OllamaModel): number {
  const aUp = isModelAvailable(a) ? 0 : 1;
  const bUp = isModelAvailable(b) ? 0 : 1;
  if (aUp !== bUp) return aUp - bUp;
  return a.name.localeCompare(b.name);
}

interface ModelPickerProps {
  models: OllamaModel[];
  selected: string[];
  onChange: (selected: string[]) => void;
  multiple?: boolean;
  ocrOnly?: boolean;
}

function ModelDetailPanel({ m }: { m: OllamaModel }) {
  const up = isModelAvailable(m);
  const hint = rowTitle(m, up);
  const sizeStr = formatModelSize(m.size);
  const detailLine = (label: string, value: string | undefined | null) =>
    value ? (
      <div className="model-detail-row">
        <span className="model-detail-label">{label}</span>
        <span className="model-detail-value">{value}</span>
      </div>
    ) : null;

  return (
    <div
      className="model-detail-panel"
      role="region"
      aria-label={`Details for ${m.name}`}
    >
      <p className="model-detail-title">{m.name}</p>
      {!up && (
        <p className="model-detail-warn muted">
          {hint ??
            "Offline — start this model on the GPU page, then refresh."}{" "}
          <Link to="/gpu">GPU</Link>
        </p>
      )}
      <div className="model-detail-grid">
        {detailLine("Engine", m.engine_label ?? m.engine_type)}
        {detailLine("Endpoint", m.vllm_endpoint_label ?? m.vllm_endpoint)}
        {detailLine("Speed", m.speed_tier)}
        {detailLine("Tier", m.tier.replace(/_/g, " "))}
        {detailLine("Inputs", m.input_modes?.join(", "))}
        {detailLine("Capabilities", m.capabilities?.length ? m.capabilities.join(", ") : null)}
        {detailLine("Families", m.families?.length ? m.families.join(", ") : null)}
        {detailLine("Size", sizeStr)}
        {detailLine("Modified", m.modified_at)}
        {m.has_parent_blob ? (
          <p className="model-detail-note muted">
            Uses a parent model blob; you may need <code>ollama pull</code> if load fails.
          </p>
        ) : null}
        {up && hint ? <p className="model-detail-note muted">{hint}</p> : null}
      </div>
    </div>
  );
}

function ModelCard({
  m,
  multiple,
  selected,
  expanded,
  onCardPress,
}: {
  m: OllamaModel;
  multiple: boolean;
  selected: string[];
  expanded: boolean;
  onCardPress: (m: OllamaModel) => void;
}) {
  const up = isModelAvailable(m);
  const isOn = selected.includes(m.name);
  const hint = rowTitle(m, up);

  return (
    <button
      type="button"
      className={[
        "model-card",
        up ? "" : "model-card-offline",
        isOn ? "model-card-selected" : "",
        expanded ? "model-card-expanded" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      title={
        hint ?? (up ? "Click for details and to select" : "Offline — click for details")
      }
      aria-pressed={multiple ? isOn : undefined}
      aria-label={
        multiple
          ? `${m.name}${isOn ? ", selected" : ", not selected"}. Toggle for arena.`
          : `${m.name}${isOn ? ", selected" : ""}. Show details and select for run.`
      }
      onClick={() => onCardPress(m)}
    >
      <span className="model-card-name">{m.name}</span>
      <span className="model-card-badges">
        {m.vllm_endpoint_label ? (
          <span className="badge badge-text">{m.vllm_endpoint_label}</span>
        ) : null}
        <SpeedBadge tier={m.speed_tier} />
        <TierBadge tier={m.tier} />
        {!up ? <span className="badge badge-offline">Offline</span> : null}
        {m.has_parent_blob ? (
          <span
            className="badge badge-text"
            title="Adapter / parent blob"
          >
            Adapter
          </span>
        ) : null}
      </span>
      {multiple && isOn ? (
        <span className="model-card-check" aria-hidden>
          ✓
        </span>
      ) : null}
    </button>
  );
}

export function ModelPicker({
  models,
  selected,
  onChange,
  multiple = false,
  ocrOnly = false,
}: ModelPickerProps) {
  const [detailFor, setDetailFor] = useState<string | null>(null);

  const list = (ocrOnly ? models.filter((m) => m.ocr_capable) : models).sort(sortModels);
  const ready = list.filter(isModelAvailable);
  const offline = list.filter((m) => !isModelAvailable(m));

  useEffect(() => {
    if (!multiple && selected[0]) setDetailFor(selected[0]);
  }, [multiple, selected]);

  const toggle = (name: string, available: boolean) => {
    if (!available) return;
    if (multiple) {
      onChange(
        selected.includes(name) ? selected.filter((s) => s !== name) : [...selected, name]
      );
    } else {
      onChange([name]);
    }
  };

  const onCardPress = (m: OllamaModel) => {
    const up = isModelAvailable(m);
    setDetailFor(m.name);
    if (up) toggle(m.name, true);
  };

  const detailModel = detailFor ? list.find((x) => x.name === detailFor) : undefined;

  if (list.length === 0) {
    return <p className="muted">No models match filter.</p>;
  }

  return (
    <div className="model-picker">
      {ready.length > 0 && (
        <div className="model-picker-group">
          <p className="model-picker-heading">Ready ({ready.length})</p>
          <div
            className="model-card-grid"
            role="group"
            aria-label={multiple ? "OCR models (pick 2 or more for arena)" : "OCR model for run"}
          >
            {ready.map((m) => (
              <ModelCard
                key={m.name}
                m={m}
                multiple={multiple}
                selected={selected}
                expanded={detailFor === m.name}
                onCardPress={onCardPress}
              />
            ))}
          </div>
        </div>
      )}
      {offline.length > 0 && (
        <div className="model-picker-group model-picker-offline">
          <p className="model-picker-heading">
            Offline ({offline.length}) — <Link to="/gpu">start on GPU page</Link>
          </p>
          <div
            className="model-card-grid model-card-grid-offline"
            role="group"
            aria-label="Offline OCR models"
          >
            {offline.map((m) => (
              <ModelCard
                key={m.name}
                m={m}
                multiple={multiple}
                selected={selected}
                expanded={detailFor === m.name}
                onCardPress={onCardPress}
              />
            ))}
          </div>
        </div>
      )}
      {detailModel ? <ModelDetailPanel m={detailModel} /> : null}
    </div>
  );
}