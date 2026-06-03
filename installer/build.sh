#!/bin/bash
# 构建EXE安装包脚本

set -e

echo "=== EasyTier Installer 构建脚本 ==="

# 检查Rust
if ! command -v cargo &> /dev/null; then
    echo "错误: 未安装Rust"
    exit 1
fi

# 检查Tauri CLI
if ! command -v cargo-tauri &> /dev/null; then
    echo "安装Tauri CLI..."
    cargo install tauri-cli
fi

# 检查EasyTier资源
if [ ! -f "resources/easytier.zip" ]; then
    echo "下载EasyTier v2.6.4..."
    mkdir -p resources
    curl -L -o resources/easytier.zip https://github.com/EasyTier/EasyTier/releases/download/v2.6.4/easytier-windows-x86_64-v2.6.4.zip
fi

# 构建
echo "开始构建..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows环境
    cargo tauri build
else
    # Linux环境 - 交叉编译
    cargo xwin build --release --target x86_64-pc-windows-msvc
fi

echo "构建完成！"
