# ==============================================================================
# VYOM+ Local Development Startup Script (PowerShell / Windows)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " VYOM+ Intelligent Voucher Classification Platform" -ForegroundColor Yellow
Write-Host " Local Full-Stack Development Launcher" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Environment Configuration Check
$EnvFile = Join-Path $RepoRoot ".env"
$EnvExample = Join-Path $RepoRoot ".env.example"
if (-not (Test-Path $EnvFile)) {
    Write-Host "[INFO] .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item $EnvExample $EnvFile
    Write-Host "[OK] Created .env template. Please configure your GEMINI_API_KEY if desired." -ForegroundColor Green
}

# 2. Backend Environment Check
$VenvPython = Join-Path $RepoRoot "backend\venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "[SETUP] Python virtualenv not found in backend/venv. Creating..." -ForegroundColor Yellow
    python -m venv (Join-Path $RepoRoot "backend\venv")
    Write-Host "[SETUP] Installing backend dependencies..." -ForegroundColor Yellow
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r (Join-Path $RepoRoot "backend\requirements-dev.txt")
}

# 3. Frontend Dependencies Check
$NodeModules = Join-Path $RepoRoot "frontend\node_modules"
if (-not (Test-Path $NodeModules)) {
    Write-Host "[SETUP] Frontend node_modules not found. Installing via npm.cmd..." -ForegroundColor Yellow
    Set-Location (Join-Path $RepoRoot "frontend")
    & npm.cmd install
    Set-Location $RepoRoot
}

Write-Host "`n[STARTING] Launching Backend FastAPI service on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$RepoRoot\backend'; & '$VenvPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "[STARTING] Launching Frontend Next.js service on http://localhost:3000..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$RepoRoot\frontend'; npm.cmd run dev"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " Both services launched in separate windows!" -ForegroundColor Green
Write-Host " - Frontend Dashboard:   http://localhost:3000" -ForegroundColor White
Write-Host " - Backend Swagger API:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host " - Health Check:         http://127.0.0.1:8000/health" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
