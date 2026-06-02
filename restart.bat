@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo ================================
echo   EasyTier 重启
echo ================================
echo.

echo   [1/3] 停止...
taskkill /F /IM easytier-core.exe >nul 2>&1
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":15889" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo   [2/3] 启动 Core...
wscript.exe "%ROOT%\easytier-core.vbs"
timeout /t 3 /nobreak >nul

tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier" >nul
if %errorlevel%==0 (
    echo   ✓ Core 已启动
) else (
    echo   ✗ Core 启动失败
    pause
    exit /b 1
)

echo   [3/3] 启动仪表盘...
if exist "%ROOT%\dashboard.vbs" (
    wscript.exe "%ROOT%\dashboard.vbs"
    timeout /t 2 /nobreak >nul
    echo   ✓ 仪表盘: http://127.0.0.1:15889
)

echo.
echo   ================================
echo   重启完成！
echo   ================================
timeout /t 2 /nobreak >nul
