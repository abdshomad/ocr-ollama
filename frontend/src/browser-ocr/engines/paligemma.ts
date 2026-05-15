import { AutoProcessor, PaliGemmaForConditionalGeneration, env } from "@huggingface/transformers";

const MODEL_ID = "onnx-community/paligemma2-3b-pt-224";
const PROMPT = "<image>detect product name and expiry date";

type ProgressInfo = { file?: string; progress?: number; status?: string };

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let processor: any = null;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let model: any = null;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let tokenizer: any = null;

export function configurePaliGemmaEnv(onProgress: (p: { file?: string; progress?: number }) => void): void {
  const e = env as typeof env & {
    progress_callback?: (progress: ProgressInfo) => void;
  };
  e.allowLocalModels = false;
  e.useBrowserCache = true;
  e.progress_callback = (progress: ProgressInfo) => {
    onProgress({
      file: progress.file,
      progress: progress.progress ?? 0,
    });
  };
}

export async function loadPaliGemma(onProgress: (p: { file?: string; progress?: number }) => void): Promise<void> {
  configurePaliGemmaEnv(onProgress);
  const e = env as typeof env & { progress_callback?: (progress: ProgressInfo) => void };
  if (!processor) {
    processor = await AutoProcessor.from_pretrained(MODEL_ID, {
      progress_callback: e.progress_callback,
    });
    model = await PaliGemmaForConditionalGeneration.from_pretrained(MODEL_ID, {
      dtype: {
        embed_tokens: "fp16",
        vision_encoder: "fp16",
        decoder_model_merged: "q4",
      },
      progress_callback: e.progress_callback,
    });
    tokenizer = processor.tokenizer;
  }
}

async function blobToImageData(buffer: ArrayBuffer): Promise<ImageData> {
  const blob = new Blob([buffer], { type: "image/png" });
  const bitmap = await createImageBitmap(blob);
  const w = bitmap.width;
  const h = bitmap.height;
  const canvas = new OffscreenCanvas(w, h);
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("OffscreenCanvas unavailable");
  ctx.drawImage(bitmap, 0, 0);
  bitmap.close();
  return ctx.getImageData(0, 0, w, h);
}

export async function runPaliGemma(buffer: ArrayBuffer, _width: number, _height: number): Promise<string> {
  if (!processor || !model || !tokenizer) throw new Error("PaliGemma not loaded");

  const imageData = await blobToImageData(buffer);
  const inputs = await processor(imageData, PROMPT);

  const output = await model.generate({
    ...inputs,
    max_new_tokens: 128,
    do_sample: false,
  });

  const tokenIds = Array.isArray(output) ? output[0] : output;
  const decoded = tokenizer.decode(tokenIds, { skip_special_tokens: true });
  return String(decoded).replace(PROMPT, "").trim();
}

export function disposePaliGemma(): void {
  processor = null;
  model = null;
  tokenizer = null;
}
