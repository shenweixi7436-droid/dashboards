@echo off
setlocal
cd /d "%~dp0"
title Publish Material Dashboard to GitHub

call "%~dp0一键更新物料看板.bat" nopause
if errorlevel 1 goto fail

echo.
echo The following material dashboard files will be published:
git status --short -- material-dashboard material-main-dashboard material-freight-dashboard build_material_dashboard.py convert_material_fonts.py "一键更新物料看板.bat" "一键发布物料看板到GitHub.bat" MATERIAL_DASHBOARD_README.md "一键更新全部看板数据.bat" dashboard_update_all.bat
echo.
set /p "CONFIRM=Type YES to commit and push these files: "
if /I not "%CONFIRM%"=="YES" goto cancelled

git add -- material-dashboard material-main-dashboard material-freight-dashboard build_material_dashboard.py convert_material_fonts.py "一键更新物料看板.bat" "一键发布物料看板到GitHub.bat" MATERIAL_DASHBOARD_README.md "一键更新全部看板数据.bat" dashboard_update_all.bat
git diff --cached --quiet
if not errorlevel 1 goto no_changes

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmm"') do set "STAMP=%%i"
git commit -m "Update material dashboard %STAMP%"
if errorlevel 1 goto fail
git push origin HEAD
if errorlevel 1 goto fail

echo.
echo Published successfully.
pause
exit /b 0

:no_changes
echo.
echo No material dashboard changes need publishing.
pause
exit /b 0

:cancelled
echo.
echo Publishing cancelled. Generated files were kept locally.
pause
exit /b 0

:fail
echo.
echo Publishing failed. Generated files were kept locally.
pause
exit /b 1
