import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getGpuDashboard,
  putGpuDeviceAssignments,
  recycleVllmService,
  startVllmService,
  stopAllVllmServices,
  stopVllmService,
  stopVllmServicesOnGpu,
} from "../api/client";
import type { GpuDashboard, GpuInfo, ModelVramDetail, VllmServiceStatus } from "../types";

function formatGib(n: number): string {
  return n < 10 ? `~${n.toFixed(1)} GiB` : `~${Math.round(n)} GiB`;
}

function formatParamsB(n: number): string {
  return n < 1 ? `${(n * 1000).toFixed(0)}M params` : `~${n % 1 === 0 ? n.toFixed(0) : n.toFixed(1)}B params`;
}

function memoryEstimateLine(svc: VllmServiceStatus): string | null {
  if (svc.vram_estimate_gib != null) {
    const span =
      svc.vram_estimate_gib_min != null && svc.vram_estimate_gib_min < svc.vram_estimate_gib
        ? `${formatGib(svc.vram_estimate_gib_min)}–${formatGib(svc.vram_estimate_gib)} VRAM`
        : `${formatGib(svc.vram_estimate_gib)} VRAM`;
    const params = svc.model_details?.find((d) => d.params_b != null)?.params_b;
    return params != null ? `${span} · ${formatParamsB(params)}` : span;
  }
  if (svc.ram_estimate_gib != null) {
    return `${formatGib(svc.ram_estimate_gib)} RAM (CPU)`;
  }
  return null;
}

function modelDetailLines(details: ModelVramDetail[] | undefined): string[] {
  if (!details?.length) return [];
  return details.map((d) => {
    const parts: string[] = [];
    if (d.vram_gib != null) parts.push(formatGib(d.vram_gib));
    else if (d.ram_gib != null) parts.push(`${formatGib(d.ram_gib)} RAM`);
    if (d.params_b != null) parts.push(formatParamsB(d.params_b));
    const size = parts.length ? ` (${parts.join(", ")})` : "";
    return `${d.id}${size}`;
  });
}

function vramFitWarning(svc: VllmServiceStatus, gpu: GpuInfo | undefined): string | null {
  if (!gpu || svc.gpu_device !== gpu.index || svc.vram_estimate_gib == null) return null;
  if (isActivelyLoaded(svc)) return null;
  const freeGib = (gpu.memory_total_mib - gpu.memory_used_mib) / 1024;
  if (svc.vram_estimate_gib > freeGib * 0.92) {
    return `May not fit: est. ${formatGib(svc.vram_estimate_gib)} vs ${freeGib.toFixed(0)} GiB free on this GPU`;
  }
  return null;
}

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

