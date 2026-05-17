import type { RunResult } from "../types";
import {
  diffFromFirstColumn,
  structuredFieldsFromRun,
  unionStructuredKeys,
} from "../utils/structuredCompare";

function shortRunLabel(run: RunResult): string {
  const ts = new Date(run.timestamp).toLocaleString();
  if (run.kind === "arena") return `Arena · ${run.id.slice(0, 8)} · ${ts}`;
  if (run.kind === "browser_scan") return `Browser · ${run.id.slice(0, 8)} · ${ts}`;
  if (run.kind === "product_scan") return `Product · ${run.model} · ${run.id.slice(0, 8)}`;
  return `${run.model} · ${run.id.slice(0, 8)}`;
}

interface StructuredComparePanelProps {
  runs: RunResult[];
  onClose: () => void;
}

export function StructuredComparePanel({ runs, onClose }: StructuredComparePanelProps) {
  const keys = unionStructuredKeys(runs);
  const rows = keys.map((key) => {
    const values = runs.map((run) => structuredFieldsFromRun(run)?.[key] ?? "—");
    const highlights = diffFromFirstColumn(values);
    return { key, values, highlights };
  });

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>Structured comparison</h2>
        <button type="button" onClick={onClose}>
          Close
        </button>
      </div>
      <p className="muted" style={{ marginTop: "0.35rem" }}>
        Comparing {runs.length} run{runs.length === 1 ? "" : "s"}. Highlighted cells differ from the first column.
      </p>
      <div className="structured-compare-scroll">
        <table className="structured-compare-table">
          <thead>
            <tr>
              <th scope="col">Field</th>
              {runs.map((run) => (
                <th key={run.id} scope="col">
                  {shortRunLabel(run)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(({ key, values, highlights }) => (
              <tr key={key}>
                <th scope="row">{key}</th>
                {values.map((v, i) => (
                  <td key={`${key}-${i}`} className={highlights[i] ? "structured-compare-diff" : undefined}>
                    {v}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
