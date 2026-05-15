import { parseEntities } from "./entityParser";
import { preprocessImage } from "./preprocess";
import type { EngineId, OcrProgress, ScanExtraction, WorkerEngine, WorkerRequest, WorkerResponse } from "./types";

import OcrWorker from "./ocr.worker?worker";

const ENGINE_STORAGE_KEY = "browser-ocr-engine";

export function resolveWorkerEngine(preferred: EngineId): WorkerEngine {
  if (preferred === "trocr" || preferred === "paligemma" || preferred === "tesseract") {
    return preferred;
  }
  const mem = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;
  if (preferred === "auto") {
    if (mem !== undefined && mem < 4) return "tesseract";
    return "trocr";
  }
  return "trocr";
}

export function suggestEngineForFailure(code: string | undefined): WorkerEngine {
  if (code === "OOM") return "tesseract";
  return "tesseract";
}

export interface OCRServiceOptions {
  engine?: EngineId;
  onProgress?: (p: OcrProgress) => void;
}

export class OCRService {
  private worker: Worker | null = null;
  private ready = false;
  private workerEngine: WorkerEngine | null = null;
  private readonly preferredEngine: EngineId;
  private readonly onProgress?: (p: OcrProgress) => void;
  private initPromise: Promise<void> | null = null;

  constructor(options: OCRServiceOptions = {}) {
    this.preferredEngine = options.engine ?? (localStorage.getItem(ENGINE_STORAGE_KEY) as EngineId) ?? "auto";
    this.onProgress = options.onProgress;
  }

  private ensureWorker(): Worker {
    if (!this.worker) {
      this.worker = new OcrWorker();
      this.worker.onmessage = (ev: MessageEvent<WorkerResponse>) => {
        const data = ev.data;
        if (data.type === "progress") {
          this.onProgress?.({
            file: data.file,
            progress: data.progress,
            status: data.status,
          });
        } else if (data.type === "ready") {
          this.ready = true;
          this.workerEngine = data.engine;
          this.onProgress?.({ progress: 100, status: "load" });
        } else if (data.type === "error") {
          this.ready = false;
        }
      };
    }
    return this.worker;
  }

  private post(msg: WorkerRequest): void {
    this.ensureWorker().postMessage(msg);
  }

  private waitForReady(): Promise<void> {
    if (this.ready) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const w = this.ensureWorker();
      const timeout = setTimeout(() => reject(new Error("Model load timed out")), 600_000);
      const handler = (ev: MessageEvent<WorkerResponse>) => {
        if (ev.data.type === "ready") {
          clearTimeout(timeout);
          w.removeEventListener("message", handler);
          resolve();
        } else if (ev.data.type === "error") {
          clearTimeout(timeout);
          w.removeEventListener("message", handler);
          reject(new Error(ev.data.message));
        }
      };
      w.addEventListener("message", handler);
    });
  }

  async init(engineOverride?: EngineId): Promise<WorkerEngine> {
    const preferred = engineOverride ?? this.preferredEngine;
    const workerEngine = resolveWorkerEngine(preferred);
    localStorage.setItem(ENGINE_STORAGE_KEY, preferred);

    if (this.initPromise && this.workerEngine === workerEngine && this.ready) {
      return workerEngine;
    }

    this.ready = false;
    this.initPromise = (async () => {
      this.post({ type: "init", engine: workerEngine });
      await this.waitForReady();
    })();

    await this.initPromise;
    return workerEngine;
  }

  async run(image: Blob | File): Promise<{ extraction: ScanExtraction; durationMs: number }> {
    if (!this.ready) {
      await this.init();
    }

    const { buffer, width, height, mime } = await preprocessImage(image);

    return new Promise((resolve, reject) => {
      const w = this.ensureWorker();
      const timeout = setTimeout(() => reject(new Error("Inference timed out")), 300_000);

      const handler = (ev: MessageEvent<WorkerResponse>) => {
        const data = ev.data;
        if (data.type === "progress") {
          this.onProgress?.({
            file: data.file,
            progress: data.progress,
            status: data.status,
          });
        } else if (data.type === "result") {
          clearTimeout(timeout);
          w.removeEventListener("message", handler);
          const engine = data.engine;
          const extraction = parseEntities(data.rawText, engine);
          resolve({ extraction, durationMs: data.durationMs });
        } else if (data.type === "error") {
          clearTimeout(timeout);
          w.removeEventListener("message", handler);
          reject(Object.assign(new Error(data.message), { code: data.code }));
        }
      };

      w.addEventListener("message", handler);
      this.post({ type: "run", image: buffer, width, height, mime });
    });
  }

  dispose(): void {
    if (this.worker) {
      this.post({ type: "dispose" });
      this.worker.terminate();
      this.worker = null;
    }
    this.ready = false;
    this.workerEngine = null;
    this.initPromise = null;
  }
}
