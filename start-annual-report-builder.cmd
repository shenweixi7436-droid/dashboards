@echo off
setlocal
cd /d "%~dp0"
python report-ai-server.py --open
if errorlevel 1 (
  echo.
  echo Failed to start the annual report builder.
  echo Check whether Python is installed and port 8765 is available.
  pause
)
