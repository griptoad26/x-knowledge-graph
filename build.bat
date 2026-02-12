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

REM Build with hidden imports for common packages
%PYTHON_CMD% -m PyInstaller --onefile --windowed --name "XKnowledgeGraph" gui.py --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import tkinter.filedialog --hidden-import tkinter.messagebox --hidden-import networkx --hidden-import pandas --hidden-import numpy

if errorlevel 1 (
    echo.
    echo ERROR: Build failed - see error above
    pause
    exit /b 1
)

if not exist "dist\XKnowledgeGraph.exe" (
    echo.
    echo ERROR: Build failed - exe not created
    pause
    exit /b 1
)

echo EXE built successfully.

REM ============================================================================
REM Step 4: Copy EXE to main folder
REM ============================================================================
echo [4/4] Preparing distribution...

echo Copying XKnowledgeGraph.exe to main folder...
copy /Y dist\XKnowledgeGraph.exe . >nul 2>&1

echo.
echo ============================================
echo   BUILD SUCCESSFUL!
echo ============================================
echo.
echo The EXE is ready: XKnowledgeGraph.exe
echo.
echo Just double-click XKnowledgeGraph.exe to run!
echo.
pause

endlocal
exit /b 0
