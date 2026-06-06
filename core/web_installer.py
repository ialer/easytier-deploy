"""
Web 安装向导服务器
提供 HTTP API 给 installer.html 调用
"""
import json, os, sys, platform, subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent.parent
WEB_DIR = HERE / "web"
PORT = 15888


class InstallerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/installer.html":
            self._serve_file(WEB_DIR / "installer.html", "text/html")
        elif path == "/api/check":
            self._api_check()
        elif path == "/api/version":
            self._api_version()
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/api/install":
            self._api_install(body)
        elif path == "/api/deploy":
            self._api_deploy(body)
        else:
            self.send_error(404)

    def _serve_file(self, filepath, content_type):
        try:
            data = filepath.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", len(data))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_error(404)

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _api_check(self):
        """环境检测"""
        checks = []
        system = platform.system()
        checks.append({"label": "操作系统", "value": f"{system} ({platform.machine()})", "ok": True})
        checks.append({"label": "Python", "value": sys.version.split()[0], "ok": True})

        # 检查核心文件
        suffix = ".exe" if system == "Windows" else ""
        core = HERE / "bin" / f"easytier-core{suffix}"
        cli = HERE / "bin" / f"easytier-cli{suffix}"
        if core.exists() and cli.exists():
            checks.append({"label": "EasyTier 核心", "value": "已就绪", "ok": True})
        else:
            checks.append({"label": "EasyTier 核心", "value": "未安装（将自动下载）", "ok": False})

        self._json_response({"checks": checks})

    def _api_version(self):
        """版本信息"""
        from .downloader import get_local_version, get_remote_version
        self._json_response({
            "local": get_local_version(),
            "remote": get_remote_version()
        })

    def _api_install(self, body):
        """安装配置"""
        from .installer import _validate_ipv4, _validate_uri
        errors = []
        if not body.get("network_name"):
            errors.append("网络名称不能为空")
        if not body.get("network_secret"):
            errors.append("网络密钥不能为空")
        if not _validate_uri(body.get("peer_uri", "")):
            errors.append("引导节点 URI 格式错误")
        if not _validate_ipv4(body.get("ipv4", "")):
            errors.append("虚拟 IP 格式错误")

        if errors:
            self._json_response({"ok": False, "errors": errors}, 400)
            return

        # 生成配置文件
        config = f"""# EasyTier 节点配置
# 由 et-deploy web installer 自动生成

[network_identity]
network_name = "{body['network_name']}"
network_secret = "{body['network_secret']}"

[[peer]]
uri = "{body['peer_uri']}"

[flags]
ipv4 = "{body['ipv4']}"
hostname = "{body.get('hostname', 'device')}"
"""
        if body.get("encryption"):
            config += f'encryption-algorithm = "{body["encryption"]}"\n'

        (HERE / "config.toml").write_text(config)
        self._json_response({"ok": True, "message": "配置已生成"})

    def _api_deploy(self, body):
        """部署"""
        from .downloader import download_core, ensure_core
        from .service import service_install, service_start

        steps = []
        try:
            # 下载核心
            steps.append({"label": "下载核心文件", "status": "running"})
            if not ensure_core():
                download_core()
            steps[-1]["status"] = "done"

            # 注册服务
            steps.append({"label": "注册服务", "status": "running"})
            service_install()
            steps[-1]["status"] = "done"

            # 启动
            steps.append({"label": "启动服务", "status": "running"})
            service_start()
            steps[-1]["status"] = "done"

            self._json_response({"ok": True, "steps": steps})
        except Exception as e:
            steps.append({"label": str(e), "status": "error"})
            self._json_response({"ok": False, "steps": steps, "error": str(e)}, 500)


def run_web_installer():
    """启动 Web 安装向导"""
    server = HTTPServer(("0.0.0.0", PORT), InstallerHandler)
    print(f"\n🌐 Web 安装向导已启动: http://127.0.0.1:{PORT}")
    print(f"   按 Ctrl+C 停止\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    run_web_installer()
