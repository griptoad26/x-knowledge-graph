#!/usr/bin/env pwsh
# XKG VPS Autonomous Controller - Simple Version
# No OpenClaw required - runs as Windows Service

$PROJECT_PATH = "C:\Projects\x-knowledge-graph"
$LOG_PATH = "C:\OpenClaw\Logs"

# Ensure log directory exists
if (!(Test-Path $LOG_PATH)) {
    New-Item -ItemType Directory -Force -Path $LOG_PATH
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $Message" | Tee-Object -FilePath "$LOG_PATH\vps-controller.log" -Append
}

# Health Monitor (runs every 30 seconds)
function Start-HealthMonitor {
    Write-Log "Health Monitor started"
    
    while ($true) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:51338" -TimeoutSec 5 -ErrorAction SilentlyContinue -UseBasicParsing
            
            if ($response -and $response.StatusCode -eq 200) {
                # OK - no logging for healthy state
            }
            else {
                Write-Log "WARNING - Server not responding (HTTP $($response.StatusCode))"
                Restart-Server
            }
        }
        catch {
            Write-Log "ERROR - Server not responding: $($_.Exception.Message)"
            Restart-Server
        }
        
        Start-Sleep -Seconds 30
    }
}

# Auto-Deploy (runs every 5 minutes)
function Start-AutoDeploy {
    Write-Log "Auto-Deploy started"
    $LAST_VERSION = $null
    
    while ($true) {
        try {
            if (Test-Path "$PROJECT_PATH\VERSION.txt") {
                $localVersion = Get-Content "$PROJECT_PATH\VERSION.txt" -ErrorAction SilentlyContinue
                
                if ($LAST_VERSION -and $localVersion -ne $LAST_VERSION) {
                    Write-Log "New version detected: $localVersion (was $LAST_VERSION)"
                    Deploy-Update
                }
                elseif ($LAST_VERSION -eq $null) {
                    Write-Log "Initial version: $localVersion"
                }
                
                $LAST_VERSION = $localVersion
            }
            else {
                Write-Log "WARNING - VERSION.txt not found"
            }
        }
        catch {
            Write-Log "ERROR - Version check failed: $($_.Exception.Message)"
        }
        
        Start-Sleep -Seconds 300  # 5 minutes
    }
}

# Deploy Update
function Deploy-Update {
    Write-Log "Starting deployment..."
    
    # Stop current server
    Stop-XKGServer
    
    # Pull latest from git
    try {
        Set-Location $PROJECT_PATH
        git fetch origin 2>&1 | Out-Null
        $output = git pull origin main 2>&1
        Write-Log "Git pull: $output"
    }
    catch {
        Write-Log "ERROR - Git pull failed: $($_.Exception.Message)"
    }
    
    # Start server
    Start-XKGServer
    
    # Verify
    Start-Sleep -Seconds 5
    Verify-Server
}

# Start XKG Server
function Start-XKGServer {
    Write-Log "Starting XKG server..."
    
    # Kill existing Python processes for XKG
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*x-knowledge-graph*" -or $_.CommandLine -like "*main.py*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Set-Location $PROJECT_PATH
    $process = Start-Process -FilePath "python" -ArgumentList "main.py --port 51338" -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue
    
    Write-Log "Server started (PID: $($process.Id))"
    return $process
}

# Stop XKG Server
function Stop-XKGServer {
    Write-Log "Stopping XKG server..."
    
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*x-knowledge-graph*" -or $_.CommandLine -like "*main.py*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Log "Server stopped"
}

# Restart Server
function Restart-Server {
    Write-Log "Restarting server..."
    Stop-XKGServer
    Start-Sleep -Seconds 2
    Start-XKGServer
}

# Verify Server
function Verify-Server {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:51338" -TimeoutSec 10 -ErrorAction SilentlyContinue -UseBasicParsing
        if ($response -and $response.StatusCode -eq 200) {
            $version = $response.Content | Select-String -Pattern 'v[0-9.]+' | ForEach-Object { $_.Matches.Value }
            Write-Log "OK - Server running (HTTP 200, $version)"
            return $true
        }
        else {
            Write-Log "ERROR - Server returned $($response.StatusCode)"
            return $false
        }
    }
    catch {
        Write-Log "ERROR - Server verification failed: $($_.Exception.Message)"
        return $false
    }
}

# Run manual check
function Run-ManualCheck {
    Write-Log "=== Manual Health Check ==="
    
    # Check Python processes
    $pythonProcs = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*x-knowledge-graph*" -or $_.CommandLine -like "*main.py*"
    }
    
    if ($pythonProcs) {
        Write-Log "Python processes found: $($pythonProcs.Count)"
        $pythonProcs | ForEach-Object { Write-Log "  PID: $($_.Id), Memory: $([math]::Round($_.WorkingSet64 / 1MB, 2)) MB" }
    }
    else {
        Write-Log "WARNING - No XKG Python processes found"
        Start-XKGServer
    }
    
    # Check port
    $portCheck = netstat -ano | findstr 51338
    if ($portCheck) {
        Write-Log "Port 51338: LISTENING"
    }
    else {
        Write-Log "WARNING - Port 51338 not listening"
        Start-XKGServer
    }
    
    # Verify HTTP
    Verify-Server
    
    Write-Log "=== Manual Check Complete ==="
}

# Parse arguments
$action = $args[0]

switch ($action) {
    "health" { Run-ManualCheck }
    "start" { Start-XKGServer }
    "stop" { Stop-XKGServer }
    "restart" { Restart-Server }
    "verify" { Verify-Server }
    "monitor" { Start-HealthMonitor }
    "deploy" { Start-AutoDeploy }
    default {
        Write-Log "XKG VPS Controller"
        Write-Log "Usage: vps-controller.ps1 [health|start|stop|restart|verify|monitor|deploy]"
        Write-Log ""
        Write-Log "Commands:"
        Write-Log "  health  - Run manual health check"
        Write-Log "  start   - Start XKG server"
        Write-Log "  stop    - Stop XKG server"
        Write-Log "  restart - Restart XKG server"
        Write-Log "  verify  - Verify server is responding"
        Write-Log "  monitor - Start health monitor (loops forever)"
        Write-Log "  deploy  - Start auto-deploy watcher (loops forever)"
    }
}
