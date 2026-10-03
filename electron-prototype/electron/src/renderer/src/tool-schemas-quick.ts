// tool-schemas-quick.ts：W8 单按钮速查 ×10（sidecar 计算型；网络类不自动运行，本地快查 quickRun）。
// 约定：pyCode 产物把 ToolResult JSON 包在 <<<JSON>>>/<<<END>>> 标记间，页面解析渲染。
// 只依赖 interactive-tools 的类型（运行时零导入）。
import type { InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '')

const WRAP = (body: string, note = ''): string =>
  `"""速查工具（页面自动呈现结果；JSON 标记供页面解析）。"""
import json
${note}
${body}
print("<<<JSON>>>")
print(json.dumps(_r, ensure_ascii=False))
print("<<<END>>>")
`

// ---------------------------------------------------------------------------
// 1. IP 查询（网络，<2s，可自动运行）
// ---------------------------------------------------------------------------
export const ipLookupSchema: InteractiveToolSchema = {
  id: 'interactive:ip-lookup',
  title: 'IP 查询',
  description: '本机出口 IP 与归属信息（ipify + ipinfo 免费接口，需联网）。results 以卡片呈现。',
  tags: ['网络', '速查'],
  fields: [],
  computeVia: 'sidecar',
  quickRun: true,
  compute: () => ({ rows: [{ label: '状态', value: '点击「运行」查询' }] }),
  pyCode: () =>
    WRAP(`import requests

_r = {}
try:
    ip = requests.get("https://api.ipify.org", timeout=10).text.strip()
    _r["primary"] = {"value": ip}
    info = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10).json()
    _r["rows"] = [
        {"label": "出口 IP", "value": ip, "copy": True},
        {"label": "归属地", "value": " ".join(str(info.get(k, "—")) for k in ("city", "region", "country"))},
        {"label": "运营商", "value": str(info.get("org", "—"))},
    ]
except Exception as e:
    _r = {"error": f"查询失败（需联网）: {e}"}`)
}

// ---------------------------------------------------------------------------
// 2. DNS 解析查询
// ---------------------------------------------------------------------------
export const dnsLookupSchema: InteractiveToolSchema = {
  id: 'interactive:dns-lookup',
  title: 'DNS 解析查询',
  description: '域名 → A 记录/别名（socket.getaddrinfo，跟随系统 DNS）。',
  tags: ['网络', '速查'],
  fields: [{ key: 'domain', label: '域名', type: 'text', required: true, placeholder: 'example.com' }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.domain) ? { rows: [{ label: '状态', value: '点击「运行」解析' }] } : { error: '请输入域名' }),
  pyCode: (v) => {
    const d = str(v.domain).trim()
    if (!d) return '# 输入域名后自动生成代码'
    return WRAP(`import socket

_r = {}
try:
    infos = socket.getaddrinfo(${JSON.stringify(d)}, None)
    addrs = sorted({(i[4][0], i[0].name) for i in infos})
    _r["primary"] = {"value": str(len(addrs)), "unit": "条记录"}
    _r["rows"] = [{"label": a, "value": fam} for a, fam in addrs]
except socket.gaierror as e:
    _r = {"error": f"解析失败: {e}"}`)
  }
}

// ---------------------------------------------------------------------------
// 3. 端口连通检查
// ---------------------------------------------------------------------------
export const portCheckSchema: InteractiveToolSchema = {
  id: 'interactive:port-check',
  title: '端口连通检查',
  description: 'TCP 连通性探测（socket connect_ex，2 秒超时）。',
  tags: ['网络', '速查'],
  fields: [
    { key: 'host', label: '主机', type: 'text', required: true, placeholder: '127.0.0.1', width: 'half' },
    { key: 'port', label: '端口', type: 'number', required: true, placeholder: '8080', width: 'half' }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.host) && v.port !== undefined
      ? { rows: [{ label: '状态', value: '点击「运行」探测' }] }
      : { error: '请补全主机与端口' },
  pyCode: (v) => {
    const host = str(v.host).trim()
    const port = Math.trunc(Number(v.port))
    if (!host || !Number.isFinite(port) || port < 1 || port > 65535) return '# 补全主机与端口后自动生成代码'
    return WRAP(`import socket

_r = {}
s = socket.socket()
s.settimeout(2)
code = s.connect_ex((${JSON.stringify(host)}, ${port}))
s.close()
ok = code == 0
_r["primary"] = {"value": "通" if ok else "不通"}
_r["rows"] = [{"label": "目标", "value": "${host}:${port}"}, {"label": "errno", "value": str(code)}]`)
  }
}

