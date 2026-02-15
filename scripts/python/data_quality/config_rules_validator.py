#!/usr/bin/env python3
"""Run JSON-defined validation rules against CSV data and export row-level violations."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

SUPPORTED_RULE_TYPES = {"required", "allowed_values", "range", "regex", "equals_column"}
VIOLATION_FIELDS = [
    "row_number",
    "record_key",
    "rule_name",
    "rule_type",
    "column",
    "value",
    "message",
]


def normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a config-driven rules engine against CSV records and export "
            "violations + summary metadata."
        )
    )
    parser.add_argument("--input", required=True, help="Source CSV file")
    parser.add_argument("--rules", required=True, help="Rules JSON file")
    parser.add_argument("--output", required=True, help="CSV output path for violations")
    parser.add_argument(
        "--summary",
        default="reports/rules_validation_summary.json",
        help="Summary JSON output path (default: reports/rules_validation_summary.json)",
    )
    parser.add_argument(
        "--key-column",
        default="",
        help="Override key column used in output (defaults to rules config key_column or student_id)",
    )
    return parser.parse_args()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def load_rules(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def row_matches_when(rule: dict[str, Any], row: dict[str, str]) -> bool:
    when = rule.get("when")
    if not isinstance(when, dict):
        return True

    column = normalize(when.get("column"))
    if not column:
        return True

    raw_value = normalize(row.get(column))
    value = raw_value if when.get("case_sensitive") else raw_value.lower()

    if "equals" in when:
        target_raw = normalize(when.get("equals"))
        target = target_raw if when.get("case_sensitive") else target_raw.lower()
        return value == target

    if "not_equals" in when:
        target_raw = normalize(when.get("not_equals"))
        target = target_raw if when.get("case_sensitive") else target_raw.lower()
        return value != target

    if "in" in when and isinstance(when.get("in"), list):
        candidates = [normalize(item) for item in when.get("in", [])]
        if not when.get("case_sensitive"):
            candidates = [item.lower() for item in candidates]
        return value in set(candidates)

    return True


def prepare_rules(config_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for idx, raw in enumerate(config_rules, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"Rule #{idx} must be an object")

        rule = dict(raw)
        rule_name = normalize(rule.get("name")) or f"rule_{idx}"
        rule_type = normalize(rule.get("type")).lower()
        column = normalize(rule.get("column"))

        if rule_type not in SUPPORTED_RULE_TYPES:
            raise ValueError(f"Rule '{rule_name}' has unsupported type '{rule_type}'")
        if not column:
            raise ValueError(f"Rule '{rule_name}' is missing required field: column")

        rule["name"] = rule_name
        rule["type"] = rule_type
        rule["column"] = column

        if rule_type == "allowed_values":
            values = rule.get("values")
            if not isinstance(values, list) or not values:
                raise ValueError(f"Rule '{rule_name}' requires non-empty 'values' list")
            if rule.get("case_sensitive"):
                rule["_allowed_values"] = {normalize(v) for v in values}
            else:
                rule["_allowed_values"] = {normalize(v).lower() for v in values}

        if rule_type == "regex":
            pattern = normalize(rule.get("pattern"))
            if not pattern:
                raise ValueError(f"Rule '{rule_name}' requires 'pattern'")
            flags = 0 if rule.get("case_sensitive") else re.IGNORECASE
            rule["_compiled_pattern"] = re.compile(pattern, flags)

        prepared.append(rule)

    return prepared


def collect_referenced_columns(required_columns: list[str], rules: list[dict[str, Any]]) -> set[str]:
    columns = {normalize(col) for col in required_columns if normalize(col)}
    for rule in rules:
        columns.add(rule["column"])
        if rule.get("type") == "equals_column":
            other_column = normalize(rule.get("other_column"))
            if other_column:
                columns.add(other_column)
        when = rule.get("when")
        if isinstance(when, dict):
            when_column = normalize(when.get("column"))
            if when_column:
                columns.add(when_column)
    return columns


def evaluate_rule(rule: dict[str, Any], row: dict[str, str]) -> str | None:
    if not row_matches_when(rule, row):
        return None

    column = rule["column"]
    value = normalize(row.get(column))
    rule_type = rule["type"]

    if rule_type == "required":
        if not value:
            return "value is required"
        return None

    if rule_type == "allowed_values":
        if not value:
            return None
        candidate = value if rule.get("case_sensitive") else value.lower()
        if candidate not in rule["_allowed_values"]:
            return f"value '{value}' is not in allowed set"
        return None

    if rule_type == "range":
        if not value:
            return None
        try:
            number = float(value)
        except ValueError:
            return f"value '{value}' is not numeric"

        if "min" in rule and number < float(rule["min"]):
            return f"value {number:g} is below min {float(rule['min']):g}"
        if "max" in rule and number > float(rule["max"]):
            return f"value {number:g} is above max {float(rule['max']):g}"
        return None

    if rule_type == "regex":
        if not value:
            return None
        if not rule["_compiled_pattern"].fullmatch(value):
            return f"value '{value}' does not match required pattern"
        return None

    if rule_type == "equals_column":
        other_column = normalize(rule.get("other_column"))
        if not other_column:
            return "rule misconfigured: other_column is required"
        other_value = normalize(row.get(other_column))
        if value != other_value:
            return f"value '{value}' does not match {other_column} '{other_value}'"
        return None

    return f"unsupported rule type '{rule_type}'"


def write_violations(path: Path, violations: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=VIOLATION_FIELDS)
        writer.writeheader()
        writer.writerows(violations)


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    rules_path = Path(args.rules)
    output_path = Path(args.output)
    summary_path = Path(args.summary)

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules JSON not found: {rules_path}")

    rules_config = load_rules(rules_path)
    if not isinstance(rules_config, dict):
        raise ValueError("Rules config must be a JSON object")

    raw_rules = rules_config.get("rules", [])
    if not isinstance(raw_rules, list):
        raise ValueError("Rules config field 'rules' must be a list")

    required_columns = [normalize(col) for col in rules_config.get("required_columns", []) if normalize(col)]
    prepared_rules = prepare_rules(raw_rules)

    headers, rows = read_rows(input_path)
    header_set = set(headers)

    key_column = normalize(args.key_column) or normalize(rules_config.get("key_column")) or "student_id"

    referenced_columns = collect_referenced_columns(required_columns, prepared_rules)
    missing_columns = sorted(col for col in referenced_columns if col not in header_set)

    violations: list[dict[str, str]] = []
    violations_by_rule: Counter[str] = Counter()

    if not missing_columns:
        for row_number, row in enumerate(rows, start=2):
            record_key = normalize(row.get(key_column))
            for rule in prepared_rules:
                message = evaluate_rule(rule, row)
                if not message:
                    continue

                rule_name = rule["name"]
                violations_by_rule[rule_name] += 1
                violations.append(
                    {
                        "row_number": str(row_number),
                        "record_key": record_key,
                        "rule_name": rule_name,
                        "rule_type": rule["type"],
                        "column": rule["column"],
                        "value": normalize(row.get(rule["column"])),
                        "message": message,
                    }
                )

    write_violations(output_path, violations)

    summary = {
        "input": str(input_path),
        "rules_file": str(rules_path),
        "rows_scanned": len(rows),
        "rule_count": len(prepared_rules),
        "key_column": key_column,
        "required_columns": required_columns,
        "missing_columns": missing_columns,
        "violation_count": len(violations),
        "violations_by_rule": dict(violations_by_rule),
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if missing_columns:
        print(
            "Validation skipped due to missing columns: "
            + ", ".join(missing_columns)
            + f". Summary written to {summary_path}"
        )
        return 2

    print(
        f"Rules validation complete: rows={len(rows)} violations={len(violations)} "
        f"-> {output_path}"
    )
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
