# EasyTier 团队部署包 v1.1.0

虚拟网络一键部署工具，适用于 Windows 设备。

## 版本历史

### v1.1.0 (2026-06-03) - 安全加固版

**安全修复 (18个):**

P0 - 功能正确性 (3个):
- bare except → except Exception
- 日志输出到stderr（不完全禁用）
- stop.bat精准终止本目录进程

P1 - 安全漏洞 (10个):
- dashboard绑定127.0.0.1（禁止0.0.0.0）
- API添加token认证（每次启动生成随机token）
- POST大小限制100KB + 格式验证
- HTML转义所有动态内容（防XSS）
- 错误信息不泄露内部细节
- 移除installer硬编码真实IP和密钥
- setup.bat输入验证特殊字符

P2 - 健壮性 (5个):
- 超时处理更完整
- 文件编码错误处理
- POST数据格式验证
- 配置校验更严格（长度、占位符检测）
- 路径处理更安全

**新增安全特性:**
- 每次启动生成随机API token
- 所有用户输入HTML转义
- 占位符替代真实IP/密钥
- 详细的安全检查清单

### v1.0.0 (2026-06-02)
- 初始版本
- EasyTier一键部署
- 可视化安装器
- Web仪表盘

## 快速开始

1. 下载 `easytier-deploy-v1.1.0.zip`
2. 解压到任意目录
3. 右键 `setup.bat` → 以管理员身份运行
4. 按提示输入配置信息

## 文件说明

| 文件 | 说明 |
|------|------|
| setup.bat | 一键部署脚本 |
| start.bat | 启动服务 |
| stop.bat | 停止服务 |
| restart.bat | 重启服务 |
| status.bat | 查看状态 |
| dashboard.py | Web仪表盘 |
| installer.html | 可视化安装器 |
| config.toml | 配置文件 |

## 安全说明

v1.1.0 修复了多个安全问题：
- API认证：仪表盘API需要token访问
- 绑定地址：仅监听127.0.0.1
- 输入验证：所有用户输入经过验证和转义
- 进程管理：精准控制本目录进程

## 仪表盘访问

启动后访问: http://127.0.0.1:15889

API Token 在 dashboard.py 启动时显示在控制台。

## 许可证

MIT License
