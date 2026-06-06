#!/usr/bin/env python3
"""
PyInstaller 构建脚本
用法:
  python3 build.py              # 构建当前平台
  python3 build.py --clean      # 清理后构建
"""
import os, sys, subprocess, shutil, platform
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST_DIR = HERE / "dist"
BUILD_DIR = HERE / "build"
APP_NAME = "et-deploy"

def clean():
    """清理构建目录"""
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
    print("  🧹 已清理构建目录")

def build():
    """使用 PyInstaller 构建"""
    system = platform.system()
    is_win = system == "Windows"
    suffix = ".exe" if is_win else ""

    print(f"\n🔨 构建 {APP_NAME} ({system} {platform.machine()})...")

    # PyInstaller 参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                          # 单文件
        "--console",                          # 保留控制台
        "--name", APP_NAME,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--noconfirm",                        # 覆盖不询问
        "--clean",                            # 清理缓存
        # 隐藏导入
        "--hidden-import", "http.server",
        "--hidden-import", "json",
        "--hidden-import", "subprocess",
        # 排除不需要的模块（减小体积）
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "PIL",
        str(HERE / "et-deploy"),
    ]

    # 添加 icon（如果存在）
    icon = HERE / "assets" / "icon.ico"
    if icon.exists() and is_win:
        cmd.extend(["--icon", str(icon)])

    print(f"  📦 开始打包...")
    r = subprocess.run(cmd, cwd=str(HERE))
    if r.returncode != 0:
        print(f"  ✗ 构建失败")
        sys.exit(1)

    output = DIST_DIR / f"{APP_NAME}{suffix}"
    if output.exists():
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"  ✓ 构建完成: {output}")
        print(f"  📏 文件大小: {size_mb:.1f} MB")
    else:
        print(f"  ✗ 输出文件不存在: {output}")
        sys.exit(1)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="清理后构建")
    args = parser.parse_args()

    if args.clean:
        clean()
    build()

if __name__ == "__main__":
    main()
