$sourceDir = Join-Path $PSScriptRoot "outputs_improved_2026-04-24_upgrade_pass5_release_candidate\dashboard"
$targetDir = Join-Path $PSScriptRoot "docs"

if (-not (Test-Path $sourceDir)) {
    Write-Error "Source dashboard directory not found: $sourceDir"
    exit 1
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

$repoRoot = (Resolve-Path $PSScriptRoot).Path
$targetResolved = (Resolve-Path $targetDir).Path
$expectedTarget = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "docs"))
if ($targetResolved -ne $expectedTarget) {
    Write-Error "Refusing to clear unexpected target directory: $targetResolved"
    exit 1
}

Get-ChildItem -LiteralPath $targetResolved -Force | Remove-Item -Recurse -Force
Copy-Item -Path (Join-Path $sourceDir "*") -Destination $targetDir -Recurse -Force

$noJekyllPath = Join-Path $targetDir ".nojekyll"
if (-not (Test-Path $noJekyllPath)) {
    New-Item -ItemType File -Path $noJekyllPath | Out-Null
}

Write-Host "GitHub Pages dashboard synced to $targetDir"
