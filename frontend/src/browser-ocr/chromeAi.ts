import type { ScanExtraction } from "./types";
import { mergeExtractions, parseEntities } from "./entityParser";

interface ChromeAiWindow extends Window {
  ai?: {
    languageModel?: {
      capabilities?: () => Promise<{ available: string }>;
      create?: (options?: Record<string, unknown>) => Promise<{
        prompt: (input: string) => Promise<string>;
        destroy?: () => void;
      }>;
    };
  };
}

export function isChromeAiAvailable(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as ChromeAiWindow;
  return Boolean(w.ai?.languageModel?.create);
}

export async function checkChromeAiCapabilities(): Promise<boolean> {
  if (!isChromeAiAvailable()) return false;
  const w = window as ChromeAiWindow;
  try {
    const caps = await w.ai?.languageModel?.capabilities?.();
    return caps?.available === "readily" || caps?.available === "after-download";
  } catch {
    return isChromeAiAvailable();
  }
}

export async function refineExtraction(rawText: string, engine: string): Promise<ScanExtraction> {
  const base = parseEntities(rawText, engine);
  if (!isChromeAiAvailable()) return base;

  const w = window as ChromeAiWindow;
  const session = await w.ai!.languageModel!.create!();
  try {
    const prompt = `From this OCR text from a product package, return JSON only with keys sku (product name or code) and expiry_date (YYYY-MM-DD or null):\n\n${rawText}`;
    const reply = await session.prompt(prompt);
    const jsonMatch = reply.match(/\{[\s\S]*\}/);
    if (!jsonMatch) return base;
    const parsed = JSON.parse(jsonMatch[0]) as { sku?: string; expiry_date?: string | null };
    return mergeExtractions(base, {
      sku: parsed.sku,
      expiry_date: parsed.expiry_date ?? null,
    });
  } catch {
    return base;
  } finally {
    session.destroy?.();
  }
}
