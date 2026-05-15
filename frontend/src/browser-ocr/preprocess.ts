export interface PreprocessOptions {
  maxEdge?: number;
  grayscale?: boolean;
  contrast?: boolean;
}

function percentile(values: number[], p: number): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.floor((sorted.length - 1) * p);
  return sorted[idx] ?? 0;
}

function contrastStretch(data: Uint8ClampedArray): void {
  const lum: number[] = [];
  for (let i = 0; i < data.length; i += 4) {
    lum.push(0.299 * data[i]! + 0.587 * data[i + 1]! + 0.114 * data[i + 2]!);
  }
  const lo = percentile(lum, 0.02);
  const hi = percentile(lum, 0.98);
  const range = hi - lo || 1;

  for (let i = 0; i < data.length; i += 4) {
    for (let c = 0; c < 3; c++) {
      const v = ((data[i + c]! - lo) / range) * 255;
      data[i + c] = Math.max(0, Math.min(255, Math.round(v)));
    }
  }
}

function toGrayscale(data: Uint8ClampedArray): void {
  for (let i = 0; i < data.length; i += 4) {
    const g = Math.round(0.299 * data[i]! + 0.587 * data[i + 1]! + 0.114 * data[i + 2]!);
    data[i] = g;
    data[i + 1] = g;
    data[i + 2] = g;
  }
}

export async function preprocessImage(
  source: Blob | File,
  options: PreprocessOptions = {}
): Promise<{ buffer: ArrayBuffer; width: number; height: number; mime: string }> {
  const { maxEdge = 1024, grayscale = true, contrast = true } = options;

  const bitmap = await createImageBitmap(source);
  const scale = Math.min(1, maxEdge / Math.max(bitmap.width, bitmap.height));
  const width = Math.max(1, Math.round(bitmap.width * scale));
  const height = Math.max(1, Math.round(bitmap.height * scale));

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Canvas 2D unavailable");

  ctx.drawImage(bitmap, 0, 0, width, height);
  bitmap.close();

  const imageData = ctx.getImageData(0, 0, width, height);
  if (grayscale) toGrayscale(imageData.data);
  if (contrast) contrastStretch(imageData.data);
  ctx.putImageData(imageData, 0, 0);

  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("Failed to encode image"))), "image/png");
  });

  const buffer = await blob.arrayBuffer();
  return { buffer, width, height, mime: "image/png" };
}
