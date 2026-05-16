import type { ScanExtraction } from "../browser-ocr/types";
import type {
  AppSettings,
  ArenaResult,
  BrowserScanResult,
  GpuDashboard,
  HealthResponse,
  HistorySummary,
  InferenceBackend,
  OllamaModel,
  PromptsConfig,
  RunResult,
  SettingsUpdateResponse,
  SampleImage,
  SingleResult,
  VllmServiceActionResult,
} from "../types";

/** Slow GPU OCR (e.g. Hunyuan) can exceed 60s; avoid premature client abort where supported. */
function longRunningOcrSignal(): AbortSignal | undefined {
  if (typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function") {
    return AbortSignal.timeout(600_000);
  }
  return undefined;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function getHealth() {
  return request<HealthResponse>("/api/health");
}

export function getGpuDashboard() {
  return request<GpuDashboard>("/api/gpu");
}

export function startVllmService(serviceId: string) {
  return request<VllmServiceActionResult>(`/api/vllm/services/${encodeURIComponent(serviceId)}/start`, {
    method: "POST",
  });
}

export function stopVllmService(serviceId: string) {
  return request<VllmServiceActionResult>(`/api/vllm/services/${encodeURIComponent(serviceId)}/stop`, {
    method: "POST",
  });
}

export function getSettings() {
  return request<AppSettings>("/api/settings");
}

export function updateSettings(inference_backend: InferenceBackend, inference_host: string) {
  return request<SettingsUpdateResponse>("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ inference_backend, inference_host }),
  });
}

export function getModels() {
  return request<{ models: OllamaModel[]; inference_backend: InferenceBackend; inference_host: string }>(
    "/api/models"
  );
}

export function getPrompts() {
  return request<PromptsConfig>("/api/prompts");
}

export function updatePrompts(data: Partial<PromptsConfig>) {
  return request<PromptsConfig>("/api/prompts", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function deleteModelPrompt(model: string) {
  return request<PromptsConfig>(`/api/prompts/${encodeURIComponent(model)}`, {
    method: "DELETE",
  });
}

export function runOcr(image: File | Blob, model: string, prompt?: string) {
  const form = new FormData();
  form.append("image", image, image instanceof File ? image.name : "capture.jpg");
  form.append("model", model);
  if (prompt?.trim()) form.append("prompt", prompt.trim());
  return request<SingleResult>("/api/ocr", {
    method: "POST",
    body: form,
    signal: longRunningOcrSignal(),
  });
}

export function runArena(
  image: File | Blob,
  models: string[],
  promptOverrides?: Record<string, string>,
  extractionMode: "text" | "product" = "text"
) {
  const form = new FormData();
  form.append("image", image, image instanceof File ? image.name : "capture.jpg");
  form.append("models", JSON.stringify(models));
  form.append("extraction_mode", extractionMode);
  if (promptOverrides && Object.keys(promptOverrides).length > 0) {
    form.append("prompt_overrides", JSON.stringify(promptOverrides));
  }
  return request<ArenaResult>("/api/arena", {
    method: "POST",
    body: form,
    signal: longRunningOcrSignal(),
  });
}

export function getHistory(offset = 0, limit = 50) {
  return request<{ items: HistorySummary[]; total: number }>(
    `/api/history?offset=${offset}&limit=${limit}`
  );
}

export function getHistoryItem(id: string) {
  return request<RunResult>(`/api/history/${id}`);
}

export function deleteHistoryItem(id: string) {
  return request<{ deleted: string }>(`/api/history/${id}`, { method: "DELETE" });
}

export function uploadImageUrl(filename: string) {
  return `/api/files/upload/${encodeURIComponent(filename)}`;
}

export function getSamples() {
  return request<{ samples: SampleImage[] }>("/api/samples").then((r) => r.samples);
}

export function sampleImageUrl(name: string) {
  return `/api/samples/${encodeURIComponent(name)}`;
}

export async function fetchSampleImage(name: string): Promise<Blob> {
  const res = await fetch(sampleImageUrl(name));
  if (!res.ok) {
    throw new Error(`Sample ${name}: ${res.statusText}`);
  }
  return res.blob();
}

export function saveBrowserScan(
  image: File | Blob,
  extraction: ScanExtraction,
  durationMs: number
) {
  const form = new FormData();
  form.append("image", image, image instanceof File ? image.name : "scan.jpg");
  form.append("sku", extraction.sku);
  if (extraction.expiry_date) form.append("expiry_date", extraction.expiry_date);
  form.append("confidence", String(extraction.confidence));
  if (extraction.raw_text) form.append("raw_text", extraction.raw_text);
  form.append("engine", extraction.engine);
  form.append("duration_ms", String(durationMs));
  return request<BrowserScanResult>("/api/scan", { method: "POST", body: form });
}
