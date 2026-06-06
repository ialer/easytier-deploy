"""
跨平台后台服务管理
- Linux: systemd --user (免 root)
- macOS: launchd user agent (免 root)
- Windows: schtasks (当前用户，免 UAC)
"""
import os, sys, platform, subprocess, signal, time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BIN_DIR = HERE / "bin"
CONFIG_FILE = HERE / "config.toml"
PID_FILE = HERE / ".et-core.pid"
LOG_DIR = HERE / "logs"

SERVICE_NAME = "easytier-core"
SERVICE_NAME_MAC = "com.easytier.core"

# ─── 平台检测 ───
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"


def _core_cmd():
    """获取 core 可执行文件路径"""
    suffix = ".exe" if IS_WINDOWS else ""
    core = BIN_DIR / f"easytier-core{suffix}"
    if not core.exists():
        print(f"  核心文件不存在: {core}")
        print("  请运行: et-deploy update")
        sys.exit(1)
    return str(core)


def _cli_cmd():
    """获取 cli 可执行文件路径"""
    suffix = ".exe" if IS_WINDOWS else ""
    return str(BIN_DIR / f"easytier-cli{suffix}")


def _ensure_log_dir():
    LOG_DIR.mkdir(exist_ok=True)
    return LOG_DIR


# ─── Linux: systemd --user ───
def _linux_service_dir():
    d = Path.home() / ".config" / "systemd" / "user"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _linux_unit_content():
    core = _core_cmd()
    logs = _ensure_log_dir()
    return f"""[Unit]
Description=EasyTier Core
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={core} -c {CONFIG_FILE}
WorkingDirectory={HERE}
Restart=on-failure
RestartSec=5
StandardOutput=append:{logs}/core.log
StandardError=append:{logs}/core.log

[Install]
WantedBy=default.target
"""


def _linux_install():
    unit = _linux_service_dir() / f"{SERVICE_NAME}.service"
    unit.write_text(_linux_unit_content())
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", SERVICE_NAME], check=True)
    print(f"  systemd 用户服务已注册: {unit}")


def _linux_start():
    subprocess.run(["systemctl", "--user", "start", SERVICE_NAME], check=True)


def _linux_stop():
    subprocess.run(["systemctl", "--user", "stop", SERVICE_NAME], check=True)


def _linux_status():
    r = subprocess.run(["systemctl", "--user", "is-active", SERVICE_NAME],
                       capture_output=True, text=True)
    return r.stdout.strip() == "active"


def _linux_restart():
    subprocess.run(["systemctl", "--user", "restart", SERVICE_NAME], check=True)


def _linux_uninstall():
    subprocess.run(["systemctl", "--user", "stop", SERVICE_NAME], check=False)
    subprocess.run(["systemctl", "--user", "disable", SERVICE_NAME], check=False)
    unit = _linux_service_dir() / f"{SERVICE_NAME}.service"
    unit.unlink(missing_ok=True)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)


# ─── macOS: launchd ───
def _mac_plist_path():
    return Path.home() / "Library" / "LaunchAgents" / f"{SERVICE_NAME_MAC}.plist"


def _mac_plist_content():
    core = _core_cmd()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{SERVICE_NAME_MAC}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{core}</string>
        <string>-c</string>
        <string>{CONFIG_FILE}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{HERE}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{_ensure_log_dir()}/core.log</string>
    <key>StandardErrorPath</key>
    <string>{_ensure_log_dir()}/core.log</string>
