@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   EasyTier 一键部署包 v1.2.0               ║
echo  ║   下载 ─ 配置 ─ 启动 ─ 开机自启          ║
echo  ╚══════════════════════════════════════════╝
echo.

set "ROOT=%~dp0"
:: 安全：正确处理路径（移除末尾反斜杠）
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "BIN=%ROOT%\bin"

:: ============================================
:: 1. 自动下载 EasyTier
:: ============================================
if exist "%BIN%\easytier-core.exe" (
    echo [1/7] EasyTier 已存在，跳过下载
    goto :skip_download
)

echo [1/7] 下载 EasyTier 程序...
echo.

where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo   ✗ 未找到 PowerShell
    echo   请手动下载: https://github.com/EasyTier/EasyTier/releases
    echo   解压后将 *.exe *.dll *.sys 放入 bin\
    pause
    exit /b 1
)

:: 获取最新版本
echo   获取最新版本...
for /f "tokens=*" %%v in ('powershell -NoProfile -Command "(Invoke-RestMethod -Uri 'https://api.github.com/repos/EasyTier/EasyTier/releases/latest' -UseBasicParsing).tag_name"') do set "VERSION=%%v"

if "%VERSION%"=="" (
    echo   ⚠ 无法获取版本，使用 v2.6.4
    set "VERSION=v2.6.4"
)
echo   版本: %VERSION!

:: 构造下载URL
set "ZIP_NAME=easytier-windows-x86_64-%VERSION%.zip"
set "DOWNLOAD_URL=https://github.com/EasyTier/EasyTier/releases/download/%VERSION%/%ZIP_NAME%"
set "ZIP_FILE=%ROOT%\%ZIP_NAME%"

:: 创建目录
mkdir "%BIN%" 2>nul

:: 下载
echo   下载中... (约30MB，可能需要几分钟)
echo   %DOWNLOAD_URL%
echo.

powershell -NoProfile -Command ^
    "$ProgressPreference='SilentlyContinue';" ^
    "try{" ^
    "  Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing;" ^
    "  Write-Host '  下载完成'" ^
    "}catch{" ^
    "  Write-Host ('  下载失败: '+$_.Exception.Message);" ^
    "  exit 1" ^
    "}"

if %errorlevel% neq 0 (
    echo.
    echo   ✗ 下载失败，请手动下载:
    echo   %DOWNLOAD_URL%
    pause
    exit /b 1
)

:: 解压
echo   解压中...
set "TEMP_DIR=%ROOT%\_extract"
mkdir "%TEMP_DIR%" 2>nul

powershell -NoProfile -Command ^
    "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TEMP_DIR%' -Force"

:: 复制所需文件
echo   安装中...
set "COUNT=0"
for /r "%TEMP_DIR%" %%f in (easytier-core.exe easytier-cli.exe Packet.dll WinDivert64.sys wintun.dll) do (
    if exist "%%f" (
        copy /y "%%f" "%BIN%\" >nul
        set /a COUNT+=1
        echo   ✓ %%~nxf
    )
)

:: 清理
rd /s /q "%TEMP_DIR%" 2>nul
del /f "%ZIP_FILE%" 2>nul

if exist "%BIN%\easytier-core.exe" (
    echo.
    echo   ✓ EasyTier %VERSION% 安装完成 (%COUNT% 个文件)
) else (
    echo.
    echo   ✗ 安装失败
    pause
    exit /b 1
)

:skip_download

:: ============================================
:: 2. 网络配置 - 安全：输入验证
:: ============================================
echo.
echo [2/7] 网络配置（所有节点一致）
echo   ───────────────────────────────────

:input_net_name
set /p "NET_NAME=  网络名称: "
if "%NET_NAME%"=="" ( echo   ✗ 不能为空 & goto :input_net_name )
:: 安全：检查特殊字符
echo "%NET_NAME%" | findstr /R "[<>|^&]" >nul && ( echo   ✗ 不能包含特殊字符 ^< ^> ^| ^& & goto :input_net_name )
if "%NET_NAME%"=="" ( echo   ✗ 不能为空 & goto :input_net_name )

:input_net_secret
set /p "NET_SECRET=*** "
if "%NET_SECRET%"=="" ( echo   ✗ 不能为空 & goto :input_net_secret )
:: 安全：检查长度
if "%NET_SECRET:~0,1%"=="" ( echo   ✗ 密钥不能为空 & goto :input_net_secret )

:input_server_uri
set /p "SERVER_URI=  引导节点 [如 tcp://1.2.3.4:11010]: "
if "%SERVER_URI%"=="" ( echo   ✗ 不能为空 & goto :input_server_uri )
:: 安全：检查URI格式
echo "%SERVER_URI%" | findstr /R "^tcp:// ^udp://" >nul || ( echo   ✗ 需要 tcp:// 或 udp:// 开头 & goto :input_server_uri )

set /p "CIDR_PREFIX=  网段 [默认 10.0.0]: "
if "%CIDR_PREFIX%"=="" set "CIDR_PREFIX=10.0.0"

:: ============================================
:: 3. 设备配置
:: ============================================
echo.
echo [3/7] 设备配置
echo   ───────────────────────────────────

set "DEFAULT_HOST=%COMPUTERNAME%"
:input_hostname
set /p "HOSTNAME=  设备名 [%DEFAULT_HOST%]: "
if "%HOSTNAME%"=="" set "HOSTNAME=%DEFAULT_HOST%"
:: 安全：检查特殊字符
echo "%HOSTNAME%" | findstr /R "[<>|^&\"/\\]" >nul && ( echo   ✗ 不能包含特殊字符 & goto :input_hostname )

echo   IP范围: %CIDR_PREFIX%.2 ~ %CIDR_PREFIX%.254
:input_vip
set /p "VIP=  IP末位: "
if "%VIP%"=="" set "VIP=2"
:: 安全：检查是否为数字
set /a "VIP_CHECK=%VIP%" 2>nul
if %VIP_CHECK% LSS 2 ( echo   ✗ 必须大于等于2 & goto :input_vip )
if %VIP_CHECK% GTR 254 ( echo   ✗ 必须小于等于254 & goto :input_vip )

:: ============================================
:: 4. 检测 Python
:: ============================================
echo.
echo [4/7] 检测 Python...

set "PYTHON_PATH="
for /f "tokens=*" %%p in ('where python3.11 2^>nul') do if not defined PYTHON_PATH set "PYTHON_PATH=%%p"
for /f "tokens=*" %%p in ('where python3 2^>nul') do if not defined PYTHON_PATH set "PYTHON_PATH=%%p"
for /f "tokens=*" %%p in ('where python 2^>nul') do if not defined PYTHON_PATH set "PYTHON_PATH=%%p"

if "%PYTHON_PATH%"=="" (
    echo   ⚠ 未找到 Python，跳过仪表盘
    echo   安装 Python 后重新运行可启用: https://python.org
) else (
    for /f "tokens=*" %%i in ('"%PYTHON_PATH%" --version 2^>^&1') do echo   ✓ %%i
)

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

(
    echo Set WshShell = CreateObject^("WScript.Shell"^)
    echo WshShell.Run """%BIN%\easytier-core.exe"" -c ""%ROOT%\config.toml""", 0, False
) > "%ROOT%\easytier-core.vbs"
echo   ✓ Core (静默)

if not "%PYTHON_PATH%"=="" (
    (
        echo Set WshShell = CreateObject^("WScript.Shell"^)
        echo WshShell.Run """%PYTHON_PATH%"" ""%ROOT%\dashboard.py""", 0, False
    ) > "%ROOT%\dashboard.vbs"
    echo   ✓ Dashboard (静默)
)

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

if not "%PYTHON_PATH%"=="" (
    schtasks /Create /TN "EasyTeam-Dashboard" /TR "wscript.exe \"%ROOT%\dashboard.vbs\"" /SC ONLOGON /RL HIGHEST /F >nul 2>&1
    echo   ✓ Dashboard 开机自启
)

:start_now

:: 启动服务
echo.
echo   启动中...
wscript.exe "%ROOT%\easytier-core.vbs"
timeout /t 2 /nobreak >nul

tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier" >nul
if %errorlevel%==0 ( echo   ✓ Core 运行中 ) else ( echo   ✗ Core 启动失败 )

if not "%PYTHON_PATH%"=="" (
    wscript.exe "%ROOT%\dashboard.vbs"
    timeout /t 2 /nobreak >nul
    echo   ✓ Dashboard 运行中
)

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
echo  ║  仪表盘: http://127.0.0.1:15889
echo  ╠══════════════════════════════════════════════╣
echo  ║  · 已静默运行（无弹窗）
echo  ║  · 已注册开机自启
echo  ║  · 管理: start/stop/restart/status.bat
echo  ╚══════════════════════════════════════════════╝
echo.
pause
