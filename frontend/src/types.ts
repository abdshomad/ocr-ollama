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
  /** Optional catalog tags for UI filtering (e.g. gpu, tables, cpu_sidecar). */
  feature_tags?: string[];
  /** true = online, false = offline, null = not probed yet */
  available?: boolean | null;
  vllm_endpoint?: string;
  vllm_endpoint_label?: string;
  engine_type?: string;
  engine_label?: string;
  speed_tier?: string;
  input_modes?: string[];
}

export interface SampleImage {
  name: string;
  label: string;
  url: string;
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
  prompt?: string;
  text?: string;
  sku?: string;
  expiry_date?: string | null;
  pipeline?: "vision" | "ocr_then_text";
  ocr_model?: string | null;
  raw_text?: string | null;
  duration_ms?: number;
  error?: string;
  inference_meta?: Record<string, unknown>;
  ollama_meta?: Record<string, unknown>;
}

export interface ArenaResult {
  id: string;
  kind: "arena";
  extraction_mode?: "text" | "product";
  timestamp: string;
  image_path: string;
  results: ArenaResultEntry[];
}

/** SSE payloads from POST /api/arena/stream */
export type ArenaSseEvent =
  | { type: "arena_model"; model: string; phase: "running" | "finished"; entry?: ArenaResultEntry }
  | { type: "arena_cancelled"; next_index: number; partial_results: ArenaResultEntry[] }
  | { type: "arena_complete"; record: ArenaResult };

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

export interface ProductScanResult {
  id: string;
  kind: "product_scan";
  timestamp: string;
  image_path: string;
  model: string;
  pipeline: "vision" | "ocr_then_text";
  duration_ms: number;
  ocr_model?: string | null;
  raw_text?: string | null;
  inference_backend?: string;
  sku: string;
  expiry_date: string | null;
}

export type RunResult = SingleResult | ArenaResult | BrowserScanResult | ProductScanResult;

export interface HistorySummary {
  id: string;
  kind: "single" | "arena" | "browser_scan" | "product_scan";
  timestamp: string;
  models: string[];
  image_filename: string;
  preview: string;
  /** Present when kind === "arena". */
  extraction_mode?: ArenaResult["extraction_mode"];
  /** Single / product_scan / browser_scan — wall-clock OCR duration when stored in result JSON. */
  duration_ms?: number;
  /** Arena runs — max duration_ms observed per model in that compare. */
  model_duration_ms?: Record<string, number>;
}

/** GET /api/models */
export interface ModelsListResponse {
  models: OllamaModel[];
  inference_backend: InferenceBackend;
  inference_host: string;
  ollama_host?: string;
  availability_pending?: boolean;
  /** Backend default output cap when inference_backend === vllm (from VLLM_MAX_TOKENS). */
  vllm_max_output_tokens?: number | null;
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

export interface ModelVramDetail {
  id: string;
  params_b?: number;
  vram_gib?: number;
  ram_gib?: number;
  note?: string;
}

export interface VllmServiceStatus {
  id: string;
  label: string;
  compose_service: string;
  gpu_device: number;
  gpu_assignment_supported?: boolean;
  port: number;
  models: string[];
  model_details?: ModelVramDetail[];
  /** Typical GPU memory to load (catalog estimate). */
  vram_estimate_gib?: number;
  vram_estimate_gib_min?: number;
  /** CPU / sidecar RAM estimate when no GPU VRAM. */
  ram_estimate_gib?: number;
  docker_state: string;
  health?: string | null;
  api_ready: boolean | null;
  container_id?: string | null;
}

export interface GpuDashboard {
  manage_enabled: boolean;
  manage_message?: string | null;
  gpus: GpuInfo[];
  gpu_query_error?: string | null;
  services: VllmServiceStatus[];
  gpu_memory_utilization: number;
  gpu_device_assignments?: Record<string, number>;
}

export interface VllmServiceActionResult {
  ok: boolean;
  action: "start" | "stop" | "recycle";
  service_id: string;
  message: string;
  service?: VllmServiceStatus | null;
}

export interface BulkVllmStopResult {
  ok: boolean;
  action: "stop_all" | "stop_gpu";
  gpu_index?: number;
  stopped_service_ids: string[];
  errors?: { service_id: string; detail: string }[] | null;
  message: string;
}

export interface GpuAssignmentsPutBody {
  assignments: Record<string, number | null>;
}

export interface GpuAssignmentsResponse {
  ok: boolean;
  assignments: Record<string, number>;
  message?: string;
}
