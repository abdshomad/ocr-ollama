import { useCallback, useEffect, useState } from "react";
import { getGpuDashboard, startVllmService, stopVllmService } from "../api/client";
import type { GpuDashboard, GpuInfo, VllmServiceStatus } from "../types";

function memPct(g: GpuInfo): number {
  if (!g.memory_total_mib) return 0;
  return Math.min(100, Math.round((g.memory_used_mib / g.memory_total_mib) * 100));
}

function stateLabel(s: VllmServiceStatus): { text: string; className: string } {
  if (s.docker_state === "local_cli") {
    if (s.api_ready === true) return { text: "CLI ready", className: "gpu-state-ready" };
    if (s.api_ready == null) return { text: "Checking…", className: "gpu-state-loading" };
    return { text: "CLI missing", className: "gpu-state-stopped" };
  }
  if (s.api_ready === true) return { text: "Ready", className: "gpu-state-ready" };
  if (s.api_ready == null && (s.docker_state === "running" || s.docker_state === "starting")) {
    return { text: "Checking…", className: "gpu-state-loading" };
  }
  if (s.docker_state === "running" || s.docker_state === "starting")
    return { text: "Loading…", className: "gpu-state-loading" };
  if (s.docker_state === "exited" || s.docker_state === "stopped")
    return { text: "Stopped", className: "gpu-state-stopped" };
  if (s.docker_state === "not_created") return { text: "Not loaded", className: "gpu-state-stopped" };
  return { text: s.docker_state, className: "gpu-state-unknown" };
}

function servicesOnGpu(services: VllmServiceStatus[], gpuIndex: number): VllmServiceStatus[] {
  const score = (s: VllmServiceStatus) => {
    if (s.api_ready) return 0;
    if (s.docker_state === "running" || s.docker_state === "starting") return 1;
    return 2;
  };
  return services
    .filter((s) => s.gpu_device === gpuIndex)
    .sort((a, b) => {
      const d = score(a) - score(b);
      if (d !== 0) return d;
      return a.label.localeCompare(b.label);
    });
}

