param(
  [string]$PythonBin = "python",
  [int]$MaxRetries = 1,
  [int]$RetainRunArtifacts = 15
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")

$LogDir = Join-Path $RepoRoot "logs"
$ReportDir = Join-Path $RepoRoot "reports"
$OutputDir = Join-Path $RepoRoot "output"

if ($MaxRetries -lt 0) {
  throw "MaxRetries must be a non-negative integer (received: $MaxRetries)"
}

if ($RetainRunArtifacts -lt 1) {
  throw "RetainRunArtifacts must be a positive integer (received: $RetainRunArtifacts)"
}

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir "daily-run-$Stamp.log"
$ManifestFile = Join-Path $ReportDir "run_manifest-$Stamp.json"
$StepStatusFile = Join-Path $ReportDir "step_status-$Stamp.csv"
$RunHistoryFile = Join-Path $ReportDir "run_history_index.json"
$script:RunFailed = $false

"step,attempt,max_attempts,exit_code,start_utc,end_utc,duration_seconds,status" | Set-Content -Path $StepStatusFile

function Run-Step {
  param(
    [string]$Label,
    [string[]]$ArgsList
  )
  $maxAttempts = $MaxRetries + 1

  for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    $startTime = Get-Date
    $startUtc = $startTime.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $start = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] START $Label (attempt $attempt/$maxAttempts)"
    $start | Tee-Object -FilePath $LogFile -Append

    & $PythonBin @ArgsList 2>&1 | Tee-Object -FilePath $LogFile -Append
    $exitCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }

    $endTime = Get-Date
    $endUtc = $endTime.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $durationSeconds = [int][Math]::Round(($endTime - $startTime).TotalSeconds)

    if ($exitCode -eq 0) {
      $done = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] DONE  $Label (attempt $attempt/$maxAttempts)"
      $done | Tee-Object -FilePath $LogFile -Append
      "$Label,$attempt,$maxAttempts,$exitCode,$startUtc,$endUtc,$durationSeconds,success" | Add-Content -Path $StepStatusFile
      return
    }

    $fail = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] FAIL  $Label (attempt $attempt/$maxAttempts, exit=$exitCode)"
    $fail | Tee-Object -FilePath $LogFile -Append
    "$Label,$attempt,$maxAttempts,$exitCode,$startUtc,$endUtc,$durationSeconds,failed" | Add-Content -Path $StepStatusFile

    if ($attempt -lt $maxAttempts) {
      $retry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] RETRY $Label (next attempt $($attempt + 1)/$maxAttempts)"
      $retry | Tee-Object -FilePath $LogFile -Append
    } else {
      $script:RunFailed = $true
    }
  }
}

function Prune-TimestampedArtifacts {
  param(
    [string]$Directory,
    [string]$Pattern,
    [string]$Label
  )

  $files = Get-ChildItem -Path $Directory -Filter $Pattern -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending

  if ($null -eq $files -or $files.Count -le $RetainRunArtifacts) {
    return
  }

  $toRemove = $files | Select-Object -Skip $RetainRunArtifacts
  foreach ($item in $toRemove) {
    Remove-Item -Path $item.FullName -Force
  }

  $retainLog = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] RETAIN $Label kept=$RetainRunArtifacts removed=$($toRemove.Count)"
  $retainLog | Tee-Object -FilePath $LogFile -Append
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

Run-Step "run_manifest" @(
  (Join-Path $RepoRoot "scripts/python/reporting/run_manifest.py"),
  "--run-id", $Stamp,
  "--status", $(if ($script:RunFailed) { "failed" } else { "success" }),
  "--report-dir", $ReportDir,
  "--output-dir", $OutputDir,
  "--log-file", $LogFile,
  "--steps-file", $StepStatusFile,
  "--manifest", $ManifestFile
)

Run-Step "run_history_index" @(
  (Join-Path $RepoRoot "scripts/python/reporting/run_history_index.py"),
  "--manifest", $ManifestFile,
  "--history", $RunHistoryFile,
  "--max-entries", "$RetainRunArtifacts"
)

Prune-TimestampedArtifacts -Directory $LogDir -Pattern "daily-run-*.log" -Label "logs"
Prune-TimestampedArtifacts -Directory $ReportDir -Pattern "run_manifest-*.json" -Label "manifests"
Prune-TimestampedArtifacts -Directory $ReportDir -Pattern "step_status-*.csv" -Label "step_status"

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Daily run complete. Status: $(if ($script:RunFailed) { 'failed' } else { 'success' }) Log: $LogFile Manifest: $ManifestFile Steps: $StepStatusFile" | Tee-Object -FilePath $LogFile -Append

if ($script:RunFailed) {
  exit 1
}
