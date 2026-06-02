@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo ================================
echo   EasyTier 停止
echo ================================
echo.

echo   [1/2] 停止 Core...
taskkill /F /IM easytier-core.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo   ✓ Core 已停止

echo   [2/2] 停止 Dashboard...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":15889" ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1
echo   ✓ Dashboard 已停止

echo.
echo   已停止
timeout /t 2 /nobreak >nul
