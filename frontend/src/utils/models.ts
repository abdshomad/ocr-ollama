import type { OllamaModel } from "../types";

/** Prefer standalone OCR models; adapter-style models often need extra blobs on the Ollama host. */
export function pickDefaultOcrModel(models: OllamaModel[]): string | undefined {
  const ocr = models.filter((m) => m.ocr_capable);
  if (!ocr.length) return undefined;
  const standalone = ocr.filter((m) => !m.has_parent_blob);
  const dedicated = (list: OllamaModel[]) =>
    list.filter((m) => m.tier === "dedicated_ocr");
  const prefer = (list: OllamaModel[]) =>
    list.find((m) => /deepseek-ai\/DeepSeek-OCR/i.test(m.name)) ??
    list.find((m) => /deepseek-ocr/i.test(m.name));
  return (
    prefer(dedicated(standalone))?.name ??
    prefer(standalone)?.name ??
    dedicated(standalone)[0]?.name ??
    standalone[0]?.name ??
    dedicated(ocr)[0]?.name ??
    ocr[0]?.name
  );
}
