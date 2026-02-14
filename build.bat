@echo off
REM ============================================================================
REM X Knowledge Graph - Windows Build Script (v0.4.30)
REM ============================================================================
REM Builds directory-based EXE for Windows 10/11
REM User only needs to: Extract .tar, double-click build.bat, double-click .exe
REM ============================================================================

setlocal EnableDelayedExpansion

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
echo [1/5] Checking Python...

if exist "python.exe" (
    set "PYTHON_CMD=python.exe"
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Please install Python 3.9-3.11 from https://python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo Python found.

REM ============================================================================
REM Step 2: Install Dependencies
REM ============================================================================
echo [2/5] Installing dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt >nul 2>&1
echo Dependencies ready.

REM ============================================================================
REM Step 3: Build the EXE
REM ============================================================================
echo [3/5] Building EXE (this may take a few minutes)...

REM Clean old build folders
if exist "dist" rmdir /s /q dist 2>nul
if exist "build" rmdir /s /q build 2>nul
if exist "XKnowledgeGraph" rmdir /s /q XKnowledgeGraph 2>nul

REM Build directory-based EXE (--onedir keeps everything together)
%PYTHON_CMD% -m PyInstaller --onedir --windowed --name "XKnowledgeGraph" main.py >nul 2>&1

if not exist "dist\XKnowledgeGraph\XKnowledgeGraph.exe" (
    echo ERROR: Build failed.
    echo Try running: python -m PyInstaller --onedir --windowed --name XKnowledgeGraph main.py
    echo.
    pause
    exit /b 1
)

echo EXE built successfully.
echo.

REM ============================================================================
REM Step 4: Prepare distribution folder
REM ============================================================================
echo [4/5] Preparing distribution...

REM Move XKnowledgeGraph folder to current directory
move "dist\XKnowledgeGraph" . >nul 2>&1
rmdir /s /q dist 2>nul

REM Copy frontend/ and core/ into XKnowledgeGraph folder
if exist "frontend" xcopy /E /Y "frontend\*" "XKnowledgeGraph\frontend\" >nul 2>&1
if exist "core" xcopy /E /Y "core\*" "XKnowledgeGraph\core\" >nul 2>&1

REM Copy main.py so source is available
if exist "main.py" copy /Y "main.py" "XKnowledgeGraph\" >nul 2>&1

echo Distribution prepared.
echo.

REM ============================================================================
REM Step 5: Cleanup
REM ============================================================================
echo [5/5] Cleaning up...

REM Remove build folder
if exist "build" rmdir /s /q build 2>nul

REM Remove __pycache__ folders
if exist "__pycache__" rmdir /s /q __pycache__ 2>nul
for /d /r . %%d in (__pycache__) do rmdir /s /q "%%d" 2>nul

echo.
echo ============================================
echo   BUILD COMPLETE!
echo ============================================
echo.
echo Your app is ready: XKnowledgeGraph\XKnowledgeGraph.exe
echo.
echo Double-click XKnowledgeGraph.exe to launch!
echo.
pause >nul
