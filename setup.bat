@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   EasyTier 团队部署工具 v1.0             ║
echo  ╚══════════════════════════════════════════╝
echo.

:: 获取脚本所在目录（项目根目录）
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

:: ============================================
:: 1. 检查必要文件
:: ============================================
echo [1/7] 检查文件...
if not exist "%ROOT%\bin\easytier-core.exe" (
    echo   ✗ 未找到 bin\easytier-core.exe
    echo   请将 EasyTier 程序文件放入 bin\ 目录
    echo   下载: https://github.com/EasyTier/EasyTier/releases
    pause
    exit /b 1
)
if not exist "%ROOT%\config.toml.example" (
    echo   ✗ 未找到 config.toml.example
    pause
    exit /b 1
)
echo   ✓ 文件检查通过

:: ============================================
:: 2. 收集网络配置（机密信息）
:: ============================================
echo.
echo [2/7] 配置网络信息（所有节点必须一致）
echo   ───────────────────────────────────

:: 网络名称
set /p "NET_NAME=  网络名称: "
if "%NET_NAME%"=="" (
    echo   ✗ 网络名称不能为空
    pause
    exit /b 1
)

:: 网络密钥
set /p "NET_SECRET=  网络密钥: "
if "%NET_SECRET%"=="" (
    echo   ✗ 网络密钥不能为空
    pause
    exit /b 1
)

:: 引导节点
set /p "SERVER_URI=  引导节点URI [如 tcp://1.2.3.4:11010]: "
if "%SERVER_URI%"=="" (
    echo   ✗ 引导节点不能为空
    pause
    exit /b 1
)

:: 网络CIDR前缀
set /p "CIDR_PREFIX=  网段前缀 [如 192.168.1，默认 10.0.0]: "
if "%CIDR_PREFIX%"=="" set "CIDR_PREFIX=10.0.0"

:: ============================================
:: 3. 收集设备配置
:: ============================================
echo.
echo [3/7] 配置设备信息
echo   ───────────────────────────────────

:: 主机名
set "DEFAULT_HOST=%COMPUTERNAME%"
set /p "HOSTNAME=  设备名称 [%DEFAULT_HOST%]: "
if "%HOSTNAME%"=="" set "HOSTNAME=%DEFAULT_HOST%"

:: 虚拟IP
echo.
echo   可用IP范围: %CIDR_PREFIX%.2 ~ %CIDR_PREFIX%.254
echo   (%CIDR_PREFIX%.1 通常保留给引导服务器)
set /p "VIP=  虚拟IP末位 [如输入 5 则为 %CIDR_PREFIX%.5]: "
if "%VIP%"=="" set "VIP=1"

:: ============================================
:: 4. 检测 Python
:: ============================================
echo.
echo [4/7] 检测 Python 环境...

set "PYTHON_CMD="

:: 优先检查 python3.11
where python3.11 >nul 2>&1 && set "PYTHON_CMD=python3.11" && goto :python_found
:: 检查 python3
where python3 >nul 2>&1 && set "PYTHON_CMD=python3" && goto :python_found
:: 检查 python
where python >nul 2>&1 && set "PYTHON_CMD=python" && goto :python_found
:: 检查 py launcher
where py >nul 2>&1 && set "PYTHON_CMD=py -3" && goto :python_found

echo   ⚠ 未检测到 Python，仪表盘功能将不可用
echo   可稍后手动安装 Python 3.11+ 后重新运行
set "PYTHON_CMD=python"
goto :python_done

:python_found
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version 2^>^&1') do echo   ✓ 检测到 %%i

:python_done

:: 获取 python 完整路径（VBS需要）
for /f "tokens=*" %%p in ('where %PYTHON_CMD: =.% 2^>nul') do set "PYTHON_PATH=%%p"
if "%PYTHON_PATH%"=="" (
    for /f "tokens=*" %%p in ('where python 2^>nul') do set "PYTHON_PATH=%%p"
)

:: ============================================
:: 5. 生成配置文件
:: ============================================
echo.
echo [5/7] 生成配置文件...

