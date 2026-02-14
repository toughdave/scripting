#!/usr/bin/env python3
"""Clean and normalize student/admissions CSV extracts for consistent downstream reporting."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%Y-%m-%d %H:%M:%S",
)


def normalize_header(name: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in name.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Clean admissions/result-operation CSV content by trimming values, "
            "normalizing headers, standardizing dates, and optionally removing duplicates."
        )
    )
    parser.add_argument("--input", required=True, help="Input CSV extract path")
    parser.add_argument("--output", required=True, help="Output normalized CSV path")
    parser.add_argument(
        "--date-columns",
        nargs="*",
        default=[],
        help="Columns to normalize to YYYY-MM-DD (for due/completion timelines)",
    )
    parser.add_argument(
        "--drop-duplicates",
        action="store_true",
        help="Drop duplicate records using --dedupe-keys (for repeated IDs or imported retries)",
    )
    parser.add_argument(
        "--dedupe-keys",
        nargs="*",
        default=["student_id"],
        help="Columns used for duplicate detection",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        original_headers = reader.fieldnames or []
        rows = list(reader)

    normalized_headers = [normalize_header(h) for h in original_headers]
    header_map = dict(zip(original_headers, normalized_headers))

    date_columns = {normalize_header(col) for col in args.date_columns}
    dedupe_keys = [normalize_header(col) for col in args.dedupe_keys]

    cleaned_rows = []
    seen = set()
    removed_duplicates = 0

    for row in rows:
        cleaned = {}
        for old_header, new_header in header_map.items():
            raw_value = row.get(old_header) or ""
            value = raw_value.strip()
            if new_header in date_columns and value:
                value = normalize_date(value)
            cleaned[new_header] = value

        if args.drop_duplicates:
            dedupe_key = tuple(cleaned.get(k, "") for k in dedupe_keys)
            if dedupe_key in seen:
                removed_duplicates += 1
                continue
            seen.add(dedupe_key)

        cleaned_rows.append(cleaned)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=normalized_headers)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(
        "Clean complete: "
        f"input_rows={len(rows)}, output_rows={len(cleaned_rows)}, "
        f"duplicates_removed={removed_duplicates} -> {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
