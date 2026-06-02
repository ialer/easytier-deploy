@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ================================
echo   EasyTier 停止
echo ================================
echo.

:: 安全：只杀本目录下的easytier进程，不杀其他目录的
echo   [1/2] 停止 EasyTier-Core...

:: 先检查进程是否存在
tasklist /FI "IMAGENAME eq easytier-core.exe" 2>nul | findstr /I "easytier" >nul
if %errorlevel% neq 0 (
    echo   ○ Core 未运行
) else (
    :: 通过wmic检查是否是本目录的进程
    set "FOUND=0"
    for /f "tokens=2" %%p in ('wmic process where "name='easytier-core.exe'" get ProcessId /value 2^>nul ^| findstr "ProcessId"') do (
        for /f "tokens=*" %%c in ('wmic process where "ProcessId=%%p" get CommandLine /value 2^>nul ^| findstr "CommandLine"') do (
            echo %%c | findstr /I "%ROOT%" >nul && (
                taskkill /F /PID %%p >nul 2>&1
                set "FOUND=1"
            )
        )
    )
    if "!FOUND!"=="1" (
        echo   ✓ Core 已停止
    ) else (
        echo   ○ 本目录无Core进程
    )
)

timeout /t 1 /nobreak >nul

echo   [2/2] 停止仪表盘...
:: 通过端口查找并杀掉Python进程
set "DASH_FOUND=0"
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":15889" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
    set "DASH_FOUND=1"
)
if "%DASH_FOUND%"=="1" (
    echo   ✓ 仪表盘已停止
) else (
    echo   ○ 仪表盘未运行
)

echo.
echo   ================================
echo   已停止
echo   ================================
timeout /t 2 /nobreak >nul
