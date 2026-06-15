@echo off
chcp 65001 >nul
"C:\Users\shenw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0update_device_channel_status.py"
echo.
echo Done. Refresh the dashboard with Ctrl + F5.
pause
