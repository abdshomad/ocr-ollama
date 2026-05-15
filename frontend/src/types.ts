export type ModelTier = "dedicated_ocr" | "vision" | "text_only";
export type InferenceBackend = "vllm" | "ollama";

export interface OllamaModel {
  name: string;
  size?: number;
  modified_at?: string;
  tier: ModelTier;
  ocr_capable: boolean;
  has_parent_blob?: boolean;
  capabilities: string[];
  families: string[];
}

export interface PromptsConfig {
  general: string;
  per_model: Record<string, string>;
}

export interface SingleResult {
  id: string;
  kind: "single";
  timestamp: string;
  model: string;
  prompt: string;
  image_path: string;
  text: string;
  duration_ms: number;
  inference_backend?: InferenceBackend;
  inference_meta?: Record<string, unknown>;
  ollama_meta?: Record<string, unknown>;
}

export interface ArenaResultEntry {
  model: string;
  prompt: string;
  text?: string;
  duration_ms?: number;
  error?: string;
  inference_meta?: Record<string, unknown>;
  ollama_meta?: Record<string, unknown>;
}

export interface ArenaResult {
  id: string;
  kind: "arena";
  timestamp: string;
  image_path: string;
  results: ArenaResultEntry[];
}

export type RunResult = SingleResult | ArenaResult;

export interface HistorySummary {
  id: string;
  kind: "single" | "arena";
  timestamp: string;
  models: string[];
  image_filename: string;
  preview: string;
}

export interface HealthResponse {
  status: string;
  inference_backend: InferenceBackend;
  inference_reachable: boolean;
  inference_host: string;
  model_count: number;
  error?: string;
}

export interface AppSettings {
  inference_backend: InferenceBackend;
  inference_host: string;
  vllm_host: string;
  ollama_host: string;
}

export interface SettingsUpdateResponse extends AppSettings, HealthResponse {}
