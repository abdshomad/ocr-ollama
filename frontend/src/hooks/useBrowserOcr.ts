import { useCallback, useEffect, useRef, useState } from "react";
import { OCRService, resolveWorkerEngine } from "../browser-ocr/OCRService";
import { refineExtraction, isChromeAiAvailable } from "../browser-ocr/chromeAi";
import type { EngineId, OcrProgress, ScanExtraction } from "../browser-ocr/types";

const CHROME_AI_KEY = "browser-ocr-chrome-ai";

export function useChromeAiPreference(): [boolean, (v: boolean) => void] {
  const [enabled, setEnabled] = useState(() => localStorage.getItem(CHROME_AI_KEY) === "1");
  const set = useCallback((v: boolean) => {
    setEnabled(v);
    localStorage.setItem(CHROME_AI_KEY, v ? "1" : "0");
  }, []);
  return [enabled, set];
}

export function useBrowserOcr(engine: EngineId) {
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<OcrProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resolvedEngine, setResolvedEngine] = useState<string | null>(null);
  const serviceRef = useRef<OCRService | null>(null);

  useEffect(() => {
    let cancelled = false;
    setReady(false);
    setError(null);
    setProgress({ progress: 0, status: "init" });

    serviceRef.current?.dispose();
    const svc = new OCRService({
      engine,
      onProgress: (p) => {
        if (!cancelled) setProgress(p);
      },
    });
    serviceRef.current = svc;

    const workerEngine = resolveWorkerEngine(engine);
    setResolvedEngine(workerEngine);

    svc
      .init(engine)
      .then((resolved) => {
        if (!cancelled) {
          setResolvedEngine(resolved);
          setReady(true);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load model");
          setLoading(false);
        }
      });

    setLoading(true);

    return () => {
      cancelled = true;
      svc.dispose();
      serviceRef.current = null;
      setReady(false);
    };
  }, [engine]);

  const runScan = useCallback(
    async (image: Blob | File, useChromeAi: boolean): Promise<{ extraction: ScanExtraction; durationMs: number }> => {
      const svc = serviceRef.current;
      if (!svc) throw new Error("OCR service not initialized");
      setRunning(true);
      setError(null);
      try {
        let { extraction, durationMs } = await svc.run(image);
        if (useChromeAi && isChromeAiAvailable() && extraction.raw_text) {
          extraction = await refineExtraction(extraction.raw_text, extraction.engine);
        }
        return { extraction, durationMs };
      } catch (e) {
        const err = e as Error & { code?: string };
        const hint =
          err.code === "OOM"
            ? " Try Fast scan (Tesseract) or a smaller engine."
            : err.code === "DOWNLOAD"
              ? " Check network for model download."
              : "";
        const msg = (err.message || "OCR failed") + hint;
        setError(msg);
        throw new Error(msg);
      } finally {
        setRunning(false);
      }
    },
    []
  );

  return {
    ready,
    loading,
    running,
    progress,
    error,
    resolvedEngine,
    runScan,
    setError,
  };
}