export function GpuPage() {
  const [data, setData] = useState<GpuDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const d = await getGpuDashboard();
      setData(d);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load GPU status");
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [refresh]);

  const handleStart = async (id: string) => {
    setBusyId(id);
    setActionMsg(null);
    setError(null);
    try {
      const r = await startVllmService(id);
      setActionMsg(r.message);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Start failed");
    } finally {
      setBusyId(null);
    }
  };

  const handleStop = async (id: string) => {
    setBusyId(id);
    setActionMsg(null);
    setError(null);
    try {
      const r = await stopVllmService(id);
      setActionMsg(r.message);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stop failed");
    } finally {
      setBusyId(null);
    }
  };

  const gpus = data?.gpus ?? [];
  const services = data?.services ?? [];
  const gpuIndices =
    gpus.length > 0
      ? gpus.map((g) => g.index)
      : [...new Set(services.map((s) => s.gpu_device))].sort((a, b) => a - b);

  return (
    <div>
      <h1>GPU &amp; models</h1>
      <p className="muted" style={{ marginTop: "-0.5rem", marginBottom: "1rem" }}>
        Each OCR model runs on its own L40. Stop a service to free VRAM; load when you need it.
        {data?.gpu_memory_utilization != null && (
          <> vLLM GPU memory target: {(data.gpu_memory_utilization * 100).toFixed(0)}%.</>
        )}
      </p>

      {error && <div className="error-banner">{error}</div>}
      {actionMsg && !error && (
        <p className="muted" style={{ marginBottom: "1rem" }}>
          {actionMsg}
        </p>
      )}

      {!data && !error && (
        <p className="muted">
          <span className="spinner" /> Loading…
        </p>
      )}

      {data && !data.manage_enabled && data.manage_message && (
        <div className="card gpu-warn">
          <p className="muted" style={{ margin: 0 }}>
            {data.manage_message} API readiness is still shown when reachable.
          </p>
        </div>
      )}

      {data?.gpu_query_error && <p className="muted">GPU metrics: {data.gpu_query_error}</p>}

      <div className="gpu-grid">
        {gpuIndices.map((idx) => {
          const gpu = gpus.find((g) => g.index === idx);
          const svcs = servicesOnGpu(services, idx);
          const pct = gpu ? memPct(gpu) : null;

          return (
            <div key={idx} className="card gpu-card">
              <h2>
                GPU {idx}
                {gpu?.name && <span className="muted"> — {gpu.name}</span>}
              </h2>

              {gpu && (
                <div className="progress-wrap" style={{ marginBottom: "0.75rem" }}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: "0.25rem" }}>
                    <span className="muted">VRAM</span>
                    <span className="muted">
                      {gpu.memory_used_mib.toLocaleString()} / {gpu.memory_total_mib.toLocaleString()} MiB
                      {gpu.utilization_pct != null && ` · ${gpu.utilization_pct}% util`}
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className={`progress-fill ${pct != null && pct > 85 ? "progress-warn" : ""}`}
                      style={{ width: `${pct ?? 0}%` }}
                    />
                  </div>
                </div>
              )}

              {svcs.length === 0 ? (
                <p className="muted" style={{ margin: 0 }}>
                  No OCR service assigned to this GPU.
                </p>
              ) : (
                svcs.map((svc, si) => {
                  const st = stateLabel(svc);
                  return (
                    <div
                      key={svc.id}
                      style={{
                        marginTop: si > 0 ? "1rem" : 0,
                        paddingTop: si > 0 ? "1rem" : 0,
                        borderTop: si > 0 ? "1px solid var(--border)" : undefined,
                      }}
                    >
                      <p style={{ margin: "0 0 0.5rem" }}>
                        <strong>{svc.label}</strong>
                        <span className={`badge gpu-badge ${st.className}`}>{st.text}</span>
                      </p>
                      <p className="muted" style={{ margin: "0 0 0.75rem", fontSize: "0.8rem" }}>
                        {svc.models.length > 0 ? (
                          <>
                            <span className="muted">Models:</span> {svc.models.join(", ")}
                          </>
                        ) : (
                          <span className="muted">Models: —</span>
                        )}
                        <br />
                        Port {svc.port}
                        {svc.compose_service ? ` · ${svc.compose_service}` : " · (local CLI)"}
                      </p>
                      <div className="row">
                        {svc.api_ready || svc.docker_state === "running" || svc.docker_state === "starting" ? (
                          <button
                            type="button"
                            disabled={!data?.manage_enabled || busyId !== null}
                            onClick={() => handleStop(svc.id)}
                          >
                            {busyId === svc.id ? (
                              <>
                                <span className="spinner" /> Stopping…
                              </>
                            ) : (
                              "Unload (free GPU)"
                            )}
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="primary"
                            disabled={!data?.manage_enabled || busyId !== null}
                            onClick={() => handleStart(svc.id)}
                          >
                            {busyId === svc.id ? (
                              <>
                                <span className="spinner" /> Loading…
                              </>
                            ) : (
                              "Load model"
                            )}
                          </button>
                        )}
                      </div>
                      {(svc.docker_state === "running" || svc.docker_state === "starting") && !svc.api_ready && (
                        <p className="muted" style={{ marginTop: "0.75rem", marginBottom: 0 }}>
                          First load can take 15–30+ minutes (weights download). Page refreshes every 5s.
                        </p>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          );
        })}
      </div>

      {services.length > 0 && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h2>All OCR services</h2>
          <ul className="gpu-service-list">
            {services.map((s) => {
              const st = stateLabel(s);
              return (
                <li key={s.id}>
                  <span>
                    {s.label} (GPU {s.gpu_device})
                    {s.models.length > 0 && (
                      <span className="muted" style={{ display: "block", fontSize: "0.8rem", marginTop: "0.15rem" }}>
                        {s.models.join(", ")}
                      </span>
                    )}
                  </span>
                  <span className={`badge gpu-badge ${st.className}`}>{st.text}</span>
                  {s.compose_service ? (
                    <span className="row">
                      {s.api_ready || s.docker_state === "running" || s.docker_state === "starting" ? (
                        <button
                          type="button"
                          disabled={!data?.manage_enabled || busyId !== null}
                          onClick={() => handleStop(s.id)}
                        >
                          Unload
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="primary"
                          disabled={!data?.manage_enabled || busyId !== null}
                          onClick={() => handleStart(s.id)}
                        >
                          Load
                        </button>
                      )}
                    </span>
                  ) : (
                    <span className="muted">Local CLI — not managed here</span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
