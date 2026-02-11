@echo off
REM ============================================================================
REM X Knowledge Graph - Windows Build Script (v0.3.10)
REM ============================================================================
REM Builds a standalone .exe for Windows 10/11
REM Simple and robust Python detection
REM ============================================================================

echo ============================================
echo   X Knowledge Graph - Windows EXE Builder
echo   Version 0.3.10
echo ============================================
echo.

REM ============================================================================
REM BRANDING OPTIONS
REM ============================================================================
set APP_NAME=X Knowledge Graph
set EXE_NAME=XKnowledgeGraph

REM ============================================================================
REM Step 1: Find Python 3.11
REM ============================================================================
echo [1/4] Finding Python 3.11...

set PYTHON_CMD=

py -3.11 --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=py -3.11

if not defined PYTHON_CMD py --version 2>nul | findstr /R "3\.11" >nul
if not errorlevel 1 if not defined PYTHON_CMD set PYTHON_CMD=py

if not defined PYTHON_CMD python --version 2>nul | findstr /R "3\.11" >nul
if not errorlevel 1 if not defined PYTHON_CMD set PYTHON_CMD=python

if not defined PYTHON_CMD python3 --version 2>nul | findstr /R "3\.11" >nul
if not errorlevel 1 if not defined PYTHON_CMD set PYTHON_CMD=python3

if not defined PYTHON_CMD if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set PYTHON_CMD=%LocalAppData%\Programs\Python\Python311\python.exe
if not defined PYTHON_CMD if exist "C:\Python311\python.exe" set PYTHON_CMD=C:\Python311\python.exe

if not defined PYTHON_CMD (
    echo ERROR: Python 3.11 not found!
    echo.
    echo Please install Python 3.11:
    echo   winget install Python.Python.3.11
    pause
    exit /b 1
)

echo Using: %PYTHON_CMD%
%PYTHON_CMD% --version

REM ============================================================================
REM Step 2: Install Dependencies
REM ============================================================================
echo [2/4] Installing dependencies...

%PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1
%PYTHON_CMD% -m pip install flask flask-cors flask-compress networkx pandas numpy pyinstaller >nul 2>&1
echo Done!

REM ============================================================================
REM Step 3: Build
REM ============================================================================
echo [3/4] Building EXE (this may take a few minutes)...

if exist "dist" rmdir /s /q dist 2>nul
if exist "build" rmdir /s /q build 2>nul

set ICON_ARG=
if exist "frontend\favicon.ico" set ICON_ARG=--icon frontend\favicon.ico
if exist "resources\icon.ico" set ICON_ARG=--icon resources\icon.ico

REM Build with all options on command line
%PYTHON_CMD% -m PyInstaller --onefile --windowed --name "%EXE_NAME%" %ICON_ARG% --hidden-import flask --hidden-import flask_cors --hidden-import flask_compress --hidden-import werkzeug --hidden-import jinja2 --hidden-import markupsafe --hidden-import click --hidden-import itsdangerous --hidden-import blinker --hidden-import networkx --hidden-import networkx.drawing --hidden-import networkx.readwrite --hidden-import pandas --hidden-import pandas._libs --hidden-import pandas._libs.window --hidden-import pandas._libs.tslibs --hidden-import numpy --hidden-import numpy.core._methods --hidden-import numpy.core.multiarray --hidden-import numpy.lib.format --add-data "frontend;frontend" --add-data "core;core" main.py

if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM ============================================================================
REM Step 4: Prepare Distribution
REM ============================================================================
echo [4/4] Preparing distribution...

if not exist "dist\data" mkdir "dist\data"
echo. > "dist\data\PLACEHOLDER.txt"
if exist "README.md" copy README.md dist\ >nul 2>&1

echo.
echo ============================================
echo   BUILD SUCCESSFUL!
echo ============================================
echo.
echo Output: dist\%EXE_NAME%.exe
echo App:    %APP_NAME%
echo.
echo Copy 'dist' folder to use.
echo.
pause
