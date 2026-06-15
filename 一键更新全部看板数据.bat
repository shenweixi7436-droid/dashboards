@echo off
cd /d "%~dp0"
echo 正在更新两个HTML看板...
"C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0generate_v2.py"
if errorlevel 1 goto fail

echo.
echo 正在更新推广促销稽核明细...
"C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0update_promo_audit_detail.py"
if errorlevel 1 goto fail

echo.
echo 正在更新线上审批流程审核明细...
"C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0update_approval_detail.py"
if errorlevel 1 goto fail

echo.
echo 正在更新智能设备台账图表...
"C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0update_device_channel_status.py"
if errorlevel 1 goto fail

echo.
echo 正在更新智能设备台账详情...
"C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0update_device_detail.py"
if errorlevel 1 goto fail

echo.
echo 全部看板数据已更新完成。
echo 请打开总看板后按 Ctrl + F5 强制刷新。
pause
exit /b 0

:fail
echo.
echo 更新失败，请截图这个窗口发给 Codex 检查。
pause
exit /b 1
