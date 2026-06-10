$dashboardDir = Join-Path $PSScriptRoot "outputs_improved_2026-04-24_upgrade_pass5_release_candidate\dashboard"

if (-not (Test-Path $dashboardDir)) {
    Write-Error "Dashboard directory not found: $dashboardDir"
    exit 1
}

Write-Host "Serving dashboard from $dashboardDir on http://127.0.0.1:8000"
Set-Location $dashboardDir
python -m http.server 8000
