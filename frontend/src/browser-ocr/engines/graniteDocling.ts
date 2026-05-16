import { AutoModelForVision2Seq, AutoProcessor, env, load_image } from "@huggingface/transformers";

const MODEL_ID = "onnx-community/granite-docling-258M-ONNX";

/** Product-label scan: shorter generation than full-page doc conversion. */
const USER_PROMPT = "Read all visible text from this image. Output plain text lines only.";

type ProgressInfo = { file?: string; progress?: number; status?: string };

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let processor: any = null;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let model: any = null;

export function configureGraniteDoclingEnv(onProgress: (p: { file?: string; progress?: number }) => void): void {
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

export async function loadGraniteDocling(onProgress: (p: { file?: string; progress?: number }) => void): Promise<void> {
  configureGraniteDoclingEnv(onProgress);
  const e = env as typeof env & { progress_callback?: (progress: ProgressInfo) => void };
  if (!processor) {
    processor = await AutoProcessor.from_pretrained(MODEL_ID, {
      progress_callback: e.progress_callback,
    });
    model = await AutoModelForVision2Seq.from_pretrained(MODEL_ID, {
      dtype: "fp32",
      progress_callback: e.progress_callback,
    });
  }
}

export async function runGraniteDocling(buffer: ArrayBuffer, mime: string): Promise<string> {
  if (!processor || !model) throw new Error("Granite Docling not loaded");

  const url = URL.createObjectURL(new Blob([buffer], { type: mime || "image/png" }));
  try {
    const image = await load_image(url);
    const messages = [
      {
        role: "user",
        content: [
          { type: "image" },
          { type: "text", text: USER_PROMPT },
        ],
      },
    ];
    const text = processor.apply_chat_template(messages, { add_generation_prompt: true });
    const inputs = await processor(text, [image], {
      do_image_splitting: false,
    });

    const generated_ids = await model.generate({
      ...inputs,
      max_new_tokens: 512,
      do_sample: false,
    });

    const start = inputs.input_ids.dims.at(-1) ?? 0;
    const newTokens = generated_ids.slice(null, [start, null]);
    const generated_texts = processor.batch_decode(newTokens, { skip_special_tokens: true });
    const out = typeof generated_texts === "string" ? generated_texts : String(generated_texts[0] ?? "");
    return out.replace(/<\|end_of_text\|>/g, "").trim();
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function disposeGraniteDocling(): void {
  processor = null;
  model = null;
}
