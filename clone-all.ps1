# clone-all.ps1
# Clone all Card Fraud Platform repositories as siblings
#
# Usage:
#   cd C:\Users\kanna\github\card-fraud-platform
#   .\clone-all.ps1
#   .\clone-all.ps1 -OrgUrl "https://github.com/your-org"
#   .\clone-all.ps1 -OrgUrl "git@github.com:your-org"

param(
    [string]$OrgUrl = ""
)

$repos = @(
    "card-fraud-platform"
    "card-fraud-rule-management"
    "card-fraud-rule-engine"
    "card-fraud-transaction-management"
    "card-fraud-intelligence-portal"
)

$parentDir = Split-Path -Parent $PSScriptRoot
if (-not $parentDir) {
    $parentDir = (Get-Location).Path | Split-Path -Parent
}

Write-Host "Cloning repos into: $parentDir" -ForegroundColor Cyan
Write-Host ""

foreach ($repo in $repos) {
    $repoPath = Join-Path $parentDir $repo

    if (Test-Path $repoPath) {
        Write-Host "[SKIP] $repo -- already exists at $repoPath" -ForegroundColor Yellow
        continue
    }

    if (-not $OrgUrl) {
        Write-Host "[SKIP] $repo -- provide -OrgUrl to clone" -ForegroundColor Yellow
        Write-Host "       Example: .\clone-all.ps1 -OrgUrl 'https://github.com/your-org'" -ForegroundColor DarkGray
        continue
    }

    $url = "$OrgUrl/$repo.git"
    Write-Host "[CLONE] $url" -ForegroundColor Green
    git clone $url $repoPath
}

Write-Host ""
Write-Host "Done. Repository layout:" -ForegroundColor Cyan

foreach ($repo in $repos) {
    $repoPath = Join-Path $parentDir $repo
    if (Test-Path $repoPath) {
        Write-Host "  [OK] $repo" -ForegroundColor Green
    } else {
        Write-Host "  [--] $repo (not cloned)" -ForegroundColor DarkGray
    }
}