</dict>
</plist>
"""


def _mac_install():
    plist = _mac_plist_path()
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_text(_mac_plist_content())
    print(f"  launchd agent 已注册: {plist}")


def _mac_start():
    plist = _mac_plist_path()
    subprocess.run(["launchctl", "unload", str(plist)], check=False)
    subprocess.run(["launchctl", "load", str(plist)], check=True)


def _mac_stop():
    plist = _mac_plist_path()
    subprocess.run(["launchctl", "unload", str(plist)], check=False)


def _mac_status():
    plist = _mac_plist_path()
    if not plist.exists():
        return False
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    return SERVICE_NAME_MAC in r.stdout


def _mac_restart():
    _mac_stop()
    time.sleep(1)
    _mac_start()


def _mac_uninstall():
    _mac_stop()
    plist = _mac_plist_path()
    plist.unlink(missing_ok=True)


# ─── Windows: schtasks (当前用户) ───
def _win_task_core():
    return f"schtasks /Create /TN \"{SERVICE_NAME}\" /TR \"\\\"{_core_cmd()}\\\" -c \\\"{CONFIG_FILE}\\\"\" /SC ONLOGON /RL HIGHEST /F"


def _win_task_dashboard():
    dashboard = HERE / "core" / "dashboard.py"
    python = sys.executable
    return f"schtasks /Create /TN \"{SERVICE_NAME}-dashboard\" /TR \"\\\"{python}\\\" \\\"{dashboard}\\\"\" /SC ONLOGON /RL HIGHEST /F"


def _win_install():
    # 注册核心服务
    r = subprocess.run(_win_task_core(), shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  注册核心服务: {r.stderr.strip()}")
    else:
        print(f"  核心服务已注册 (计划任务: {SERVICE_NAME})")

    # 注册仪表盘服务
    r = subprocess.run(_win_task_dashboard(), shell=True, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  仪表盘服务已注册 (计划任务: {SERVICE_NAME}-dashboard)")


def _win_start():
    subprocess.run(f"schtasks /Run /TN \"{SERVICE_NAME}\"", shell=True, check=True)


def _win_stop():
    subprocess.run(f"schtasks /End /TN \"{SERVICE_NAME}\"", shell=True, check=False)
    # 也尝试杀进程
    subprocess.run("taskkill /F /IM easytier-core.exe", shell=True, check=False)


def _win_status():
    r = subprocess.run(f"schtasks /Query /TN \"{SERVICE_NAME}\" /FO CSV",
                       shell=True, capture_output=True, text=True)
    return "Ready" in r.stdout or "Running" in r.stdout


def _win_restart():
    _win_stop()
    time.sleep(2)
    _win_start()


def _win_uninstall():
    subprocess.run(f"schtasks /Delete /TN \"{SERVICE_NAME}\" /F", shell=True, check=False)
    subprocess.run(f"schtasks /Delete /TN \"{SERVICE_NAME}-dashboard\" /F", shell=True, check=False)


# ─── 统一接口 ───
def _platform_fn(name):
    prefix = "linux" if IS_LINUX else ("mac" if IS_MACOS else "win")
    fn = globals().get(f"_{prefix}_{name}")
    if not fn:
        print(f"  不支持的平台: {platform.system()}")
        sys.exit(1)
    return fn


def service_install():
    """注册后台服务"""
    print("\n 注册后台服务...")
    _platform_fn("install")()
    print(f"  服务已注册，开机自启")


def service_start():
    """启动服务"""
    from .downloader import ensure_core
    ensure_core()
    if not CONFIG_FILE.exists():
        print("  配置文件不存在，请先运行: et-deploy install")
        sys.exit(1)
    print("\n启动 EasyTier...")
    try:
        _platform_fn("start")()
        time.sleep(2)
        if service_status():
            print("  服务已启动")
        else:
            print("  服务启动中，请稍后检查状态")
    except subprocess.CalledProcessError as e:
        print(f"  启动失败: {e}")


def service_stop():
    """停止服务"""
    print("\n停止 EasyTier...")
    try:
        _platform_fn("stop")()
        print("  服务已停止")
    except Exception as e:
        print(f"  停止时出错: {e}")


def service_restart():
    """重启服务"""
    print("\n重启 EasyTier...")
    try:
        _platform_fn("restart")()
        time.sleep(2)
        if service_status():
            print("  服务已重启")
        else:
            print("  重启中，请稍后检查状态")
    except Exception as e:
        print(f"  重启失败: {e}")


def service_status():
    """查询服务状态"""
    return _platform_fn("status")()


def service_uninstall():
    """卸载服务"""
    print("\n 卸载服务...")
    service_stop()
    _platform_fn("uninstall")()
    print("  服务已卸载")


def print_status():
    """打印详细状态"""
    from .downloader import get_local_version, get_remote_version

    print("\n╔══════════════════════════════════════════╗")
    print("║         EasyTier 节点状态                ║")
    print("╚══════════════════════════════════════════╝")

    # 版本
    local = get_local_version()
    remote = get_remote_version()
    print(f"\n  📦 版本: v{local}" if local else "\n  📦 版本: 未安装")
    if remote and local != remote:
        print(f"  📦 最新: v{remote} (运行 et-deploy update 更新)")

    # 服务状态
    running = service_status()
    print(f"\n  服务: {'🟢 运行中' if running else '🔴 未运行'}")

    # CLI 信息
    if running:
        try:
            cli = _cli_cmd()
            r = subprocess.run([cli, "peer"], capture_output=True, text=True, timeout=5)
            if r.stdout.strip():
                print(f"\n  ── 对等节点 ──")
                print(r.stdout)
        except:
            pass

    print(f"\n  仪表盘: http://127.0.0.1:15889")
    print()
