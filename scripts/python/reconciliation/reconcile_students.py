#!/usr/bin/env python3
"""Reconcile admissions/result student records across source and target datasets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def index_rows(rows: list[dict[str, str]], key: str) -> tuple[dict[str, dict[str, str]], int, int]:
    indexed: dict[str, dict[str, str]] = {}
    duplicates = 0
    missing_key = 0

    for row in rows:
        record_key = normalize(row.get(key))
        if not record_key:
            missing_key += 1
            continue
        if record_key in indexed:
            duplicates += 1
            continue
        indexed[record_key] = row

    return indexed, duplicates, missing_key


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile student records between upstream operational extracts "
            "and downstream reporting/approval datasets."
        )
    )
    parser.add_argument("--source", required=True, help="Source CSV path (e.g., admissions/result operations)")
    parser.add_argument("--target", required=True, help="Target CSV path (e.g., reporting or approved register)")
    parser.add_argument("--output", required=True, help="Output reconciliation CSV")
    parser.add_argument("--summary", required=True, help="Output reconciliation summary JSON")
    parser.add_argument("--key", default="student_id", help="Record key column")
    parser.add_argument(
        "--compare-columns",
        nargs="*",
        default=["score", "status", "email", "department"],
        help="Columns to compare when key exists in both datasets",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = Path(args.source)
    target_path = Path(args.target)
    output_path = Path(args.output)
    summary_path = Path(args.summary)

    source_rows = read_rows(source_path)
    target_rows = read_rows(target_path)

    source_idx, source_dupes, source_missing_key = index_rows(source_rows, args.key)
    target_idx, target_dupes, target_missing_key = index_rows(target_rows, args.key)

    all_keys = sorted(set(source_idx) | set(target_idx))

    result_rows: list[dict[str, str]] = []
    counts = {
        "match": 0,
        "mismatch": 0,
        "source_only": 0,
        "target_only": 0,
    }

    for record_key in all_keys:
        source_row = source_idx.get(record_key)
        target_row = target_idx.get(record_key)

        if source_row and not target_row:
            status = "source_only"
            mismatches: list[str] = []
        elif target_row and not source_row:
            status = "target_only"
            mismatches = []
        else:
            mismatches = []
            for col in args.compare_columns:
                if normalize(source_row.get(col)) != normalize(target_row.get(col)):
                    mismatches.append(col)
            status = "mismatch" if mismatches else "match"

        counts[status] += 1

        out_row = {
            "record_key": record_key,
            "status": status,
            "mismatch_columns": "|".join(mismatches),
        }
        for col in args.compare_columns:
            out_row[f"source_{col}"] = normalize(source_row.get(col)) if source_row else ""
            out_row[f"target_{col}"] = normalize(target_row.get(col)) if target_row else ""

        result_rows.append(out_row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["record_key", "status", "mismatch_columns"] + [
        item for col in args.compare_columns for item in (f"source_{col}", f"target_{col}")
    ]

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result_rows)

    summary = {
        "source_records": len(source_rows),
        "target_records": len(target_rows),
        "source_duplicates_ignored": source_dupes,
        "target_duplicates_ignored": target_dupes,
        "source_missing_key_rows": source_missing_key,
        "target_missing_key_rows": target_missing_key,
        "counts": counts,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Reconciliation complete: {counts} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
