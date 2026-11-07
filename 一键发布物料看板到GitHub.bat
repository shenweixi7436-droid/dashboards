@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Update and Publish Material Dashboards to GitHub

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
echo Step 1/4: Updating local material and device dashboard data...
echo Source: "%SOURCE%"
"%PY%" "%~dp0update_material_device_dashboards.py" --source "%SOURCE%" --dashboard-dir "%DASHBOARD_DIR%"
if errorlevel 1 goto fail

echo.
echo Step 2/4: Building material and device GitHub Pages dashboards...
"%PY%" "%~dp0publish_material_device_dashboards.py"
if errorlevel 1 goto fail

echo.
echo Files prepared for publishing:
git status --short -- material-main-dashboard device-main-dashboard material-freight-dashboard publish_material_device_dashboards.py update_material_device_dashboards.py "一键更新物料看板.bat" "一键发布物料看板到GitHub.bat" dashboard_update_all.bat
echo.
echo Step 3/4: Creating Git commit...
git add -- material-main-dashboard device-main-dashboard material-freight-dashboard publish_material_device_dashboards.py update_material_device_dashboards.py "一键更新物料看板.bat" "一键发布物料看板到GitHub.bat" dashboard_update_all.bat
git diff --cached --quiet
if not errorlevel 1 goto no_changes

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmm"') do set "STAMP=%%i"
git commit -m "Update material dashboard %STAMP%"
if errorlevel 1 goto fail
echo.
echo Step 4/4: Pushing to GitHub...
git push origin HEAD
if errorlevel 1 goto fail

echo.
echo Published successfully.
echo GitHub Pages will deploy the pushed files automatically.
pause
exit /b 0

:no_changes
echo.
echo No material dashboard changes need publishing.
pause
exit /b 0

:missing_source
echo.
echo Source workbook was not found:
echo %SOURCE%
pause
exit /b 1

:missing_dashboard
echo.
echo Material or device main dashboard was not found in:
echo %DASHBOARD_DIR%
pause
exit /b 1

:missing_python
echo.
echo Python runtime was not found. Please ask Codex to repair this update tool.
pause
exit /b 1

:fail
echo.
echo Update or publishing failed. Generated local files were kept.
pause
exit /b 1
