@echo off
setlocal
cd /d "%~dp0"
set "PY=C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

echo Updating dashboard HTML files...
"%PY%" "%~dp0generate_v2.py"
if errorlevel 1 goto fail

echo Updating promo audit detail data...
"%PY%" "%~dp0update_promo_audit_detail.py"
if errorlevel 1 goto fail

echo Updating approval detail data...
"%PY%" "%~dp0update_approval_detail.py"
if errorlevel 1 goto fail

echo Updating device chart data...
"%PY%" "%~dp0update_device_channel_status.py"
if errorlevel 1 goto fail

echo Updating device detail data...
"%PY%" "%~dp0update_device_detail.py"
if errorlevel 1 goto fail

echo Updating month-aware dashboard data...
"%PY%" "%~dp0update_work_month_data.py"
if errorlevel 1 goto fail

if not exist "%~dp0assets\data\store-audit-popup.js" goto missing_data
if not exist "%~dp0assets\data\device-ban-action.js" goto missing_data
findstr /C:"window.STORE_AUDIT_POPUP_BY_MONTH" "%~dp0assets\data\store-audit-popup.js" >nul
if errorlevel 1 goto missing_data
findstr /C:"window.DEVICE_BAN_ACTION_BY_MONTH" "%~dp0assets\data\device-ban-action.js" >nul
if errorlevel 1 goto missing_data

echo Updating store business analysis dashboard...
"%PY%" "%~dp0..\build_audit_dashboard.py"
if errorlevel 1 goto fail

echo Updating schedule of progress dashboard...
"%PY%" "%~dp0..\scripts\build_material_development_dashboard.py"
if errorlevel 1 goto fail

robocopy "%~dp0..\dist" "%~dp0Schedule of Progress\dist" material_development_progress_dashboard.html warning-vector.svg /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto fail
robocopy "%~dp0..\dist\assets\fonts" "%~dp0Schedule of Progress\dist\assets\fonts" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto fail
robocopy "%~dp0..\dist\assets\images" "%~dp0Schedule of Progress\dist\assets\images" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto fail
robocopy "%~dp0..\dist\assets\previews" "%~dp0Schedule of Progress\dist\assets\previews" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto fail

echo Updating material inventory dashboard for GitHub Pages...
"%PY%" "%~dp0build_material_dashboard.py"
if errorlevel 1 goto fail

echo.
echo Update completed. Open dashboard-index from the desktop and press Ctrl+F5.
pause
exit /b 0

:missing_data
echo.
echo Update failed: store-audit-popup.js or device-ban-action.js is missing.
pause
exit /b 1

:fail
echo.
echo Update failed. Please send this window screenshot to Codex.
pause
exit /b 1
