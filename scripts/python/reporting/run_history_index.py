#!/usr/bin/env python3
"""Update a cross-run history index from run manifest artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Append or upsert a run entry in a run-history JSON index "
            "using data from a generated run manifest."
        )
    )
    parser.add_argument("--manifest", required=True, help="Path to run manifest JSON")
    parser.add_argument("--history", required=True, help="Path to run history JSON")
    parser.add_argument("--max-entries", type=int, default=200, help="Maximum run entries to retain")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def normalize_history(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        runs = payload.get("runs")
        if isinstance(runs, list):
            return [row for row in runs if isinstance(row, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def main() -> int:
    args = parse_args()

    if args.max_entries < 1:
        raise ValueError(f"--max-entries must be a positive integer (received: {args.max_entries})")

    manifest_path = Path(args.manifest).resolve()
    history_path = Path(args.history).resolve()

    manifest = load_json(manifest_path)
    run_id = str(manifest.get("run_id") or "").strip()
    if not run_id:
        raise ValueError(f"Manifest is missing run_id: {manifest_path}")

    entry = {
        "run_id": run_id,
        "status": str(manifest.get("status") or ""),
        "generated_utc": str(manifest.get("generated_utc") or ""),
        "manifest_file": str(manifest_path),
        "log_file": str((manifest.get("paths") or {}).get("log_file") or ""),
        "steps_file": str((manifest.get("paths") or {}).get("steps_file") or ""),
        "counts": {
            "report_files": int((manifest.get("counts") or {}).get("report_files") or 0),
            "output_files": int((manifest.get("counts") or {}).get("output_files") or 0),
            "steps_total": int((manifest.get("counts") or {}).get("steps_total") or 0),
            "steps_failed": int((manifest.get("counts") or {}).get("steps_failed") or 0),
            "steps_retried": int((manifest.get("counts") or {}).get("steps_retried") or 0),
        },
    }

    existing_runs: list[dict[str, Any]] = []
    if history_path.exists() and history_path.is_file():
        try:
            existing_payload = load_json(history_path)
            existing_runs = normalize_history(existing_payload)
        except json.JSONDecodeError:
            existing_runs = []

    merged_runs = [row for row in existing_runs if str(row.get("run_id") or "") != run_id]
    merged_runs.append(entry)
    merged_runs.sort(key=lambda row: str(row.get("generated_utc") or ""), reverse=True)
    merged_runs = merged_runs[: args.max_entries]

    payload = {
        "updated_utc": datetime.now(tz=timezone.utc).isoformat(),
        "max_entries": args.max_entries,
        "total_runs": len(merged_runs),
        "runs": merged_runs,
    }

    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(
        "Run history updated: "
        f"run_id={run_id}, total_runs={payload['total_runs']} -> {history_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
