"""
Web 监控仪表盘
"""
import json, os, platform, subprocess, time, secrets
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

HERE = Path(__file__).resolve().parent.parent
BIN_DIR = HERE / "bin"
CONFIG_FILE = HERE / "config.toml"
WEB_DIR = HERE / "web"
PORT = 15889

IS_WIN = platform.system() == "Windows"


def _cli_cmd():
    suffix = ".exe" if IS_WIN else ""
    return str(BIN_DIR / f"easytier-cli{suffix}")


def _run_cli(args):
    try:
        r = subprocess.run([_cli_cmd()] + args, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:
        return ""


def _parse_table(output):
    rows = []
    for line in output.split("\n"):
        if line.startswith("|") and "---" not in line:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if cols:
                rows.append(cols)
    return rows


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/dashboard":
            self._serve_file(WEB_DIR / "dashboard.html", "text/html")
        elif path == "/api/peers":
            self._api_peers()
        elif path == "/api/node":
            self._api_node()
        elif path == "/api/routes":
            self._api_routes()
        elif path == "/api/stats":
            self._api_stats()
        elif path == "/api/config":
            self._api_config_get()
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/api/config":
            self._api_config_save(body)
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

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _api_peers(self):
        output = _run_cli(["peer"])
        rows = _parse_table(output)
        peers = []
        for cols in rows:
            if len(cols) >= 8:
                peers.append({
                    "ipv4": cols[0], "hostname": cols[1],
                    "cost": cols[2], "latency": cols[3],
                    "loss": cols[4], "rx": cols[5], "tx": cols[6],
                    "tunnel": cols[7], "nat": cols[8] if len(cols)>8 else "",
                    "version": cols[9] if len(cols)>9 else "",
                })
        self._json({"peers": peers, "count": len(peers)})

    def _api_node(self):
        output = _run_cli(["node"])
        info = {}
        for line in output.split("\n"):
            if line.startswith("|"):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 2:
                    k, v = cols[0], cols[1]
                    if k == "Virtual IP": info["vip"] = v
                    elif k == "Hostname": info["hostname"] = v
                    elif k == "Peer ID": info["peer_id"] = v
                    elif k == "Public IPv4": info["pub_v4"] = v
                    elif k == "UDP Stun Type": info["nat_type"] = v
        self._json(info)

    def _api_routes(self):
        output = _run_cli(["route"])
        rows = _parse_table(output)
        routes = [{"cidr": c[0], "hostname": c[1], "hop": c[2]}
                  for c in rows if len(c) >= 3]
        self._json({"routes": routes})

    def _api_stats(self):
        output = _run_cli(["stats"])
        stats = {}
        for line in output.split("\n"):
            if line.startswith("|") and "---" not in line:
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 2 and cols[0] != "Metric Name":
                    name, val = cols[0], cols[1]
                    if "traffic_bytes" in name and "forwarded" not in name:
                        stats[name] = val
                    elif "compression" in name:
                        stats[name] = val
        self._json(stats)

    def _api_config_get(self):
        try:
            config = CONFIG_FILE.read_text()
            self._json({"config": config})
        except FileNotFoundError:
            self._json({"config": ""})

    def _api_config_save(self, body):
        config = body.get("config", "")
        if not config:
            self._json({"ok": False, "error": "配置不能为空"}, 400)
            return
        CONFIG_FILE.write_text(config)
        self._json({"ok": True, "message": "配置已保存，重启服务后生效"})


def run_dashboard():
    server = HTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"\n🌐 监控仪表盘: http://127.0.0.1:{PORT}")
    print(f"   按 Ctrl+C 停止\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    run_dashboard()