function isActivelyLoaded(s: VllmServiceStatus): boolean {
  const ds = s.docker_state;
  if (ds === "running" || ds === "starting") return true;
  return Boolean(s.api_ready);
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

function gpuPickerValues(gpus: GpuInfo[], services: VllmServiceStatus[]): number[] {
  const s = new Set<number>();
  gpus.forEach((g) => s.add(g.index));
  services.forEach((x) => s.add(x.gpu_device));
  for (let i = -1; i <= 7; i++) s.add(i);
  return [...s].sort((a, b) => a - b);
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

  const gpuOptionList = useMemo(
    () => gpuPickerValues(data?.gpus ?? [], data?.services ?? []),
    [data?.gpus, data?.services]
  );

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

  const handleStopAll = async () => {
    if (!data?.manage_enabled) return;
    if (
      !window.confirm("Stop every loaded OCR compose service on this host? This frees all GPU VRAM it holds.")
    ) {
      return;
    }
    setBusyId("stop-all");
    setActionMsg(null);
    setError(null);
    try {
      const r = await stopAllVllmServices();
      setActionMsg(r.message + (r.errors?.length ? ` See ${r.errors.length} error(s).` : ""));
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Bulk stop failed");
    } finally {
      setBusyId(null);
    }
  };

  const handleStopGpu = async (gpuIndex: number) => {
    if (!data?.manage_enabled) return;
    if (
      !window.confirm(`Stop every loaded OCR service assigned to GPU ${gpuIndex} in this UI (running or loading)?`)
    ) {
      return;
    }
    setBusyId(`stop-gpu-${gpuIndex}`);
    setActionMsg(null);
    setError(null);
    try {
      const r = await stopVllmServicesOnGpu(gpuIndex);
      setActionMsg(r.message + (r.errors?.length ? ` See ${r.errors.length} error(s).` : ""));
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "GPU bulk stop failed");
    } finally {
      setBusyId(null);
    }
  };

  const handleGpuAssignmentChange = async (svc: VllmServiceStatus, nextGpu: number) => {
    if (!svc.gpu_assignment_supported || nextGpu === svc.gpu_device) return;
    setBusyId(`gpu:${svc.id}`);
    setActionMsg(null);
    setError(null);
    try {
      const put = await putGpuDeviceAssignments({ assignments: { [svc.id]: nextGpu } });
      setActionMsg(put.message ?? "GPU assignment updated");
      await refresh();
      const needsRecycle = Boolean(data?.manage_enabled && svc.compose_service && isActivelyLoaded(svc));
      if (needsRecycle) {
        const r = await recycleVllmService(svc.id);
        setActionMsg(r.message);
        await refresh();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "GPU assignment failed");
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

  const hasComposeServices = services.some((s) => Boolean(s.compose_service?.trim()));
  const busy = busyId !== null;

  return (
    <div>
      <h1>GPU &amp; models</h1>
      <p className="muted" style={{ marginTop: "-0.5rem", marginBottom: "1rem" }}>
        Each OCR model can run as its own container. Stop a service to free VRAM; load when you need it. GPU index
        overrides are applied when compose starts a service (or use recycle after a change while one is loaded).
        Model sizes are catalog estimates (weights + typical overhead), not live measurements.
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

      {data?.manage_enabled && hasComposeServices && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <div className="row" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
            <p style={{ margin: 0 }} className="muted">
              Stop every compose service that is running or still loading models.
            </p>
            <button type="button" disabled={busy} onClick={handleStopAll}>
              {busyId === "stop-all" ? (
                <>
                  <span className="spinner" /> Stopping…
                </>
              ) : (
                "Unload all OCR engines"
              )}
            </button>
          </div>
        </div>
      )}

      <div className="gpu-grid">
        {gpuIndices.map((idx) => {
          const gpu = gpus.find((g) => g.index === idx);
          const svcs = servicesOnGpu(services, idx);
          const pct = gpu ? memPct(gpu) : null;
          const hasActiveOnCard = svcs.some((s) => isActivelyLoaded(s) && s.compose_service);

          return (
            <div key={idx} className="card gpu-card">
              <div
                className="row"
                style={{
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.75rem",
                  flexWrap: "wrap",
                  gap: "0.5rem",
                }}
              >
                <h2 style={{ margin: 0 }}>
                  GPU {idx}
                  {gpu?.name && <span className="muted"> — {gpu.name}</span>}
                </h2>
                {data?.manage_enabled && hasActiveOnCard && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => handleStopGpu(idx)}
                  >
                    {busyId === `stop-gpu-${idx}` ? (
                      <>
                        <span className="spinner" /> Stopping…
                      </>
                    ) : (
                      "Unload all on this GPU"
                    )}
                  </button>
                )}
              </div>

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
                  No OCR service assigned to this GPU in this view.
                </p>
              ) : (
                svcs.map((svc, si) => {
                  const st = stateLabel(svc);
                  const showAssign = Boolean(svc.gpu_assignment_supported && svc.compose_service);
                  const memLine = memoryEstimateLine(svc);
                  const fitWarn = vramFitWarning(svc, gpu);
                  const detailLines = modelDetailLines(svc.model_details);
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
                        {memLine && (
                          <>
                            <span className="muted">Est. size:</span> {memLine}
                            <br />
                          </>
                        )}
                        {detailLines.length > 1 && (
                          <>
                            {detailLines.map((line) => (
                              <span key={line} style={{ display: "block" }}>
                                {line}
                              </span>
                            ))}
                          </>
                        )}
                        {svc.model_details?.some((d) => d.note) && (
                          <span style={{ display: "block", fontStyle: "italic" }}>
                            {svc.model_details.find((d) => d.note)?.note}
                          </span>
                        )}
                        {fitWarn && (
                          <span className="gpu-fit-warn" style={{ display: "block", marginTop: "0.25rem" }}>
                            {fitWarn}
                          </span>
                        )}
                        Port {svc.port}
                        {svc.compose_service ? ` · ${svc.compose_service}` : " · (local CLI)"}
                      </p>
                      {showAssign && (
                        <label className="row" style={{ marginBottom: "0.75rem", gap: "0.5rem", alignItems: "center" }}>
                          <span className="muted">Compose GPU index</span>
                          <select
                            value={svc.gpu_device}
                            disabled={busy}
                            onChange={(e) => handleGpuAssignmentChange(svc, Number(e.target.value))}
                          >
                            {gpuOptionList.map((n) => (
                              <option key={n} value={n}>
                                {n === -1 ? `${n} (CPU / no device)` : n}
                              </option>
                            ))}
                          </select>
                        </label>
                      )}
                      <div className="row">
                        {svc.api_ready || svc.docker_state === "running" || svc.docker_state === "starting" ? (
                          <button
                            type="button"
                            disabled={!data?.manage_enabled || busy}
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
                            disabled={!data?.manage_enabled || busy}
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
              const showAssign = Boolean(s.gpu_assignment_supported && s.compose_service);
              const memLine = memoryEstimateLine(s);
              return (
                <li key={s.id}>
                  <span>
                    {s.label} (GPU {s.gpu_device})
                    {s.models.length > 0 && (
                      <span className="muted" style={{ display: "block", fontSize: "0.8rem", marginTop: "0.15rem" }}>
                        {s.models.join(", ")}
                      </span>
                    )}
                    {memLine && (
                      <span className="muted" style={{ display: "block", fontSize: "0.8rem" }}>
                        {memLine}
                      </span>
                    )}
                  </span>
                  {showAssign && (
                    <label className="row" style={{ gap: "0.35rem", alignItems: "center" }}>
                      <span className="muted">GPU</span>
                      <select
                        value={s.gpu_device}
                        disabled={busy}
                        onChange={(e) => handleGpuAssignmentChange(s, Number(e.target.value))}
                      >
                        {gpuOptionList.map((n) => (
                          <option key={n} value={n}>
                            {n}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                  <span className={`badge gpu-badge ${st.className}`}>{st.text}</span>
                  {s.compose_service ? (
                    <span className="row">
                      {s.api_ready || s.docker_state === "running" || s.docker_state === "starting" ? (
                        <button
                          type="button"
                          disabled={!data?.manage_enabled || busy}
                          onClick={() => handleStop(s.id)}
                        >
                          Unload
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="primary"
                          disabled={!data?.manage_enabled || busy}
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
