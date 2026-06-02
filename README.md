# EasyTier 团队部署包

虚拟网络一键部署工具，适用于 Windows 设备。

## 快速开始

### 1. 下载发行包
从 [GitHub Releases](../../releases) 下载最新版本，或 clone 本仓库。

### 2. 放入 EasyTier 程序
从 [EasyTier Releases](https://github.com/EasyTier/EasyTier/releases) 下载 Windows 版本，将以下文件放入 `bin/` 目录：
- `easytier-core.exe`
- `easytier-cli.exe`
- `Packet.dll`
- `WinDivert64.sys`
- `wintun.dll`

### 3. 运行安装
```
右键 setup.bat → 以管理员身份运行
```

按提示输入：
- **网络名称** — 团队统一的网络名（所有节点必须一致）
- **网络密钥** — 团队统一的密钥（所有节点必须一致）
- **引导节点URI** — 如 `tcp://1.2.3.4:11010`
- **网段前缀** — 如 `192.168.1`（默认 `10.0.0`）
- **设备名称** — 你的设备标识（默认使用计算机名）
- **虚拟IP末位** — 网段内唯一的末位数字

安装脚本会自动：
- ✅ 生成 `config.toml` 配置文件
- ✅ 生成 VBS 隐藏启动器
- ✅ 注册开机自启计划任务
- ✅ 启动 EasyTier-Core 和仪表盘

### 4. 验证
- 仪表盘：http://127.0.0.1:15889
- 运行 `status.bat` 查看节点状态

## 目录结构

```
EasyTier/
├── bin/                    # EasyTier 程序文件（用户放入）
│   ├── easytier-core.exe
│   ├── easytier-cli.exe
│   └── ...
├── config.toml.example    # 配置模板
├── config.toml            # 实际配置（setup.bat 生成，已 gitignore）
├── dashboard.py           # 监控仪表盘
├── setup.bat              # 一键安装（需管理员）
├── start.bat              # 启动
├── stop.bat               # 停止
├── restart.bat            # 重启
├── status.bat             # 查看状态
└── README.md
```

## 管理命令

| 命令 | 说明 |
|------|------|
| `setup.bat` | 首次安装（需管理员） |
| `start.bat` | 启动 EasyTier + 仪表盘 |
| `stop.bat` | 停止所有服务 |
| `restart.bat` | 重启所有服务 |
| `status.bat` | 查看节点状态 |

## 仪表盘功能

访问 http://127.0.0.1:15889

- 📊 设备统计（总数、P2P直连、中继转发）
- 💻 本机节点信息（虚拟IP、公网IP、NAT类型）
- 🔥 STUN 诊断
- 📈 流量统计（收发量、压缩比、转发量）
- 📋 在线设备表格（延迟、丢包、隧道类型）
- 🌐 网络拓扑图（Canvas 绘制）
- 📉 延迟趋势图
- 🗺️ 路由表
- ✏️ 在线编辑配置文件

## 配置说明

编辑 `config.toml`（或通过仪表盘在线编辑）：

```toml
[network_identity]
network_name = "YOUR_NETWORK"    # 网络名，所有节点相同
network_secret = "YOUR_SECRET"   # 密钥，所有节点相同

[[peer]]
uri = "tcp://YOUR_SERVER:11010"  # 引导节点

[flags]
ipv4 = "10.0.0.5/24"            # 虚拟IP，每台设备不同
hostname = "my-device"           # 设备名
listeners = []                   # 监听端口
```

### 虚拟IP分配建议

- `.1` 通常保留给引导服务器
- `.2 ~ .254` 分配给团队设备
- 建议按设备编号分配，避免冲突

## 加密配置

如需启用端到端加密，取消 `config.toml` 中的注释：

```toml
encryption-algorithm = "aes-gcm"
```

⚠️ **注意**：加密必须全网统一开启，否则设备间无法通信。

## 常见问题

**Q: 如何查看连接状态？**
运行 `status.bat` 或访问仪表盘。

**Q: 如何修改配置？**
编辑 `config.toml` 后运行 `restart.bat`，或通过仪表盘在线编辑。

**Q: 如何卸载？**
运行 PowerShell（管理员）：
```powershell
Unregister-ScheduledTask -TaskName "EasyTeam-Core" -Confirm:$false
Unregister-ScheduledTask -TaskName "EasyTeam-Dashboard" -Confirm:$false
```

## 网络架构

```
设备A  ──┐
设备B  ──┼── 引导服务器(VPS) ── P2P直连/中继
设备C  ──┘
```

所有设备连接到引导节点，建立 P2P 直连或通过引导服务器中继通信。
