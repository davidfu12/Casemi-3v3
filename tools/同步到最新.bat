@echo off
chcp 65001 >nul
REM 把本地代码变成 GitHub 上的最新版（会先备份本地改动）
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0同步到最新.ps1" %*
echo.
pause
