import type { OllamaModel } from "../types";

function TierBadge({ tier }: { tier: OllamaModel["tier"] }) {
  if (tier === "dedicated_ocr") return <span className="badge badge-ocr">OCR</span>;
  if (tier === "vision") return <span className="badge badge-vision">Vision</span>;
  return <span className="badge badge-text">Text</span>;
}

interface ModelPickerProps {
  models: OllamaModel[];
  selected: string[];
  onChange: (selected: string[]) => void;
  multiple?: boolean;
  ocrOnly?: boolean;
}

export function ModelPicker({
  models,
  selected,
  onChange,
  multiple = false,
  ocrOnly = false,
}: ModelPickerProps) {
  const list = ocrOnly ? models.filter((m) => m.ocr_capable) : models;

  const toggle = (name: string) => {
    if (multiple) {
      onChange(
        selected.includes(name) ? selected.filter((s) => s !== name) : [...selected, name]
      );
    } else {
      onChange([name]);
    }
  };

  return (
    <div className="model-list">
      {list.map((m) => (
        <label key={m.name} className="model-row">
          <input
            type={multiple ? "checkbox" : "radio"}
            name="model"
            checked={selected.includes(m.name)}
            onChange={() => toggle(m.name)}
          />
          <span>{m.name}</span>
          <TierBadge tier={m.tier} />
          {m.has_parent_blob && (
            <span className="badge badge-text" title="Uses a parent model blob; may need ollama pull if load fails">
              Adapter
            </span>
          )}
        </label>
      ))}
      {list.length === 0 && <p className="muted">No models match filter.</p>}
    </div>
  );
}
