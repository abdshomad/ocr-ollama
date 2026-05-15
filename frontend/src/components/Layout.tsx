import { NavLink, Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import { getHealth } from "../api/client";
import type { HealthResponse } from "../types";

function healthLabel(h: HealthResponse): string {
  const backend = h.inference_backend ?? "vllm";
  const name = backend === "vllm" ? "vLLM" : "Ollama";
  const reachable = h.inference_reachable;
  const count = h.model_count ?? 0;
  return reachable ? `${name} (${count} models)` : `${name} offline`;
}

export function Layout() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() =>
        setHealth({
          status: "error",
          inference_backend: "vllm",
          inference_reachable: false,
          inference_host: "",
          model_count: 0,
          error: "API unreachable",
        })
      );
  }, []);

  const reachable = health?.inference_reachable ?? false;

  return (
    <div className="app-shell">
      <nav>
        <NavLink to="/" className="brand" end>
          OCR Ollama
        </NavLink>
        <NavLink to="/" end>
          Run
        </NavLink>
        <NavLink to="/arena">Arena</NavLink>
        <NavLink to="/history">History</NavLink>
        <NavLink to="/settings">Settings</NavLink>
        {health && (
          <span className={`muted ${reachable ? "health-ok" : "health-bad"}`}>{healthLabel(health)}</span>
        )}
      </nav>
      <Outlet />
    </div>
  );
}
