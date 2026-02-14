param(
  [string]$PythonBin = "python"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")

$LogDir = Join-Path $RepoRoot "logs"
$ReportDir = Join-Path $RepoRoot "reports"
$OutputDir = Join-Path $RepoRoot "output"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir "daily-run-$Stamp.log"

function Run-Step {
  param(
    [string]$Label,
    [string[]]$ArgsList
  )

  $start = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] START $Label"
  $start | Tee-Object -FilePath $LogFile -Append

  & $PythonBin @ArgsList 2>&1 | Tee-Object -FilePath $LogFile -Append

  $done = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] DONE  $Label"
  $done | Tee-Object -FilePath $LogFile -Append
}

Run-Step "csv_profile" @(
  (Join-Path $RepoRoot "scripts/python/data_quality/csv_profile.py"),
  "--input", (Join-Path $RepoRoot "data/sample/student_records_source.csv"),
  "--output", (Join-Path $ReportDir "student_profile.json")
)

Run-Step "csv_clean_normalize" @(
  (Join-Path $RepoRoot "scripts/python/data_quality/csv_clean_normalize.py"),
  "--input", (Join-Path $RepoRoot "data/sample/student_records_source.csv"),
  "--output", (Join-Path $OutputDir "student_records_clean.csv"),
  "--date-columns", "due_date", "completed_at",
  "--drop-duplicates"
)

Run-Step "reconcile_students" @(
  (Join-Path $RepoRoot "scripts/python/reconciliation/reconcile_students.py"),
  "--source", (Join-Path $RepoRoot "data/sample/student_records_source.csv"),
  "--target", (Join-Path $RepoRoot "data/sample/student_records_target.csv"),
  "--output", (Join-Path $ReportDir "reconciliation.csv"),
  "--summary", (Join-Path $ReportDir "reconciliation_summary.json")
)

Run-Step "sla_at_risk_report" @(
  (Join-Path $RepoRoot "scripts/python/reporting/sla_at_risk_report.py"),
  "--input", (Join-Path $RepoRoot "data/sample/exam_tasks.csv"),
  "--output", (Join-Path $ReportDir "sla_at_risk.csv"),
  "--summary", (Join-Path $ReportDir "sla_summary.json"),
  "--threshold-days", "2"
)

Run-Step "etl_runner_apply" @(
  (Join-Path $RepoRoot "scripts/python/etl/etl_runner.py"),
  "--config", (Join-Path $RepoRoot "data/sample/etl_config.json"),
  "--apply"
)

Run-Step "system_health_snapshot" @(
  (Join-Path $RepoRoot "scripts/python/systems/system_health_snapshot.py"),
  "--output", (Join-Path $ReportDir "system_snapshot.json")
)

Run-Step "db_smoke_test" @(
  (Join-Path $RepoRoot "scripts/python/systems/db_smoke_test.py"),
  "--output", (Join-Path $ReportDir "db_smoke.json")
)

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Daily run complete. Log: $LogFile" | Tee-Object -FilePath $LogFile -Append
