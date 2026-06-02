@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo ================================
echo   EasyTier 启动
echo ================================
echo.

:: 检查是否已运行
tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier" >nul
if %errorlevel%==0 (
    echo   ⚠ EasyTier-Core 已在运行
    echo   如需重启请运行 restart.bat
    timeout /t 3 /nobreak >nul
    exit /b 0
)

:: 启动 Core
echo   [1/2] 启动 EasyTier-Core...
wscript.exe "%ROOT%\easytier-core.vbs"
timeout /t 3 /nobreak >nul

tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier" >nul
if %errorlevel%==0 (
    echo   ✓ Core 已启动
) else (
    echo   ✗ Core 启动失败
    echo   请检查 config.toml 和 bin\easytier-core.exe
    pause
    exit /b 1
)

:: 启动仪表盘
echo   [2/2] 启动仪表盘...
if exist "%ROOT%\dashboard.vbs" (
    wscript.exe "%ROOT%\dashboard.vbs"
    timeout /t 2 /nobreak >nul
    echo   ✓ 仪表盘: http://127.0.0.1:15889
) else (
    echo   ⏭ 仪表盘未配置（运行 setup.bat 配置）
)

echo.
echo   ================================
echo   启动完成！
echo   仪表盘: http://127.0.0.1:15889
echo   ================================
timeout /t 3 /nobreak >nul
