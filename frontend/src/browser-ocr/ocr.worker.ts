import type { WorkerEngine, WorkerRequest, WorkerResponse } from "./types";
import { disposePaliGemma, loadPaliGemma, runPaliGemma } from "./engines/paligemma";
import { disposeTrocr, loadTrocr, runTrocr } from "./engines/trocr";
import { disposeTesseract, loadTesseract, runTesseract } from "./engines/tesseract";

let activeEngine: WorkerEngine | null = null;

function post(msg: WorkerResponse): void {
  self.postMessage(msg);
}

function onProgress(file: string | undefined, progress: number, status: "download" | "load" | "run" | "init"): void {
  post({ type: "progress", file, progress, status });
}

function classifyError(err: unknown): WorkerResponse {
  const message = err instanceof Error ? err.message : String(err);
  const lower = message.toLowerCase();
  let code: "OOM" | "DOWNLOAD" | "INFERENCE" | "UNKNOWN" = "UNKNOWN";
  if (lower.includes("out of memory") || lower.includes("oom") || lower.includes("allocation")) {
    code = "OOM";
  } else if (lower.includes("fetch") || lower.includes("download") || lower.includes("network")) {
    code = "DOWNLOAD";
  } else if (lower.includes("inference") || lower.includes("onnx") || lower.includes("wasm")) {
    code = "INFERENCE";
  }
  return { type: "error", message, code };
}

async function initEngine(engine: WorkerEngine): Promise<void> {
  onProgress(undefined, 0, "init");
  const progressCb = (p: { file?: string; progress?: number }) => {
    onProgress(p.file, Math.round((p.progress ?? 0) * 100), "download");
  };

  if (engine === "trocr") {
    await loadTrocr(progressCb);
  } else if (engine === "paligemma") {
    await loadPaliGemma(progressCb);
  } else {
    await loadTesseract((p) => onProgress(undefined, Math.round(p.progress * 100), "load"));
  }
  activeEngine = engine;
  post({ type: "ready", engine });
}

async function runInference(
  engine: WorkerEngine,
  buffer: ArrayBuffer,
  width: number,
  height: number,
  mime: string
): Promise<void> {
  const start = performance.now();
  onProgress(undefined, 0, "run");

  let rawText = "";
  if (engine === "trocr") {
    const url = URL.createObjectURL(new Blob([buffer], { type: mime }));
    try {
      rawText = await runTrocr(url);
    } finally {
      URL.revokeObjectURL(url);
    }
  } else if (engine === "paligemma") {
    rawText = await runPaliGemma(buffer, width, height);
  } else {
    rawText = await runTesseract(buffer);
  }

  const durationMs = Math.round(performance.now() - start);
  post({ type: "result", rawText, engine, durationMs });
}

async function disposeAll(): Promise<void> {
  disposeTrocr();
  disposePaliGemma();
  await disposeTesseract();
  activeEngine = null;
}

self.onmessage = async (ev: MessageEvent<WorkerRequest>) => {
  const msg = ev.data;
  try {
    if (msg.type === "init") {
      if (activeEngine && activeEngine !== msg.engine) {
        await disposeAll();
      }
      await initEngine(msg.engine);
    } else if (msg.type === "run") {
      const engine = activeEngine ?? "trocr";
      await runInference(engine, msg.image, msg.width, msg.height, msg.mime);
    } else if (msg.type === "dispose") {
      await disposeAll();
    }
  } catch (err) {
    post(classifyError(err));
  }
};
