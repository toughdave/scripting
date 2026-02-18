#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_DIR="${REPO_ROOT}/logs"
REPORT_DIR="${REPO_ROOT}/reports"
OUTPUT_DIR="${REPO_ROOT}/output"

mkdir -p "${LOG_DIR}" "${REPORT_DIR}" "${OUTPUT_DIR}"

STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="${LOG_DIR}/daily-run-${STAMP}.log"
MANIFEST_FILE="${REPORT_DIR}/run_manifest-${STAMP}.json"

run_step() {
  local label="$1"
  shift
  echo "[$(date +%F' '%T)] START ${label}" | tee -a "${LOG_FILE}"
  "$@" 2>&1 | tee -a "${LOG_FILE}"
  echo "[$(date +%F' '%T)] DONE  ${label}" | tee -a "${LOG_FILE}"
}

run_step "csv_profile" \
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/python/data_quality/csv_profile.py" \
  --input "${REPO_ROOT}/data/sample/student_records_source.csv" \
  --output "${REPORT_DIR}/student_profile.json"

run_step "csv_clean_normalize" \
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/python/data_quality/csv_clean_normalize.py" \
  --input "${REPO_ROOT}/data/sample/student_records_source.csv" \
  --output "${OUTPUT_DIR}/student_records_clean.csv" \
  --date-columns due_date completed_at \
  --drop-duplicates

run_step "reconcile_students" \
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/python/reconciliation/reconcile_students.py" \
  --source "${REPO_ROOT}/data/sample/student_records_source.csv" \
  --target "${REPO_ROOT}/data/sample/student_records_target.csv" \
  --output "${REPORT_DIR}/reconciliation.csv" \
  --summary "${REPORT_DIR}/reconciliation_summary.json"

run_step "sla_at_risk_report" \
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/python/reporting/sla_at_risk_report.py" \
  --input "${REPO_ROOT}/data/sample/exam_tasks.csv" \
  --output "${REPORT_DIR}/sla_at_risk.csv" \
  --summary "${REPORT_DIR}/sla_summary.json" \
  --threshold-days 2

run_step "etl_runner_apply" \
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/python/etl/etl_runner.py" \
  --config "${REPO_ROOT}/data/sample/etl_config.json" \
  --apply

run_step "system_health_snapshot" \
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/python/systems/system_health_snapshot.py" \
  --output "${REPORT_DIR}/system_snapshot.json"

run_step "db_smoke_test" \
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/python/systems/db_smoke_test.py" \
  --output "${REPORT_DIR}/db_smoke.json"

run_step "run_manifest" \
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/python/reporting/run_manifest.py" \
  --run-id "${STAMP}" \
  --status "success" \
  --report-dir "${REPORT_DIR}" \
  --output-dir "${OUTPUT_DIR}" \
  --log-file "${LOG_FILE}" \
  --manifest "${MANIFEST_FILE}"

echo "[$(date +%F' '%T)] Daily run complete. Log: ${LOG_FILE} Manifest: ${MANIFEST_FILE}" | tee -a "${LOG_FILE}"
