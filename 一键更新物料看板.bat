@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Update Material Dashboard for GitHub Pages

set "PY=C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "PYTHONUTF8=1"
set "PYTHONWARNINGS=ignore::UserWarning:openpyxl.worksheet._reader"
if not exist "%PY%" goto missing_python

echo.
echo Updating source data and building the GitHub Pages dashboard...
"%PY%" "%~dp0build_material_dashboard.py"
if errorlevel 1 goto fail

echo.
echo Material dashboard update completed.
echo Preview: %~dp0material-dashboard\index.html
echo This step does not commit or push Git changes.
echo.
if /I "%~1"=="nopause" exit /b 0
pause
exit /b 0

:missing_python
echo.
echo Python runtime was not found. Please ask Codex to repair this update tool.
if /I "%~1"=="nopause" exit /b 1
pause
exit /b 1

:fail
echo.
echo Material dashboard update failed. Please send this window to Codex.
if /I "%~1"=="nopause" exit /b 1
pause
exit /b 1
