@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║         EasyTier 节点状态                 ║
echo  ╚══════════════════════════════════════════╝
echo.

:: 进程状态
echo  ── 进程 ──
tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier"
if %errorlevel% neq 0 echo   ✗ EasyTier-Core 未运行
echo.

:: 计划任务状态
echo  ── 计划任务 ──
schtasks /Query /TN "EasyTeam-Core" /FO LIST 2>nul | findstr /I "Status"
if %errorlevel% neq 0 echo   ⚠ EasyTeam-Core 任务未注册（运行 setup.bat 注册）
schtasks /Query /TN "EasyTeam-Dashboard" /FO LIST 2>nul | findstr /I "Status"
if %errorlevel% neq 0 echo   ⚠ EasyTeam-Dashboard 任务未注册
echo.

:: 网络信息
echo  ── 网络 ──
if exist "%ROOT%\bin\easytier-cli.exe" (
    "%ROOT%\bin\easytier-cli.exe" peer 2>nul
) else (
    echo   ⚠ 未找到 easytier-cli.exe
)
echo.

:: 仪表盘
echo  ── 仪表盘 ──
echo   http://127.0.0.1:15889
echo.

pause
