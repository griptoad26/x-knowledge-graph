@echo off
REM XKG VPS Controller Service Setup
REM Run as Administrator

echo ==========================================
echo XKG VPS Controller - Service Setup
echo ==========================================
echo.

REM Check for NSSM
where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo NSSM not found. Installing via Chocolatey...
    choco install nssm -y
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install NSSM
        exit /b 1
    )
)
echo NSSM found

REM Create directories
if not exist C:\OpenClaw\agents mkdir C:\OpenClaw\agents
if not exist C:\OpenClaw\Logs mkdir C:\OpenClaw\Logs
echo Directories created

REM Check for PowerShell script
if not exist C:\OpenClaw\agents\vps-controller.ps1 (
    echo ERROR: vps-controller.ps1 not found
    exit /b 1
)
echo PowerShell script found

REM Stop existing service (if any)
echo.
nssm stop XKGController 2>nul
nssm remove XKGController confirm 2>nul

REM Install service
echo Installing service...
nssm install XKGController "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
nssm set XKGController AppParameters "-ExecutionPolicy Bypass -File C:\OpenClaw\agents\vps-controller.ps1 monitor"
nssm set XKGController AppDirectory "C:\OpenClaw\agents"
nssm set XKGController DisplayName "XKG Controller"
nssm set XKGController Description "XKG Health Monitor and Auto-Deploy"
nssm set XKGController Start SERVICE_AUTO_START
nssm set XKGController AppExit Default Restart
nssm set XKGController AppStdout C:\OpenClaw\Logs\service-stdout.log
nssm set XKGController AppStderr C:\OpenClaw\Logs\service-stderr.log
nssm set XKGController AppStdoutCreationDisposition 4
nssm set XKGController AppStderrCreationDisposition 4

REM Start service
echo.
nssm start XKGController

REM Verify
timeout /t 5 /nobreak >nul
nssm status XKGController

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Service: XKGController
echo Status: Running (check above)
echo Logs: C:\OpenClaw\Logs\
echo.
echo Commands:
echo   nssm start XKGController  - Start service
echo   nssm stop XKGController   - Stop service
echo   nssm restart XKGController - Restart service
echo   nssm status XKGController - Check status
echo.
echo PowerShell commands:
echo   C:\OpenClaw\agents\vps-controller.ps1 health - Manual check
echo   C:\OpenClaw\agents\vps-controller.ps1 verify - Verify server
echo   C:\OpenClaw\agents\vps-controller.ps1 restart - Restart server
