# EasyTier 团队部署包 v1.2.0

虚拟网络一键部署工具，适用于 Windows 设备。

## 版本历史

### v1.2.0 (2026-06-03) - EXE安装包版

**新增功能：**
- 🎉 **EXE图形化安装包** — 基于Tauri框架，内置EasyTier v2.6.4
- 🎨 **深色主题界面** — 参考VS Code/Discord设计风格
- 📝 **5步安装流程** — 欢迎→环境检查→网络配置→部署→完成
- 🔧 **可视化配置编辑器** — 左右分栏，实时预览
- 📦 **一键安装** — 自动解压、配置、注册自启

**安全加固（v1.1.0）：**
- 修复18个安全问题（P0×3 + P1×10 + P2×5）
- API Token认证
- 绑定127.0.0.1
- HTML转义防XSS
- 输入验证

### v1.1.0 (2026-06-03) - 安全加固版
- 安全修复和加固

### v1.0.0 (2026-06-02)
- 初始版本

## 安装方式

### 方式1：EXE安装包（推荐）

1. 下载 `EasyTier-Installer-v1.2.0-full.tar.gz`
2. 解压
3. 双击 `启动安装.bat` 或 `EasyTier-Installer.exe`
4. 按界面提示操作

**特点：**
- 图形化界面，无需命令行
- 内置EasyTier，无需额外下载
- 自动注册开机自启

### 方式2：命令行安装

1. 下载仓库 zip 或 git clone
2. 运行 `setup.bat`（管理员权限）
3. 按提示输入配置信息

### 方式3：可视化安装（网页版）

1. 双击 `installer.html`（浏览器打开）
2. 按向导操作
3. 下载生成的配置文件

## 文件说明

| 文件 | 说明 |
|------|------|
| `EasyTier-Installer-v1.2.0-full.tar.gz` | EXE安装包（内置EasyTier） |
| `setup.bat` | 命令行安装脚本 |
| `installer.html` | 网页版可视化安装器 |
| `dashboard.py` | Web仪表盘 (v5.2) |
| `start.bat` | 启动服务 |
| `stop.bat` | 停止服务 |
| `restart.bat` | 重启服务 |
| `status.bat` | 查看状态 |
| `config.toml.example` | 配置模板 |

## 管理命令

| 命令 | 说明 |
|------|------|
| `setup.bat` | 首次安装（需管理员） |
| `start.bat` | 启动 EasyTier + 仪表盘 |
| `stop.bat` | 停止所有服务 |
| `restart.bat` | 重启所有服务 |
| `status.bat` | 查看节点状态 |

## 仪表盘

启动后访问: http://127.0.0.1:15889

## 安全特性

v1.2.0 包含以下安全加固：
- ✅ API Token认证（每次启动生成随机token）
- ✅ 绑定127.0.0.1（禁止外部访问）
- ✅ HTML转义防XSS
- ✅ 输入验证和大小限制
- ✅ 日志审计

## 技术栈

- **EXE安装包**: Rust + Tauri v2
- **仪表盘**: Python + http.server
- **安装器**: HTML/CSS/JavaScript
- **部署脚本**: Windows Batch

## 许可证

MIT License
