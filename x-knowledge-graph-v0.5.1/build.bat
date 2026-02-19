@echo off
REM X Knowledge Graph - Windows Build Script
REM Builds production-ready EXE with PyInstaller

echo ========================================
echo   X Knowledge Graph - Windows Build
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set APP_NAME=XKnowledgeGraph
set VERSION_FILE=%SCRIPT_DIR%VERSION.txt
set BUILD_DIR=%SCRIPT_DIR%build
set DIST_DIR=%SCRIPT_DIR%dist

REM Read version
for /f "tokens=*" %%a in (%VERSION_FILE%) do set VERSION=%%a

echo Version: %VERSION%
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"

mkdir "%DIST_DIR%"

REM Install dependencies if needed
echo Checking dependencies...
pip install -q pyinstaller flask flask-cors requests 2>nul

REM Run PyInstaller
echo.
echo Building EXE with PyInstaller...
echo.

pyinstaller --onefile ^
    --name %APP_NAME% ^
    --windowed ^
    --clean ^
    --noconsole ^
    --add-data "frontend;frontend" ^
    --add-data "core;core" ^
    --hidden-import flask ^
    --hidden-import flask_cors ^
    --hidden-import requests ^
    --collect-all flask_cors ^
    main.py

echo.
if exist "%DIST_DIR%\%APP_NAME%.exe" (
    echo ========================================
    echo   BUILD SUCCESSFUL
    echo ========================================
    echo.
    for %%I in ("%DIST_DIR%\%APP_NAME%.exe") do set SIZE=%%~zI
    echo File: %DIST_DIR%\%APP_NAME%.exe
    echo Size: %SIZE% bytes
    
    REM Generate checksum
    echo.
    echo Generating SHA256 checksum...
    powershell -Command "(Get-FileHash '%DIST_DIR%\%APP_NAME%.exe' -Algorithm SHA256).Hash | Out-File '%DIST_DIR%\checksum.txt'"
    echo Checksum saved to: %DIST_DIR%\checksum.txt
    
    echo.
    echo Next steps:
    echo   1. Test the EXE: %DIST_DIR%\%APP_NAME%.exe
    echo   2. Run validation: python validate.py
    echo   3. If passed, run: upload-release.ps1
    echo.
) else (
    echo BUILD FAILED - EXE not found!
    exit /b 1
)

pause
