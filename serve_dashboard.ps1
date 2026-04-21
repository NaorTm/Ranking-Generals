$dashboardDir = Join-Path $PSScriptRoot "outputs_cleaned_2026-04-21_fullpopulation_authoritative\dashboard"

if (-not (Test-Path $dashboardDir)) {
    Write-Error "Dashboard directory not found: $dashboardDir"
    exit 1
}

Write-Host "Serving dashboard from $dashboardDir on http://127.0.0.1:8000"
Set-Location $dashboardDir
python -m http.server 8000
