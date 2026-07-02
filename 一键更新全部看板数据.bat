@echo off
setlocal
cd /d "%~dp0"
set "PY=C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

echo Updating dashboard HTML files...
"%PY%" "%~dp0generate_v2.py"
if errorlevel 1 goto fail

echo.
echo Updating promo audit detail data...
"%PY%" "%~dp0update_promo_audit_detail.py"
if errorlevel 1 goto fail

echo.
echo Updating approval detail data...
"%PY%" "%~dp0update_approval_detail.py"
if errorlevel 1 goto fail

echo.
echo Updating device chart data...
"%PY%" "%~dp0update_device_channel_status.py"
if errorlevel 1 goto fail

echo.
echo Updating device detail data...
"%PY%" "%~dp0update_device_detail.py"
if errorlevel 1 goto fail

echo.
echo Updating month-aware key work data...
"%PY%" "%~dp0update_work_month_data.py"
if errorlevel 1 goto fail

echo.
echo Updating store business analysis dashboard...
"%PY%" "%~dp0..\build_audit_dashboard.py"
if errorlevel 1 goto fail

echo.
echo Done. Open index.html and press Ctrl+F5 to refresh.
pause
exit /b 0

:fail
echo.
echo Update failed. Please send this window screenshot to Codex.
pause
exit /b 1
