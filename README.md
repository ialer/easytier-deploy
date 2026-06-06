# EasyTier 跨平台部署工具

一键部署 + 后台运行 + 开机自启 + 实时监控，支持 Windows / Linux / macOS。

## 特性

- 🖥️ **跨平台** — Windows、Linux、macOS 全支持
- ⬇️ **自动下载** — 首次运行自动下载对应平台的 EasyTier 核心
- 🔄 **版本检测** — 一键检查并更新到最新版本
- 🔧 **免 root** — Linux/macOS 使用用户级服务，无需提权
- 📊 **Web 仪表盘** — 实时监控网络状态
- 🌐 **Web 安装向导** — 可视化配置，适合不熟悉命令行的用户
- 🤫 **静默运行** — 后台服务，开机自启，无弹窗

## 快速开始

### 1. 安装 Python 3.8+

```bash
# Windows: 从 python.org 下载
# macOS:
brew install python3
# Linux:
sudo apt install python3   # Debian/Ubuntu
sudo dnf install python3   # Fedora
```

### 2. 获取工具

```bash
git clone https://github.com/ialer/easytier-deploy.git
cd easytier-deploy
chmod +x et-deploy  # Linux/macOS
```

### 3. 交互式安装

```bash
python3 et-deploy install
```

按提示输入网络名称、密钥、引导节点等信息，工具会自动：
- ✅ 下载 EasyTier 核心文件
- ✅ 生成配置文件
- ✅ 注册后台服务（开机自启）
- ✅ 启动服务

### 4. Web 安装向导（可选）

```bash
python3 et-deploy web-install
# 浏览器打开 http://127.0.0.1:15888
```

提供图形化配置界面，适合团队成员使用。

## 管理命令

| 命令 | 说明 |
|------|------|
| `et-deploy install` | 首次安装 |
| `et-deploy start` | 启动服务 |
| `et-deploy stop` | 停止服务 |
| `et-deploy restart` | 重启服务 |
| `et-deploy status` | 查看状态 |
| `et-deploy update` | 更新 EasyTier 核心 |
| `et-deploy dashboard` | 启动监控仪表盘 |
| `et-deploy web-install` | 启动 Web 安装向导 |
| `et-deploy uninstall` | 卸载服务 |

## 后台服务

| 平台 | 机制 | 特点 |
|------|------|------|
| Linux | systemd --user | 免 root，用户级服务 |
| macOS | launchd agent | 免 root，用户级 |
| Windows | Task Scheduler | 免 UAC，当前用户 |

服务注册后自动开机自启，崩溃自动重启。

## 监控仪表盘

```bash
et-deploy dashboard
# 浏览器打开 http://127.0.0.1:15889
```

功能：
- 📊 在线节点数、延迟、丢包率
- 🌐 本机信息（虚拟 IP、公网 IP、NAT 类型）
- 📋 对等节点列表
- 🗺️ 路由表
- ⚙️ 在线编辑配置

## 目录结构

```
easytier-deploy/
├── et-deploy              # 主入口脚本
├── core/                  # 核心模块
│   ├── __init__.py
│   ├── downloader.py      # 二进制下载 + 版本检测
│   ├── installer.py       # 交互式安装
│   ├── service.py         # 跨平台服务管理
│   ├── dashboard.py       # 监控仪表盘后端
│   └── web_installer.py   # Web 安装向导后端
├── web/                   # Web 前端
│   ├── installer.html     # 安装向导页面
│   └── dashboard.html     # 监控仪表盘页面
├── bin/                   # EasyTier 核心文件（自动下载）
├── config.toml            # 节点配置（自动生成）
├── config.toml.example    # 配置模板
├── logs/                  # 运行日志
├── README.md
└── .gitignore
```

## 虚拟 IP 分配

- `.1` 通常保留给引导服务器
- `.2 ~ .254` 分配给团队设备
- 建议按设备编号分配，避免冲突

## 常见问题

**Q: 如何查看连接状态？**
运行 `et-deploy status` 或访问仪表盘。

**Q: 如何修改配置？**
编辑 `config.toml` 后运行 `et-deploy restart`，或通过仪表盘在线编辑。

**Q: 如何更新 EasyTier？**
运行 `et-deploy update`，自动下载最新版本。

**Q: 如何卸载？**
运行 `et-deploy uninstall`。

## 网络架构

```
设备A  ──┐
设备B  ──┼── 引导服务器(VPS) ── P2P直连/中继
设备C  ──┘
```

所有设备连接到引导节点，建立 P2P 直连或通过引导服务器中继通信。
