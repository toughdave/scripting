#!/usr/bin/env python3
"""Profile a CSV file and output column-level quality stats as JSON."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

NULL_VALUES = {"", "null", "none", "na", "n/a"}


def is_null(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in NULL_VALUES


def to_number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def profile_csv(input_path: Path) -> dict[str, Any]:
    with input_path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        rows = list(reader)

    profile: dict[str, Any] = {
        "file": str(input_path),
        "row_count": len(rows),
        "column_count": len(headers),
        "columns": {},
    }

    for header in headers:
        values = [(row.get(header) or "").strip() for row in rows]
        non_null = [v for v in values if not is_null(v)]
        null_count = len(values) - len(non_null)

        numeric_values = [to_number(v) for v in non_null]
        numeric_clean = [n for n in numeric_values if n is not None]
        is_numeric_column = bool(non_null) and len(numeric_clean) == len(non_null)

        col_profile: dict[str, Any] = {
            "null_count": null_count,
            "null_rate": round((null_count / len(values)), 4) if values else 0.0,
            "distinct_count": len(set(non_null)),
            "sample_values": sorted(set(non_null))[:5],
        }

        if is_numeric_column:
            col_profile["numeric_min"] = min(numeric_clean)
            col_profile["numeric_max"] = max(numeric_clean)

        profile["columns"][header] = col_profile

    return profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile CSV columns and output JSON stats.")
    parser.add_argument("--input", required=True, help="Path to source CSV file")
    parser.add_argument("--output", required=True, help="Path to write JSON profile")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    result = profile_csv(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(
        f"Profile complete: rows={result['row_count']}, columns={result['column_count']} -> {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
