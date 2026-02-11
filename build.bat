@echo off
REM ============================================================================
REM X Knowledge Graph - Windows Build Script (v0.4.2)
REM ============================================================================
REM Builds a standalone .exe for Windows 10/11
REM Run this in the folder where you extracted the distribution
REM ============================================================================

setlocal

echo ============================================
echo   X Knowledge Graph - Windows EXE Builder
echo ============================================
echo.

REM Get current directory
set "CURRENT_DIR=%~dp0"
cd /d "%CURRENT_DIR%"

echo Working directory: %CURRENT_DIR%
echo.

REM ============================================================================
REM Step 1: Check Python
REM ============================================================================
echo [1/4] Checking Python...

if exist "python.exe" (
    set "PYTHON_CMD=python.exe"
    echo Found local Python
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install Python 3.9-3.11 from https://python.org/downloads/
    pause
    exit /b 1
)
echo Python found.

REM ============================================================================
REM Step 2: Install Dependencies
REM ============================================================================
echo [2/4] Installing dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed.

REM ============================================================================
REM Step 3: Build the EXE
REM ============================================================================
echo [3/4] Building EXE (this may take a few minutes)...

REM Clean old build
if exist "dist" rmdir /s /q dist 2>nul
mkdir dist

REM Build (use --collect-all for all dependencies)
%PYTHON_CMD% -m PyInstaller --onefile --windowed --name "XKnowledgeGraph" --collect-all gui.py 2>&1 | findstr /I "Building completed"

if errorlevel 1 (
    echo ERROR: Build failed - check output above
    pause
    exit /b 1
)

if not exist "dist\XKnowledgeGraph.exe" (
    echo ERROR: Build failed - exe not created
    pause
    exit /b 1
)

echo EXE built successfully.

REM ============================================================================
REM Step 4: Prepare Distribution
REM ============================================================================
echo [4/4] Preparing distribution...

REM Copy essential files
copy /Y requirements.txt dist\ >nul 2>&1
copy /Y README.md dist\ >nul 2>&1

REM Copy folders
xcopy /E /Y core dist\core\ >nul 2>&1
xcopy /E /Y frontend dist\frontend\ >nul 2>&1
xcopy /E /Y test_data dist\test_data\ >nul 2>&1
if exist "data" xcopy /E /Y data dist\data\ >nul 2>&1

echo.
echo ============================================
echo   BUILD SUCCESSFUL!
echo ============================================
echo.
echo The EXE is ready: dist\XKnowledgeGraph.exe
echo.
echo To distribute:
echo   1. Copy the 'dist' folder
echo   2. Recipients only need to run XKnowledgeGraph.exe
echo   3. No Python or installation required!
echo.
echo Test locally:
echo   dist\XKnowledgeGraph.exe
echo.
pause

endlocal
exit /b 0
