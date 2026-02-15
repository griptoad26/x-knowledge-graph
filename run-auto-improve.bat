@echo off
REM X Knowledge Graph - Autonomous Improvement Loop
REM Detects failures → Analyzes → Fixes → Pushes improvements

echo ========================================
echo   X Knowledge Graph - Auto Improve Loop
echo ========================================
echo.
echo This loop will:
echo   1. Pull latest code
echo   2. Run validation
echo   3. Auto-fix any issues found
echo   4. Push improvements to GitHub
echo.
echo WARNING: Commits will be pushed automatically!
echo ========================================
echo.

set APP_DIR=C:\Projects\x-knowledge-graph

pause

:LOOP
echo.
echo [%date% %time%] Improvement cycle starting...
cd /d %APP_DIR%
git pull

REM Check if auto-improve script exists
if exist auto-improve.ps1 (
    echo Running auto-improver...
    python auto-improve.ps1
) else (
    echo Running validation only...
    set HEADLESS=1 && python validate.py
)

echo.
echo Waiting 5 minutes before next cycle...
timeout /t 300 /nobreak >nul
goto LOOP
