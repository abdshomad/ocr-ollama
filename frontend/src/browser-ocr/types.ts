export type EngineId = "auto" | "trocr" | "paligemma" | "tesseract";

export type WorkerEngine = "trocr" | "paligemma" | "tesseract";

export interface ScanExtraction {
  sku: string;
  expiry_date: string | null;
  confidence: number;
  raw_text?: string;
  engine: string;
}

export interface OcrProgress {
  file?: string;
  progress: number;
  status: "download" | "load" | "run" | "init";
}

export type WorkerRequest =
  | { type: "init"; engine: WorkerEngine }
  | { type: "run"; image: ArrayBuffer; width: number; height: number; mime: string }
  | { type: "dispose" };

export type WorkerResponse =
  | { type: "progress"; file?: string; progress: number; status: "download" | "load" | "run" | "init" }
  | { type: "ready"; engine: WorkerEngine }
  | { type: "result"; rawText: string; engine: string; durationMs: number }
  | { type: "error"; message: string; code: "OOM" | "DOWNLOAD" | "INFERENCE" | "UNKNOWN" };

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
