# One-Click Launch Script for AI Steganography System
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting AI Steganography System Services...            " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start Python Engine (Port 8000)
Write-Host "[1/3] Launching Python FastAPI Engine (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\python_engine'; Write-Host '--- Python FastAPI Engine (Port 8000) ---' -ForegroundColor Cyan; python run_engine.py"

# 2. Start ASP.NET Core Web API (Port 5000)
Write-Host "[2/3] Launching ASP.NET Core Web API (Port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\backend\StegoApi'; Write-Host '--- ASP.NET Core Web API (Port 5000) ---' -ForegroundColor Cyan; dotnet run"

# 3. Start React Frontend (Port 5173)
Write-Host "[3/3] Launching React Frontend (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\frontend'; Write-Host '--- React Frontend (Port 5173) ---' -ForegroundColor Cyan; npm run dev"

Write-Host ""
Write-Host "All 3 services have been launched in separate terminal windows!" -ForegroundColor Green
Write-Host "Open your browser at:" -ForegroundColor White
Write-Host "  Frontend:    http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:5000/api/health" -ForegroundColor Cyan
Write-Host "  Python Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
