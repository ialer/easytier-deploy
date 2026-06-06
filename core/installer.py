"""
交互式安装向导
"""
import os, sys, platform, re, secrets, string
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CONFIG_FILE = HERE / "config.toml"
CONFIG_EXAMPLE = HERE / "config.toml.example"


def _generate_secret(length=24):
    """生成随机密钥"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _input_with_default(prompt, default):
    """带默认值的输入"""
    val = input(f"  {prompt} [{default}]: ").strip()
    return val if val else default


def _validate_ipv4(s):
    """验证 IPv4 格式"""
    parts = s.split("/")
    if len(parts) != 2:
        return False
    ip_parts = parts[0].split(".")
    if len(ip_parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in ip_parts) and parts[1].isdigit()
    except ValueError:
        return False


def _validate_uri(s):
    """验证 URI 格式"""
    return bool(re.match(r'^(tcp|udp|wss?)://.+:\d+$', s))


def run_install():
    """交互式安装"""
    print("""
╔══════════════════════════════════════════════╗
║     EasyTier 团队网络 — 安装向导             ║
╚══════════════════════════════════════════════╝
""")

    # 检测平台
    system = platform.system()
    print(f"  💻 操作系统: {system} ({platform.machine()})")
    print(f"  📂 安装目录: {HERE}")
    print()

    # 检查核心文件
    from .downloader import ensure_core, get_local_version, get_remote_version
    if not ensure_core():
        print("  ✗ 核心文件下载失败，请检查网络")
        sys.exit(1)

    local_ver = get_local_version()
    remote_ver = get_remote_version()
    if remote_ver and local_ver != remote_ver:
        print(f"  📦 发现新版本 v{remote_ver}，当前 v{local_ver}")
        update = input("  是否更新？[Y/n]: ").strip().lower()
        if update != "n":
            from .downloader import download_core
            download_core(remote_ver, force=True)

    print("\n── 网络配置 ──\n")

    # 网络名称
    network_name = _input_with_default("网络名称 (所有节点必须一致)", "sn-team")

    # 网络密钥
    default_secret = _generate_secret()
    network_secret = _input_with_default("网络密钥 (所有节点必须一致)", default_secret)

    # 引导节点
    print("\n  引导节点 URI 格式: tcp://IP:端口")
    peer_uri = _input_with_default("引导节点 URI", "tcp://96.44.141.123:11010")
    while not _validate_uri(peer_uri):
        print("  ✗ 格式错误，示例: tcp://1.2.3.4:11010")
        peer_uri = _input_with_default("引导节点 URI", "tcp://96.44.141.123:11010")

    # 网段
    print("\n  虚拟 IP 格式: X.X.X.X/24")
    print("  建议: 引导服务器用 .1，其他设备 .2~.254")
    ipv4 = _input_with_default("虚拟 IP (含子网)", "10.0.0.1/24")
    while not _validate_ipv4(ipv4):
        print("  ✗ 格式错误，示例: 10.0.0.5/24")
        ipv4 = _input_with_default("虚拟 IP (含子网)", "10.0.0.1/24")

    # 主机名
    default_hostname = platform.node() or "device"
    hostname = _input_with_default("设备名称", default_hostname)

    # 加密
    print("\n  加密选项:")
    print("    1. 不加密 (默认)")
    print("    2. AES-GCM (全网必须统一)")
    enc_choice = _input_with_default("选择", "1")
    encryption = "aes-gcm" if enc_choice == "2" else ""

    # 生成配置
    print("\n⚙️  生成配置文件...")
    config = f"""# EasyTier 节点配置
# 由 et-deploy 自动生成

[network_identity]
network_name = "{network_name}"
network_secret = "{network_secret}"

[[peer]]
uri = "{peer_uri}"

[flags]
ipv4 = "{ipv4}"
hostname = "{hostname}"
"""
    if encryption:
        config += f'encryption-algorithm = "{encryption}"\n'

    CONFIG_FILE.write_text(config)
    print(f"  ✓ 配置已写入: {CONFIG_FILE}")

    # 注册服务
    from .service import service_install
    service_install()

    # 启动
    start = input("\n  是否立即启动？[Y/n]: ").strip().lower()
    if start != "n":
        from .service import service_start
        service_start()

    print(f"""
╔══════════════════════════════════════════════╗
║  ✅ 安装完成！                               ║
║                                              ║
║  管理命令:                                    ║
║    et-deploy start     启动                  ║
║    et-deploy stop      停止                  ║
║    et-deploy status    状态                  ║
║    et-deploy update    更新核心              ║
║    et-deploy restart   重启                  ║
║                                              ║
║  仪表盘: http://127.0.0.1:15889             ║
╚══════════════════════════════════════════════╝
""")
