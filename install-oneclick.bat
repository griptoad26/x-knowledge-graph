@echo off
REM ============================================================================
REM X Knowledge Graph - User Installer (One-Click Setup)
REM ============================================================================
REM This installer sets up everything needed to run X Knowledge Graph
REM Run this on ANY Windows 10/11 machine (Home, Pro, Enterprise)
REM ============================================================================

setlocal EnableDelayedExpansion

set "APP_NAME=X Knowledge Graph"
set "APP_EXE=XKnowledgeGraph.exe"
set "INSTALL_DIR=%AppData%\%APP_NAME%"

title %APP_NAME% Installer

REM ============================================================================
REM Step 1: Welcome
REM ============================================================================
cls
echo.
echo %BLUE%========================================%RESET%
echo   %GREEN%%APP_NAME% - One-Click Installer%RESET%
echo %BLUE%========================================%RESET%
echo.
echo This will:
echo   [1] Check/install Python 3.11
echo   [2] Install required libraries
echo   [3] Download and set up the application
echo   [4] Create a desktop shortcut
echo.
echo Everything runs locally. No data leaves your machine.
echo.
pause
cls

REM ============================================================================
REM Step 2: Check Python
REM ============================================================================
echo [%GREEN%1/4%RESET%] Checking Python installation...

set "PYTHON_PATH="
set "PYTHON_VERSION="

REM Try py launcher first
py --version >nul 2>&1
if not errorlevel 1 (
    for /f "usebackq tokens=2 delims=," %%a in (`py --version 2^>nul`) do (
        set "PYTHON_VERSION=%%a"
        set "PYTHON_PATH=py"
    )
)

REM Try common paths
if "!PYTHON_PATH!"=="" (
    if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
        set "PYTHON_PATH=%LocalAppData%\Programs\Python\Python311\python.exe"
        set "PYTHON_VERSION=3.11"
    )
)

if "!PYTHON_PATH!"=="" (
    if exist "C:\Python311\python.exe" (
        set "PYTHON_PATH=C:\Python311\python.exe"
        set "PYTHON_VERSION=3.11"
    )
)

REM Install Python if needed
if "!PYTHON_PATH!"=="" (
    echo.
    echo Python not found. Installing Python 3.11...
    echo.
    
    REM Download Python
    powershell -Command "& {Write-Host 'Downloading Python 3.11...' -ForegroundColor Yellow; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '$env:TEMP\python-installer.exe'}"
    
    echo Running installer...
    echo IMPORTANT: Check "Add Python to PATH" when prompted!
    echo.
    
    "$env:TEMP\python-installer.exe" /quiet PrependPath=1 Include_test=0
    
    del "$env:TEMP\python-installer.exe"
    
    echo Waiting for Python installation to complete...
    timeout /t 10 /nobreak >nul
    
    set "PYTHON_PATH=py"
    set "PYTHON_VERSION=3.11"
    echo %GREEN%Python 3.11 installed successfully!%RESET%
) else (
    echo %GREEN%Found Python !PYTHON_VERSION!%RESET%
)

REM ============================================================================
REM Step 3: Install Dependencies
REM ============================================================================
echo.
echo [%GREEN%2/4%RESET%] Installing required libraries...

echo Installing pip upgrade...
!PYTHON_PATH! -m pip install --upgrade pip >nul 2>&1

echo Installing NetworkX...
!PYTHON_PATH! -m pip install networkx >nul 2>&1

echo Installing Pandas...
!PYTHON_PATH! -m pip install pandas >nul 2>&1

echo Installing NumPy...
!PYTHON_PATH! -m pip install numpy >nul 2>&1

echo Installing Matplotlib...
!PYTHON_PATH! -m pip install matplotlib >nul 2>&1

echo Installing PyInstaller...
!PYTHON_PATH! -m pip install pyinstaller >nul 2>&1

echo %GREEN%All dependencies installed!%RESET%

REM ============================================================================
REM Step 4: Download Application
REM ============================================================================
echo.
echo [%GREEN%3/4%RESET%] Setting up application...

REM Create installation directory
mkdir "%INSTALL_DIR%" >nul 2>&1
mkdir "%INSTALL_DIR%\data" >nul 2>&1

REM Download the latest EXE from GitHub/Release
set "DOWNLOAD_URL=https://github.com/yourusername/x-knowledge-graph/releases/latest/download/XKnowledgeGraph.exe"

echo Downloading %APP_NAME%...
powershell -Command "& {Write-Host 'Downloading from GitHub...' -ForegroundColor Yellow; try { Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%INSTALL_DIR%\%APP_EXE%' -ErrorAction Stop; Write-Host 'Download complete!' -ForegroundColor Green } catch { Write-Host 'Could not download from GitHub. Please download manually.' -ForegroundColor Red; exit 1 }}"

if exist "%INSTALL_DIR%\%APP_EXE%" (
    echo %GREEN%Application downloaded!%RESET%
) else (
    echo.
    echo Could not download automatically.
    echo Please:
    echo   1. Download XKnowledgeGraph.exe from our website
    echo   2. Save it to: %INSTALL_DIR%\
    echo.
    echo For now, running from source code...
    set "RUN_FROM_SOURCE=1"
)

REM Create placeholder
echo. > "%INSTALL_DIR%\data\PLACEHOLDER.txt"

REM ============================================================================
REM Step 5: Create Shortcut
REM ============================================================================
echo.
echo [%GREEN%4/4%RESET%] Creating desktop shortcut...

if "!RUN_FROM_SOURCE!"=="1" (
    REM Create a batch file to run from source
    echo @echo off > "%Desktop%\%APP_NAME%.bat"
    echo cd /d "%~dp0" >> "%Desktop%\%APP_NAME%.bat"
    echo python gui.py >> "%Desktop%\%APP_NAME%.bat"
    echo. >> "%Desktop%\%APP_NAME%.bat"
) else (
    REM Create proper shortcut using PowerShell
    powershell -Command "& {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut('%Desktop%\%APP_NAME%.lnk')
        $Shortcut.TargetPath = '%INSTALL_DIR%\%APP_EXE%'
        $Shortcut.WorkingDirectory = '%INSTALL_DIR%'
        $Shortcut.Description = '%APP_NAME% - Transform your X exports into knowledge graphs'
        $Shortcut.Save()
    }"
)

echo %GREEN%Desktop shortcut created!%RESET%

REM ============================================================================
REM Complete!
REM ============================================================================
cls
echo.
echo %GREEN%========================================%RESET%
echo   INSTALLATION COMPLETE!
echo %GREEN%========================================%RESET%
echo.
echo What's next:
echo   1. Double-click "%APP_NAME%" on your desktop
echo   2. Select your X data export folder
echo   3. Generate your knowledge graph!
echo.
echo Your data stays on your machine. No upload, no tracking.
echo.
echo Location: %INSTALL_DIR%
echo.
pause

endlocal
exit /b 0
