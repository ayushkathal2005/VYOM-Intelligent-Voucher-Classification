# ==============================================================================
# VYOM+ Test & Verification Suite Runner (PowerShell / Windows)
# ==============================================================================
param(
    [switch]$SkipFrontendBuild = $false
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Running VYOM+ Full System Verification Suite" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $RepoRoot "backend\venv\Scripts\python.exe"

# 1. Backend Verification
Write-Host "`n[1/2] Running Backend Pytest Suite..." -ForegroundColor Yellow
& $VenvPython -m pytest -v (Join-Path $RepoRoot "backend\tests")
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[ERROR] Backend test suite failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "[OK] All Backend Tests Passed!" -ForegroundColor Green

# 2. Frontend Production Build Verification
if (-not $SkipFrontendBuild) {
    Write-Host "`n[2/2] Running Frontend Production Compilation (Turbopack / TypeScript)..." -ForegroundColor Yellow
    Set-Location (Join-Path $RepoRoot "frontend")
    & npm.cmd run build
    $BuildExit = $LASTEXITCODE
    Set-Location $RepoRoot
    if ($BuildExit -ne 0) {
        Write-Host "`n[ERROR] Frontend build failed with exit code $BuildExit" -ForegroundColor Red
        exit $BuildExit
    }
    Write-Host "[OK] Frontend Production Build Verified Successfully!" -ForegroundColor Green
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " ALL CHECKS PASSED: 100% GREEN ACROSS ENTIRE PLATFORM" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
exit 0
