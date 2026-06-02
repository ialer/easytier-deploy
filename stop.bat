@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo ================================
echo   EasyTier 停止
echo ================================
echo.

echo   [1/2] 停止 Core...
tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier-core" >nul 2>&1
if %errorlevel%==0 (
    taskkill /F /IM easytier-core.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo   ✓ Core 已停止
) else (
    echo   - Core 未在运行
)

echo   [2/2] 停止 Dashboard...
set "DASH_STOPPED=0"
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":15889" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
    set "DASH_STOPPED=1"
)
if "%DASH_STOPPED%"=="1" (
    echo   ✓ Dashboard 已停止
) else (
    echo   - Dashboard 未在运行
)

echo.
echo   已完成
timeout /t 2 /nobreak >nul
