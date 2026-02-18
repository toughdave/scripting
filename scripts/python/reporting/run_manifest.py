#!/usr/bin/env python3
"""Generate a run manifest for workflow observability artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a JSON run manifest that indexes workflow artifacts "
            "from reports/output directories with file metadata."
        )
    )
    parser.add_argument("--run-id", required=True, help="Run identifier (for example: 20260218-153323)")
    parser.add_argument("--status", default="success", help="Run status label")
    parser.add_argument("--report-dir", required=True, help="Path to report artifacts directory")
    parser.add_argument("--output-dir", required=True, help="Path to output artifacts directory")
    parser.add_argument("--log-file", required=True, help="Path to workflow log file")
    parser.add_argument("--steps-file", default="", help="Optional step status CSV path")
    parser.add_argument("--manifest", required=True, help="Output manifest JSON path")
    return parser.parse_args()


def collect_files(root: Path) -> list[dict[str, Any]]:
    if not root.exists() or not root.is_dir():
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        stat = path.stat()
        records.append(
            {
                "relative_path": str(path.relative_to(root)),
                "size_bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return records


def load_steps_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.is_file():
        return []

    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for item in reader:
            exit_code_raw = (item.get("exit_code") or "").strip()
            duration_raw = (item.get("duration_seconds") or "").strip()
            rows.append(
                {
                    "step": (item.get("step") or "").strip(),
                    "status": (item.get("status") or "").strip(),
                    "exit_code": int(exit_code_raw) if exit_code_raw.lstrip("-").isdigit() else None,
                    "start_utc": (item.get("start_utc") or "").strip(),
                    "end_utc": (item.get("end_utc") or "").strip(),
                    "duration_seconds": int(duration_raw) if duration_raw.isdigit() else None,
                }
            )
    return rows


def main() -> int:
    args = parse_args()

    report_dir = Path(args.report_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    log_file = Path(args.log_file).resolve()
    steps_file = Path(args.steps_file).resolve() if args.steps_file else None
    manifest_path = Path(args.manifest).resolve()

    report_files = collect_files(report_dir)
    output_files = collect_files(output_dir)
    steps = load_steps_csv(steps_file) if steps_file else []
    failed_steps = [row for row in steps if row.get("status") == "failed"]

    log_exists = log_file.exists()
    log_size = log_file.stat().st_size if log_exists else 0

    payload = {
        "run_id": args.run_id,
        "status": args.status,
        "generated_utc": datetime.now(tz=timezone.utc).isoformat(),
        "paths": {
            "report_dir": str(report_dir),
            "output_dir": str(output_dir),
            "log_file": str(log_file),
            "steps_file": str(steps_file) if steps_file else "",
        },
        "counts": {
            "report_files": len(report_files),
            "output_files": len(output_files),
            "total_files": len(report_files) + len(output_files),
            "steps_total": len(steps),
            "steps_failed": len(failed_steps),
        },
        "log": {
            "exists": log_exists,
            "size_bytes": log_size,
        },
        "steps": steps,
        "reports": report_files,
        "outputs": output_files,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(
        "Run manifest written: "
        f"run_id={args.run_id}, total_files={payload['counts']['total_files']} -> {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
