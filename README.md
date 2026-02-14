# scripting

Cross-platform automation and data-quality scripts for real operational use cases.

## Scope

- Target OS: Linux + Windows
- Databases: MySQL + Postgres
- Demo DB: SQLite
- Excel-first workflow, Google Sheets secondary
- Power BI: local templates only for now

## Repository layout

```text
scripts/
  sql/
    mysql/
    postgres/
    sqlite/
    templates/
  python/
    data_quality/
    reconciliation/
    reporting/
    etl/
    systems/
  workflow/
data/
  sample/
  seed/
powerbi/
  powerquery/
google-sheets/
  apps-script/
```

## Python setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install pandas openpyxl psutil python-dotenv
```

## Quick start

1. Seed a demo database using files in `data/seed/sql_seed_demo_academic_dataset/`
2. Run CSV profiling and cleaning scripts in `scripts/python/data_quality/`
3. Run reconciliation and SLA report scripts in `scripts/python/reconciliation/` and `scripts/python/reporting/`
4. Use workflow wrappers in `scripts/workflow/` for scheduled execution

### Example commands

```bash
# Profile source dataset
python scripts/python/data_quality/csv_profile.py \
  --input data/sample/student_records_source.csv \
  --output reports/student_profile.json

# Clean and normalize source dataset
python scripts/python/data_quality/csv_clean_normalize.py \
  --input data/sample/student_records_source.csv \
  --output output/student_records_clean.csv \
  --date-columns due_date completed_at \
  --drop-duplicates

# Reconcile source vs target
python scripts/python/reconciliation/reconcile_students.py \
  --source data/sample/student_records_source.csv \
  --target data/sample/student_records_target.csv \
  --output reports/reconciliation.csv \
  --summary reports/reconciliation_summary.json

# SLA at-risk report
python scripts/python/reporting/sla_at_risk_report.py \
  --input data/sample/exam_tasks.csv \
  --output reports/sla_at_risk.csv \
  --summary reports/sla_summary.json \
  --threshold-days 2
```

## Dependencies

- Python: `pandas`, `openpyxl`, `psutil`, `python-dotenv`
- MySQL client: optional (for DB smoke tests)
- Postgres client: optional (for DB smoke tests)

## Notes

- Scripts should default to safe/read-only behavior where possible.
- Keep generated outputs in `output/`, `reports/`, or `artifacts/` (already gitignored).

## Implemented so far

- SQL quality checks:
  - `scripts/sql/mysql/mysql_validate_results_integrity.sql`
  - `scripts/sql/postgres/postgres_validate_results_integrity.sql`
  - `scripts/sql/sqlite/sqlite_validate_results_integrity.sql`
  - `scripts/sql/mysql/mysql_find_duplicates_by_keys.sql`
  - `scripts/sql/postgres/postgres_find_duplicates_by_keys.sql`
  - `scripts/sql/sqlite/sqlite_find_duplicates_by_keys.sql`
  - `scripts/sql/templates/sql_reconciliation_diff_template.sql`
- Python data/reporting scripts:
  - `scripts/python/data_quality/csv_profile.py`
  - `scripts/python/data_quality/csv_clean_normalize.py`
  - `scripts/python/data_quality/excel_validate_workbook.py`
  - `scripts/python/etl/etl_runner.py`
  - `scripts/python/reconciliation/reconcile_students.py`
  - `scripts/python/reporting/sla_at_risk_report.py`
  - `scripts/python/reporting/excel_export_audit_packet.py`
  - `scripts/python/systems/system_health_snapshot.py`
  - `scripts/python/systems/db_smoke_test.py`
- Workflow wrappers:
  - `scripts/workflow/schedule_daily_run.sh`
  - `scripts/workflow/schedule_daily_run.ps1`
- BI/spreadsheet templates:
  - `powerbi/powerquery/powerquery_data_quality_template.pq`
  - `google-sheets/apps-script/apps_script_validation_rules.gs`
- Demo datasets and DB seeds:
  - `data/sample/*.csv`
  - `data/sample/etl_config.json`
  - `data/seed/sql_seed_demo_academic_dataset/{mysql.sql,postgres.sql,sqlite.sql}`
