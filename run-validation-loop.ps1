# X Knowledge Graph - Automated Validation Loop
# Runs validation every 5 minutes, uploads results to GitHub Gist
# PAUSED by default - requires manual start

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  X Knowledge Graph - Validation Loop" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = "C:\Projects\x-knowledge-graph"
$DesktopXDir = "$env:USERPROFILE\Desktop\x_export"
$DesktopGrokDir = "$env:USERPROFILE\Desktop\grok_export"
$GistTokenEnv = "GITHUB_GIST_TOKEN"
$FailureThreshold = 0.10  # 10% failure threshold

# Check if GitHub token is set
if (-not $env:GITHUB_GIST_TOKEN) {
    Write-Host "WARNING: GitHub Gist token not set!" -ForegroundColor Yellow
    Write-Host "  Results will not be uploaded to Gist."
    Write-Host "  Set with: `$env:GITHUB_GIST_TOKEN = `"your-token`""
    Write-Host ""
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  App Directory: $AppDir"
Write-Host "  X Export (Desktop): $DesktopXDir"
Write-Host "  Grok Export (Desktop): $DesktopGrokDir"
Write-Host "  Failure Threshold: $([int]($FailureThreshold * 100))%"
Write-Host ""

# Check for production data
$UseProductionData = $false
if (Test-Path $DesktopXDir) {
    Write-Host "Using PRODUCTION data from Desktop" -ForegroundColor Cyan
    $UseProductionData = $true
    $env:X_EXPORT_PATH = "$DesktopXDir\data"
    $env:GROK_EXPORT_PATH = $DesktopGrokDir
} else {
    Write-Host "Using TEST data (production not found)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LOOP IS PAUSED" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run a single validation cycle, run:" -ForegroundColor White
Write-Host "  .\run-validation.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "To resume the loop, set \$Paused = \$false below and re-run this script." -ForegroundColor White
Write-Host ""

# PAUSED BY DEFAULT - requires manual intervention
$Paused = $true

if ($Paused) {
    Write-Host "Loop is paused. Exiting." -ForegroundColor Yellow
    exit 0
}

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
        $output = python validate.py 2>&1 | Out-String
        Write-Host $output
        
        # Parse results
        if ($output -match "Total Tests:\s*(\d+)") {
            $totalTests = [int]$Matches[1]
        }
        if ($output -match "Failed:\s*(\d+)") {
            $failedTests = [int]$Matches[1]
        } else {
            $failedTests = 0
        }
        
        # Check threshold
        if ($totalTests -gt 0) {
            $failureRate = $failedTests / $totalTests
            
            if ($failureRate -gt $FailureThreshold) {
                Write-Host ""
                Write-Host "⚠️  ALERT: Failure rate ($(($failureRate * 100).ToString('F2'))%) exceeds threshold!" -ForegroundColor Red
                Write-Host "Loop will pause. Manual intervention required." -ForegroundColor Red
                
                # Send alert (implement your notification here)
                # Send-Message -Channel $AlertChannel -Message "Validation failed: $failedTests/$totalTests tests failed"
                
                Write-Host ""
                Write-Host "Loop paused due to high failure rate." -ForegroundColor Yellow
                exit 2
            }
        }
        
    } catch {
        Write-Host "Validation failed: $_" -ForegroundColor Red
    }
    
    # Wait 5 minutes before next run
    Write-Host ""
    Write-Host "Waiting 5 minutes before next run..." -ForegroundColor Green
    Start-Sleep -Seconds 300  # 5 minutes
}
