#!/usr/bin/env python3
"""Interactive GPU usage viewer — list compute clients and optionally stop them."""

from __future__ import annotations

import csv
import getpass
import io
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Optional

_SIGTERM = getattr(signal, "SIGTERM", 15)
_SIGKILL = getattr(signal, "SIGKILL", 9)


@dataclass(frozen=True)
class GpuInfo:
    index: int
    uuid: str
    name: str
    memory_used_mib: int
    memory_total_mib: int
    util_pct: Optional[int]


@dataclass(frozen=True)
class GpuProcess:
    list_index: int
    gpu_index: int
    pid: int
    process_name: str
    memory_mib: int
    user: str
    cmdline: str
    container_hint: str


def _run_nvidia_smi(*args: str) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["nvidia-smi", *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        return 127, "", "nvidia-smi not found (install NVIDIA drivers)"
    except subprocess.TimeoutExpired:
        return 124, "", "nvidia-smi timed out"
    return proc.returncode, proc.stdout, proc.stderr


def _parse_csv_rows(text: str) -> list[list[str]]:
    text = text.strip()
    if not text:
        return []
    reader = csv.reader(io.StringIO(text))
    return [[cell.strip() for cell in row] for row in reader]


def _proc_field(pid: int, name: str) -> str:
    try:
        with open(f"/proc/{pid}/{name}", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return ""


def _process_user(pid: int) -> str:
    status = _proc_field(pid, "status")
    for line in status.splitlines():
        if line.startswith("Uid:"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    import pwd

                    return pwd.getpwuid(int(parts[1])).pw_name
                except (ImportError, KeyError, ValueError):
                    return parts[1]
    try:
        st = os.stat(f"/proc/{pid}")
        import pwd

        return pwd.getpwuid(st.st_uid).pw_name
    except (OSError, ImportError, KeyError):
        return "?"


def _process_cmdline(pid: int) -> str:
    raw = _proc_field(pid, "cmdline")
    if raw:
        return raw.replace("\0", " ").strip() or "?"
    comm = _proc_field(pid, "comm")
    return comm or "?"


def _container_hint(pid: int) -> str:
    cgroup = _proc_field(pid, "cgroup")
    if not cgroup:
        return ""
    for line in cgroup.splitlines():
        if "docker" in line or "containerd" in line or "kubepods" in line:
            parts = line.rsplit("/", 1)
            if len(parts) == 2 and parts[1]:
                short = parts[1]
                if len(short) > 14:
                    short = short[:12] + "…"
                return short
    return ""


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def query_gpus() -> tuple[list[GpuInfo], str | None]:
    code, out, err = _run_nvidia_smi(
        "--query-gpu=index,uuid,name,memory.used,memory.total,utilization.gpu",
        "--format=csv,noheader,nounits",
    )
    if code != 0:
        return [], (err or out or "nvidia-smi failed").strip()

    gpus: list[GpuInfo] = []
    for row in _parse_csv_rows(out):
        if len(row) < 5:
            continue
        try:
            util: Optional[int] = None
            if len(row) > 5 and row[5] not in ("", "[N/A]", "N/A"):
                util = int(float(row[5]))
            gpus.append(
                GpuInfo(
                    index=int(row[0]),
                    uuid=row[1],
                    name=row[2],
                    memory_used_mib=int(float(row[3])),
                    memory_total_mib=int(float(row[4])),
                    util_pct=util,
                )
            )
        except ValueError:
            continue
    return gpus, None


def query_gpu_processes(uuid_to_index: dict[str, int]) -> tuple[list[GpuProcess], str | None]:
    code, out, err = _run_nvidia_smi(
        "--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory",
        "--format=csv,noheader,nounits",
    )
    if code != 0:
        return [], (err or out or "nvidia-smi compute-apps query failed").strip()

    processes: list[GpuProcess] = []
    for i, row in enumerate(_parse_csv_rows(out), start=1):
        if len(row) < 4:
            continue
        uuid, pid_s, pname, mem_s = row[0], row[1], row[2], row[3]
        gpu_index = uuid_to_index.get(uuid, -1)
        try:
            pid = int(pid_s)
            memory_mib = int(float(mem_s))
        except ValueError:
            continue
        processes.append(
            GpuProcess(
                list_index=i,
                gpu_index=gpu_index,
                pid=pid,
                process_name=pname,
                memory_mib=memory_mib,
                user=_process_user(pid) if _pid_alive(pid) else "?",
                cmdline=_process_cmdline(pid) if _pid_alive(pid) else "(exited)",
                container_hint=_container_hint(pid) if _pid_alive(pid) else "",
            )
        )
    processes.sort(key=lambda p: (p.gpu_index, -p.memory_mib, p.pid))
    return [
        GpuProcess(
            list_index=i,
            gpu_index=p.gpu_index,
            pid=p.pid,
            process_name=p.process_name,
            memory_mib=p.memory_mib,
            user=p.user,
            cmdline=p.cmdline,
            container_hint=p.container_hint,
        )
        for i, p in enumerate(processes, start=1)
    ], None


def _bar(used: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "[" + "?" * width + "]"
    frac = min(1.0, max(0.0, used / total))
    filled = int(frac * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def print_snapshot(gpus: list[GpuInfo], processes: list[GpuProcess]) -> None:
    print()
    print("=" * 72)
    print("  GPU summary")
    print("=" * 72)
    if not gpus:
        print("  (no GPUs reported)")
    for g in gpus:
        util = f"{g.util_pct}%" if g.util_pct is not None else "n/a"
        pct = 100.0 * g.memory_used_mib / g.memory_total_mib if g.memory_total_mib else 0
        print(
            f"  GPU {g.index}: {g.name}  "
            f"{g.memory_used_mib:,} / {g.memory_total_mib:,} MiB ({pct:.0f}%)  util {util}"
        )
        print(f"           {_bar(g.memory_used_mib, g.memory_total_mib)}")

    print()
    print("-" * 72)
    print("  Processes using GPU memory (via nvidia-smi)")
    print("-" * 72)
    if not processes:
        print("  (none)")
        return

    me = getpass.getuser()
    for p in processes:
        gpu = f"GPU {p.gpu_index}" if p.gpu_index >= 0 else "GPU ?"
        alive = _pid_alive(p.pid)
        owner_mark = "" if p.user == me or p.user == "?" else "  [other user]"
        docker = f"  container:{p.container_hint}" if p.container_hint else ""
        status = "" if alive else "  [pid not running]"
        cmd = p.cmdline if len(p.cmdline) <= 90 else p.cmdline[:87] + "..."
        print(
            f"  [{p.list_index:2}] {gpu}  PID {p.pid:>7}  {p.memory_mib:>6} MiB  "
            f"{p.user:<12}{owner_mark}{status}"
        )
        print(f"       name: {p.process_name}{docker}")
        print(f"       cmd:  {cmd}")
    print()


def _confirm(prompt: str) -> bool:
    try:
        ans = input(f"{prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return ans in ("y", "yes")


def _send_signal(pid: int, sig: int, sig_name: str) -> tuple[bool, str]:
    if pid <= 1:
        return False, "refusing to signal init or invalid pid"
    if not _pid_alive(pid):
        return True, "process already exited"
    try:
        os.kill(pid, sig)
    except PermissionError:
        return False, f"permission denied (try sudo for PID {pid})"
    except ProcessLookupError:
        return True, "process already exited"
    except OSError as e:
        return False, str(e)
    return True, f"sent {sig_name} to {pid}"


def _wait_exit(pid: int, timeout: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.25)
    return not _pid_alive(pid)


def stop_process(
    proc: GpuProcess,
    *,
    force: bool = False,
) -> bool:
    if not _pid_alive(proc.pid):
        print(f"  PID {proc.pid} is not running.")
        return True

    print(f"  Target: PID {proc.pid} ({proc.user}) — {proc.process_name}")
    print(f"  Cmd:    {proc.cmdline}")
    if proc.user != getpass.getuser() and proc.user != "?":
        print(f"  Warning: process owner is '{proc.user}', not you.")

    if not force and not _confirm("  Send SIGTERM?"):
        print("  Cancelled.")
        return False

    ok, msg = _send_signal(proc.pid, _SIGTERM, "SIGTERM")
    print(f"  {msg}")
    if not ok:
        return False

    if _wait_exit(proc.pid):
        print(f"  PID {proc.pid} exited.")
        return True

    if force:
        ok, msg = _send_signal(proc.pid, _SIGKILL, "SIGKILL")
        print(f"  {msg}")
        if ok and _wait_exit(proc.pid, timeout=3.0):
            print(f"  PID {proc.pid} killed.")
            return True
        print(f"  PID {proc.pid} may still be running.")
        return not _pid_alive(proc.pid)

    if _confirm("  Still running. Send SIGKILL?"):
        ok, msg = _send_signal(proc.pid, _SIGKILL, "SIGKILL")
        print(f"  {msg}")
        if ok and _wait_exit(proc.pid, timeout=3.0):
            print(f"  PID {proc.pid} killed.")
            return True
    print(f"  PID {proc.pid} may still be running.")
    return not _pid_alive(proc.pid)


def _pick_process(processes: list[GpuProcess], prompt: str) -> Optional[GpuProcess]:
    if not processes:
        print("  No GPU processes to act on.")
        return None
    try:
        raw = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        print("  Enter a list number from the table above.")
        return None
    for p in processes:
        if p.list_index == n:
            return p
    print(f"  No process with list index [{n}].")
    return None


def _refresh() -> tuple[list[GpuInfo], list[GpuProcess], str | None]:
    gpus, err = query_gpus()
    if err:
        return [], [], err
    uuid_to_index = {g.uuid: g.index for g in gpus}
    processes, perr = query_gpu_processes(uuid_to_index)
    if perr:
        return gpus, [], perr
    return gpus, processes, None


def _menu() -> None:
    print("free_gpu — interactive GPU memory manager")
    print(f"Running as: {getpass.getuser()}")
    print("Press Ctrl+C anytime to quit.\n")

    gpus: list[GpuInfo] = []
    processes: list[GpuProcess] = []

    while True:
        gpus, processes, err = _refresh()
        if err:
            print(f"\nError: {err}\n")
        print_snapshot(gpus, processes)

        print("Actions:")
        print("  [r] Refresh")
        print("  [k] Stop one process (by list number)")
        print("  [g] Stop all processes on a GPU index")
        print("  [p] Stop by PID")
        print("  [q] Exit")
        try:
            choice = input("\nChoice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if choice in ("q", "quit", "exit"):
            print("Bye.")
            break
        if choice in ("r", "refresh"):
            continue
        if choice in ("k", "kill"):
            proc = _pick_process(processes, "  List number to stop: ")
            if proc:
                stop_process(proc)
            input("\n  Press Enter to continue...")
            continue
        if choice in ("g", "gpu"):
            try:
                raw = input("  GPU index (0, 1, …): ").strip()
                gpu_idx = int(raw)
            except (EOFError, KeyboardInterrupt):
                print()
                continue
            except ValueError:
                print("  Invalid GPU index.")
                input("\n  Press Enter to continue...")
                continue
            targets = [p for p in processes if p.gpu_index == gpu_idx]
            if not targets:
                print(f"  No processes on GPU {gpu_idx}.")
            elif _confirm(f"  SIGTERM {len(targets)} process(es) on GPU {gpu_idx}?"):
                for p in targets:
                    print(f"\n--- [{p.list_index}] PID {p.pid} ---")
                    stop_process(p, force=True)
            input("\n  Press Enter to continue...")
            continue
        if choice in ("p", "pid"):
            try:
                raw = input("  PID: ").strip()
                pid = int(raw)
            except (EOFError, KeyboardInterrupt):
                print()
                continue
            except ValueError:
                print("  Invalid PID.")
                input("\n  Press Enter to continue...")
                continue
            match = next((p for p in processes if p.pid == pid), None)
            if match:
                stop_process(match)
            else:
                stub = GpuProcess(
                    list_index=0,
                    gpu_index=-1,
                    pid=pid,
                    process_name="(manual)",
                    memory_mib=0,
                    user=_process_user(pid) if _pid_alive(pid) else "?",
                    cmdline=_process_cmdline(pid) if _pid_alive(pid) else "(exited)",
                    container_hint=_container_hint(pid) if _pid_alive(pid) else "",
                )
                stop_process(stub)
            input("\n  Press Enter to continue...")
            continue

        print("  Unknown choice. Use r, k, g, p, or q.")
        input("\n  Press Enter to continue...")


def main() -> int:
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        print("Note: running as root — you can stop any user's GPU processes.\n")
    try:
        _menu()
    except KeyboardInterrupt:
        print("\nBye.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
