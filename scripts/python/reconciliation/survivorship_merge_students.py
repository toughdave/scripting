#!/usr/bin/env python3
"""Create a survivorship merged student dataset from source and target extracts."""

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


def index_rows(rows: list[dict[str, str]], key_column: str) -> tuple[dict[str, dict[str, str]], int, int]:
    indexed: dict[str, dict[str, str]] = {}
    duplicate_count = 0
    missing_key_rows = 0

    for row in rows:
        record_key = normalize(row.get(key_column))
        if not record_key:
            missing_key_rows += 1
            continue
        if record_key in indexed:
            duplicate_count += 1
            continue
        indexed[record_key] = row

    return indexed, duplicate_count, missing_key_rows


def resolve_columns(
    source_rows: list[dict[str, str]],
    target_rows: list[dict[str, str]],
    key_column: str,
    requested_columns: list[str],
) -> list[str]:
    if requested_columns:
        return [col for col in requested_columns if col != key_column]

    source_columns = list(source_rows[0].keys()) if source_rows else []
    target_columns = list(target_rows[0].keys()) if target_rows else []

    combined = []
    seen: set[str] = set()
    for col in source_columns + target_columns:
        if col == key_column or col in seen:
            continue
        seen.add(col)
        combined.append(col)
    return combined


def choose_value(
    source_value: str,
    target_value: str,
    priority: list[str],
) -> tuple[str, str, bool]:
    """Return (chosen_value, chosen_from, is_conflict)."""
    source_value = normalize(source_value)
    target_value = normalize(target_value)

    if source_value and target_value and source_value == target_value:
        return source_value, "both", False

    if source_value and target_value and source_value != target_value:
        preferred = priority[0]
        if preferred == "source":
            return source_value, "source", True
        return target_value, "target", True

    if source_value:
        return source_value, "source", False

    if target_value:
        return target_value, "target", False

    return "", "none", False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a survivorship merge output for student records by resolving "
            "source vs target conflicts with an explicit priority order."
        )
    )
    parser.add_argument("--source", required=True, help="Source CSV path")
    parser.add_argument("--target", required=True, help="Target CSV path")
    parser.add_argument("--output", required=True, help="Merged output CSV path")
    parser.add_argument("--summary", required=True, help="Summary JSON path")
    parser.add_argument(
        "--conflicts-output",
        default="",
        help="Optional conflict details CSV path (defaults next to --output)",
    )
    parser.add_argument("--key", default="student_id", help="Primary key column")
    parser.add_argument(
        "--columns",
        nargs="*",
        default=[],
        help="Columns to merge (default: inferred from source + target headers)",
    )
    parser.add_argument(
        "--priority",
        nargs="+",
        default=["target", "source"],
        help="Conflict resolution order, e.g. --priority target source",
    )
    return parser.parse_args()


def validate_priority(priority: list[str]) -> list[str]:
    cleaned = [normalize(item).lower() for item in priority if normalize(item)]
    if not cleaned:
        return ["target", "source"]

    allowed = {"source", "target"}
    if any(item not in allowed for item in cleaned):
        invalid = [item for item in cleaned if item not in allowed]
        raise ValueError(f"Invalid priority option(s): {', '.join(invalid)}")

    ordered: list[str] = []
    for item in cleaned:
        if item not in ordered:
            ordered.append(item)

    for fallback in ("target", "source"):
        if fallback not in ordered:
            ordered.append(fallback)

    return ordered


def main() -> int:
    args = parse_args()

    source_path = Path(args.source)
    target_path = Path(args.target)
    output_path = Path(args.output)
    summary_path = Path(args.summary)

    if not source_path.exists():
        raise FileNotFoundError(f"Source CSV not found: {source_path}")
    if not target_path.exists():
        raise FileNotFoundError(f"Target CSV not found: {target_path}")

    priority = validate_priority(args.priority)

    source_rows = read_rows(source_path)
    target_rows = read_rows(target_path)

    source_idx, source_dupes, source_missing = index_rows(source_rows, args.key)
    target_idx, target_dupes, target_missing = index_rows(target_rows, args.key)

    merge_columns = resolve_columns(source_rows, target_rows, args.key, args.columns)
    all_keys = sorted(set(source_idx) | set(target_idx))

    merged_rows: list[dict[str, str]] = []
    conflict_rows: list[dict[str, str]] = []

    counts = {
        "both_sources": 0,
        "source_only": 0,
        "target_only": 0,
        "field_conflicts": 0,
    }

    for record_key in all_keys:
        source_row = source_idx.get(record_key)
        target_row = target_idx.get(record_key)

        if source_row and target_row:
            record_origin = "both"
            counts["both_sources"] += 1
        elif source_row:
            record_origin = "source_only"
            counts["source_only"] += 1
        else:
            record_origin = "target_only"
            counts["target_only"] += 1

        merged = {
            args.key: record_key,
            "record_origin": record_origin,
        }

        for column in merge_columns:
            source_value = normalize(source_row.get(column)) if source_row else ""
            target_value = normalize(target_row.get(column)) if target_row else ""
            chosen_value, chosen_from, is_conflict = choose_value(source_value, target_value, priority)

            merged[column] = chosen_value
            merged[f"source_of_{column}"] = chosen_from

            if is_conflict:
                counts["field_conflicts"] += 1
                conflict_rows.append(
                    {
                        "record_key": record_key,
                        "column": column,
                        "source_value": source_value,
                        "target_value": target_value,
                        "chosen_value": chosen_value,
                        "chosen_from": chosen_from,
                        "priority": ">".join(priority),
                    }
                )

        merged_rows.append(merged)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        fieldnames = [args.key, "record_origin"] + merge_columns + [f"source_of_{col}" for col in merge_columns]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_rows)

    if args.conflicts_output:
        conflicts_path = Path(args.conflicts_output)
    else:
        conflicts_path = output_path.with_name(output_path.stem + "_conflicts.csv")

    conflicts_path.parent.mkdir(parents=True, exist_ok=True)
    with conflicts_path.open("w", newline="", encoding="utf-8") as fh:
        fieldnames = [
            "record_key",
            "column",
            "source_value",
            "target_value",
            "chosen_value",
            "chosen_from",
            "priority",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(conflict_rows)

    summary = {
        "source_records": len(source_rows),
        "target_records": len(target_rows),
        "merged_records": len(merged_rows),
        "priority": priority,
        "key_column": args.key,
        "merge_columns": merge_columns,
        "source_duplicates_ignored": source_dupes,
        "target_duplicates_ignored": target_dupes,
        "source_missing_key_rows": source_missing,
        "target_missing_key_rows": target_missing,
        "counts": counts,
        "conflicts_output": str(conflicts_path),
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        "Survivorship merge complete: "
        f"records={len(merged_rows)} "
        f"both={counts['both_sources']} "
        f"source_only={counts['source_only']} "
        f"target_only={counts['target_only']} "
        f"conflicts={counts['field_conflicts']}"
    )
    print(f"Merged output: {output_path}")
    print(f"Conflicts output: {conflicts_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
