import type { OllamaModel } from "../types";
import { isModelAvailable } from "../components/ModelPicker";

export { isModelAvailable };

/** Prefer standalone OCR models that are online. */
export function pickDefaultOcrModel(models: OllamaModel[]): string | undefined {
  const ocr = models.filter((m) => m.ocr_capable && isModelAvailable(m));
  if (!ocr.length) return undefined;
  const standalone = ocr.filter((m) => !m.has_parent_blob);
  const dedicated = (list: OllamaModel[]) =>
    list.filter((m) => m.tier === "dedicated_ocr");
  const prefer = (list: OllamaModel[]) =>
    list.find((m) => /lightonai\/LightOnOCR/i.test(m.name)) ??
    list.find((m) => /nvidia\/nemotron-ocr-v2/i.test(m.name)) ??
    list.find((m) => /^deepseek-ai\/DeepSeek-OCR$/i.test(m.name)) ??
    list.find((m) => /deepseek-ai\/DeepSeek-OCR/i.test(m.name)) ??
    list.find((m) => /zai-org\/GLM-OCR/i.test(m.name)) ??
    list.find((m) => /glm-ocr/i.test(m.name)) ??
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

/** Default arena pair: both vLLM OCR models when up, else any two online OCR models. */
export function pickDefaultArenaModels(models: OllamaModel[]): string[] {
  const ocr = models.filter((m) => m.ocr_capable && isModelAvailable(m));
  const lightonDeepseek = ["lightonai/LightOnOCR-2-1B", "deepseek-ai/DeepSeek-OCR"].filter((id) =>
    ocr.some((m) => m.name === id)
  );
  if (lightonDeepseek.length >= 2) return lightonDeepseek;
  const vllmPair = ["deepseek-ai/DeepSeek-OCR", "zai-org/GLM-OCR"].filter((id) =>
    ocr.some((m) => m.name === id)
  );
  if (vllmPair.length >= 2) return vllmPair;
  if (ocr.length >= 2) return ocr.slice(0, 2).map((m) => m.name);
  const one = pickDefaultOcrModel(models);
  return one ? [one] : [];
}
