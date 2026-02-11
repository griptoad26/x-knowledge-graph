@echo off
REM ============================================================================
REM X Knowledge Graph - Quick Run (No Build Required!)
REM ============================================================================
REM For users with Python installed
REM ============================================================================

setlocal

echo ============================================
echo   X Knowledge Graph - Quick Start
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install Python 3.9-3.11 from https://python.org/downloads/
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt >nul 2>&1

echo.
echo Starting X Knowledge Graph...
echo.
echo Options:
echo   [1] Run Desktop App (GUI)
echo   [2] Run Web App (browser opens)
echo   [3] Exit
echo.

set /p CHOICE="Select option (1-3): "

if "%CHOICE%"=="1" (
    echo Starting Desktop App...
    python gui.py
) else if "%CHOICE%"=="2" (
    echo Starting Web App...
    echo The app will open at: http://localhost:5000
    python main.py
) else (
    echo Exiting...
    exit /b 0
)

endlocal
pause
