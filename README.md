# EasyTier 跨平台部署工具

一键部署 + 后台运行 + 开机自启 + 实时监控，支持 Windows / Linux / macOS。

**零依赖** — 下载即可用，无需安装 Python 或其他环境。

## 下载

从 [GitHub Releases](../../releases) 下载对应平台的可执行文件：

| 平台 | 文件 |
|------|------|
| Linux x64 | `et-deploy-linux-x64` |
| Linux ARM64 | `et-deploy-linux-arm64` |
| macOS x64 | `et-deploy-macos-x64` |
| macOS ARM64 | `et-deploy-macos-arm64` |
| Windows x64 | `et-deploy-windows-x64.exe` |

## 快速开始

### Linux / macOS

```bash
chmod +x et-deploy-linux-*
./et-deploy-linux-x64 install
```

### Windows

```cmd
et-deploy-windows-x64.exe install
```

### Web 安装向导（可选）

```bash
./et-deploy web-install
# 浏览器打开 http://127.0.0.1:15888
```

## 特性

- 🖥️ **跨平台** — Windows、Linux、macOS 全支持
- ⬇️ **自动下载** — 首次运行自动下载对应平台的 EasyTier 核心
- 🔄 **版本检测** — 一键检查并更新到最新版本
- 🔧 **免 root** — Linux/macOS 使用用户级服务，无需提权
- 📊 **Web 仪表盘** — 实时监控网络状态
- 🤫 **静默运行** — 后台服务，开机自启，无弹窗
- 📦 **零依赖** — 打包为单个可执行文件，无需 Python

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

## 从源码构建

如果需要自行构建：

```bash
# 安装 Python 3.8+ 和 PyInstaller
pip install pyinstaller

# 构建
python3 build.py

# 输出在 dist/ 目录
```

发布时推送到 GitHub tag 会自动构建多平台版本：
```bash
git tag v2.0.0
git push --tags
```

## 目录结构

```
easytier-deploy/
├── et-deploy              # 入口脚本
├── build.py               # PyInstaller 构建脚本
├── core/                  # 核心模块
│   ├── downloader.py      # 二进制下载 + 版本检测
│   ├── installer.py       # 交互式安装
│   ├── service.py         # 跨平台服务管理
│   ├── dashboard.py       # 监控仪表盘后端
│   └── web_installer.py   # Web 安装向导后端
├── web/                   # Web 前端
│   ├── installer.html     # 安装向导页面
│   └── dashboard.html     # 监控仪表盘页面
├── .github/workflows/     # CI/CD 自动构建
│   └── release.yml
├── config.toml.example    # 配置模板
└── README.md
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
