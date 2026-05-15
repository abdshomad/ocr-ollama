import type { ArenaResult, ArenaResultEntry } from "../types";

interface ArenaGridProps {
  results: ArenaResultEntry[];
  extractionMode?: ArenaResult["extraction_mode"];
}

function isProductEntry(r: ArenaResultEntry, mode?: ArenaResult["extraction_mode"]): boolean {
  return mode === "product" || r.sku !== undefined;
}

export function ArenaGrid({ results, extractionMode }: ArenaGridProps) {
  const productMode = extractionMode === "product" || results.some((r) => r.sku !== undefined);
  const withDuration = results.filter((r) => r.duration_ms && r.duration_ms > 0 && !r.error);
  const fastest =
    withDuration.length > 0
      ? withDuration.reduce((a, b) => ((a.duration_ms ?? 0) < (b.duration_ms ?? 0) ? a : b)).model
      : null;

  const copyAll = () => {
    const text = results
      .map((r) => {
        if (isProductEntry(r, extractionMode)) {
          if (r.error) return `=== ${r.model} ===\nError: ${r.error}`;
          return `=== ${r.model} ===\nSKU: ${r.sku ?? ""}\nExpiry: ${r.expiry_date ?? "—"}`;
        }
        return `=== ${r.model} ===\n${r.error ? `Error: ${r.error}` : r.text ?? ""}`;
      })
      .join("\n\n");
    void navigator.clipboard.writeText(text);
  };

  return (
    <>
      <div className="row" style={{ marginBottom: "0.75rem" }}>
        <button type="button" onClick={copyAll}>
          Copy all
        </button>
      </div>
      <div className="arena-grid">
        {results.map((r) => (
          <article
            key={r.model}
            className={`arena-card${r.model === fastest ? " fastest" : ""}`}
          >
            <div className="meta">
              <strong>{r.model}</strong>
              <span>
                {r.error
                  ? "failed"
                  : productMode
                    ? `${r.duration_ms ?? 0} ms · ${r.pipeline ?? ""}`
                    : `${r.duration_ms ?? 0} ms · ${(r.text ?? "").length} chars`}
              </span>
            </div>
            {r.error ? (
              <p className="health-bad">{r.error}</p>
            ) : productMode ? (
              <dl className="scan-fields">
                <dt>SKU / Product</dt>
                <dd>{r.sku ?? "—"}</dd>
                <dt>Expiry date</dt>
                <dd>{r.expiry_date ?? "—"}</dd>
                {r.pipeline === "ocr_then_text" && r.ocr_model && (
                  <>
                    <dt>OCR model</dt>
                    <dd>{r.ocr_model}</dd>
                  </>
                )}
              </dl>
            ) : (
              <pre className="ocr-text">{r.text || "(empty)"}</pre>
            )}
          </article>
        ))}
      </div>
    </>
  );
}
