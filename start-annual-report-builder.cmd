@echo off
setlocal
cd /d "%~dp0"
set "REPORT_URL=http://127.0.0.1:8765/annual-report-builder.html"
set "PYTHONW=%LocalAppData%\Programs\Python\Python312\pythonw.exe"

powershell -NoProfile -Command "if (-not (Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue)) { exit 1 }"
if errorlevel 1 (
  if exist "%PYTHONW%" (
    start "" "%PYTHONW%" "%~dp0report-ai-server.py" --port 8765
  ) else (
    start "" /min python "%~dp0report-ai-server.py" --port 8765
  )
  timeout /t 2 /nobreak >nul
)

start "" "%REPORT_URL%"
endlocal
