#!/usr/bin/env python3
"""Generate an SLA at-risk report from checkpoint/task data."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create SLA at-risk and overdue report from CSV.")
    parser.add_argument("--input", required=True, help="Input tasks CSV")
    parser.add_argument("--output", required=True, help="Output at-risk CSV")
    parser.add_argument("--summary", required=True, help="Output summary JSON")
    parser.add_argument("--threshold-days", type=int, default=2, help="At-risk threshold in days")
    parser.add_argument("--as-of", default=date.today().isoformat(), help="As-of date (YYYY-MM-DD)")
    return parser.parse_args()


def classify_row(
    row: dict[str, str],
    as_of: date,
    threshold_days: int,
) -> tuple[str, int | None]:
    status = (row.get("status") or "").strip().lower()
    due = parse_date(row.get("due_date"))
    completed = parse_date(row.get("completed_at"))

    if due is None:
        return "no_due_date", None

    days_to_due = (due - as_of).days

    if completed is not None:
        if completed > due:
            return "late_completed", days_to_due
        return "completed_on_time", days_to_due

    if status not in {"open", "in_progress"}:
        return "not_active", days_to_due

    if days_to_due < 0:
        return "overdue", days_to_due
    if days_to_due <= threshold_days:
        return "at_risk", days_to_due
    return "on_track", days_to_due


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary)

    as_of = parse_date(args.as_of)
    if as_of is None:
        raise ValueError("--as-of must be a valid date in YYYY-MM-DD format")

    with input_path.open("r", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    at_risk_rows: list[dict[str, str]] = []
    states = Counter()

    for row in rows:
        risk_state, days_to_due = classify_row(row, as_of, args.threshold_days)
        states[risk_state] += 1

        if risk_state in {"at_risk", "overdue"}:
            out = dict(row)
            out["risk_state"] = risk_state
            out["days_to_due"] = "" if days_to_due is None else str(days_to_due)
            at_risk_rows.append(out)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys()) + ["risk_state", "days_to_due"] if rows else [
        "risk_state",
        "days_to_due",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(at_risk_rows)

    summary = {
        "as_of": as_of.isoformat(),
        "threshold_days": args.threshold_days,
        "total_rows": len(rows),
        "at_risk_rows": len(at_risk_rows),
        "state_counts": dict(states),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        f"SLA report complete: at_risk={len(at_risk_rows)} "
        f"(from {len(rows)} rows) -> {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
