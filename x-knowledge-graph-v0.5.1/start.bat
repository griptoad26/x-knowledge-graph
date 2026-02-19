@echo off
REM X Knowledge Graph - VPS Start Script (Windows)
REM Usage: Double-click or run from PowerShell

echo Starting X Knowledge Graph...
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Navigate to app directory
cd /d "%SCRIPT_DIR%"

REM Start Python in background (Windows)
start "" python main.py

echo App started!
echo.
echo Access at: http://localhost:51338
echo Health check: curl http://localhost:51338/health
echo.
echo To stop: taskkill /F /IM python.exe
pause
