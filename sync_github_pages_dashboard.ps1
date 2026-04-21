$sourceDir = Join-Path $PSScriptRoot "outputs_cleaned_2026-04-21_fullpopulation_authoritative\dashboard"
$targetDir = Join-Path $PSScriptRoot "docs"

if (-not (Test-Path $sourceDir)) {
    Write-Error "Source dashboard directory not found: $sourceDir"
    exit 1
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

Get-ChildItem -LiteralPath $targetDir -Force | Remove-Item -Recurse -Force
Copy-Item -Path (Join-Path $sourceDir "*") -Destination $targetDir -Recurse -Force

$noJekyllPath = Join-Path $targetDir ".nojekyll"
if (-not (Test-Path $noJekyllPath)) {
    New-Item -ItemType File -Path $noJekyllPath | Out-Null
}

Write-Host "GitHub Pages dashboard synced to $targetDir"
