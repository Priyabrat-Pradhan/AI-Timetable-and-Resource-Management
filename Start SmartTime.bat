@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-smarttime.ps1"
if errorlevel 1 (
    echo.
    echo SmartTime could not start. Review the message above and the backend log files.
    pause
    exit /b 1
)
