import { env, pipeline } from "@huggingface/transformers";

const MODEL_ID = "Xenova/trocr-base-handwritten";

type ProgressInfo = { file?: string; progress?: number; status?: string };

// Pipeline typing is heavy; runtime API is image-to-text(url | RawImage).
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let pipe: any = null;

export function configureEnv(onProgress: (p: { file?: string; progress?: number }) => void): void {
  const e = env as typeof env & {
    progress_callback?: (progress: ProgressInfo) => void;
  };
  e.allowLocalModels = false;
  e.useBrowserCache = true;
  if (env.backends?.onnx?.wasm) {
    env.backends.onnx.wasm.numThreads = Math.min(4, navigator.hardwareConcurrency ?? 2);
  }
  e.progress_callback = (progress: ProgressInfo) => {
    onProgress({
      file: progress.file,
      progress: progress.progress ?? 0,
    });
  };
}

export async function loadTrocr(onProgress: (p: { file?: string; progress?: number }) => void): Promise<void> {
  configureEnv(onProgress);
  if (!pipe) {
    const e = env as typeof env & { progress_callback?: (progress: ProgressInfo) => void };
    pipe = await pipeline("image-to-text", MODEL_ID, {
      dtype: "q8",
      progress_callback: e.progress_callback,
    });
  }
}

export async function runTrocr(imageUrl: string): Promise<string> {
  if (!pipe) throw new Error("TrOCR not loaded");
  const out = await pipe(imageUrl);
  if (Array.isArray(out)) {
    return out
      .map((x: unknown) =>
        typeof x === "object" && x && "generated_text" in x
          ? String((x as { generated_text: string }).generated_text)
          : String(x)
      )
      .join("\n");
  }
  if (typeof out === "object" && out && "generated_text" in out) {
    return String((out as { generated_text: string }).generated_text);
  }
  return String(out ?? "");
}

export function disposeTrocr(): void {
  pipe = null;
}
