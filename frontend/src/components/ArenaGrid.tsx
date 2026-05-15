import type { ArenaResultEntry } from "../types";

interface ArenaGridProps {
  results: ArenaResultEntry[];
}

export function ArenaGrid({ results }: ArenaGridProps) {
  const withDuration = results.filter((r) => r.duration_ms && r.duration_ms > 0 && !r.error);
  const fastest =
    withDuration.length > 0
      ? withDuration.reduce((a, b) => ((a.duration_ms ?? 0) < (b.duration_ms ?? 0) ? a : b)).model
      : null;

  const copyAll = () => {
    const text = results
      .map((r) => `=== ${r.model} ===\n${r.error ? `Error: ${r.error}` : r.text ?? ""}`)
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
                  : `${r.duration_ms ?? 0} ms · ${(r.text ?? "").length} chars`}
              </span>
            </div>
            {r.error ? (
              <p className="health-bad">{r.error}</p>
            ) : (
              <pre className="ocr-text">{r.text || "(empty)"}</pre>
            )}
          </article>
        ))}
      </div>
    </>
  );
}
