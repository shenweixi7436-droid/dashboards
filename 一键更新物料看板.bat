@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Update Material and Device Dashboards

set "PY=C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "SOURCE=C:\Users\shenw\Desktop\物料&设备数据分析\2026年物料及设备出库数据汇总.xlsx"
set "DASHBOARD_DIR=C:\Users\shenw\Desktop\看板\物料小组看板"
set "PYTHONUTF8=1"
set "PYTHONWARNINGS=ignore::UserWarning:openpyxl.worksheet._reader"
if not exist "%PY%" goto missing_python
if not exist "%SOURCE%" goto missing_source
if not exist "%DASHBOARD_DIR%\营销物料数据主看板.html" goto missing_dashboard
if not exist "%DASHBOARD_DIR%\设备主看版.html" goto missing_dashboard

echo.
echo Source: "%SOURCE%"
echo Updating material and device dashboard data...
"%PY%" "%~dp0update_material_device_dashboards.py" --source "%SOURCE%" --dashboard-dir "%DASHBOARD_DIR%"
if errorlevel 1 goto fail

echo.
echo Update completed.
echo Material dashboard: %DASHBOARD_DIR%\营销物料数据主看板.html
echo Device dashboard:   %DASHBOARD_DIR%\设备主看版.html
echo Only the specified workbook was read. No other workbook is used.
echo.
if /I "%~1"=="nopause" exit /b 0
pause
exit /b 0

:missing_source
echo.
echo Source workbook was not found:
echo %SOURCE%
if /I "%~1"=="nopause" exit /b 1
pause
exit /b 1

:missing_dashboard
echo.
echo Material or device main dashboard was not found in:
echo %DASHBOARD_DIR%
if /I "%~1"=="nopause" exit /b 1
pause
exit /b 1

:missing_python
echo.
echo Python runtime was not found. Please ask Codex to repair this update tool.
if /I "%~1"=="nopause" exit /b 1
pause
exit /b 1

:fail
echo.
echo Dashboard update failed. Please send this window to Codex.
if /I "%~1"=="nopause" exit /b 1
pause
exit /b 1
