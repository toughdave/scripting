# scripting

Operational scripting toolkit built from hands-on academic IT and instructional operations.

## Why this repository exists

This repository captures the scripting patterns I used and refined across two core roles:

- **Systems & Data Analyst / System Programmer (FUTA, 2017-2023)** supporting admissions, examinations, results processing, and reporting workflows at scale
- **Computer Technology Instructor (Pures College, 2024-2025)** teaching practical systems administration, networking, and data workflow implementation in lab environments

The goal is simple: turn recurring operations into reliable, auditable, and repeatable workflows across Linux and Windows, with outputs that can stand up to operational review.

## Professional profile

- Information Systems Analyst and Computer Science professional (M.Tech. in Computer Science)
- Experience supporting large academic IT operations handling **4,000+ student records/users**
- Delivered data processing automation with Python, MySQL, Excel, and Google Sheets
- Built workflows for reconciliation, result integrity checks, and audit-ready reporting
- Managed practical IT instruction and assessment workflows for **250+ students**

## Professional context behind the scripts

These scripts reflect day-to-day operational needs from environments with high-volume records, strict reporting timelines, and compliance-sensitive processes:

- reconciliation of admissions and results records between operational extracts and approved reporting outputs
- data quality checks before grade publication windows and committee sign-off
- repeatable ETL runs for admissions and academic performance datasets
- checkpoint/SLA monitoring for exam readiness, compliance, and support tasks
- audit packet preparation for leadership, registry, and quality-assurance review teams
- lightweight system and database smoke checks before reporting cycles

## What this toolkit is used for now

- building reusable data-quality routines for CSV/Excel pipelines
- validating key records and catching duplicates, nulls, and status anomalies early
- documenting reconciliation outcomes for transparent decision-making and approvals
- handling incomplete or inconsistent identifiers with fuzzy reconciliation suggestions
- resolving source-vs-target field conflicts with explicit survivorship priority rules
- supporting analytics preparation for Power BI/Excel reporting layers
- creating cross-platform workflows that can run as scheduled jobs

## How these scripts were applied in practice

### Systems & Data Analyst / System Programmer

- supported recurring admissions and examination data cycles with Python, MySQL, Excel, and Google Sheets
- reduced manual record handling risk through repeatable validation, reconciliation, and ETL routines
- used discrepancy reports and integrity checks to prepare result data before publication workflows
- supported operational systems handling 4,000+ records/users, where repeatability and auditability were essential

### Computer Technology Instructor

- used script-driven data validation examples to teach practical SQL/Python workflows
- adapted the same reconciliation and quality-check patterns for student lab assignments and project assessments
- reinforced operational thinking: validate inputs, detect anomalies early, and produce traceable outputs

## Business and enterprise applicability

Although this repository uses academic-style sample data, the workflow pattern is directly transferable to enterprise operations:

- customer/master-data quality validation
- CRM/ERP reconciliation and variance reporting
- SLA monitoring for operations and support queues
- compliance evidence packaging and audit preparation
- ETL pre-flight checks and post-run summaries for BI teams

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

## Expanded sample data included

The sample datasets are intentionally richer to mirror realistic operational review scenarios.

- `data/sample/student_records_source.csv`
  - 140 student records across admissions cohorts and multiple departments
  - includes intentional quality issues: duplicate IDs, missing email/department, out-of-range scores, and status exceptions
- `data/sample/student_records_target.csv`
  - 140 records with overlapping and non-overlapping IDs for reconciliation behavior
  - includes realistic score/status/department differences for mismatch reporting
- `data/sample/exam_tasks.csv`
  - 140 operational checkpoints tied to admissions, exam integrity, reporting, and compliance
  - includes overdue, at-risk, completed-on-time, and late-completed patterns for SLA testing
- `data/sample/validation_rules.json`
  - JSON rule pack for config-driven CSV validation
  - includes required-field, score-range, status, and conditional validation examples

Equivalent SQL seed data is available in:
`data/seed/sql_seed_demo_academic_dataset/{mysql.sql,postgres.sql,sqlite.sql}`

## Python setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install pandas openpyxl psutil python-dotenv
```

## Quick start

1. Seed a demo database using files in `data/seed/sql_seed_demo_academic_dataset/`
2. Run data profiling, normalization, and rules-based validation scripts in `scripts/python/data_quality/`
3. Run reconciliation and SLA scripts in `scripts/python/reconciliation/` and `scripts/python/reporting/`
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

# Run config-driven validation rules
python scripts/python/data_quality/config_rules_validator.py \
  --input data/sample/student_records_source.csv \
  --rules data/sample/validation_rules.json \
  --output reports/rules_violations.csv \
  --summary reports/rules_validation_summary.json

# Reconcile source vs target
python scripts/python/reconciliation/reconcile_students.py \
  --source data/sample/student_records_source.csv \
  --target data/sample/student_records_target.csv \
  --output reports/reconciliation.csv \
  --summary reports/reconciliation_summary.json

# Fuzzy reconciliation when IDs are missing or inconsistent
python scripts/python/reconciliation/fuzzy_match_students.py \
  --source data/sample/student_records_source.csv \
  --target data/sample/student_records_target.csv \
  --output reports/reconciliation_fuzzy.csv \
  --summary reports/reconciliation_fuzzy_summary.json \
  --threshold 0.86

# Survivorship merge for source-vs-target conflicts
python scripts/python/reconciliation/survivorship_merge_students.py \
  --source data/sample/student_records_source.csv \
  --target data/sample/student_records_target.csv \
  --output reports/reconciliation_survivorship.csv \
  --summary reports/reconciliation_survivorship_summary.json \
  --priority target source

# SLA at-risk report
python scripts/python/reporting/sla_at_risk_report.py \
  --input data/sample/exam_tasks.csv \
  --output reports/sla_at_risk.csv \
  --summary reports/sla_summary.json \
  --threshold-days 2

# Config-driven ETL apply run
python scripts/python/etl/etl_runner.py \
  --config data/sample/etl_config.json \
  --apply
```

## Portfolio alignment

This toolkit maps directly to the types of projects I have delivered:

1. **Academic Results Analytics Dashboard**
   - feeds cleaner, validated datasets into BI layers
   - supports anomaly tracking and KPI reliability
2. **Admissions Data Quality Audit**
   - applies duplicate detection, field validation, and reconciliation workflows
3. **Examination Integrity Monitoring**
   - structures checkpoint/SLA monitoring and evidence-oriented reporting

## Dependencies

- Python: `pandas`, `openpyxl`, `psutil`, `python-dotenv`
- MySQL client: optional (for DB smoke tests)
- Postgres client: optional (for DB smoke tests)

## Notes

- Scripts default to safe/read-only behavior where possible.
- Keep generated outputs in `output/`, `reports/`, or `artifacts/` (already gitignored).
- Use `scripts/workflow/schedule_daily_run.sh` (Linux) or `scripts/workflow/schedule_daily_run.ps1` (Windows) for full routine execution.
