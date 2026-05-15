import { createWorker, type Worker } from "tesseract.js";

let worker: Worker | null = null;

export async function loadTesseract(onProgress?: (p: { progress: number }) => void): Promise<void> {
  if (worker) return;
  worker = await createWorker("eng", 1, {
    logger: (m) => {
      if (m.status === "loading tesseract core" || m.status === "initializing tesseract") {
        onProgress?.({ progress: m.progress ?? 0 });
      }
    },
  });
}

export async function runTesseract(buffer: ArrayBuffer): Promise<string> {
  if (!worker) throw new Error("Tesseract not loaded");
  const blob = new Blob([buffer], { type: "image/png" });
  const { data } = await worker.recognize(blob);
  return data.text.trim();
}

export async function disposeTesseract(): Promise<void> {
  if (worker) {
    await worker.terminate();
    worker = null;
  }
}
