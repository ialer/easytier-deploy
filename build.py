#!/usr/bin/env python3
"""
PyInstaller build script
Usage:
  python3 build.py              # Build for current platform
  python3 build.py --clean      # Clean and build
"""
import os, sys, subprocess, shutil, platform
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST_DIR = HERE / "dist"
BUILD_DIR = HERE / "build"
APP_NAME = "et-deploy"

def clean():
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
    print("  Cleaned build directories")

def build():
    system = platform.system()
    is_win = system == "Windows"
    suffix = ".exe" if is_win else ""

    print(f"\nBuilding {APP_NAME} ({system} {platform.machine()})...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", APP_NAME,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--noconfirm",
        "--clean",
        "--hidden-import", "http.server",
        "--hidden-import", "json",
        "--hidden-import", "subprocess",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "PIL",
        str(HERE / "et-deploy"),
    ]

    icon = HERE / "assets" / "icon.ico"
    if icon.exists() and is_win:
        cmd.extend(["--icon", str(icon)])

    print("  Packaging...")
    r = subprocess.run(cmd, cwd=str(HERE))
    if r.returncode != 0:
        print("  Build FAILED")
        sys.exit(1)

    output = DIST_DIR / f"{APP_NAME}{suffix}"
    if output.exists():
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"  OK: {output}")
        print(f"  Size: {size_mb:.1f} MB")
    else:
        print(f"  Output not found: {output}")
        sys.exit(1)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    if args.clean:
        clean()
    build()

if __name__ == "__main__":
    main()
