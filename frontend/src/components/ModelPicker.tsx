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

function ModelRow({
  m,
  multiple,
  selected,
  onToggle,
}: {
  m: OllamaModel;
  multiple: boolean;
  selected: string[];
  onToggle: (name: string, available: boolean) => void;
}) {
  const up = isModelAvailable(m);
  return (
    <label
      className={`model-row${up ? "" : " model-row-disabled"}`}
      title={up ? undefined : "Start this model on the GPU page, then refresh"}
    >
      <input
        type={multiple ? "checkbox" : "radio"}
        name="model"
        checked={selected.includes(m.name)}
        disabled={!up}
        onChange={() => onToggle(m.name, up)}
      />
      <span className="model-row-name">{m.name}</span>
      {m.vllm_endpoint_label && (
        <span className="badge badge-text">{m.vllm_endpoint_label}</span>
      )}
      <SpeedBadge tier={m.speed_tier} />
      <TierBadge tier={m.tier} />
      {!up && <span className="badge badge-offline">Offline</span>}
      {m.has_parent_blob && (
        <span
          className="badge badge-text"
          title="Uses a parent model blob; may need ollama pull if load fails"
        >
          Adapter
        </span>
      )}
    </label>
  );
}

export function ModelPicker({
  models,
  selected,
  onChange,
  multiple = false,
  ocrOnly = false,
}: ModelPickerProps) {
  const list = (ocrOnly ? models.filter((m) => m.ocr_capable) : models).sort(sortModels);
  const ready = list.filter(isModelAvailable);
  const offline = list.filter((m) => !isModelAvailable(m));

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

  if (list.length === 0) {
    return <p className="muted">No models match filter.</p>;
  }

  return (
    <div className="model-picker">
      {ready.length > 0 && (
        <div className="model-picker-group">
          <p className="model-picker-heading">Ready ({ready.length})</p>
          <div className="model-list">
            {ready.map((m) => (
              <ModelRow
                key={m.name}
                m={m}
                multiple={multiple}
                selected={selected}
                onToggle={toggle}
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
          <div className="model-list">
            {offline.map((m) => (
              <ModelRow
                key={m.name}
                m={m}
                multiple={multiple}
                selected={selected}
                onToggle={toggle}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}