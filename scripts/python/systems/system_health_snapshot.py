#!/usr/bin/env python3
"""Capture a lightweight system health snapshot (CPU, memory, disk, platform)."""

from __future__ import annotations

import argparse
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path


def bytes_to_gb(value: int | float) -> float:
    return round(float(value) / (1024**3), 3)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write system health snapshot JSON.")
    parser.add_argument("--output", required=True, help="Output JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    snapshot = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
    }

    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        du = psutil.disk_usage("/")
        snapshot["cpu_percent"] = psutil.cpu_percent(interval=0.2)
        snapshot["memory"] = {
            "total_gb": bytes_to_gb(vm.total),
            "available_gb": bytes_to_gb(vm.available),
            "used_percent": vm.percent,
        }
        snapshot["disk_root"] = {
            "total_gb": bytes_to_gb(du.total),
            "free_gb": bytes_to_gb(du.free),
            "used_percent": du.percent,
        }
    except Exception:
        # Fallback without psutil
        st = os.statvfs("/")
        total = st.f_frsize * st.f_blocks
        free = st.f_frsize * st.f_bavail
        used = total - free
        used_pct = round((used / total) * 100, 2) if total else 0.0
        snapshot["cpu_percent"] = None
        snapshot["memory"] = {"total_gb": None, "available_gb": None, "used_percent": None}
        snapshot["disk_root"] = {
            "total_gb": bytes_to_gb(total),
            "free_gb": bytes_to_gb(free),
            "used_percent": used_pct,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    print(f"System snapshot written -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
