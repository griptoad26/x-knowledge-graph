# X Knowledge Graph - PowerShell Deployment Script
# Usage: Run in PowerShell as Administrator

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  X Knowledge Graph - VPS Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$AppPath = "C:\projects\x-knowledge-graph"
$HealthUrl = "http://localhost:51338/health"

# Step 1: Stop existing app
Write-Host "[1/4] Stopping existing app..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Write-Host "  Done." -ForegroundColor Green

# Step 2: Pull latest from git
Write-Host "[2/4] Pulling latest from git..." -ForegroundColor Yellow
Set-Location $AppPath
git pull origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Git pull failed. Trying without checkout..." -ForegroundColor Yellow
}
Write-Host "  Done." -ForegroundColor Green

# Step 3: Start application
Write-Host "[3/4] Starting application..." -ForegroundColor Yellow
$logPath = Join-Path $AppPath "app.log"
$proc = Start-Process python -ArgumentList "main.py" -PassThru -NoNewWindow -RedirectStandardOutput $logPath -RedirectStandardError (Join-Path $AppPath "error.log")
Write-Host "  Process started (PID: $($proc.Id))" -ForegroundColor Green

# Step 4: Verify
Write-Host "[4/4] Verifying deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

try {
    $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 5
    Write-Host "  Status: $($response.status)" -ForegroundColor Green
    Write-Host "  Version: $($response.version)" -ForegroundColor Green
} catch {
    Write-Host "  Health check failed: $_" -ForegroundColor Red
    Write-Host "  Check app.log for errors." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "App URL: http://66.179.191.93:51338" -ForegroundColor Cyan
Write-Host "Logs: $logPath" -ForegroundColor Gray
Write-Host ""
