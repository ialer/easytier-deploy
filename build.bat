@echo off
chcp 65001 >nul
setlocal

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   EasyTier 打包工具                       ║
echo  ╚══════════════════════════════════════════╝
echo.

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "OUTPUT=%ROOT%\release"
set "PKG=%OUTPUT%\easytier-deploy"

:: 清理旧包
if exist "%OUTPUT%" rd /s /q "%OUTPUT%"
mkdir "%PKG%" 2>nul

echo [1/3] 复制文件...

:: 核心文件
copy /y "%ROOT%\setup.bat" "%PKG%\" >nul && echo   ✓ setup.bat
copy /y "%ROOT%\dashboard.py" "%PKG%\" >nul && echo   ✓ dashboard.py
copy /y "%ROOT%\config.toml.example" "%PKG%\" >nul && echo   ✓ config.toml.example

:: 管理脚本
copy /y "%ROOT%\start.bat" "%PKG%\" >nul && echo   ✓ start.bat
copy /y "%ROOT%\stop.bat" "%PKG%\" >nul && echo   ✓ stop.bat
copy /y "%ROOT%\restart.bat" "%PKG%\" >nul && echo   ✓ restart.bat
copy /y "%ROOT%\status.bat" "%PKG%\" >nul && echo   ✓ status.bat

:: 说明文档
copy /y "%ROOT%\README.md" "%PKG%\" >nul && echo   ✓ README.md

:: 创建空的 bin 目录（用户通过 setup.bat 自动下载）
mkdir "%PKG%\bin" 2>nul
echo 此目录由 setup.bat 自动下载 EasyTier 程序 > "%PKG%\bin\README.txt"
echo 无需手动操作                                    >> "%PKG%\bin\README.txt"
echo   ✓ bin\ (空目录，运行时自动下载)

echo.
echo [2/3] 打包...

:: 创建zip
powershell -NoProfile -Command ^
    "Compress-Archive -Path '%PKG%\*' -DestinationPath '%OUTPUT%\easytier-deploy.zip' -Force; " ^
    "Write-Host '  ✓ easytier-deploy.zip'"

:: 获取大小
for %%f in ("%OUTPUT%\easytier-deploy.zip") do set "SIZE=%%~zf"
set /a SIZE_KB=%SIZE%/1024

echo.
echo [3/3] 完成！
echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   输出: release\easytier-deploy.zip           ║
echo  ║   大小: %SIZE_KB% KB (不含EasyTier程序)        ║
echo  ╠══════════════════════════════════════════════╣
echo  ║   分发方式:                                   ║
echo  ║   1. 发送 zip 给团队成员                      ║
echo  ║   2. 解压后右键 setup.bat 以管理员运行        ║
echo  ║   3. 按提示输入网络信息即可完成部署           ║
echo  ║                                              ║
echo  ║   程序会自动从 GitHub 下载 EasyTier           ║
echo  ║   无需手动安装任何依赖                        ║
echo  ╚══════════════════════════════════════════════╝
echo.
pause
