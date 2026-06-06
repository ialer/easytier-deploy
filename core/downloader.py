"""
EasyTier 核心文件自动下载 + 版本检测
"""
import os, sys, json, zipfile, shutil, hashlib
import urllib.request, urllib.error
from pathlib import Path

GITHUB_API = "https://api.github.com/repos/EasyTier/EasyTier/releases"
GITHUB_RELEASES = "https://github.com/EasyTier/EasyTier/releases"

# 平台映射
PLATFORM_MAP = {
    "linux-x86_64":  "x86_64-unknown-linux-gnu",
    "linux-aarch64": "aarch64-unknown-linux-gnu",
    "darwin-x86_64": "x86_64-apple-darwin",
    "darwin-arm64":  "aarch64-apple-darwin",
    "win32-amd64":   "x86_64-pc-windows-msvc",
}

NEED_FILES = {
    "linux": ["easytier-core", "easytier-cli"],
    "darwin": ["easytier-core", "easytier-cli"],
    "win32": ["easytier-core.exe", "easytier-cli.exe"],
}

HERE = Path(__file__).resolve().parent.parent
BIN_DIR = HERE / "bin"
VERSION_FILE = BIN_DIR / ".et-version"


def get_platform_key():
    import platform
    system = platform.system().lower()
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch = "aarch64"
    else:
        arch = "x86_64"
    return f"{system}-{arch}"


def get_remote_version():
    """从 GitHub API 获取最新版本号"""
    try:
        req = urllib.request.Request(
            f"{GITHUB_API}/latest",
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get("tag_name", "").lstrip("v")
    except Exception as e:
        print(f"  ⚠ 获取远程版本失败: {e}")
        return None


def get_local_version():
    """读取本地已安装版本"""
    try:
        return VERSION_FILE.read_text().strip()
    except FileNotFoundError:
        return None


def get_download_url(version, platform_key):
    """构造下载 URL"""
    et_platform = PLATFORM_MAP.get(platform_key)
    if not et_platform:
        print(f"  ✗ 不支持的平台: {platform_key}")
        return None

    is_win = platform_key.startswith("win32")
    ext = ".zip" if is_win else ".tar.gz"
    filename = f"easytier-{version}-{et_platform}{ext}"
    return f"{GITHUB_RELEASES}/download/v{version}/{filename}"


def download_file(url, dest):
    """下载文件，显示进度"""
    print(f"  ↓ 下载中: {url.split('/')[-1]}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "et-deploy/2.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 65536
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                        print(f"\r  [{bar}] {pct}% ({downloaded}/{total})", end="", flush=True)
            print()
        return True
    except Exception as e:
        print(f"\n  ✗ 下载失败: {e}")
        return False


def extract_archive(archive_path, platform_key):
    """解压下载的文件到 bin/"""
    is_win = platform_key.startswith("win32")
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    if is_win:
        with zipfile.ZipFile(archive_path, "r") as zf:
            for name in zf.namelist():
                basename = os.path.basename(name)
                if basename and any(basename.startswith(p) for p in ["easytier-core", "easytier-cli"]):
                    print(f"  📦 解压: {basename}")
                    with zf.open(name) as src, open(BIN_DIR / basename, "wb") as dst:
                        dst.write(src.read())
    else:
        import tarfile
        with tarfile.open(archive_path, "r:gz" if archive_path.endswith(".tar.gz") else "r:*") as tf:
            for member in tf.getmembers():
                basename = os.path.basename(member.name)
                if basename and any(basename.startswith(p) for p in ["easytier-core", "easytier-cli"]):
                    print(f"  📦 解压: {basename}")
                    member.name = basename
                    tf.extract(member, str(BIN_DIR))
                    # 确保有执行权限
                    os.chmod(BIN_DIR / basename, 0o755)


def download_core(version=None, force=False):
    """下载 EasyTier 核心文件"""
    platform_key = get_platform_key()
    local_ver = get_local_version()

    if not version:
        version = get_remote_version()
        if not version:
            print("  ✗ 无法获取最新版本")
            return False

    if local_ver == version and not force:
        print(f"  ✓ 已是最新版本 v{version}")
        return True

    if local_ver:
        print(f"  📦 更新: v{local_ver} → v{version}")
    else:
        print(f"  📦 首次下载: v{version}")

    url = get_download_url(version, platform_key)
    if not url:
        return False

    # 下载到临时文件
    import tempfile
    is_win = platform_key.startswith("win32")
    suffix = ".zip" if is_win else ".tar.gz"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()

    try:
        if not download_file(url, tmp.name):
            return False
        extract_archive(tmp.name, platform_key)
        # 记录版本
        VERSION_FILE.write_text(version)
        print(f"  ✓ 安装完成 v{version}")
        return True
    finally:
        try:
            os.unlink(tmp.name)
        except:
            pass


def update_core():
    """更新 EasyTier 核心"""
    print("\n🔍 检查 EasyTier 更新...")
    local_ver = get_local_version()
    remote_ver = get_remote_version()

    if not remote_ver:
        print("  ✗ 无法获取远程版本信息")
        return

    print(f"  本地版本: v{local_ver}" if local_ver else "  本地版本: 未安装")
    print(f"  最新版本: v{remote_ver}")

    if local_ver == remote_ver:
        print("  ✓ 已是最新版本")
        return

    print(f"\n📦 开始更新...")
    if download_core(remote_ver, force=True):
        print("\n✓ 更新完成！建议运行 restart 重启服务。")
    else:
        print("\n✗ 更新失败")


def ensure_core():
    """确保核心文件存在，不存在则下载"""
    platform_key = get_platform_key()
    suffix = ".exe" if platform_key.startswith("win32") else ""
    core_path = BIN_DIR / f"easytier-core{suffix}"
    cli_path = BIN_DIR / f"easytier-cli{suffix}"

    if core_path.exists() and cli_path.exists():
        return True

    print("\n📦 EasyTier 核心文件未找到，开始自动下载...")
    return download_core()
