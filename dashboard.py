#!/usr/bin/env python3
"""EasyTier 虚拟网络监控面板 v4 - 通用版"""
import subprocess, time, http.server, os, pathlib, json, re, html as html_mod, secrets, hashlib
from string import Template
from collections import defaultdict

_here = pathlib.Path(__file__).resolve().parent
CLI = str(_here / "bin" / "easytier-cli.exe")
CONFIG_TOML = str(_here / "config.toml")
PORT = 15889
REFRESH = 8
AUTH_TOKEN = secrets.token_hex(16)  # Generate random token on each start

def _check_auth(handler):
    """Check API auth via query param or header"""
    token = handler.headers.get("X-Auth-Token", "")
    if not token:
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(handler.path).query)
        token = qs.get("token", [""])[0]
    return token == AUTH_TOKEN
HISTORY_MAX = 60

_latency_history = defaultdict(list)
_peer_history = []


def get_network_name():
    """从 config.toml 读取网络名称"""
    try:
        with open(CONFIG_TOML, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'network_name\s*=\s*"(.+)"', line.strip())
                if m:
                    return m.group(1)
    except Exception:
        pass
    return "EasyTier"


def get_hostname():
    """从 config.toml 读取主机名"""
    try:
        with open(CONFIG_TOML, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'hostname\s*=\s*"(.+)"', line.strip())
                if m:
                    return m.group(1)
    except:
        pass
    return "unknown"


