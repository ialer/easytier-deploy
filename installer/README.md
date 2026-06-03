# EXE安装包构建说明

## 环境要求

- Rust 1.77+
- Node.js (可选)
- Windows SDK (交叉编译需要)

## 构建步骤

### 1. 安装依赖

```bash
# 安装Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 安装Tauri CLI
cargo install tauri-cli

# (可选) 安装交叉编译工具
cargo install cargo-xwin
rustup target add x86_64-pc-windows-msvc
```

### 2. 下载EasyTier

```bash
# 下载EasyTier v2.6.4
curl -L -o resources/easytier.zip https://github.com/EasyTier/EasyTier/releases/download/v2.6.4/easytier-windows-x86_64-v2.6.4.zip
```

### 3. 构建

```bash
# 本地构建 (需要Windows环境)
cargo tauri build

# 交叉编译 (Linux -> Windows)
cargo xwin build --release --target x86_64-pc-windows-msvc
```

### 4. 打包

构建完成后，将以下文件打包：

```
EasyTier-Installer-vX.X.X-full/
├── EasyTier-Installer.exe    # 主程序
├── resources/
│   └── easytier.zip          # EasyTier程序
├── 启动安装.bat              # 启动脚本
└── 说明.txt                  # 使用说明
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `src/lib.rs` | Rust后端逻辑 |
| `index.html` | 前端界面 |
| `Cargo.toml` | Rust依赖配置 |
| `tauri.conf.json` | Tauri配置 |
| `resources/` | 资源文件目录 |

## 功能特性

- 图形化安装界面（深色主题）
- 自动解压安装EasyTier
- 自动生成配置文件
- 自动注册开机自启
- 一键部署，无需手动操作
