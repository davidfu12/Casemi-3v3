@echo off
chcp 65001 >nul
REM 拉取 → 提交 → 推送，一步完成
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0一键推送.ps1" %*
echo.
pause
