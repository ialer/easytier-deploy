@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo ================================
echo   EasyTier 停止
echo ================================
echo.

echo   [1/2] 停止 EasyTier-Core...
taskkill /F /IM easytier-core.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo   ✓ Core 已停止

echo   [2/2] 停止仪表盘...
:: 通过端口查找并杀掉Python进程
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":15889" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)
echo   ✓ 仪表盘已停止

echo.
echo   ================================
echo   已停止
echo   ================================
timeout /t 2 /nobreak >nul
