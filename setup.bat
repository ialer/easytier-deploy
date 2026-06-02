@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   EasyTier 一键部署                      ║
echo  ╚══════════════════════════════════════════╝
echo.

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "BIN=%ROOT%\bin"
set "PY=%ROOT%\python\python.exe"
set "PYW=%ROOT%\python\pythonw.exe"
set "EASYTIER_VER=v2.6.4"

:: ============================================
:: 1. 环境检查
:: ============================================
echo [1/7] 环境检查...

if not exist "%BIN%\easytier-core.exe" (
    echo   ✗ 缺少 bin\easytier-core.exe
    echo   请重新下载完整安装包
    pause
    exit /b 1
)

if not exist "%PY%" (
    echo   ✗ 缺少 python\python.exe
    echo   请重新下载完整安装包
    pause
    exit /b 1
)

echo   ✓ EasyTier %EASYTIER_VER%
for /f "tokens=*" %%v in ('"%PY%" --version 2^>^&1') do echo   ✓ %%v (内置)

:: ============================================
:: 2. 检查更新（可选）
:: ============================================
echo.
echo [2/7] 检查更新...

set "LATEST_VER="
for /f "tokens=*" %%v in ('powershell -NoProfile -Command "try{(Invoke-RestMethod -Uri 'https://api.github.com/repos/EasyTier/EasyTier/releases/latest' -UseBasicParsing -TimeoutSec 5).tag_name}catch{''}" 2^>nul') do set "LATEST_VER=%%v"

if "%LATEST_VER%"=="" (
    echo   ⚠ 无法连接更新服务器，使用当前版本
    goto :skip_update
)

if "%LATEST_VER%"=="%EASYTIER_VER%" (
    echo   ✓ 已是最新版本 %EASYTIER_VER%
    goto :skip_update
)

echo.
echo   ┌──────────────────────────────────────┐
echo   │  发现新版本!                          │
echo   │  当前: %EASYTIER_VER%                        │
echo   │  最新: !LATEST_VER!                        │
echo   └──────────────────────────────────────┘
echo.
set /p "DO_UPDATE=  是否更新? (Y/n): "
if /i "%DO_UPDATE%"=="n" (
    echo   保持当前版本
    goto :skip_update
)

echo.
echo   下载 !LATEST_VER! ...
set "DL_URL=https://github.com/EasyTier/EasyTier/releases/download/!LATEST_VER!/easytier-windows-x86_64-!LATEST_VER!.zip"
set "DL_FILE=%ROOT%\_update.zip"
set "DL_DIR=%ROOT%\_update"

powershell -NoProfile -Command ^
    "$ProgressPreference='SilentlyContinue';" ^
    "try{" ^
    "  Invoke-WebRequest -Uri '%DL_URL%' -OutFile '%DL_FILE%' -UseBasicParsing -TimeoutSec 120;" ^
    "  Write-Host '  下载完成'" ^
    "}catch{" ^
    "  Write-Host ('  下载失败: '+$_.Exception.Message);" ^
    "  exit 1" ^
    "}"

if %errorlevel% neq 0 (
    echo   ⚠ 更新失败，继续使用当前版本
    del /f "%DL_FILE%" 2>nul
    goto :skip_update
)

:: 解压并替换
mkdir "%DL_DIR%" 2>nul
powershell -NoProfile -Command "Expand-Archive -Path '%DL_FILE%' -DestinationPath '%DL_DIR%' -Force"

:: 停止当前服务
taskkill /F /IM easytier-core.exe >nul 2>&1

:: 替换文件
for /r "%DL_DIR%" %%f in (easytier-core.exe easytier-cli.exe Packet.dll WinDivert64.sys wintun.dll) do (
    if exist "%%f" (
        copy /y "%%f" "%BIN%\" >nul
        echo   ✓ %%~nxf
    )
)

:: 清理
rd /s /q "%DL_DIR%" 2>nul
del /f "%DL_FILE%" 2>nul

set "EASYTIER_VER=!LATEST_VER!"
echo.
echo   ✓ 已更新到 !LATEST_VER!

:skip_update

:: ============================================
:: 3. 网络配置
:: ============================================
echo.
echo [3/7] 网络配置（所有节点必须一致）
echo   ───────────────────────────────────

set /p "NET_NAME=  网络名称: "
if "%NET_NAME%"=="" ( echo   ✗ 不能为空 & pause & exit /b 1 )

set /p "NET_SECRET=*** "
if "%NET_SECRET%"=="" ( echo   ✗ 不能为空 & pause & exit /b 1 )

set /p "SERVER_URI=  引导节点 [如 tcp://1.2.3.4:11010]: "
if "%SERVER_URI%"=="" ( echo   ✗ 不能为空 & pause & exit /b 1 )

set /p "CIDR_PREFIX=  网段 [默认 10.0.0]: "
if "%CIDR_PREFIX%"=="" set "CIDR_PREFIX=10.0.0"

:: ============================================
:: 4. 设备配置
:: ============================================
echo.
echo [4/7] 设备配置
echo   ───────────────────────────────────

set "DEFAULT_HOST=%COMPUTERNAME%"
set /p "HOSTNAME=  设备名 [%DEFAULT_HOST%]: "
if "%HOSTNAME%"=="" set "HOSTNAME=%DEFAULT_HOST%"

echo   IP范围: %CIDR_PREFIX%.2 ~ %CIDR_PREFIX%.254
set /p "VIP=  IP末位: "
if "%VIP%"=="" set "VIP=2"

:: ============================================
:: 5. 生成配置
:: ============================================
echo.
echo [5/7] 生成配置...

(
    echo # 自动生成 - %date% %time%
    echo [network_identity]
    echo network_name = "%NET_NAME%"
    echo network_secret = "%NET_SECRET%"
    echo [[peer]]
    echo uri = "%SERVER_URI%"
    echo [flags]
    echo ipv4 = "%CIDR_PREFIX%.%VIP%/24"
    echo hostname = "%HOSTNAME%"
    echo listeners = []
) > "%ROOT%\config.toml"
echo   ✓ config.toml

:: ============================================
:: 6. 生成启动器
:: ============================================
echo.
echo [6/7] 生成启动器...

:: Core 启动器（静默）
(
    echo Set WshShell = CreateObject^("WScript.Shell"^)
    echo WshShell.Run """%BIN%\easytier-core.exe"" -c ""%ROOT%\config.toml""", 0, False
) > "%ROOT%\easytier-core.vbs"
echo   ✓ Core (静默)

:: Dashboard 启动器（使用内置Python，静默）
(
    echo Set WshShell = CreateObject^("WScript.Shell"^)
    echo WshShell.Run """%PYW%"" ""%ROOT%\dashboard.py""", 0, False
) > "%ROOT%\dashboard.vbs"
echo   ✓ Dashboard (静默)

:: ============================================
:: 7. 开机自启 + 启动
:: ============================================
echo.
echo [7/7] 开机自启...

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo   ⚠ 需管理员权限，右键重新运行
    goto :start_now
)