// ---------------------------------------------------------------------------
// 4. HTTP 头检查器
// ---------------------------------------------------------------------------
export const httpHeadersSchema: InteractiveToolSchema = {
  id: 'interactive:http-headers',
  title: 'HTTP 头检查器',
  description: '查看响应头（GET，10 秒超时）：缓存/安全/CORS 相关头一目了然。',
  tags: ['网络', '速查'],
  fields: [{ key: 'url', label: 'URL', type: 'text', required: true, placeholder: 'https://example.com' }],
  computeVia: 'sidecar',
  compute: (v) => (str(v.url) ? { rows: [{ label: '状态', value: '点击「运行」请求' }] } : { error: '请输入 URL' }),
  pyCode: (v) => {
    const url = str(v.url).trim()
    if (!url) return '# 输入 URL 后自动生成代码'
    return WRAP(`import requests

_r = {}
try:
    resp = requests.get(${JSON.stringify(url)}, timeout=10)
    _r["primary"] = {"value": str(resp.status_code)}
    interesting = ("content-type", "cache-control", "server", "content-encoding",
                   "strict-transport-security", "access-control-allow-origin", "set-cookie")
    _r["rows"] = [{"label": k, "value": (v[:80] + "…") if len(v := str(val)) > 80 else v, "copy": True}
                  for k, val in resp.headers.items() if k.lower() in interesting or True][:14]
except Exception as e:
    _r = {"error": f"请求失败（需联网）: {e}"}`)
  }
}

// ---------------------------------------------------------------------------
// 5. 网速测试（慢，不自动运行）
// ---------------------------------------------------------------------------
export const speedTestSchema: InteractiveToolSchema = {
  id: 'interactive:speed-test',
  title: '网速测试',
  description: '下载 1MB×3 次取均值（httpbin 字节端点，需联网，约 10 秒）。',
  tags: ['网络', '速查'],
  fields: [],
  computeVia: 'sidecar',
  compute: () => ({ rows: [{ label: '状态', value: '点击「运行」测速（约 10 秒）' }] }),
  pyCode: () =>
    WRAP(`import time

import requests

_r = {}
try:
    for i in range(3):
        t0 = time.monotonic()
        data = requests.get("https://httpbin.org/bytes/1048576", timeout=30).content
        secs = time.monotonic() - t0
        sizes.append(len(data) / secs / 1024 / 1024)
        print(f"第{i + 1}次: {sizes[-1]:.2f} MB/s")
    avg = sum(sizes) / len(sizes)
    _r = {"primary": {"value": f"{avg:.2f}", "unit": "MB/s 均值"}}
except Exception as e:
    _r = {"error": f"测速失败（需联网）: {e}"}`)
}

// ---------------------------------------------------------------------------
// 6-9. 本地快查（psutil/platform，quickRun）
// ---------------------------------------------------------------------------
export const batterySchema: InteractiveToolSchema = {
  id: 'interactive:battery',
  title: '电池状态',
  description: '电量/充电状态/剩余时间（psutil；台式机无电池时给引导）。',
  tags: ['系统', '速查'],
  fields: [],
  computeVia: 'sidecar',
  quickRun: true,
  compute: () => ({ rows: [{ label: '状态', value: '点击「运行」读取' }] }),
  pyCode: () =>
    WRAP(`import psutil

b = psutil.sensors_battery()
if b is None:
    _r = {"error": "未检测到电池（台式机/外接显示器供电）"}
else:
    _r = {
        "primary": {"value": str(round(b.percent)), "unit": "% 电量"},
        "rows": [
            {"label": "电源", "value": "已接通" if b.power_plugged else "电池供电"},
            {"label": "剩余时间", "value": f"{b.secsleft // 3600}h{(b.secsleft % 3600) // 60}m" if b.secsleft > 0 else "—"},
        ],
    }`)
}

export const diskUsageSchema: InteractiveToolSchema = {
  id: 'interactive:disk-usage',
  title: '磁盘使用仪表',
  description: '各挂载点总容量/已用/可用（shutil.disk_usage）。',
  tags: ['系统', '速查'],
  fields: [],
  computeVia: 'sidecar',
  quickRun: true,
  compute: () => ({ rows: [{ label: '状态', value: '点击「运行」读取' }] }),
  pyCode: () =>
    WRAP(`import shutil

_r = {"table": {"columns": ["挂载点", "总容量", "已用", "可用", "使用率"], "rows": []}}
for mount in ("/", "/Volumes/Data", "/home"):
    try:
        u = shutil.disk_usage(mount)
    except OSError:
        continue
    if u.total == 0:
        continue  # 虚拟挂载点（如 macOS /home auto_master）
    g = lambda n: f"{n / 1024 ** 3:.0f}G"
    _r["table"]["rows"].append([mount, g(u.total), g(u.used), g(u.free), f"{u.used / u.total * 100:.0f}%"])`)
}

