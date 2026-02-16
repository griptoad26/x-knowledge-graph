@echo off
REM X Knowledge Graph - Start on Specific Port
REM Usage: start.bat [port]

set PORT=%1
if "%PORT%"=="" set PORT=51338

echo Starting X Knowledge Graph on port %PORT%...

cd /d %~dp0
python main.py

echo App started on http://localhost:%PORT%
echo Health check: curl http://localhost:%PORT%/health
