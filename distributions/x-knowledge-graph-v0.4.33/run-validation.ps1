# X Knowledge Graph - Single Validation Run
# Runs validation once, checks failure rate, alerts if >10% fail
# Uses production data from Desktop

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  X Knowledge Graph - Validation Run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = "C:\Projects\x-knowledge-graph"
$DesktopXDir = "$env:USERPROFILE\Desktop\x_export"
$DesktopGrokDir = "$env:USERPROFILE\Desktop\grok_export"
$FailureThreshold = 0.10  # 10% failure threshold
$AlertChannel = "#alerts"  # Change to desired alert channel

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

# Run validation
Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] Validation Run" -ForegroundColor Cyan
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
    } elseif ($output -match "Failed:\s*(\d+)") {
        $failedTests = [int]$Matches[1]
    } else {
        # Try alternative pattern
        if ($output -match "colors.REDFailed:\s*(\d+)") {
            $failedTests = [int]$Matches[1]
        } else {
            $failedTests = 0
        }
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  VALIDATION RESULTS" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Total Tests: $totalTests"
    Write-Host "  Failed: $failedTests"
    
    if ($totalTests -gt 0) {
        $failureRate = $failedTests / $totalTests
        Write-Host "  Failure Rate: $([math]::Round($failureRate * 100, 2))%"
        
        if ($failureRate -gt $FailureThreshold) {
            Write-Host ""
            Write-Host "  ⚠️  ALERT: Failure rate exceeds $([int]($FailureThreshold * 100))%!" -ForegroundColor Red
            Write-Host "  LOOP PAUSED - Manual intervention required" -ForegroundColor Red
            
            # Create alert
            $alertMessage = "🚨 X Knowledge Graph Validation Alert`n" +
                          "Failure Rate: $([math]::Round($failureRate * 100, 2))% ($failedTests/$totalTests tests failed)`n" +
                          "Threshold: $([int]($FailureThreshold * 100))%`n" +
                          "Production Data: $UseProductionData`n" +
                          "Time: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))"
            
            Write-Host ""
            Write-Host "Alert would be sent:" -ForegroundColor Yellow
            Write-Host $alertMessage -ForegroundColor White
        } else {
            Write-Host ""
            Write-Host "  ✅ Validation passed (failure rate within threshold)" -ForegroundColor Green
        }
    }
    
} catch {
    Write-Host "Validation failed: $_" -ForegroundColor Red
    $failedTests = -1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VALIDATION COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Loop is PAUSED. Do not proceed until further directed." -ForegroundColor Yellow
Write-Host ""

# Exit with appropriate code
if ($failedTests -eq -1) {
    exit 1
} elseif ($totalTests -gt 0 -and ($failedTests / $totalTests) -gt $FailureThreshold) {
    exit 2  # Threshold exceeded
} else {
    exit 0  # Success
}