:: 从模板生成 config.toml
(
    echo # EasyTier 节点配置 - 自动生成
    echo # 生成时间: %date% %time%
    echo # 设备: %HOSTNAME%
    echo.
    echo [network_identity]
    echo network_name = "%NET_NAME%"
    echo network_secret = "%NET_SECRET%"
    echo.
    echo # 引导节点
    echo [[peer]]
    echo uri = "%SERVER_URI%"
    echo.
    echo [flags]
    echo ipv4 = "%CIDR_PREFIX%.%VIP%/24"
    echo hostname = "%HOSTNAME%"
    echo listeners = []
    echo # encryption-algorithm = "aes-gcm"
) > "%ROOT%\config.toml"

echo   ✓ config.toml 已生成
echo     设备名: %HOSTNAME%
echo     虚拟IP: %CIDR_PREFIX%.%VIP%/24

:: ============================================
:: 6. 生成启动器
:: ============================================
echo.
echo [6/7] 生成启动器...

:: EasyTier Core VBS 启动器（隐藏窗口）
(
    echo Set WshShell = CreateObject^("WScript.Shell"^)
    echo WshShell.Run "%ROOT%\bin\easytier-core.exe -c %ROOT%\config.toml", 0, False
) > "%ROOT%\easytier-core.vbs"
echo   ✓ easytier-core.vbs

:: Dashboard VBS 启动器（隐藏窗口）
if not "%PYTHON_PATH%"=="" (
    (
        echo Set WshShell = CreateObject^("WScript.Shell"^)
        echo WshShell.Run "%PYTHON_PATH% %ROOT%\dashboard.py", 0, False
    ) > "%ROOT%\dashboard.vbs"
    echo   ✓ dashboard.vbs
) else (
    echo   ⏭ 跳过 dashboard.vbs（未检测到Python）
)

:: ============================================
:: 7. 注册计划任务（开机自启）
:: ============================================
echo.
echo [7/7] 注册计划任务...

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo   ⚠ 需要管理员权限注册计划任务
    echo   请右键「以管理员身份运行」此脚本
    echo   或手动注册: 以管理员运行 install.bat
    goto :skip_tasks
)

:: EasyTier Core
schtasks /Delete /TN "EasyTeam-Core" /F >nul 2>&1
schtasks /Create /TN "EasyTeam-Core" /TR "wscript.exe \"%ROOT%\easytier-core.vbs\"" /SC ONLOGON /RL HIGHEST /F >nul 2>&1
if %errorlevel%==0 (
    echo   ✓ EasyTeam-Core 计划任务已注册
) else (
    echo   ✗ EasyTeam-Core 注册失败
)

:: Dashboard
if not "%PYTHON_PATH%"=="" (
    schtasks /Delete /TN "EasyTeam-Dashboard" /F >nul 2>&1
    schtasks /Create /TN "EasyTeam-Dashboard" /TR "wscript.exe \"%ROOT%\dashboard.vbs\"" /SC ONLOGON /RL HIGHEST /F >nul 2>&1
    if %errorlevel%==0 (
        echo   ✓ EasyTeam-Dashboard 计划任务已注册
    ) else (
        echo   ✗ EasyTeam-Dashboard 注册失败
    )
)

:skip_tasks

:: ============================================
:: 完成
:: ============================================
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   ✓ 部署完成！                            ║
echo  ╠══════════════════════════════════════════╣
echo  ║   网络: %NET_NAME%
echo  ║   设备: %HOSTNAME%
echo  ║   虚拟IP: %CIDR_PREFIX%.%VIP%
echo  ║   仪表盘: http://127.0.0.1:15889
echo  ║   配置文件: %ROOT%\config.toml
echo  ╠══════════════════════════════════════════╣
echo  ║   启动: 运行 start.bat
echo  ║   停止: 运行 stop.bat
echo  ║   状态: 运行 status.bat
echo  ╚══════════════════════════════════════════╝
echo.

:: 询问是否立即启动
set /p "START=是否立即启动 EasyTier? (Y/n): "
if /i "%START%"=="n" goto :end

echo.
echo 启动中...
wscript.exe "%ROOT%\easytier-core.vbs"
timeout /t 2 /nobreak >nul

:: 验证
tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier" >nul
if %errorlevel%==0 (
    echo ✓ EasyTier-Core 已启动
) else (
    echo ✗ EasyTier-Core 启动失败，请检查日志
)

if not "%PYTHON_PATH%"=="" (
    wscript.exe "%ROOT%\dashboard.vbs"
    timeout /t 2 /nobreak >nul
    echo ✓ 仪表盘已启动: http://127.0.0.1:15889
)

:end
echo.
pause