schtasks /Delete /TN "EasyTeam-Core" /F >nul 2>&1
schtasks /Delete /TN "EasyTeam-Dashboard" /F >nul 2>&1

schtasks /Create /TN "EasyTeam-Core" /TR "wscript.exe \"%ROOT%\easytier-core.vbs\"" /SC ONLOGON /RL HIGHEST /F >nul 2>&1
echo   ✓ Core 开机自启

schtasks /Create /TN "EasyTeam-Dashboard" /TR "wscript.exe \"%ROOT%\dashboard.vbs\"" /SC ONLOGON /RL HIGHEST /F >nul 2>&1
echo   ✓ Dashboard 开机自启

:start_now

:: 启动服务
echo.
echo   启动中...
wscript.exe "%ROOT%\easytier-core.vbs"
timeout /t 2 /nobreak >nul

tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier" >nul
if %errorlevel%==0 ( echo   ✓ Core 运行中 ) else ( echo   ✗ Core 启动失败 )

wscript.exe "%ROOT%\dashboard.vbs"
timeout /t 2 /nobreak >nul
echo   ✓ Dashboard 运行中

:: ============================================
:: 完成
:: ============================================
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║           ✓ 部署完成！                        ║
echo  ╠══════════════════════════════════════════════╣
echo  ║  网络:   %NET_NAME%
echo  ║  设备:   %HOSTNAME%
echo  ║  虚拟IP: %CIDR_PREFIX%.%VIP%
echo  ║  版本:   %EASYTIER_VER%
echo  ║  仪表盘: http://127.0.0.1:15889
echo  ╠══════════════════════════════════════════════╣
echo  ║  · 所有服务已静默运行（无弹窗）
echo  ║  · 已注册开机自启
echo  ║  · 仪表盘使用内置Python，无需安装
echo  ║  · 管理: start/stop/restart/status.bat
echo  ╚══════════════════════════════════════════════╝
echo.
pause
