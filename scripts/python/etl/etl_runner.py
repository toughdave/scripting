#!/usr/bin/env python3
"""Config-driven ETL for admissions/result CSV pipelines (extract -> transform -> validate -> load)."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%Y-%m-%d %H:%M:%S",
)


def normalize_date(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(base_dir: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run ETL for operational academic datasets using JSON configuration "
            "(cleaning, date normalization, required-field checks, and dedupe)."
        )
    )
    parser.add_argument("--config", required=True, help="Path to ETL config JSON")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write output dataset. Without this flag, runs in dry mode.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    cfg = load_config(config_path)
    config_dir = config_path.parent
    source_csv = resolve_path(config_dir, cfg["source_csv"])
    output_csv = resolve_path(config_dir, cfg["output_csv"])
    summary_json = resolve_path(config_dir, cfg.get("summary_json", "reports/etl_summary.json"))

    if not source_csv.exists():
        raise FileNotFoundError(f"Source CSV not found: {source_csv}")

    required_columns = cfg.get("required_columns", [])
    date_columns = set(cfg.get("date_columns", []))
    drop_duplicates_by = cfg.get("drop_duplicates_by", [])

    with source_csv.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        rows = list(reader)

    missing_required_cols = [c for c in required_columns if c not in headers]

    transformed: list[dict[str, str]] = []
    seen = set()
    duplicate_rows_removed = 0
    missing_required_values = 0

    for row in rows:
        cleaned: dict[str, str] = {}
        for h in headers:
            value = (row.get(h) or "").strip()
            if h in date_columns and value:
                value = normalize_date(value)
            cleaned[h] = value

        row_missing = any(not cleaned.get(col, "") for col in required_columns)
        if row_missing:
            missing_required_values += 1

        if drop_duplicates_by:
            dedupe_key = tuple(cleaned.get(col, "") for col in drop_duplicates_by)
            if dedupe_key in seen:
                duplicate_rows_removed += 1
                continue
            seen.add(dedupe_key)

        transformed.append(cleaned)

    summary = {
        "config": str(config_path),
        "source_csv": str(source_csv),
        "output_csv": str(output_csv),
        "dry_run": not args.apply,
        "input_rows": len(rows),
        "output_rows": len(transformed),
        "duplicate_rows_removed": duplicate_rows_removed,
        "missing_required_columns": missing_required_cols,
        "rows_missing_required_values": missing_required_values,
        "required_columns": required_columns,
    }

    if args.apply:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=headers)
            writer.writeheader()
            writer.writerows(transformed)

    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(
        f"ETL {mode} complete: input={len(rows)} output={len(transformed)} "
        f"duplicates_removed={duplicate_rows_removed}"
    )
    print(f"Summary: {summary_json}")
    if args.apply:
        print(f"Output: {output_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
