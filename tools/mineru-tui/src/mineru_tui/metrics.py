from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

import psutil


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def hostname() -> str:
    try:
        return platform.node() or "localhost"
    except Exception:
        return "localhost"


def cpu_percent() -> float:
    try:
        return float(psutil.cpu_percent(interval=None))
    except Exception:
        return 0.0


def cpu_bar(pct: float, width: int = 10) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = int(round((pct / 100.0) * width))
    filled = max(0, min(width, filled))
    return f"{'█' * filled}{'░' * (width - filled)}"


def load_avg_str() -> str:
    try:
        load = os.getloadavg()
        return f"{load[0]:.1f} / {load[1]:.1f} / {load[2]:.1f}"
    except (AttributeError, OSError):
        return "n/a"


def process_count() -> int:
    try:
        return len(psutil.pids())
    except Exception:
        return 0


def memory_str() -> str:
    try:
        vm = psutil.virtual_memory()
        used_g = vm.used / (1024**3)
        total_g = vm.total / (1024**3)
        return f"{used_g:.1f} / {total_g:.1f} GiB"
    except Exception:
        return "n/a"


def swap_str() -> str:
    try:
        sw = psutil.swap_memory()
        if sw.total == 0:
            return "0.0 / 0.0 GiB"
        u = sw.used / (1024**3)
        t = sw.total / (1024**3)
        return f"{u:.1f} / {t:.1f} GiB"
    except Exception:
        return "n/a"


def temp_str() -> str:
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return "n/a"
        best: float | None = None
        for _name, entries in temps.items():
            for e in entries:
                if e.current is None:
                    continue
                if best is None or e.current > best:
                    best = e.current
        if best is None:
            return "n/a"
        return f"{best:.0f}°C"
    except (AttributeError, NotImplementedError):
        return "n/a"


def disk_free_str(path: Path) -> str:
    try:
        resolved = path.resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(resolved)
        free_g = usage.free / (1024**3)
        return f"{free_g:.0f} GiB free"
    except OSError:
        return "n/a"


def docker_ps_running(container_name: str) -> bool:
    if not container_name or not _docker_available():
        return False
    try:
        r = subprocess.run(
            [
                "docker",
                "inspect",
                "-f",
                "{{.State.Running}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.returncode == 0 and r.stdout.strip().lower() == "true"
    except (OSError, subprocess.SubprocessError):
        return False


def docker_cpu_percent(container_name: str) -> str:
    if not container_name or not _docker_available():
        return "n/a"
    try:
        r = subprocess.run(
            [
                "docker",
                "stats",
                container_name,
                "--no-stream",
                "--format",
                "{{.CPUPerc}}",
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if r.returncode != 0:
            return "n/a"
        return r.stdout.strip() or "n/a"
    except (OSError, subprocess.SubprocessError):
        return "n/a"


def format_system_block(output_dir: Path, container_name: str | None) -> str:
    cpu = cpu_percent()
    lines = [
        f"CPU        {cpu:>3.0f}%  {cpu_bar(cpu)}",
        f"Load       {load_avg_str()}",
        f"Procs      {process_count()}",
        f"RAM        {memory_str()}",
        f"Swap       {swap_str()}",
        f"Temp       {temp_str()}",
        f"Disk out   {disk_free_str(output_dir)}",
        f"Docker CPU {docker_cpu_percent(container_name) if container_name else 'n/a'}",
    ]
    return "\n".join(lines)


_PAGE_RE = re.compile(
    r"(\d+)\s*/\s*(\d+)|(\d+)\s+of\s+(\d+)|page\s+(\d+)\s*/\s*(\d+)",
    re.I,
)


def parse_pages_from_log_line(line: str) -> tuple[int | None, int | None]:
    """Best-effort (done, total) extraction from MinerU / pipeline logs."""
    m = _PAGE_RE.search(line)
    if not m:
        return None, None
    if m.group(1) and m.group(2):
        return int(m.group(1)), int(m.group(2))
    if m.group(3) and m.group(4):
        return int(m.group(3)), int(m.group(4))
    if m.group(5) and m.group(6):
        return int(m.group(5)), int(m.group(6))
    return None, None
