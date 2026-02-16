<#
.SYNOPSIS
    X Knowledge Graph - Full Test Suite Runner
.DESCRIPTION
    Runs comprehensive tests on the X Knowledge Graph application,
    validates all views, and generates reports.
.PARAMETER Quick
    Run only quick smoke tests
.PARAMETER JSON
    Output results as JSON only
.PARAMETER HTML
    Generate HTML report
.PARAMETER NoGist
    Skip GitHub Gist upload
.EXAMPLE
    .\run-full-tests.ps1
    .\run-full-tests.ps1 -Quick -HTML
#>

param(
    [switch]$Quick,
    [switch]$JSON,
    [switch]$HTML,
    [switch]$NoGist
)

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PythonPath = "$ProjectRoot\venv\Scripts\python.exe"
$TestScript = "$ProjectRoot\test_all_views.py"
$ResultsFile = "$ProjectRoot\test_results.json"
$HTMLReport = "$ProjectRoot\test_report.html"
$LogFile = "$ProjectRoot\testing.log"
$GITHUB_TOKEN = $env:GITHUB_GIST_TOKEN

# Colors for console output
$Colors = @{
    Green = [System.ConsoleColor]::Green
    Red = [System.ConsoleColor]::Red
    Yellow = [System.ConsoleColor]::Yellow
    Cyan = [System.ConsoleColor]::Cyan
    White = [System.ConsoleColor]::White
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $LogEntry
    Write-Host $LogEntry
}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor $Colors.Cyan
    Write-Host "  $Title" -ForegroundColor $Colors.Cyan
    Write-Host ("=" * 70) -ForegroundColor $Colors.Cyan
    Write-Host ""
}

function Test-PythonInstallation {
    Write-Log "Checking Python installation..."
    
    if (-not (Test-Path $PythonPath)) {
        # Try system Python
        try {
            $PythonVersion = & python --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $PythonPath = "python"
                Write-Log "Using system Python: $PythonVersion"
                return $true
            }
        } catch {
            Write-Log "Python not found" -Level "ERROR"
            return $false
        }
    }
    
    if (Test-Path $PythonPath) {
        $Version = & $PythonPath --version 2>&1
        Write-Log "Python found: $Version"
        return $true
    }
    
    Write-Log "Python executable not found at: $PythonPath" -Level "ERROR"
    return $false
}

function Test-DataPaths {
    Write-Log "Checking data paths..."
    
    $DesktopXDir = "$env:USERPROFILE\Desktop\x_export"
    $DesktopGrokDir = "$env:USERPROFILE\Desktop\grok_export"
    
    if (Test-Path $DesktopXDir) {
        Write-Log "X export found: $DesktopXDir"
    } else {
        Write-Log "X export not found (will use test data)" -Level "WARNING"
    }
    
    if (Test-Path $DesktopGrokDir) {
        Write-Log "Grok export found: $DesktopGrokDir"
    } else {
        Write-Log "Grok export not found (will use test data)" -Level "WARNING"
    }
    
    return $true
}

function Run-PythonTests {
    param([bool]$QuickMode)
    
    Write-Header "Running Python Validation Tests"
    
    $Arguments = @()
    if ($QuickMode) { $Arguments += "--quick" }
    if ($JSON) { $Arguments += "--json" }
    if ($HTML) { $Arguments += "--html" }
    if (-not $NoGist -and $GITHUB_TOKEN) { $Arguments += "--gist" }
    
    $Arguments += "--output"
    $Arguments += $ResultsFile
    
    try {
        $Output = & $PythonPath $TestScript @Arguments 2>&1
        $ExitCode = $LASTEXITCODE
        
        # Log output
        $Output | ForEach-Object { Write-Log $_ }
        
        return $ExitCode
    }
    catch {
        Write-Log "Test execution failed: $_" -Level "ERROR"
        return 1
    }
}

function Test-HTTPEndpoints {
    Write-Header "Testing HTTP Endpoints"
    
    $Port = 5000
    $BaseUrl = "http://localhost:$Port"
    
    # Check if server is running
    try {
        $HealthCheck = Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 5
        if ($HealthCheck.status -eq 'ok') {
            Write-Log "Health check passed" -Level "INFO"
        }
    }
    catch {
        Write-Log "Server not running (skipping HTTP tests)" -Level "WARNING"
        return $true
    }
    
    # Test various endpoints
    $Endpoints = @(
        "/api/graph",
        "/api/actions",
        "/api/topics"
    )
    
    foreach ($Endpoint in $Endpoints) {
        try {
            $Response = Invoke-RestMethod -Uri "$BaseUrl$Endpoint" -TimeoutSec 10
            Write-Log "Endpoint $Endpoint: OK" -ForegroundColor $Colors.Green
        }
        catch {
            Write-Log "Endpoint $Endpoint: FAILED" -ForegroundColor $Colors.Red
        }
    }
    
    return $true
}

function Validate-FileOutputs {
    Write-Header "Validating File Outputs"
    
    $OutputFiles = @(
        @{ Path = $ResultsFile; Description = "JSON Results" },
        @{ Path = $HTMLReport; Description = "HTML Report" }
    )
    
    foreach ($File in $OutputFiles) {
        if (Test-Path $File.Path) {
            $Size = (Get-Item $File.Path).Length
            Write-Log "$($File.Description): $Size bytes" -ForegroundColor $Colors.Green
        }
        else {
            Write-Log "$($File.Description): Not found" -ForegroundColor $Colors.Yellow
        }
    }
    
    return $true
}

function Generate-Summary {
    param([int]$ExitCode, [double]$Duration)
    
    Write-Header "TEST SUMMARY"
    
    Write-Host "Duration: $([math]::Round($Duration, 2)) seconds" -ForegroundColor $Colors.White
    Write-Host "Results File: $ResultsFile" -ForegroundColor $Colors.White
    
    if ($HTML -and (Test-Path $HTMLReport)) {
        Write-Host "HTML Report: $HTMLReport" -ForegroundColor $Colors.White
    }
    
    if ($ExitCode -eq 0) {
        Write-Host ""
        Write-Host "✓ ALL TESTS PASSED" -ForegroundColor $Colors.Green
        Write-Log "All tests passed" -Level "INFO"
    }
    else {
        Write-Host ""
        Write-Host "✗ SOME TESTS FAILED" -ForegroundColor $Colors.Red
        Write-Log "Some tests failed" -Level "ERROR"
    }
    
    Write-Host ""
    
    return $ExitCode
}

# Main Execution
Write-Header "X KNOWLEDGE GRAPH - AUTOMATED TEST SUITE"
Write-Log "Starting automated tests..."
Write-Log "Project Root: $ProjectRoot"
Write-Log "Python Path: $PythonPath"

$GlobalStartTime = Get-Date

# Pre-flight checks
if (-not (Test-PythonInstallation)) {
    Write-Log "Python installation check failed" -Level "ERROR"
    exit 1
}

Test-DataPaths

# Run tests
$ExitCode = Run-PythonTests -QuickMode:$Quick

# Test HTTP endpoints (if server is running)
Test-HTTPEndpoints

# Validate outputs
Validate-FileOutputs

$GlobalDuration = (New-TimeSpan -Start $GlobalStartTime -End (Get-Date)).TotalSeconds

# Generate summary
Generate-Summary -ExitCode $ExitCode -Duration $GlobalDuration

exit $ExitCode
