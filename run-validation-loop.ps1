# X Knowledge Graph - Automated Validation Loop
# Runs validation every 5 minutes, uploads results to GitHub Gist

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  X Knowledge Graph - Validation Loop" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = "C:\Projects\x-knowledge-graph"
$GistTokenEnv = "GITHUB_GIST_TOKEN"

# Check if GitHub token is set
if (-not $env:GITHUB_GIST_TOKEN) {
    Write-Host "WARNING: GitHub Gist token not set!" -ForegroundColor Yellow
    Write-Host "  Results will not be uploaded to Gist."
    Write-Host "  Set with: `$env:GITHUB_GIST_TOKEN = `"your-token`""
    Write-Host ""
}

Write-Host "Starting automated validation loop..." -ForegroundColor Green
Write-Host "  Interval: Every 5 minutes"
Write-Host "  App Directory: $AppDir"
Write-Host ""

$loopCount = 0
while ($true) {
    $loopCount++
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host "[$timestamp] Run #$loopCount" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    
    # Pull latest code
    Write-Host "Pulling latest changes..." -ForegroundColor Yellow
    try {
        Push-Location $AppDir
        git pull | Out-Host
        Pop-Location
    } catch {
        Write-Host "Git pull failed: $_" -ForegroundColor Red
    }
    
    # Run validation
    Write-Host "Running validation..." -ForegroundColor Yellow
    try {
        $env:PYTHONUNBUFFERED = "1"
        python validate.py
    } catch {
        Write-Host "Validation failed: $_" -ForegroundColor Red
    }
    
    # Wait 5 minutes before next run
    Write-Host ""
    Write-Host "Waiting 5 minutes before next run..." -ForegroundColor Green
    Start-Sleep -Seconds 300  # 5 minutes
}
