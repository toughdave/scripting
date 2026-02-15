#!/usr/bin/env python3
"""Suggest fuzzy source-to-target student matches when IDs are missing or inconsistent."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


@dataclass
class TargetCandidate:
    key: str
    row: dict[str, str]
    name_key: str
    department: str


def normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_name(value: str) -> str:
    return " ".join(normalize(value).lower().split())


def join_name(row: dict[str, str], columns: list[str]) -> str:
    return " ".join(normalize(row.get(col)) for col in columns if normalize(row.get(col)))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_target_candidates(
    rows: list[dict[str, str]],
    key_column: str,
    name_columns: list[str],
    department_column: str,
) -> tuple[dict[str, TargetCandidate], list[TargetCandidate], dict[str, int]]:
    by_key: dict[str, TargetCandidate] = {}
    all_candidates: list[TargetCandidate] = []

    duplicate_keys = 0
    missing_key_rows = 0

    for row in rows:
        key = normalize(row.get(key_column))
        if not key:
            missing_key_rows += 1
            continue

        candidate = TargetCandidate(
            key=key,
            row=row,
            name_key=normalize_name(join_name(row, name_columns)),
            department=normalize(row.get(department_column)).lower() if department_column else "",
        )

        if key in by_key:
            duplicate_keys += 1
            continue

        by_key[key] = candidate
        all_candidates.append(candidate)

    return by_key, all_candidates, {
        "target_duplicate_keys_ignored": duplicate_keys,
        "target_missing_key_rows": missing_key_rows,
    }


def similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def choose_fuzzy_candidate(
    source_row: dict[str, str],
    source_key: str,
    candidates: list[TargetCandidate],
    consumed_target_keys: set[str],
    name_columns: list[str],
    department_column: str,
    threshold: float,
) -> tuple[TargetCandidate | None, float, str]:
    source_name = normalize_name(join_name(source_row, name_columns))
    source_department = normalize(source_row.get(department_column)).lower() if department_column else ""

    if not source_name:
        reason = "No usable source name fields for fuzzy match"
        if source_key:
            reason = f"Source key '{source_key}' not present in target and {reason.lower()}"
        return None, 0.0, reason

    best_candidate: TargetCandidate | None = None
    best_score = 0.0

    for candidate in candidates:
        if candidate.key in consumed_target_keys:
            continue

        score = similarity(source_name, candidate.name_key)
        if source_department and candidate.department and source_department == candidate.department:
            score = min(1.0, score + 0.06)

        if score > best_score:
            best_score = score
            best_candidate = candidate

    if best_candidate and best_score >= threshold:
        return best_candidate, best_score, "Name similarity match"

    reason = f"Best candidate score {best_score:.3f} below threshold {threshold:.2f}"
    if source_key:
        reason = f"Source key '{source_key}' not present in target and {reason.lower()}"
    return None, best_score, reason


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate fuzzy student matches for reconciliation workflows when "
            "source keys are absent, renamed, or mismatched."
        )
    )
    parser.add_argument("--source", required=True, help="Source CSV (operational extract)")
    parser.add_argument("--target", required=True, help="Target CSV (reference/reporting extract)")
    parser.add_argument("--output", required=True, help="Output CSV for exact/fuzzy match decisions")
    parser.add_argument("--summary", required=True, help="Output JSON summary path")
    parser.add_argument("--key", default="student_id", help="Primary key column")
    parser.add_argument(
        "--name-columns",
        nargs="+",
        default=["first_name", "last_name"],
        help="Columns used to build fuzzy name keys",
    )
    parser.add_argument(
        "--department-column",
        default="department",
        help="Optional department column for similarity boost (set empty string to disable)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.86,
        help="Minimum fuzzy score accepted as a match",
    )
    return parser.parse_args()


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

    source_rows = read_rows(source_path)
    target_rows = read_rows(target_path)

    department_column = normalize(args.department_column)
    target_by_key, target_candidates, target_stats = build_target_candidates(
        target_rows,
        key_column=args.key,
        name_columns=args.name_columns,
        department_column=department_column,
    )

    consumed_target_keys: set[str] = set()
    result_rows: list[dict[str, str]] = []

    counts = {
        "exact_key": 0,
        "fuzzy_name": 0,
        "no_match": 0,
    }

    for source_row in source_rows:
        source_key = normalize(source_row.get(args.key))
        source_name = join_name(source_row, args.name_columns)
        source_department = normalize(source_row.get(department_column)) if department_column else ""

        if source_key and source_key in target_by_key and source_key not in consumed_target_keys:
            candidate = target_by_key[source_key]
            consumed_target_keys.add(candidate.key)
            counts["exact_key"] += 1
            result_rows.append(
                {
                    "source_record_key": source_key,
                    "source_name": source_name,
                    "source_department": source_department,
                    "target_record_key": candidate.key,
                    "target_name": join_name(candidate.row, args.name_columns),
                    "target_department": normalize(candidate.row.get(department_column)) if department_column else "",
                    "match_type": "exact_key",
                    "match_score": "1.000",
                    "reason": "Key match",
                }
            )
            continue

        candidate, score, reason = choose_fuzzy_candidate(
            source_row,
            source_key=source_key,
            candidates=target_candidates,
            consumed_target_keys=consumed_target_keys,
            name_columns=args.name_columns,
            department_column=department_column,
            threshold=args.threshold,
        )

        if candidate:
            consumed_target_keys.add(candidate.key)
            counts["fuzzy_name"] += 1
            result_rows.append(
                {
                    "source_record_key": source_key,
                    "source_name": source_name,
                    "source_department": source_department,
                    "target_record_key": candidate.key,
                    "target_name": join_name(candidate.row, args.name_columns),
                    "target_department": normalize(candidate.row.get(department_column)) if department_column else "",
                    "match_type": "fuzzy_name",
                    "match_score": f"{score:.3f}",
                    "reason": reason,
                }
            )
        else:
            counts["no_match"] += 1
            result_rows.append(
                {
                    "source_record_key": source_key,
                    "source_name": source_name,
                    "source_department": source_department,
                    "target_record_key": "",
                    "target_name": "",
                    "target_department": "",
                    "match_type": "no_match",
                    "match_score": f"{score:.3f}",
                    "reason": reason,
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        fieldnames = [
            "source_record_key",
            "source_name",
            "source_department",
            "target_record_key",
            "target_name",
            "target_department",
            "match_type",
            "match_score",
            "reason",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result_rows)

    summary = {
        "source_records": len(source_rows),
        "target_records": len(target_rows),
        "threshold": args.threshold,
        "name_columns": args.name_columns,
        "department_column": department_column,
        "counts": counts,
        "target_unmatched_records": len(target_by_key) - len(consumed_target_keys),
        **target_stats,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        "Fuzzy reconciliation complete: "
        f"exact={counts['exact_key']} "
        f"fuzzy={counts['fuzzy_name']} "
        f"no_match={counts['no_match']}"
    )
    print(f"Output: {output_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
