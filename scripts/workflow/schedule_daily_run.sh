#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
MAX_RETRIES="${MAX_RETRIES:-1}"
RETAIN_RUN_ARTIFACTS="${RETAIN_RUN_ARTIFACTS:-15}"
LOG_DIR="${REPO_ROOT}/logs"
REPORT_DIR="${REPO_ROOT}/reports"
OUTPUT_DIR="${REPO_ROOT}/output"

if ! [[ "${MAX_RETRIES}" =~ ^[0-9]+$ ]]; then
  echo "MAX_RETRIES must be a non-negative integer (received: ${MAX_RETRIES})" >&2
  exit 2
fi

if ! [[ "${RETAIN_RUN_ARTIFACTS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "RETAIN_RUN_ARTIFACTS must be a positive integer (received: ${RETAIN_RUN_ARTIFACTS})" >&2
  exit 2
fi

mkdir -p "${LOG_DIR}" "${REPORT_DIR}" "${OUTPUT_DIR}"

STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="${LOG_DIR}/daily-run-${STAMP}.log"
MANIFEST_FILE="${REPORT_DIR}/run_manifest-${STAMP}.json"
STEP_STATUS_FILE="${REPORT_DIR}/step_status-${STAMP}.csv"
RUN_STATUS="success"

printf "step,attempt,max_attempts,exit_code,start_utc,end_utc,duration_seconds,status\n" > "${STEP_STATUS_FILE}"

run_step() {
  local label="$1"
  shift
  local start_epoch end_epoch duration exit_code
  local start_utc end_utc
  local attempt=1
  local max_attempts=$((MAX_RETRIES + 1))

  while (( attempt <= max_attempts )); do
    start_epoch="$(date +%s)"
    start_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    echo "[$(date +%F' '%T)] START ${label} (attempt ${attempt}/${max_attempts})" | tee -a "${LOG_FILE}"

    set +e
    "$@" 2>&1 | tee -a "${LOG_FILE}"
    exit_code=${PIPESTATUS[0]}
    set -e

    end_epoch="$(date +%s)"
    end_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    duration=$((end_epoch - start_epoch))

    if [[ ${exit_code} -eq 0 ]]; then
      echo "[$(date +%F' '%T)] DONE  ${label} (attempt ${attempt}/${max_attempts})" | tee -a "${LOG_FILE}"
      printf "%s,%s,%s,%s,%s,%s,%s,%s\n" "${label}" "${attempt}" "${max_attempts}" "${exit_code}" "${start_utc}" "${end_utc}" "${duration}" "success" >> "${STEP_STATUS_FILE}"
      return
    fi

    echo "[$(date +%F' '%T)] FAIL  ${label} (attempt ${attempt}/${max_attempts}, exit=${exit_code})" | tee -a "${LOG_FILE}"
    printf "%s,%s,%s,%s,%s,%s,%s,%s\n" "${label}" "${attempt}" "${max_attempts}" "${exit_code}" "${start_utc}" "${end_utc}" "${duration}" "failed" >> "${STEP_STATUS_FILE}"

    if (( attempt < max_attempts )); then
      echo "[$(date +%F' '%T)] RETRY ${label} (next attempt $((attempt + 1))/${max_attempts})" | tee -a "${LOG_FILE}"
    else
      RUN_STATUS="failed"
    fi

    attempt=$((attempt + 1))
  done
}

prune_timestamped_artifacts() {
  local directory="$1"
  local pattern="$2"
  local label="$3"
  local -a files=()

  mapfile -t files < <(ls -1t "${directory}"/${pattern} 2>/dev/null || true)
  if (( ${#files[@]} <= RETAIN_RUN_ARTIFACTS )); then
    return
  fi

  for file in "${files[@]:RETAIN_RUN_ARTIFACTS}"; do
    rm -f -- "${file}"
  done

  echo "[$(date +%F' '%T)] RETAIN ${label} kept=${RETAIN_RUN_ARTIFACTS} removed=$(( ${#files[@]} - RETAIN_RUN_ARTIFACTS ))" | tee -a "${LOG_FILE}"
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
  --status "${RUN_STATUS}" \
  --report-dir "${REPORT_DIR}" \
  --output-dir "${OUTPUT_DIR}" \
  --log-file "${LOG_FILE}" \
  --steps-file "${STEP_STATUS_FILE}" \
  --manifest "${MANIFEST_FILE}"

prune_timestamped_artifacts "${LOG_DIR}" "daily-run-*.log" "logs"
prune_timestamped_artifacts "${REPORT_DIR}" "run_manifest-*.json" "manifests"
prune_timestamped_artifacts "${REPORT_DIR}" "step_status-*.csv" "step_status"

echo "[$(date +%F' '%T)] Daily run complete. Status: ${RUN_STATUS} Log: ${LOG_FILE} Manifest: ${MANIFEST_FILE} Steps: ${STEP_STATUS_FILE}" | tee -a "${LOG_FILE}"

if [[ "${RUN_STATUS}" != "success" ]]; then
  exit 1
fi
