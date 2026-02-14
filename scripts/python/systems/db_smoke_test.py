#!/usr/bin/env python3
"""Run lightweight database readiness checks for reporting/admissions processing windows."""

from __future__ import annotations

import argparse
import json
import socket
import sqlite3
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run quick DB reachability checks for SQLite, MySQL, and Postgres endpoints "
            "used by operational data workflows."
        )
    )
    parser.add_argument("--output", required=True, help="Output summary JSON")
    parser.add_argument("--sqlite-path", default="", help="SQLite DB file path")
    parser.add_argument("--mysql-host", default="", help="MySQL host")
    parser.add_argument("--mysql-port", type=int, default=3306, help="MySQL port")
    parser.add_argument("--postgres-host", default="", help="Postgres host")
    parser.add_argument("--postgres-port", type=int, default=5432, help="Postgres port")
    parser.add_argument("--timeout", type=float, default=2.0, help="Socket timeout seconds")
    return parser.parse_args()


def socket_check(host: str, port: int, timeout: float) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "ok"
    except Exception as exc:
        return False, str(exc)


def sqlite_check(path: Path) -> tuple[bool, str]:
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    checks: dict[str, dict[str, str | bool]] = {}
    failures = 0
    requested = 0

    if args.sqlite_path:
        requested += 1
        ok, detail = sqlite_check(Path(args.sqlite_path))
        checks["sqlite"] = {"ok": ok, "detail": detail, "path": args.sqlite_path}
        failures += 0 if ok else 1

    if args.mysql_host:
        requested += 1
        ok, detail = socket_check(args.mysql_host, args.mysql_port, args.timeout)
        checks["mysql"] = {
            "ok": ok,
            "detail": detail,
            "host": args.mysql_host,
            "port": args.mysql_port,
        }
        failures += 0 if ok else 1

    if args.postgres_host:
        requested += 1
        ok, detail = socket_check(args.postgres_host, args.postgres_port, args.timeout)
        checks["postgres"] = {
            "ok": ok,
            "detail": detail,
            "host": args.postgres_host,
            "port": args.postgres_port,
        }
        failures += 0 if ok else 1

    if requested == 0:
        # Always run at least one check.
        requested = 1
        ok, detail = sqlite_check(Path(":memory:"))
        checks["sqlite_memory"] = {"ok": ok, "detail": detail}
        failures += 0 if ok else 1

    summary = {
        "requested_checks": requested,
        "failed_checks": failures,
        "all_passed": failures == 0,
        "checks": checks,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"DB smoke test complete: failed={failures}/{requested} -> {output_path}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
