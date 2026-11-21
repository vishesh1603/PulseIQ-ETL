# PulseIQ — Run ETL Now (PowerShell convenience wrapper)
# Usage: .\scripts\run_etl_now.ps1
# This triggers an immediate on-demand ETL run. Equivalent to:
#   python scripts/scheduler.py --run-now

Write-Host "PulseIQ ETL — Manual Trigger" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Check Docker warehouse is running
Write-Host "`nChecking warehouse health..." -ForegroundColor Yellow
$warehouseStatus = docker compose -f "$ProjectRoot\docker-compose.yml" ps warehouse --format json 2>$null | ConvertFrom-Json
if ($warehouseStatus -and $warehouseStatus.Health -eq "healthy") {
    Write-Host "  Warehouse: HEALTHY" -ForegroundColor Green
} else {
    Write-Host "  Warehouse may not be running. Start it with: docker compose up -d warehouse" -ForegroundColor Yellow
}

# Run the ETL pipeline immediately
Write-Host "`nStarting ETL pipeline..." -ForegroundColor Yellow
$python = if (Test-Path "$ProjectRoot\venv\Scripts\python.exe") {
    "$ProjectRoot\venv\Scripts\python.exe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    "python"
} else {
    "C:\Users\DELL\anaconda3\python.exe"
}

& $python "$ProjectRoot\scripts\scheduler.py" --run-now

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nETL run SUCCEEDED" -ForegroundColor Green
} else {
    Write-Host "`nETL run FAILED (exit code $LASTEXITCODE)" -ForegroundColor Red
    Write-Host "Check logs/etl.log and logs/scheduler.log for details." -ForegroundColor Yellow
}
