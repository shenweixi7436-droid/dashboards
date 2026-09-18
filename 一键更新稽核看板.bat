@echo off
setlocal
title Update Audit Dashboards
cd /d "%~dp0"
set "PY=C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "LOG=%~dp0update-audit.log"
set "STEP=STARTUP"
> "%LOG%" echo Update started %DATE% %TIME%

echo Updating audit dashboards only. Material dashboards are NOT updated.
echo To update material dashboards, run the dedicated material dashboard updater.

echo.
echo Updating main dashboard HTML files...
call :run_script "MAIN_DASHBOARDS" "%~dp0generate_v2.py"
if errorlevel 1 goto fail

echo.
echo Updating promo audit detail data...
call :run_script "PROMO_AUDIT" "%~dp0update_promo_audit_detail.py"
if errorlevel 1 goto fail

echo.
echo Updating approval detail data...
call :run_script "APPROVAL_AUDIT" "%~dp0update_approval_detail.py"
if errorlevel 1 goto fail

echo.
echo Updating device chart data...
call :run_script "DEVICE_CHANNEL" "%~dp0update_device_channel_status.py"
if errorlevel 1 goto fail

echo.
echo Updating device detail data...
call :run_script "DEVICE_DETAIL" "%~dp0update_device_detail.py"
if errorlevel 1 goto fail

echo.
echo Updating device region analysis data...
call :run_script "DEVICE_REGION" "%~dp0build_device_region_analysis.py"
if errorlevel 1 goto fail

echo.
echo Updating month-aware key work data...
call :run_script "WORK_MONTH_DATA" "%~dp0update_work_month_data.py"
if errorlevel 1 goto fail

echo.
echo Updating device ban action data...
call :run_script "DEVICE_BAN" "%~dp0build_device_ban_action.py"
if errorlevel 1 goto fail

echo.
echo Updating store audit detail snapshot...
call :run_script "STORE_AUDIT" "%~dp0build_store_audit_dashboard.py"
if errorlevel 1 goto fail

echo.
echo Updating gift anomaly live data...
call :run_script "GIFT_LIVE_DATA" "%~dp0build_gift_anomaly_dashboard.py"
if errorlevel 1 goto fail

echo.
echo Updating gift anomaly dashboard page (assets/pages)...
call :run_script "GIFT_ANOMALY_PAGE" "%~dp0update_gift_anomaly_page.py"
if errorlevel 1 goto fail

echo.
echo Updating schedule of progress dashboard...
call :run_script "SCHEDULE_PROGRESS" "%~dp0..\scripts\build_material_development_dashboard.py"
if errorlevel 1 goto fail

robocopy "%~dp0..\dist" "%~dp0Schedule of Progress\dist" material_development_progress_dashboard.html warning-vector.svg /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto fail

robocopy "%~dp0..\dist\assets\fonts" "%~dp0Schedule of Progress\dist\assets\fonts" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto fail

robocopy "%~dp0..\dist\assets\images" "%~dp0Schedule of Progress\dist\assets\images" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto fail

if exist "%~dp0..\dist\assets\previews\" (
    robocopy "%~dp0..\dist\assets\previews" "%~dp0Schedule of Progress\dist\assets\previews" /E /NFL /NDL /NJH /NJS /NP >nul
    if errorlevel 8 goto fail
)

echo.
echo Done. Open index.html and press Ctrl+F5 to refresh.
echo Material dashboards were skipped. Use the dedicated material updater for them.
echo Update log: %LOG%
pause
exit /b 0

:fail
echo.
echo Update failed at: %STEP%
echo Full log: %LOG%
type "%LOG%"
pause
exit /b 1

:run_script
set "STEP=%~1"
echo [RUN] %STEP%
echo [RUN] %STEP% >> "%LOG%"
"%PY%" "%~2" >> "%LOG%" 2>&1
if errorlevel 1 exit /b 1
echo [OK] %STEP%
echo [OK] %STEP% >> "%LOG%"
exit /b 0
