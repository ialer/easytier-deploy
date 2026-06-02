@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo ================================
echo   EasyTier 启动
echo ================================
echo.

tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier" >nul
if %errorlevel%==0 (
    echo   ⚠ 已在运行，如需重启运行 restart.bat
    timeout /t 3 /nobreak >nul
    exit /b 0
)

echo   [1/2] 启动 Core...
wscript.exe "%ROOT%\easytier-core.vbs"
timeout /t 3 /nobreak >nul

tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier" >nul
if %errorlevel%==0 ( echo   ✓ Core 已启动 ) else ( echo   ✗ Core 启动失败 & pause & exit /b 1 )

echo   [2/2] 启动 Dashboard...
if exist "%ROOT%\dashboard.vbs" (
    wscript.exe "%ROOT%\dashboard.vbs"
    timeout /t 2 /nobreak >nul
    echo   ✓ Dashboard: http://127.0.0.1:15889
) else ( echo   ⏭ 仪表盘未配置 )

echo.
echo   启动完成！
timeout /t 3 /nobreak >nul
