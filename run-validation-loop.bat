@echo off
REM X Knowledge Graph - Automated Validation Loop
REM Runs validation every 5 minutes

echo ========================================
echo   X Knowledge Graph - Validation Loop
echo ========================================
echo.

set APP_DIR=C:\Projects\x-knowledge-graph
set INTERVAL_MINUTES=5

:LOOP
echo [%date% %time%] Starting validation...
cd /d %APP_DIR%
git pull
python validate.py

echo.
echo Waiting %INTERVAL_MINUTES% minutes before next run...
timeout /t %INTERVAL_MINUTES% /nobreak >nul
goto LOOP
