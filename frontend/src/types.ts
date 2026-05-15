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
  /** vLLM endpoint reachable (dual-model Compose). Omitted = available. */
  available?: boolean;
  vllm_endpoint?: string;
  vllm_endpoint_label?: string;
  speed_tier?: string;
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

export interface BrowserScanResult {
  id: string;
  kind: "browser_scan";
  timestamp: string;
  image_path: string;
  sku: string;
  expiry_date: string | null;
  confidence: number;
  raw_text: string;
  engine: string;
  duration_ms: number;
}

export type RunResult = SingleResult | ArenaResult | BrowserScanResult;

export interface HistorySummary {
  id: string;
  kind: "single" | "arena" | "browser_scan";
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

export interface GpuInfo {
  index: number;
  name: string;
  memory_used_mib: number;
  memory_total_mib: number;
  utilization_pct: number | null;
}

export interface VllmServiceStatus {
  id: string;
  label: string;
  compose_service: string;
  gpu_device: number;
  port: number;
  models: string[];
  docker_state: string;
  health?: string | null;
  api_ready: boolean;
  container_id?: string | null;
}

export interface GpuDashboard {
  manage_enabled: boolean;
  manage_message?: string | null;
  gpus: GpuInfo[];
  gpu_query_error?: string | null;
  services: VllmServiceStatus[];
  gpu_memory_utilization: number;
}

export interface VllmServiceActionResult {
  ok: boolean;
  action: "start" | "stop";
  service_id: string;
  message: string;
  service?: VllmServiceStatus | null;
}
