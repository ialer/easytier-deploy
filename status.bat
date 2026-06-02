@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║         EasyTier 节点状态                 ║
echo  ╚══════════════════════════════════════════╝
echo.

echo  ── 进程 ──
tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier"
if %errorlevel% neq 0 echo   ✗ Core 未运行
echo.

echo  ── 计划任务 ──
schtasks /Query /TN "EasyTeam-Core" /FO LIST 2>nul | findstr /I "Status"
schtasks /Query /TN "EasyTeam-Dashboard" /FO LIST 2>nul | findstr /I "Status"
echo.

echo  ── 网络 ──
if exist "%ROOT%\bin\easytier-cli.exe" (
    "%ROOT%\bin\easytier-cli.exe" peer 2>nul
) else ( echo   ⚠ easytier-cli 未找到 )
echo.

echo  ── 仪表盘 ──
echo   http://127.0.0.1:15889
echo.

pause