export const systemInfoSchema: InteractiveToolSchema = {
  id: 'interactive:system-info',
  title: '系统信息报告',
  description: '系统/Python 环境/硬件概况（platform + os + psutil）。',
  tags: ['系统', '速查'],
  fields: [],
  computeVia: 'sidecar',
  quickRun: true,
  compute: () => ({ rows: [{ label: '状态', value: '点击「运行」读取' }] }),
  pyCode: () =>
    WRAP(`import os
import platform
import sys

_r = {
    "rows": [
        {"label": "系统", "value": f"{platform.system()} {platform.release()} ({platform.machine()})"},
        {"label": "Python", "value": sys.version.split()[0]},
        {"label": "CPU 核数", "value": str(os.cpu_count())},
        {"label": "内存", "value": f"{psutil.virtual_memory().total / 1024 ** 3:.0f} GB"},
    ]
}
import psutil`)
}

export const processTopSchema: InteractiveToolSchema = {
  id: 'interactive:process-top',
  title: '进程资源 Top 榜',
  description: '内存占用 Top 10 进程（psutil，瞬时快照）。',
  tags: ['系统', '速查'],
  fields: [],
  computeVia: 'sidecar',
  quickRun: true,
  compute: () => ({ rows: [{ label: '状态', value: '点击「运行」读取' }] }),
  pyCode: () =>
    WRAP(`import psutil

procs = []
for p in psutil.process_iter(["pid", "name", "memory_info"]):
    try:
        procs.append((p.info["memory_info"].rss, p.info["pid"], p.info["name"] or "?"))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue
procs.sort(reverse=True)
_r = {
    "table": {
        "columns": ["PID", "进程", "内存"],
        "rows": [[str(pid), name[:28], f"{rss / 1024 / 1024:.0f} MB"] for rss, pid, name in procs[:10]],
    }
}`)
}

// ---------------------------------------------------------------------------
// 10. 媒体信息探测（ffprobe；本机需装 ffmpeg 套件）
// ---------------------------------------------------------------------------
export const mediaInfoSchema: InteractiveToolSchema = {
  id: 'interactive:media-info',
  title: '媒体信息探测',
  description: 'ffprobe 读取媒体文件：时长/分辨率/编码/码率/体积（需本机安装 ffmpeg）。',
  tags: ['媒体', '速查'],
  fields: [
    {
      key: 'file',
      label: '媒体文件',
      type: 'file',
      required: true,
      accept: ['mp4', 'mov', 'mkv', 'mp3', 'm4a', 'wav', 'gif']
    }
  ],
  computeVia: 'sidecar',
  compute: (v) =>
    str(v.file) ? { rows: [{ label: '状态', value: '点击「运行」探测' }] } : { error: '请选择媒体文件' },
  pyCode: (v) => {
    const file = str(v.file)
    if (!file) return '# 选择媒体文件后自动生成代码'
    return `"""媒体信息探测（ffprobe）。"""
import json
import os
import shutil
import subprocess

ff = shutil.which("ffprobe")
if not ff:
    raise SystemExit("未找到 ffprobe（brew install ffmpeg）")
raw = subprocess.run(
    [ff, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", ${JSON.stringify(file)}],
    capture_output=True, text=True)
try:
    info = json.loads(raw.stdout)
except json.JSONDecodeError:
    raise SystemExit("无法解析媒体文件（文件损坏或格式不支持）")
f = info.get("format", {})
dur = float(f.get("duration", 0))
rows = [
    {"label": "容器", "value": f.get("format_name", "?")},
    {"label": "时长", "value": f"{int(dur // 60)}m{int(dur % 60):02d}s"},
    {"label": "体积", "value": f"{int(f.get('size', 0)) / 1024 / 1024:.1f} MB"},
    {"label": "码率", "value": f"{int(f.get('bit_rate', 0)) / 1000:.0f} kbps"},
]
for s in info.get("streams", [])[:2]:
    if s.get("codec_type") == "video":
        rows.append({"label": "视频", "value": f"{s.get('codec_name')} {s.get('width')}x{s.get('height')}"})
    elif s.get("codec_type") == "audio":
        rows.append({"label": "音频", "value": f"{s.get('codec_name')} {s.get('sample_rate', '?')} Hz"})
print("<<<JSON>>>")
print(json.dumps({"rows": rows}, ensure_ascii=False))
print("<<<END>>>")
`
  }
}

export const QUICK_SCHEMAS: InteractiveToolSchema[] = [
  ipLookupSchema,
  dnsLookupSchema,
  portCheckSchema,
  httpHeadersSchema,
  speedTestSchema,
  batterySchema,
  diskUsageSchema,
  systemInfoSchema,
  processTopSchema,
  mediaInfoSchema
]