# ---------- 数据采集 ----------
def run_cli(cmd):
    try:
        r = subprocess.run([CLI] + cmd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except:
        return ""


def parse_table(output):
    rows = []
    for line in output.split("\n"):
        if line.startswith("|") and "---" not in line and "ipv4" not in line.lower():
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if cols:
                rows.append(cols)
    return rows


def get_peers():
    rows = parse_table(run_cli(["peer"]))
    peers = []
    for cols in rows:
        if len(cols) >= 9:
            peers.append({
                "ipv4": cols[0], "hostname": cols[1], "cost": cols[2],
                "latency": cols[3], "loss": cols[4], "rx": cols[5],
                "tx": cols[6], "tunnel": cols[7], "nat": cols[8],
                "version": cols[9] if len(cols) > 9 else "",
            })
    now = time.time()
    for p in peers:
        if p["cost"] != "Local" and p["latency"] != "-":
            try:
                lat = float(p["latency"])
                _latency_history[p["hostname"]].append((now, lat))
                if len(_latency_history[p["hostname"]]) > HISTORY_MAX:
                    _latency_history[p["hostname"]].pop(0)
            except:
                pass
    _peer_history.append((now, len(peers)))
    if len(_peer_history) > HISTORY_MAX:
        _peer_history.pop(0)
    return peers


def get_routes():
    rows = parse_table(run_cli(["route"]))
    return [{"cidr": c[0], "hostname": c[1], "hop": c[2],
             "cost": c[3] if len(c) > 3 else ""} for c in rows if len(c) >= 4]


def get_node_info():
    output = run_cli(["node"])
    info = {}
    for line in output.split("\n"):
        if line.startswith("|"):
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 2:
                k, v = cols[0], cols[1]
                if k == "Virtual IP":
                    info["vip"] = v
                elif k == "Hostname":
                    info["hostname"] = v
                elif k == "Peer ID":
                    info["peer_id"] = v
                elif k == "Public IPv4":
                    info["pub_v4"] = v
                elif k == "Public IPv6":
                    info["pub_v6"] = v
                elif k == "UDP Stun Type":
                    info["nat_udp"] = v
                elif k.startswith("Listener"):
                    info.setdefault("listeners", []).append(v)
                elif k.startswith("Interface IPv4"):
                    info.setdefault("ifaces_v4", []).append(v)
    return info


def get_stun():
    output = run_cli(["stun"])
    info = {}
    for line in output.split("\n"):
        line = line.strip()
        if "udp_nat_type:" in line:
            info["udp_nat"] = line.split(":")[1].strip().rstrip(",").rstrip("}")
        elif "tcp_nat_type:" in line:
            info["tcp_nat"] = line.split(":")[1].strip().rstrip(",").rstrip("}")
        elif "public_ip:" in line:
            info["pub_ip"] = line.split(":", 1)[1].strip().rstrip("]").lstrip("[")
        elif "min_port:" in line:
            info["min_port"] = line.split(":")[1].strip().rstrip(",").rstrip("}")
        elif "max_port:" in line:
            info["max_port"] = line.split(":")[1].strip().rstrip(",").rstrip("}")
    return info


def get_traffic_stats():
    output = run_cli(["stats"])
    stats = {}
    for line in output.split("\n"):
        if line.startswith("|") and "---" not in line:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 3 and cols[0] != "Metric Name":
                name, val = cols[0], cols[1]
                if name == "traffic_bytes_rx" and "by_instance" not in name and "control" not in name and "self" not in name:
                    stats["total_rx"] = val
                elif name == "traffic_bytes_tx" and "by_instance" not in name and "control" not in name and "self" not in name:
                    stats["total_tx"] = val
                elif name == "traffic_packets_rx" and "by_instance" not in name and "control" not in name and "self" not in name:
                    stats["pkt_rx"] = val
                elif name == "traffic_packets_tx" and "by_instance" not in name and "control" not in name and "self" not in name:
                    stats["pkt_tx"] = val
                elif name == "compression_bytes_rx_before":
                    stats["comp_rx_before"] = val
                elif name == "compression_bytes_rx_after":
                    stats["comp_rx_after"] = val
                elif name == "compression_bytes_tx_before":
                    stats["comp_tx_before"] = val
                elif name == "compression_bytes_tx_after":
                    stats["comp_tx_after"] = val
                elif name == "traffic_bytes_forwarded":
                    stats["forwarded"] = val
    return stats


NAT_CN = {
    "FullCone": "全锥形", "SymmetricEasyInc": "对称易增",
    "Symmetric": "对称型", "PortRestricted": "端口限制",
    "RestrictedCone": "限制锥形"
}


# ---------- HTML ----------
HTML = Template(r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>$net_name - 虚拟网络监控</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Microsoft YaHei','PingFang SC','Segoe UI',sans-serif;background:#0a0e14;color:#c9d1d9;padding:20px 24px;min-height:100vh}
h1{color:#79c0ff;font-size:1.5em;margin-bottom:4px}
.sub{color:#6e7681;font-size:.8em;margin-bottom:18px}
.sub .t{color:#7ee787}

.stats{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.stat{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:12px 16px;flex:1;min-width:100px;text-align:center}
.stat .n{font-size:1.6em;font-weight:700;line-height:1.1}
.stat .l{color:#8b949e;font-size:.7em;margin-top:3px}
.c-blue .n{color:#79c0ff}.c-green .n{color:#3fb950}.c-yellow .n{color:#d29922}.c-purple .n{color:#bc8cff}

.info-grid{display:grid;grid-template-columns:1fr 1fr 1.5fr;gap:14px;margin-bottom:18px}
@media(max-width:900px){.info-grid{grid-template-columns:1fr}}
.panel{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px 16px;overflow:hidden}
.panel:hover{border-color:#58a6ff}
.panel h3{color:#79c0ff;font-size:.82em;margin-bottom:8px;display:flex;align-items:center;gap:5px}

.ir{display:flex;gap:4px;padding:3px 0;font-size:.78em;border-bottom:1px solid #1c2128;align-items:center}
.ir:last-child{border:none}
.ik{color:#6e7681;min-width:62px;flex-shrink:0;font-size:.9em}
.iv{color:#e6edf3;word-break:break-all;font-family:'Cascadia Code','Fira Code',monospace;font-size:.85em}

.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:2px 16px}
.stat-grid .ir{padding:2px 0}

.listener{display:inline-block;background:rgba(88,166,255,.1);border:1px solid rgba(88,166,255,.2);color:#58a6ff;padding:0 6px;border-radius:4px;font-size:.68em;margin:1px 3px 1px 0;font-family:monospace}

.cfg-btn{display:inline-flex;align-items:center;gap:4px;background:rgba(88,166,255,.1);border:1px solid rgba(88,166,255,.25);color:#58a6ff;padding:4px 10px;border-radius:6px;font-size:.75em;cursor:pointer;text-decoration:none;margin-top:8px;transition:all .2s}
.cfg-btn:hover{background:rgba(88,166,255,.2);border-color:#58a6ff}
.cfg-btn .ico{font-size:1em}

.vis-grid{display:grid;grid-template-columns:1.2fr 1fr;gap:14px;margin-bottom:18px}
@media(max-width:900px){.vis-grid{grid-template-columns:1fr}}
.vis-wrap{position:relative;width:100%;height:340px}
.vis-wrap canvas{width:100%;height:100%}

.section{color:#79c0ff;font-size:.95em;margin:16px 0 7px;padding-left:10px;border-left:3px solid #58a6ff}
table{width:100%;border-collapse:collapse;background:#161b22;border-radius:10px;overflow:hidden;margin-bottom:18px}
th{background:#21262d;color:#8b949e;text-align:left;padding:7px 10px;font-size:.73em;font-weight:600}
td{padding:6px 10px;border-bottom:1px solid #1c2128;font-size:.82em;font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:none}
tr:hover td{background:#1c2128}
.ip{color:#79c0ff;font-family:'Cascadia Code','Fira Code',monospace;font-size:.82em;cursor:pointer}
.ip:hover{text-decoration:underline}
.host{font-weight:600}
.local-row .host{color:#3fb950}
.tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.68em;font-weight:600}
.tag-local{background:rgba(63,185,80,.15);color:#3fb950;border:1px solid rgba(63,185,80,.3)}
.tag-p2p{background:rgba(88,166,255,.12);color:#58a6ff;border:1px solid rgba(88,166,255,.25)}
.tag-relay{background:rgba(210,153,34,.12);color:#d29922;border:1px solid rgba(210,153,34,.25)}
.nc{color:#e6edf3;font-family:'Cascadia Code','Fira Code',monospace}
.vr{color:#6e7681;font-size:.76em}

.modal-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.6);z-index:1000;justify-content:center;align-items:center}
.modal-overlay.show{display:flex}
.modal{background:#161b22;border:1px solid #30363d;border-radius:12px;width:90%;max-width:700px;max-height:80vh;display:flex;flex-direction:column}
.modal h3{color:#79c0ff;padding:14px 18px;border-bottom:1px solid #21262d;font-size:.9em;display:flex;justify-content:space-between;align-items:center}
.modal h3 .close{cursor:pointer;color:#8b949e;font-size:1.2em;padding:0 4px}
.modal h3 .close:hover{color:#f85149}
.modal textarea{flex:1;background:#0d1117;color:#e6edf3;border:none;padding:14px 18px;font-family:'Cascadia Code','Fira Code',monospace;font-size:.85em;resize:none;outline:none;min-height:300px}
.modal .bar{display:flex;gap:8px;padding:10px 18px;border-top:1px solid #21262d;justify-content:flex-end}
.modal .bar button{padding:6px 16px;border-radius:6px;border:1px solid #30363d;background:#21262d;color:#c9d1d9;cursor:pointer;font-size:.82em}
.modal .bar .save{background:#238636;border-color:#238636;color:#fff}
.modal .bar .save:hover{background:#2ea043}
.modal .msg{padding:4px 18px;font-size:.78em;color:#6e7681}

.footer{color:#30363d;font-size:.65em;text-align:center;margin-top:18px;padding-top:12px;border-top:1px solid #161b22}
.copied{position:fixed;top:20px;right:20px;background:#238636;color:#fff;padding:6px 14px;border-radius:8px;font-size:.82em;z-index:999;opacity:0;transition:opacity .3s;pointer-events:none}
.copied.show{opacity:1}
</style>
</head>
<body>
<div class="copied" id="copied">已复制!</div>

<div class="modal-overlay" id="cfgModal">
<div class="modal">
  <h3><span>&#9998; 编辑节点配置 &mdash; config.toml</span><span class="close" onclick="closeCfg()">&times;</span></h3>
  <div class="msg">修改后点击保存，需重启 EasyTier-Core 生效。</div>
  <textarea id="cfgText" spellcheck="false"></textarea>
  <div class="bar">
    <button onclick="closeCfg()">取消</button>
    <button class="save" onclick="saveCfg()">&#128190; 保存</button>
  </div>
</div>
</div>

<h1>&#127760; $net_name</h1>
<p class="sub">设备: $hostname &nbsp;&#8226;&nbsp; 每 ${refresh} 秒自动刷新 &nbsp;&#8226;&nbsp; 更新于 <span class="t">$timestamp</span></p>

<div class="stats">
  <div class="stat c-blue"><div class="n">$total</div><div class="l">设备总数</div></div>
  <div class="stat c-green"><div class="n">$p2p_count</div><div class="l">P2P 直连</div></div>
  <div class="stat c-yellow"><div class="n">$relay_count</div><div class="l">中继转发</div></div>
  <div class="stat c-purple"><div class="n">1</div><div class="l">本机节点</div></div>
</div>

<div class="info-grid">
  <div class="panel">
    <h3>&#128187; 本机节点</h3>
    <div class="ir"><span class="ik">虚拟 IP</span><span class="iv ip" onclick="copyTxt(this)">$node_vip</span></div>
    <div class="ir"><span class="ik">主机名</span><span class="iv">$node_hostname</span></div>
    <div class="ir"><span class="ik">公网 v4</span><span class="iv ip" onclick="copyTxt(this)">$node_pub_v4</span></div>
    <div class="ir"><span class="ik">公网 v6</span><span class="iv ip" onclick="copyTxt(this)" style="font-size:.72em">$node_pub_v6</span></div>
    <div class="ir"><span class="ik">NAT</span><span class="iv">$node_nat</span></div>
    <div class="ir"><span class="ik">Peer ID</span><span class="iv">$node_peer_id</span></div>
    <div class="ir"><span class="ik">监听协议</span><span class="iv">$listeners</span></div>
    <a class="cfg-btn" onclick="openCfg()"><span class="ico">&#9998;</span> 编辑节点配置</a>
  </div>

  <div class="panel">
    <h3>&#128293; STUN 诊断</h3>
    <div class="ir"><span class="ik">UDP NAT</span><span class="iv">$stun_udp_nat</span></div>
    <div class="ir"><span class="ik">TCP NAT</span><span class="iv">$stun_tcp_nat</span></div>
    <div class="ir"><span class="ik">公网 IP</span><span class="iv ip" onclick="copyTxt(this)">$stun_pub_ip</span></div>
    <div class="ir"><span class="ik">端口范围</span><span class="iv">$stun_ports</span></div>
  </div>

  <div class="panel">
    <h3>&#128200; 流量统计</h3>
    <div class="stat-grid">
      <div class="ir"><span class="ik">总接收</span><span class="iv nc">$total_rx</span></div>
      <div class="ir"><span class="ik">总发送</span><span class="iv nc">$total_tx</span></div>
      <div class="ir"><span class="ik">收包</span><span class="iv nc">$pkt_rx</span></div>
      <div class="ir"><span class="ik">发包</span><span class="iv nc">$pkt_tx</span></div>
      <div class="ir"><span class="ik">压缩前收</span><span class="iv nc">$comp_rx_before</span></div>
      <div class="ir"><span class="ik">压缩后收</span><span class="iv nc">$comp_rx_after</span></div>
      <div class="ir"><span class="ik">压缩前发</span><span class="iv nc">$comp_tx_before</span></div>
      <div class="ir"><span class="ik">压缩后发</span><span class="iv nc">$comp_tx_after</span></div>
      <div class="ir"><span class="ik">压缩比</span><span class="iv nc">$comp_ratio</span></div>
      <div class="ir"><span class="ik">转发量</span><span class="iv nc">$forwarded</span></div>
    </div>
  </div>
</div>

<h2 class="section">&#128225; 在线设备</h2>
<table>
<tr><th>虚拟 IP</th><th>主机名</th><th>连接</th><th>延迟</th><th>丢包</th><th>接收</th><th>发送</th><th>隧道</th><th>NAT</th><th>版本</th></tr>
$peer_rows
</table>

<div class="vis-grid">
  <div>
    <h2 class="section">&#127759; 网络拓扑</h2>
    <div class="panel vis-wrap"><canvas id="topo"></canvas></div>
  </div>
  <div>
    <h2 class="section">&#128200; 延迟趋势</h2>
    <div class="panel vis-wrap"><canvas id="chart"></canvas></div>
  </div>
</div>

<h2 class="section">&#128506; 路由表</h2>
<table>
<tr><th>网段</th><th>主机名</th><th>下一跳</th><th>开销</th></tr>
$route_rows
</table>

<div class="footer">EasyTier 虚拟网络监控 &nbsp;&#8226;&nbsp; $net_name</div>

<script>
function copyTxt(el){navigator.clipboard.writeText(el.textContent).then(()=>{let c=document.getElementById('copied');c.classList.add('show');setTimeout(()=>c.classList.remove('show'),1200)})}

var _refreshTimer=null;
function startRefresh(){stopRefresh();_refreshTimer=setTimeout(function(){location.reload()},${refresh}*1000)}
function stopRefresh(){if(_refreshTimer){clearTimeout(_refreshTimer);_refreshTimer=null}}
startRefresh();

function openCfg(){
  stopRefresh();
  fetch('/api/config',{headers:{'X-Auth-Token':_apiToken}}).then(function(r){return r.text()}).then(function(t){
    document.getElementById('cfgText').value=t;
    document.getElementById('cfgModal').classList.add('show');
    document.getElementById('cfgText').focus();
  }).catch(function(){alert('无法读取配置文件')});
}
function closeCfg(){
  document.getElementById('cfgModal').classList.remove('show');
  startRefresh();
}
function saveCfg(){
  var txt=document.getElementById('cfgText').value;
  fetch('/api/config',{method:'POST',body:txt,headers:{'X-Auth-Token':_apiToken}}).then(function(r){return r.text()}).then(function(t){
    alert(t);closeCfg();
  }).catch(function(){alert('保存失败')});
}

(function(){
  const cv=document.getElementById('topo'),ctx=cv.getContext('2d');
  const W=cv.parentElement.clientWidth-4,H=340;
  cv.width=W*2;cv.height=H*2;cv.style.width=W+'px';cv.style.height=H+'px';ctx.scale(2,2);
  const peers=$topo_json;const cx=W/2,cy=H/2,r=Math.min(W,H)*0.33;
  const local=peers.find(p=>p.cost==='Local'),others=peers.filter(p=>p.cost!=='Local');
  others.forEach((p,i)=>{
    const a=-Math.PI/2+i*2*Math.PI/others.length;
    const x=cx+r*Math.cos(a),y=cy+r*Math.sin(a);
    ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(x,y);
    ctx.strokeStyle=p.cost==='p2p'?'rgba(63,185,80,.35)':'rgba(210,153,34,.35)';
    ctx.lineWidth=p.cost==='p2p'?2:1.5;if(p.cost!=='p2p')ctx.setLineDash([4,4]);ctx.stroke();ctx.setLineDash([]);
    if(p.latency!=='-'){const mx=(cx+x)/2,my=(cy+y)/2;ctx.fillStyle='#6e7681';ctx.font='9px sans-serif';ctx.textAlign='center';ctx.fillText(p.latency+'ms',mx,my-3)}
  });
  function dn(x,y,l,s,c,rs){ctx.beginPath();ctx.arc(x,y,rs,0,Math.PI*2);ctx.fillStyle=c;ctx.fill();ctx.strokeStyle='rgba(255,255,255,.12)';ctx.lineWidth=1;ctx.stroke();ctx.fillStyle='#e6edf3';ctx.font='bold 10px sans-serif';ctx.textAlign='center';ctx.fillText(l,x,y+3);ctx.fillStyle='#8b949e';ctx.font='8px sans-serif';ctx.fillText(s,x,y+14)}
  dn(cx,cy,local?local.hostname:'',local?local.ipv4.split('/')[0]:'','#3fb950',22);
  others.forEach((p,i)=>{const a=-Math.PI/2+i*2*Math.PI/others.length;const x=cx+r*Math.cos(a),y=cy+r*Math.sin(a);dn(x,y,p.hostname,p.ipv4.split('/')[0],p.cost==='p2p'?'#58a6ff':'#d29922',16)});
})();

(function(){
  const cv=document.getElementById('chart'),ctx=cv.getContext('2d');
  const W=cv.parentElement.clientWidth-4,H=340;
  cv.width=W*2;cv.height=H*2;cv.style.width=W+'px';cv.style.height=H+'px';ctx.scale(2,2);
  const data=$chart_json,keys=Object.keys(data);
  if(!keys.length){ctx.fillStyle='#6e7681';ctx.font='13px sans-serif';ctx.textAlign='center';ctx.fillText('等待数据...',W/2,H/2);return}
  let maxL=0;keys.forEach(k=>data[k].forEach(d=>{if(d[1]>maxL)maxL=d[1]}));maxL=Math.max(maxL,50);
  const p={t:16,r:12,b:24,l:44},cw=W-p.l-p.r,ch=H-p.t-p.b;
  ctx.strokeStyle='#21262d';ctx.lineWidth=.5;
  for(let i=0;i<=4;i++){const y=p.t+ch*i/4;ctx.beginPath();ctx.moveTo(p.l,y);ctx.lineTo(W-p.r,y);ctx.stroke();ctx.fillStyle='#6e7681';ctx.font='9px monospace';ctx.textAlign='right';ctx.fillText(Math.round(maxL*(1-i/4))+'ms',p.l-4,y+3)}
  const colors=['#58a6ff','#3fb950','#d29922','#f0883e','#bc8cff','#f778ba','#79c0ff'];
  keys.forEach((k,ki)=>{
    const pts=data[k];if(pts.length<2)return;
    ctx.beginPath();ctx.strokeStyle=colors[ki%colors.length];ctx.lineWidth=1.5;
    pts.forEach((d,j)=>{const x=p.l+cw*j/(HISTORY_MAX-1),y=p.t+ch*(1-d[1]/maxL);j===0?ctx.moveTo(x,y):ctx.lineTo(x,y)});
    ctx.stroke();
    const last=pts[pts.length-1],lx=p.l+cw*(pts.length-1)/(HISTORY_MAX-1),ly=p.t+ch*(1-last[1]/maxL);
    ctx.fillStyle=colors[ki%colors.length];ctx.font='9px sans-serif';ctx.textAlign='left';ctx.fillText(k+' '+last[1]+'ms',lx+3,ly+3);
  });
})();
</script>
</body>
</html>
""")


def render():
    net_name = get_network_name()
    hostname = get_hostname()
    peers = get_peers()
    routes = get_routes()
    node = get_node_info()
    stun = get_stun()
    stats = get_traffic_stats()
    total = len(peers)
    p2p = sum(1 for p in peers if p["cost"] == "p2p")
    relay = sum(1 for p in peers if "relay" in p["cost"])

    rows = []
    for p in peers:
        nat_cn = NAT_CN.get(p["nat"], p["nat"])
        if p["cost"] == "Local":
            tag, cls = '<span class="tag tag-local">本机</span>', ' class="local-row"'
        elif p["cost"] == "p2p":
            tag, cls = '<span class="tag tag-p2p">P2P</span>', ''
        else:
            tag, cls = '<span class="tag tag-relay">中继</span>', ''
        def esc(s):
            return html_mod.escape(str(s), quote=True)
        rows.append(
            f'<tr{cls}><td class="ip" onclick="copyTxt(this)">{esc(p["ipv4"])}</td>'
            f'<td class="host">{esc(p["hostname"])}</td><td>{tag}</td>'
            f'<td class="nc">{esc(p["latency"])}</td><td class="nc">{esc(p["loss"])}</td>'
            f'<td class="nc">{esc(p["rx"])}</td><td class="nc">{esc(p["tx"])}</td>'
            f'<td>{esc(p["tunnel"])}</td><td>{esc(nat_cn)}</td>'
            f'<td class="vr">{esc(p["version"])}</td></tr>'
        )

    rrows = [
        f'<tr><td class="ip">{html_mod.escape(str(r["cidr"]))}</td><td>{html_mod.escape(str(r["hostname"]))}</td>'
        f'<td>{html_mod.escape(str(r["hop"]))}</td><td class="nc">{html_mod.escape(str(r["cost"]))}</td></tr>'
        for r in routes
    ]

    listeners_html = "".join(
        f'<span class="listener">{html_mod.escape(str(l))}</span>' for l in node.get("listeners", [])
    )

    comp_ratio = "-"
    try:
        rb = float(stats.get("comp_rx_before", "0 B").split()[0])
        ra = float(stats.get("comp_rx_after", "0 B").split()[0])
        if ra > 0:
            comp_ratio = f"{(1 - rb / ra) * 100:.1f}%"
    except Exception:
        pass

    topo_data = [
        {"ipv4": p["ipv4"], "hostname": p["hostname"],
         "cost": p["cost"], "latency": p["latency"]}
        for p in peers
    ]
    chart_data = {
        h: [(t, lat) for t, lat in pts]
        for h, pts in _latency_history.items()
    }

    return HTML.safe_substitute(
        api_token=AUTH_TOKEN, net_name=net_name, hostname=hostname,
        refresh=REFRESH, timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        total=total, p2p_count=p2p, relay_count=relay,
        total_rx=stats.get("total_rx", "-"), total_tx=stats.get("total_tx", "-"),
        pkt_rx=stats.get("pkt_rx", "-"), pkt_tx=stats.get("pkt_tx", "-"),
        comp_rx_before=stats.get("comp_rx_before", "-"),
        comp_rx_after=stats.get("comp_rx_after", "-"),
        comp_tx_before=stats.get("comp_tx_before", "-"),
        comp_tx_after=stats.get("comp_tx_after", "-"),
        comp_ratio=comp_ratio, forwarded=stats.get("forwarded", "-"),
        node_vip=node.get("vip", "-"), node_hostname=node.get("hostname", "-"),
        node_pub_v4=node.get("pub_v4", "-"), node_pub_v6=node.get("pub_v6", "-"),
        node_nat=NAT_CN.get(node.get("nat_udp", ""), node.get("nat_udp", "-")),
        node_peer_id=node.get("peer_id", "-"), listeners=listeners_html or "-",
        stun_udp_nat=NAT_CN.get(stun.get("udp_nat", ""), stun.get("udp_nat", "-")),
        stun_tcp_nat=NAT_CN.get(stun.get("tcp_nat", ""), stun.get("tcp_nat", "-")),
        stun_pub_ip=stun.get("pub_ip", "-"),
        stun_ports=f'{stun.get("min_port", "?")} - {stun.get("max_port", "?")}',
        topo_json=json.dumps(topo_data), chart_json=json.dumps(chart_data),
        peer_rows="\n".join(rows) or '<tr><td colspan="10" style="text-align:center;color:#6e7681">暂无设备</td></tr>',
        route_rows="\n".join(rrows) or '<tr><td colspan="4" style="text-align:center;color:#6e7681">暂无路由</td></tr>',
    )


class Handler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path.startswith("/api/config"):
            if not _check_auth(self):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden: invalid token")
                return
            try:
                with open(CONFIG_TOML, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Config file not found")
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Cannot read config: {e}".encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(render().encode("utf-8"))

    def do_POST(self):
        if self.path.startswith("/api/config"):
            if not _check_auth(self):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden: invalid token")
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                if length > 100_000:  # 100KB limit
                    self.send_response(413)
                    self.end_headers()
                    self.wfile.write(b"Payload too large")
                    return
                body = self.rfile.read(length).decode("utf-8")
                # Validate TOML basics
                if "[network_identity]" not in body and "[flags]" not in body:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Invalid config: missing required sections")
                    return
                with open(CONFIG_TOML, "w", encoding="utf-8") as f:
                    f.write(body)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write("配置已保存! 请重启 EasyTier-Core 生效。".encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"保存失败: {e}".encode("utf-8"))

    def log_message(self, fmt, *args):
        # Log to stderr for debugging (not suppressed)
        import sys
        print(f"[{time.strftime('%H:%M:%S')}] {fmt % args}", file=sys.stderr)


if __name__ == "__main__":
    os.chdir(_here)
    print(f"Dashboard v4: http://127.0.0.1:{PORT}", flush=True)
    print(f"API Token: {AUTH_TOKEN}  (use in X-Auth-Token header or ?token= param)", flush=True)
    http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
