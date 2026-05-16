import type { ScanExtraction } from "./types";

const MONTHS: Record<string, number> = {
  JAN: 1,
  FEB: 2,
  MAR: 3,
  APR: 4,
  MAY: 5,
  JUN: 6,
  JUL: 7,
  AUG: 8,
  SEP: 9,
  OCT: 10,
  NOV: 11,
  DEC: 12,
  JANUARY: 1,
  FEBRUARY: 2,
  MARCH: 3,
  APRIL: 4,
  JUNE: 6,
  JULY: 7,
  AUGUST: 8,
  SEPTEMBER: 9,
  OCTOBER: 10,
  NOVEMBER: 11,
  DECEMBER: 12,
};

const DATE_PATTERNS: { re: RegExp; parse: (m: RegExpMatchArray) => string | null }[] = [
  {
    re: /\b(?:BEST\s*BEFORE|USE\s*BY|EXP(?:IRY)?|BB)[:\s]*(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})\b/gi,
    parse: (m) => isoFromDmy(m[1], m[2], m[3]),
  },
  {
    re: /\b(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})\b/g,
    parse: (m) => isoFromDmy(m[1], m[2], m[3]),
  },
  {
    re: /\b(\d{1,2})[\/\-.](\d{4})\b/g,
    parse: (m) => isoFromParts(Number(m[2]), Number(m[1]), 1),
  },
  {
    re: /\b(20\d{2})-(\d{1,2})(?:-(\d{1,2}))?\b/g,
    parse: (m) => isoFromParts(Number(m[1]), Number(m[2]), m[3] ? Number(m[3]) : 1),
  },
  {
    re: /\b([A-Z]{3,9})\s+['']?(\d{2}|\d{4})\b/gi,
    parse: (m) => {
      const mon = MONTHS[m[1].toUpperCase()];
      if (!mon) return null;
      let y = Number(m[2]);
      if (y < 100) y += 2000;
      return isoFromParts(y, mon, 1);
    },
  },
];

function isoFromDmy(d: string, m: string, y: string): string | null {
  let day = Number(d);
  let month = Number(m);
  let year = Number(y);
  if (year < 100) year += 2000;
  if (month > 12 && day <= 12) [day, month] = [month, day];
  return isoFromParts(year, month, day);
}

function isoFromParts(year: number, month: number, day: number): string | null {
  if (month < 1 || month > 12 || day < 1 || day > 31 || year < 1990 || year > 2100) return null;
  const dt = new Date(Date.UTC(year, month - 1, day));
  if (dt.getUTCFullYear() !== year || dt.getUTCMonth() !== month - 1 || dt.getUTCDate() !== day) {
    return null;
  }
  return dt.toISOString().slice(0, 10);
}

function extractExpiry(text: string): { date: string | null; strength: number } {
  const upper = text.toUpperCase();
  let best: { date: string | null; strength: number } = { date: null, strength: 0 };

  for (const { re, parse } of DATE_PATTERNS) {
    re.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(upper)) !== null) {
      const iso = parse(m);
      if (iso) {
        const strength = /BEST|USE\s*BY|EXP/i.test(m[0]) ? 0.95 : 0.7;
        if (strength > best.strength) best = { date: iso, strength };
      }
    }
  }
  return best;
}

function extractSkuFromStructured(text: string): string | null {
  const product = text.match(/(?:product|item|name)\s*[:\-]\s*([^\n,;]+)/i);
  if (product?.[1]?.trim()) return product[1].trim();
  const sku = text.match(/\b(?:sku|upc|ean|code)\s*[:\-#]?\s*([A-Z0-9][A-Z0-9\-]{4,})\b/i);
  if (sku?.[1]) return sku[1].trim();
  return null;
}

function extractSkuHeuristic(text: string, expiryLineRe: RegExp): string {
  const structured = extractSkuFromStructured(text);
  if (structured) return structured;

  const lines = text
    .split(/\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && !expiryLineRe.test(l));

  const tokens: string[] = [];
  for (const line of lines) {
    const matches = line.match(/[A-Z0-9][A-Z0-9\-]{5,}/gi);
    if (matches) tokens.push(...matches);
    const words = line.match(/[A-Za-z][A-Za-z0-9\s\-]{3,}/g);
    if (words) tokens.push(...words.map((w) => w.trim()));
  }

  if (tokens.length === 0) {
    const fallback = text.replace(/\s+/g, " ").trim().slice(0, 80);
    return fallback || "unknown";
  }

  tokens.sort((a, b) => b.length - a.length);
  return tokens[0] ?? "unknown";
}

export function parseEntities(rawText: string, engine: string): ScanExtraction {
  const text = rawText.trim();
  const expiry = extractExpiry(text);
  const expiryLineRe = /\b(?:BEST|USE\s*BY|EXP|\d{1,2}[\/\-.]\d)/i;
  const sku = extractSkuHeuristic(text, expiryLineRe);

  const skuScore = Math.min(1, sku.length / 12);
  const dateScore = expiry.strength;
  const engineBoost =
    engine === "paligemma" ? 0.1 : engine === "granite" ? 0.08 : engine === "trocr" ? 0.05 : 0;
  const confidence = Math.min(1, Math.max(0.15, skuScore * 0.5 + dateScore * 0.45 + engineBoost));

  return {
    sku,
    expiry_date: expiry.date,
    confidence: Math.round(confidence * 100) / 100,
    raw_text: text,
    engine,
  };
}

export function mergeExtractions(
  base: ScanExtraction,
  refined: Partial<Pick<ScanExtraction, "sku" | "expiry_date">>
): ScanExtraction {
  return {
    ...base,
    sku: refined.sku?.trim() || base.sku,
    expiry_date: refined.expiry_date ?? base.expiry_date,
    confidence: Math.min(1, base.confidence + 0.1),
  };
}
