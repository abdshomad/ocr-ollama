import type { OllamaModel } from "../types";

function TierBadge({ tier }: { tier: OllamaModel["tier"] }) {
  if (tier === "dedicated_ocr") return <span className="badge badge-ocr">OCR</span>;
  if (tier === "vision") return <span className="badge badge-vision">Vision</span>;
  return <span className="badge badge-text">Text</span>;
}

function isAvailable(m: OllamaModel): boolean {
  return m.available !== false;
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
  const list = (ocrOnly ? models.filter((m) => m.ocr_capable) : models).sort((a, b) => {
    const aUp = isAvailable(a) ? 0 : 1;
    const bUp = isAvailable(b) ? 0 : 1;
    if (aUp !== bUp) return aUp - bUp;
    return a.name.localeCompare(b.name);
  });

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

  return (
    <div className="model-list">
      {list.map((m) => {
        const up = isAvailable(m);
        return (
          <label
            key={m.name}
            className={`model-row${up ? "" : " model-row-disabled"}`}
            title={up ? undefined : "Model server is not ready yet"}
          >
            <input
              type={multiple ? "checkbox" : "radio"}
              name="model"
              checked={selected.includes(m.name)}
              disabled={!up}
              onChange={() => toggle(m.name, up)}
            />
            <span>{m.name}</span>
            {m.vllm_endpoint_label && (
              <span className="badge badge-text">{m.vllm_endpoint_label}</span>
            )}
            <TierBadge tier={m.tier} />
            {!up && <span className="badge badge-text">Offline</span>}
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
      })}
      {list.length === 0 && <p className="muted">No models match filter.</p>}
    </div>
  );
}
