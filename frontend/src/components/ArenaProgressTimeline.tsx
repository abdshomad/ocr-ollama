import type { ArenaResultEntry } from "../types";

export type ArenaTimelineStepState =
  | "queued"
  | "running"
  | "done"
  | "error"
  | "skipped"
  | "cancelled";

export interface ArenaTimelineStep {
  model: string;
  state: ArenaTimelineStepState;
  entry?: ArenaResultEntry;
}

function stateLabel(state: ArenaTimelineStepState): string {
  switch (state) {
    case "queued":
      return "Queued";
    case "running":
      return "Running";
    case "done":
      return "Done";
    case "error":
      return "Error";
    case "skipped":
      return "Skipped";
    case "cancelled":
      return "Stopped";
  }
}

export function ArenaProgressTimeline({ steps }: { steps: ArenaTimelineStep[] }) {
  if (steps.length === 0) return null;
  return (
    <ul className="arena-timeline" aria-label="Arena progress by model">
      {steps.map((s) => (
        <li key={s.model} className={`arena-timeline-row arena-timeline-${s.state}`}>
          <span className="arena-timeline-dot" aria-hidden />
          <span className="arena-timeline-model">{s.model}</span>
          <span className="arena-timeline-status muted">{stateLabel(s.state)}</span>
          {s.state === "running" ? (
            <span className="arena-timeline-spin">
              <span className="spinner" aria-hidden />
            </span>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
