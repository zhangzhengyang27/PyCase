// tool-schemas-crawler-lab.ts：爬虫实验室（crawler/crawler2/crawler3 三个教案系列 62 条归并单页）。
// 57 类型一一对应语料家族（playwright/selenium 需浏览器二进制保持详情兜底；天气/汇率/图片下载
// 已路由到既有真实工具页）。移植口径与 games-lab 相同：类型实现忠实对应语料教学点，差异参数全部页面化。
//
// 离线自播种：公共序章起一个线程化本地 fixture 服务器（JSON API / HTML 页 / 慢端点 / 状态码端点 /
// 登录态 / RSS / m3u8……），字段里的目标 URL 留空 = 抓本地演示服务器（离线可跑通），填真实 URL 则直连
// ——「示例要能真实运行」的产品承诺在断网环境下依然成立；请求失败也按语料口径优雅分类展示。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '').trim()
const int = (v: unknown, def: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, Math.trunc(Number(v) || def)))

// ---------------------------------------------------------------------------
// 公共 Python 序章：requests + 本地 fixture 服务器（全部端点见 _route 分发表）
// ---------------------------------------------------------------------------
const CRAWLER_HEAD = `"""（爬虫实验室生成脚本：留空 URL = 抓本地演示服务器，离线可跑）"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import requests

_FLAKY_HITS = {"n": 0}


class _FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8", headers=None):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _page_html(self, n):
        items = "".join(f'<li class="item"><a href="/page/{n}#i{i}">条目 {n}-{i}</a></li>' for i in range(1, 4))
        return f"<html><head><title>列表页 {n}</title></head><body><ul>{items}</ul></body></html>"

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[-1] for k, v in parse_qs(u.query).items()}
        p = u.path
        if p == "/api/items":
            page = int(q.get("page", 1))
            items = [{"id": (page - 1) * 5 + i, "name": f"物品 {(page - 1) * 5 + i}", "price": round(3.5 + i * 1.2, 2)} for i in range(1, 6)]
            self._send(200, json.dumps({"page": page, "pages": 3, "items": items}, ensure_ascii=False), "application/json")
        elif p == "/flaky":
            _FLAKY_HITS["n"] += 1
            if _FLAKY_HITS["n"] <= int(q.get("fail_until", 2)):
                self._send(503, "service unavailable")
            else:
                self._send(200, json.dumps({"ok": True, "attempt": _FLAKY_HITS["n"]}), "application/json")
        elif p.startswith("/status/"):
            self._send(int(p.split("/")[-1]), f"status {p.split('/')[-1]}")
        elif p == "/download.bin":
            kb = min(int(q.get("kb", 64)), 512)
            self._send(200, bytes(range(256)) * (kb * 1024 // 256), "application/octet-stream")
        elif p == "/slow":
            time.sleep(int(q.get("ms", 3000)) / 1000)
            self._send(200, "finally done")
        elif p == "/robots.txt":
            self._send(200, "User-agent: *\\nDisallow: /private/\\nCrawl-delay: 1\\n", "text/plain")
        elif p == "/etag":
            if self.headers.get("If-None-Match") == '"demo-v1"':
                self._send(304, "")
            else:
                self._send(200, json.dumps({"rev": "demo-v1", "data": [1, 2, 3]}), "application/json", {"ETag": '"demo-v1"'})
        elif p == "/lastmod":
            if self.headers.get("If-Modified-Since") == "Wed, 01 Oct 2025 08:00:00 GMT":
                self._send(304, "")
            else:
                self._send(200, json.dumps({"updated": True}), "application/json", {"Last-Modified": "Wed, 01 Oct 2025 08:00:00 GMT"})
        elif p == "/private/secret":
            self._send(200, "机密内容")
        elif p == "/protected":
            auth = self.headers.get("Authorization", "")
            cookie = self.headers.get("Cookie", "")
            if auth == "Bearer demo-token-123" or "token=demo-token-123" in cookie:
                self._send(200, json.dumps({"secret": "受保护数据"}, ensure_ascii=False), "application/json")
            else:
                self._send(401, "unauthorized")
        elif p == "/page/1" or p == "/page/2" or p == "/page/3":
            self._send(200, self._page_html(int(p.split("/")[-1])))
        elif p == "/quotes":
            rows = "".join(f'<div class="quote"><span class="text">{t}</span><small class="author">{a}</small></div>'
                           for t, a in [("滴水穿石", "佚名"), ("学而时习之", "孔子"), ("兼听则明", "魏征")])
            self._send(200, f"<html><body>{rows}</body></html>")
        elif p == "/table":
            trs = "".join(f"<tr><td>{n}</td><td>{c}</td><td>{p2}</td></tr>"
                          for n, c, p2 in [("键盘", "外设", 199), ("鼠标", "外设", 99), ("显示器", "显示", 999)])
            self._send(200, f"<html><body><table id='goods'>{trs}</table></body></html>")
        elif p == "/feed.xml":
            self._send(200, "<?xml version='1.0'?><rss version='2.0'><channel><title>技术快讯</title>"
                            "<item><title>Python 3.14 发布</title><pubDate>Mon, 01 Sep 2025 09:00:00 GMT</pubDate></item>"
                            "<item><title>pytest 9 新特性</title><pubDate>Tue, 02 Sep 2025 09:00:00 GMT</pubDate></item>"
                            "</channel></rss>", "application/xml")
        elif p == "/data.csv":
            self._send(200, "city,pm25\\n北京,42\\n上海,31\\n广州,18\\n", "text/csv")
        elif p == "/dirty":
            self._send(200, json.dumps({"records": [
                {"name": " alice ", "age": "31", "city": "北京"},
                {"name": "bob", "age": "四十二", "city": "上海"},
                {"name": " alice ", "age": "31", "city": "北京"},
                {"name": "cindy", "age": "25", "city": ""},
            ]}, ensure_ascii=False), "application/json")
        elif p == "/repos/demo/pycase":
            self._send(200, json.dumps({"full_name": "demo/pycase", "stargazers_count": 128, "forks_count": 17,
                                        "language": "Python", "description": "示例仓库"}), "application/json")
        elif p == "/users/1":
            self._send(200, json.dumps({"id": 1, "name": "叶小慕", "email": "demo@example.com"}), "application/json")
        elif p == "/users/1/posts":
            self._send(200, json.dumps([{"id": 101, "user_id": 1, "title": "第一篇"}, {"id": 102, "user_id": 1, "title": "第二篇"}]), "application/json")
        elif p == "/posts/101/comments" or p == "/posts/102/comments":
            pid = int(p.split("/")[2])
            self._send(200, json.dumps([{"id": 9, "post_id": pid, "body": "写得真好"}]), "application/json")
        elif p == "/api/rest_v1/page/summary/Python":
            self._send(200, json.dumps({"title": "Python", "extract": "Python 是一种广泛使用的解释型高级编程语言。",
                                        "content_urls": {"desktop": {"page": "https://example.org/Python"}}}), "application/json")
        elif p == "/echo-headers":
            self._send(200, json.dumps({"seen": dict(self.headers), "order": [k for k in self.headers.keys()]}, ensure_ascii=False), "application/json")
        elif p == "/signed":
            self._send(200, json.dumps({"sig": q.get("sig", ""), "ts": q.get("ts", ""), "verified": q.get("sig") != ""}), "application/json")
        elif p == "/video/index.m3u8":
            self._send(200, "#EXTM3U\\n#EXT-X-TARGETDURATION:4\\n#EXTINF:4.0,\\nseg1.ts\\n#EXTINF:4.0,\\nseg2.ts\\n#EXTINF:2.0,\\nseg3.ts\\n#EXT-X-ENDLIST\\n",
                       "application/vnd.apple.mpegurl")
        elif p.startswith("/video/seg"):
            self._send(200, bytes(range(256)) * 64, "video/mp2t")
        else:
            self._send(404, "not found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        u = urlparse(self.path)
        if u.path == "/login":
            self._send(200, json.dumps({"token": "demo-token-123"}), "application/json",
                       {"Set-Cookie": "token=demo-token-123; Path=/"})
        else:
            self._send(200, json.dumps({"echo": raw, "ctype": self.headers.get("Content-Type", "")}, ensure_ascii=False), "application/json")


SRV = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
threading.Thread(target=SRV.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
`

// ---------------------------------------------------------------------------
// 类型注册表
// ---------------------------------------------------------------------------
export interface CrawlerType {
  value: string
  label: string
  description: string
  fields?: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const F = (key: string, label: string, def = '', help?: string): FieldSpec => ({
  key,
  label,
  type: 'text',
  default: def,
  width: 'half',
  ...(help ? { help } : {})
})
const N = (key: string, label: string, def: number, help?: string): FieldSpec => ({
  key,
  label,
  type: 'number',
  default: def,
  width: 'half',
  ...(help ? { help } : {})
})
const SEL = (key: string, label: string, def: string, opts: string[]): FieldSpec => ({
  key,
  label,
  type: 'select',
  default: def,
  width: 'half',
  options: opts.map((o) => ({ value: o, label: o }))
})
/** 目标 URL 字段：留空 = 本地演示服务器（pyCode 生成 `TARGET = "..." or BASE + <fixture>`） */
const URL_F = () => F('url', '目标 URL（留空 = 本地演示服务器）')

const ct = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): CrawlerType => ({ value, label, description, fields, body })

/** URL 字段的标准解析行：用户填了就直连，留空回落本地 fixture */
const targetLine = (v: Record<string, unknown>, fixture: string): string =>
  `TARGET = ${JSON.stringify(str(v.url))} or BASE + ${JSON.stringify(fixture)}`

export const CRAWLER_TYPES: CrawlerType[] = [
  // ================= 请求与响应 =================
  ct(
    'http-get',
    'GET 请求与响应解读',
    'GET 请求基础：状态码/响应头/编码/JSON 正文各部分的读取与解读。',
    [URL_F()],
    (v) => `${targetLine(v, '/api/items?page=1')}
resp = requests.get(TARGET, params={"q": "python", "page": 1}, timeout=10)
print("状态码:", resp.status_code)
print("响应头 Content-Type:", resp.headers.get("Content-Type"))
print("编码:", resp.encoding)
data = resp.json()
print("服务端看到的查询参数:", json.dumps(resp.request.url.split("?")[-1] if "?" in resp.request.url else "", ensure_ascii=False))
print("正文条目数:", len(data.get("items", [])))
print("首个条目:", json.dumps(data["items"][0], ensure_ascii=False))`
  ),
  ct(
    'http-headers',
    '请求头与 UA 伪装',
    '自定义 User-Agent 与请求头：让请求看起来像浏览器，服务端视角对比。',
    [F('ua', 'User-Agent', 'Mozilla/5.0 (Macintosh) PyCaseDemo/1.0'), URL_F()],
    (v) => `${targetLine(v, '/echo-headers')}
headers = {"User-Agent": ${JSON.stringify(str(v.ua) || 'Mozilla/5.0 PyCaseDemo/1.0')}, "Accept-Language": "zh-CN,zh;q=0.9"}
resp = requests.get(TARGET, headers=headers, timeout=10)
seen = resp.json()["seen"]
print("服务端收到的 UA:", seen.get("User-Agent", "<缺省 requests/***>"))
print("Accept-Language:", seen.get("Accept-Language", "<未携带>"))
print("结论: 不带自定义头时 requests 会自报家门 requests/<版本>")`
  ),
  ct(
    'http-status',
    '状态码分类处理',
    '2xx 成功 / 3xx 跳转 / 4xx 客户端错 / 5xx 服务端错的分支处理表。',
    [SEL('code', '探测状态码', '404', ['200', '301', '403', '404', '500', '503'])],
    (v) => `TARGET = BASE + "/status/${int(v.code, 404, 100, 599)}"
resp = requests.get(TARGET, timeout=10, allow_redirects=False)
code = resp.status_code
family = "2xx 成功" if code < 300 else "3xx 跳转" if code < 400 else "4xx 客户端错误" if code < 500 else "5xx 服务端错误"
print(f"状态码 {code} → {family}")
if code >= 400:
    print("应答动作: 重试/告警/放弃（按业务分级）")
elif code >= 300:
    print("跳转目标:", resp.headers.get("Location", "<无>"))
else:
    print("正文:", resp.text[:40])`
  ),
  ct(
    'http-post',
    'POST 表单提交',
    '表单/JSON 两种 POST 形态，服务端回显验证 payload。',
    [F('name', '昵称', '小叶'), F('comment', '留言', 'PyCase 演示')],
    (v) => `TARGET = ${JSON.stringify(str(v.url))} or BASE + "/echo"
form = {"name": ${JSON.stringify(str(v.name) || '小叶')}, "comment": ${JSON.stringify(str(v.comment) || 'PyCase 演示')}}
r1 = requests.post(TARGET, data=form, timeout=10)
print("表单 POST →", r1.status_code, r1.json()["echo"])
r2 = requests.post(TARGET, json=form, timeout=10)
print("JSON  POST →", r2.status_code, "ctype =", r2.json()["ctype"])
print("两种形态的服务端接收差异：data= 是表单编码，json= 是 application/json")`
  ),
  ct(
    'http-session',
    '会话与 Cookie',
    'requests.Session 登录拿 token → 携带会话访问受保护页。',
    [URL_F()],
    (v) => `${targetLine(v, '/protected')}
s = requests.Session()
login = s.post(BASE + "/login", data={"user": "demo", "pwd": "demo"}, timeout=10)
token = login.json()["token"]
s.headers["Authorization"] = "Bearer " + token
print("登录获得 token:", token)
resp = s.get(TARGET, timeout=10)
print("受保护页状态:", resp.status_code, "（下面裸请求对照应为 401）")
plain = requests.get(TARGET, timeout=10)
print("裸请求状态:", plain.status_code)`
  ),
  ct(
    'http-download',
    '流式下载大文件',
    'stream=True 分块下载，边下边计数，不把大文件整个读进内存。',
    [N('kb', '文件大小（KB）', 128), N('chunk', '分块大小（KB）', 16)],
    (v) => `kb = ${int(v.kb, 128, 8, 512)}
TARGET = ${JSON.stringify(str(v.url))} or BASE + f"/download.bin?kb={kb}"
chunk = ${int(v.chunk, 16, 1, 256)} * 1024
done = 0
with requests.get(TARGET, stream=True, timeout=30) as r:
    r.raise_for_status()
    with open("download.bin", "wb") as f:
        for block in r.iter_content(chunk_size=chunk):
            f.write(block)
            done += len(block)
            print(f"\\r已下载 {done // 1024} KB", end="")
print(f"\\n完成：{done // 1024} KB → download.bin")`
  ),
  ct(
    'http-proxy',
    '代理配置',
    'proxies 字典配置与代理失败（连接拒绝）的优雅处理。',
    [F('proxy', '代理地址', 'http://127.0.0.1:9'), URL_F()],
    (v) => `${targetLine(v, '/api/items?page=1')}
proxies = {"http": ${JSON.stringify(str(v.proxy) || 'http://127.0.0.1:9')}, "https": ${JSON.stringify(str(v.proxy) || 'http://127.0.0.1:9')}}
try:
    resp = requests.get(TARGET, proxies=proxies, timeout=5)
    print("经代理访问 →", resp.status_code)
except requests.exceptions.ProxyError:
    print("代理不可达（演示端点故意用 127.0.0.1:9）→ 降级直连")
    resp = requests.get(TARGET, timeout=10)
    print("直连 →", resp.status_code, "条目数:", len(resp.json()["items"]))`
  ),
  ct(
    'http-retry',
    '超时与重试退避',
    '指数退避重试：目标端点前 N 次返回 503，之后恢复 200。',
    [N('retries', '最大重试', 5), N('fail', '前 N 次失败', 2)],
    (v) => `TARGET = BASE + "/flaky?fail_until=${int(v.fail, 2, 0, 8)}"
max_retries = ${int(v.retries, 5, 1, 10)}
for attempt in range(1, max_retries + 1):
    try:
        resp = requests.get(TARGET, timeout=5)
        if resp.status_code == 200:
            print(f"第 {attempt} 次 → 200 成功:", resp.json())
            break
        raise requests.exceptions.HTTPError(f"HTTP {resp.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
        wait = 2 ** attempt
        print(f"第 {attempt} 次失败（{e}）→ 退避 {wait}s")
        time.sleep(min(wait, 2))
else:
    print(f"重试耗尽（{max_retries} 次后仍 503）→ 放弃本次抓取并记录")`
  ),
  ct(
    'antiban-ua-pool',
    'UA 池轮换',
    '随机 UA 池 + 每次请求换身份，服务端视角验证。',
    [N('size', '池大小', 3)],
    (v) => `import random

random.seed(42)
POOL = ["Mozilla/5.0 (Macintosh) Safari/605", "Mozilla/5.0 (Windows) Firefox/128.0",
        "Mozilla/5.0 (X11) Chrome/126.0", "PyCaseDemo/1.0"][:${int(v.size, 3, 1, 4)}]
for i in range(3):
    ua = random.choice(POOL)
    resp = requests.get(BASE + "/echo-headers", headers={"User-Agent": ua}, timeout=10)
    seen = resp.json()["seen"].get("User-Agent")
    print(f"第 {i + 1} 次请求身份: {seen}")
print("池中身份数:", len(POOL), "——轮换降低单一指纹的封禁概率")`
  ),
  ct(
    'antiban-backoff',
    '退避抖动',
    '指数退避 + 随机抖动（jitter），避免固定间隔被识别为机器人节奏。',
    [N('fail', '前 N 次失败', 2)],
    (v) => `import random

random.seed(7)
TARGET = BASE + "/flaky?fail_until=${int(v.fail, 2, 0, 8)}"
attempt = 0
while attempt < 8:
    attempt += 1
    resp = requests.get(TARGET, timeout=5)
    if resp.status_code == 200:
        print(f"第 {attempt} 次成功:", resp.json())
        break
    base = min(2 ** attempt, 8)
    wait = base * (0.5 + random.random())
    print(f"第 {attempt} 次 {resp.status_code} → 退避 {wait:.1f}s（指数+抖动）")
    time.sleep(min(wait, 2) / 2)`
  ),
  ct(
    'fingerprint',
    '请求指纹与自报家门',
    '服务端视角看默认请求头全集与顺序——理解为什么裸 requests 容易被识别。',
    [URL_F()],
    (v) => `${targetLine(v, '/echo-headers')}
resp = requests.get(TARGET, timeout=10)
data = resp.json()
print("服务端看到的请求头（按到达顺序）:")
for k in data["order"]:
    print(f"  {k}: {str(data['seen'][k])[:60]}")
print("\\n要点: User-Agent 自报 requests/版本、头顺序固定——都是可被指纹化的特征")`
  ),

  // ================= 礼仪与限速 =================
  ct(
    'robots',
    'robots.txt 礼仪',
    '解析 robots.txt 判断路径可抓性，做守规矩的爬虫。',
    [SEL('path', '探测路径', '/private/secret', ['/api/items?page=1', '/private/secret', '/page/1'])],
    (v) => `import urllib.robotparser

rp = urllib.robotparser.RobotFileParser()
rp.parse(requests.get(BASE + "/robots.txt", timeout=10).text.splitlines())
probe = ${JSON.stringify(str(v.path))}
agent, ok = "*", rp.can_fetch("*", "http://demo" + probe)
print("robots.txt: Disallow: /private/，Crawl-delay: 1")
print(f"路径 {probe} 可抓: {ok}")
if not ok:
    print("决定: 跳过该路径（礼仪优先）")
else:
    resp = requests.get(BASE + probe, timeout=10)
    print("抓取 →", resp.status_code, resp.text[:30])`
  ),
  ct(
    'antiban-cookie',
    'Cookie 登录态',
    '手动管理 Cookie：登录拿 Set-Cookie → 原样携带访问受保护页。',
    [URL_F()],
    (v) => `${targetLine(v, '/protected')}
s = requests.Session()
login = s.post(BASE + "/login", data={"user": "demo", "pwd": "demo"}, timeout=10)
print("登录响应 Cookie:", s.cookies.get_dict())
token = login.json()["token"]
# 手动构造带凭据的 Cookie（对比 Session 自动管理）
cookies = {"token": token}
resp = requests.get(TARGET, cookies=cookies, timeout=10)
print("带 Cookie →", resp.status_code)
resp2 = requests.get(TARGET, timeout=10)
print("不带   →", resp2.status_code, "（应 401：凭据缺失）")`
  ),
  ct(
    'throttle-domain',
    '分域限速',
    '每个域名维护上次访问时间，不足间隔就等待——对单域友好、多域并行。',
    [N('gap', '同域间隔（秒）', 0.4)],
    (v) => `gap = ${int(Math.round(Number(v.gap ?? 0.4) * 10), 4, 1, 20) / 10}
LAST_HIT = {}
def polite_get(url):
    from urllib.parse import urlsplit
    domain = urlsplit(url).netloc
    wait = LAST_HIT.get(domain, 0) + gap - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    LAST_HIT[domain] = time.monotonic()
    return requests.get(url, timeout=10)

for n in (1, 2, 3):
    r = polite_get(BASE + f"/page/{n}")
    print(f"/page/{n} → {r.status_code}（同域强制间隔 {gap}s）")
print("多域场景下各域独立计时，互不拖慢")`
  ),
  ct(
    'rate-limit',
    '限速器',
    '令牌速率控制：每分钟最多 N 次请求，超速排队。',
    [N('per_min', '每分钟上限', 30), N('burst', '本次请求数', 5)],
    (v) => `per_min = ${int(v.per_min, 30, 1, 600)}
min_gap = 60.0 / per_min
burst = ${int(v.burst, 5, 1, 20)}
t0 = time.monotonic()
for i in range(burst):
    due = t0 + i * min_gap
    wait = due - time.monotonic()
    if wait > 0:
        time.sleep(min(wait, 0.5))
    resp = requests.get(BASE + "/api/items?page=1", timeout=10)
    print(f"第 {i + 1} 次 → {resp.status_code}")
print(f"限速 {per_min}/min（间隔 {min_gap * 1000:.0f}ms）执行 {burst} 次完毕")`
  ),

  // ================= 解析提取 =================
  ct(
    'parse-json',
    'JSON API 解析',
    'resp.json() 结构化解析：字段读取、缺省兜底、类型校验。',
    [URL_F()],
    (v) => `${targetLine(v, '/api/items?page=1')}
data = requests.get(TARGET, timeout=10).json()
print("顶层键:", list(data.keys()))
for item in data.get("items", []):
    print(f"  #{item.get('id')} {item.get('name', '<无名>')} ¥{item.get('price', 0)}")
print("兜底演示:", data.get("不存在的键", "<默认值>"))`
  ),
  ct(
    'parse-jsonpath',
    '深层嵌套容错',
    '深层 JSON 链式取值：每一层都可能缺失时的安全下钻写法。',
    [URL_F()],
    (v) => `${targetLine(v, '/users/1/posts')}
posts = requests.get(TARGET, timeout=10).json()
first = (posts or [{}])[0]
print("首篇标题:", first.get("title", "<无>"))
pid = first.get("id")
comments = requests.get(BASE + f"/posts/{pid}/comments" if pid else BASE + "/posts/0/comments", timeout=10).json()
body = (comments[0].get("body") if comments else None) or "<空>"
print("首条评论:", body)
# 链式容错范式：每层给默认值，杜绝 KeyError/TypeError
city = ((data := requests.get(BASE + '/users/1', timeout=10).json()) or {}).get("profile", {}).get("city", "未填写")
print("用户城市:", city)`
  ),
  ct(
    'parse-bs4',
    'BeautifulSoup 解析',
    'soup 选择器入门：title / find_all / get_text 的基本盘。',
    [URL_F()],
    (v) => `${targetLine(v, '/page/1')}
from bs4 import BeautifulSoup

html = requests.get(TARGET, timeout=10).text
soup = BeautifulSoup(html, "html.parser")
print("页面标题:", soup.title.string)
items = soup.find_all("li", class_="item")
print(f"列表项 ×{len(items)}:")
for li in items:
    print(" ", li.get_text(strip=True))`
  ),
  ct(
    'parse-find',
    'find/find_all 链式定位',
    'find 收窄范围 → find_all 精取：两级定位的窄化范式。',
    [URL_F()],
    (v) => `${targetLine(v, '/quotes')}
from bs4 import BeautifulSoup

soup = BeautifulSoup(requests.get(TARGET, timeout=10).text, "html.parser")
for box in soup.find_all("div", class_="quote"):
    text = box.find("span", class_="text")
    author = box.find("small", class_="author")
    print(f"「{text.get_text(strip=True)}」—— {author.get_text(strip=True) if author else '佚名'}")`
  ),
  ct(
    'parse-xpath',
    'lxml XPath',
    'lxml.etree 的 XPath 定位：路径表达式与文本提取。',
    [URL_F()],
    (v) => `${targetLine(v, '/page/2')}
from lxml import etree

tree = etree.HTML(requests.get(TARGET, timeout=10).text)
print("标题:", tree.xpath("//title/text()")[0])
links = tree.xpath("//li[@class='item']/a/text()")
print("链接文案:", links)
print("含'条目'的项:", [t for t in links if "条目" in t])`
  ),
  ct(
    'parse-regex',
    '正则批量提取',
    're.findall + 分组批量抽取结构化片段，正则回退兜底解析。',
    [URL_F()],
    (v) => `${targetLine(v, '/page/3')}
import re

html = requests.get(TARGET, timeout=10).text
pairs = re.findall(r'href="([^"]*)"[^>]*>([^<]+)</a>', html)
print(f"提取到 {len(pairs)} 组链接:")
for href, text in pairs:
    print(f"  {text} → {href}")
ids = re.findall(r'/page/(\\d)', html)
print("页码引用:", sorted(set(ids)))`
  ),
  ct(
    'bs4-quotes',
    '名言站点解析',
    '完整小案例：名言+作者结构化抽取（quotes.toscrape 模式）。',
    [URL_F()],
    (v) => `${targetLine(v, '/quotes')}
from bs4 import BeautifulSoup

soup = BeautifulSoup(requests.get(TARGET, timeout=10).text, "html.parser")
rows = []
for q in soup.select("div.quote"):
    rows.append({"quote": q.select_one("span.text").get_text(strip=True),
                 "author": q.select_one("small.author").get_text(strip=True)})
for r in rows:
    print(f"「{r['quote']}」 {r['author']}")
print("共", len(rows), "条（CSS 选择器 select 一次定位两层）")`
  ),
  ct(
    'bs4-table',
    'HTML 表格解析',
    '表格 → 结构化行：表头当键、行变字典，直通后续存储。',
    [URL_F()],
    (v) => `${targetLine(v, '/table')}
from bs4 import BeautifulSoup

soup = BeautifulSoup(requests.get(TARGET, timeout=10).text, "html.parser")
table = soup.find("table", id="goods")
rows = [[td.get_text(strip=True) for td in tr.find_all("td")] for tr in table.find_all("tr")]
print("原始行:", rows)
total = sum(int(r[2]) for r in rows)
print(f"{len(rows)} 类商品，总价 ¥{total}，均价 ¥{total // len(rows)}")`
  ),
  ct(
    'bs4-attr',
    '属性过滤定位',
    '按属性存在/取值过滤节点：attrs 参数与属性选择器。',
    [URL_F()],
    (v) => `${targetLine(v, '/page/1')}
from bs4 import BeautifulSoup

soup = BeautifulSoup(requests.get(TARGET, timeout=10).text, "html.parser")
has_href = soup.find_all("a", href=True)
print("带 href 的链接 ×", len(has_href))
demo = soup.find("a", attrs={"href": "/page/1#i1"})
print("精确属性命中:", demo.get_text(strip=True) if demo else "<无>")
print("模糊 class 命中 ×", len(soup.find_all(class_="item")))`
  ),
  ct(
    'bs4-tree',
    '节点树导航',
    '树系关系：parent / children / next_sibling 在结构化页面上的走法。',
    [URL_F()],
    (v) => `${targetLine(v, '/quotes')}
from bs4 import BeautifulSoup

soup = BeautifulSoup(requests.get(TARGET, timeout=10).text, "html.parser")
first = soup.find("div", class_="quote")
print("父节点:", first.parent.name)
print("子节点序列:", [c.name for c in first.children if getattr(c, "name", None)])
texts = first.find("span", class_="text")
print("同父下的作者:", texts.find_next_sibling("small").get_text(strip=True) if texts else "<无>")`
  ),
  ct(
    'bs4-regex-class',
    '正则 class 匹配',
    'class_=re.compile(...) 一次匹配一族动态类名（item / item-2 / item-hot…）。',
    [URL_F()],
    (v) => `${targetLine(v, '/page/1')}
import re

from bs4 import BeautifulSoup

soup = BeautifulSoup(requests.get(TARGET, timeout=10).text, "html.parser")
hits = soup.find_all(class_=re.compile(r"^item"))
print(f"class 以 item 开头的节点 ×{len(hits)}")
for h in hits[:3]:
    print(" ", h.get("class"), "→", h.get_text(strip=True))`
  ),

  // ================= 并发与抓取策略 =================
  ct(
    'paginate',
    '分页抓取',
    '循环翻页聚合：pages 上限 / 停止条件 / 进度展示。',
    [N('pages', '抓取页数', 3)],
    (v) => `pages = ${int(v.pages, 3, 1, 3)}
all_items = []
for page in range(1, pages + 1):
    data = requests.get(BASE + f"/api/items?page={page}", timeout=10).json()
    all_items.extend(data["items"])
    print(f"第 {page}/{data['pages']} 页 → +{len(data['items'])} 条")
prices = [i["price"] for i in all_items]
print(f"共 {len(all_items)} 条，价格区间 ¥{min(prices)}~¥{max(prices)}")`
  ),
  ct(
    'thread-pool',
    '线程池并发抓取',
    'ThreadPoolExecutor 多线程并发 + as_completed 顺序消费结果。',
    [N('workers', '线程数', 4)],
    (v) => `from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch(n):
    r = requests.get(BASE + f"/page/{n}", timeout=10)
    return n, r.status_code, len(r.text)

workers = ${int(v.workers, 4, 1, 8)}
with ThreadPoolExecutor(max_workers=workers) as pool:
    futures = [pool.submit(fetch, n) for n in (1, 2, 3)]
    for fut in as_completed(futures):
        n, code, size = fut.result()
        print(f"/page/{n} → {code}（{size} 字节）")
print(f"线程池 {workers} 并发抓取 3 页完成")`
  ),
  ct(
    'async-aiohttp',
    'asyncio 异步抓取',
    'aiohttp + asyncio.gather 事件循环并发，与线程池的适用差异。',
    [N('pages', '并发页数', 3)],
    (v) => `import asyncio

import aiohttp

PAGES = ${int(v.pages, 3, 1, 3)}

async def fetch(session, n):
    async with session.get(BASE + f"/page/{n}") as resp:
        return n, resp.status, len(await resp.text())

async def main():
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*(fetch(session, n) for n in range(1, PAGES + 1)))
    for n, code, size in sorted(results):
        print(f"/page/{n} → {code}（{size} 字节）")

asyncio.run(main())
print("异步并发完成：IO 密集场景比线程池更省资源")`
  ),
  ct(
    'incremental',
    '增量抓取指纹',
    '内容指纹（sha256）判变更：没变就跳过，变了才入库。',
    [],
    () => `import hashlib

seen = {}
for path in ("/api/items?page=1", "/quotes", "/api/items?page=1"):
    body = requests.get(BASE + path, timeout=10).content
    fp = hashlib.sha256(body).hexdigest()[:12]
    if seen.get(path) == fp:
        print(f"{path} → 指纹 {fp} 未变，跳过")
    else:
        print(f"{path} → 指纹 {fp} 新/已变更，处理入库")
        seen[path] = fp
print("增量口径：同一内容第二次访问零处理成本")`
  ),
  ct(
    'dedup-queue',
    'URL 去重队列',
    'seen 集合 + FIFO 队列：发现新链接入队、重复链接只处理一次。',
    [],
    () => `from collections import deque

frontier = deque(["/page/1"])
seen = set()
visited = 0
while frontier and visited < 6:
    path = frontier.popleft()
    if path in seen:
        continue
    seen.add(path)
    visited += 1
    html = requests.get(BASE + path, timeout=10).text
    import re
    for link in re.findall(r'href="(/page/\\d[^"]*)"', html):
        frontier.append(link.split("#")[0])
    print(f"访问 {path}，队列 {len(frontier)}，已去重池 {len(seen)}")
print(f"广度优先爬取 {visited} 页，重复链接全部被 seen 挡住")`
  ),
  ct(
    'graceful-shutdown',
    '优雅退出',
    'Ctrl+C 信号与 KeyboardInterrupt 的收尾：保存进度、关闭资源、不丢数据。',
    [N('rounds', '抓取轮数', 6)],
    (v) => `rounds = ${int(v.rounds, 6, 2, 20)}
saved = []
try:
    for i in range(1, rounds + 1):
        time.sleep(0.2)
        saved.append(f"第 {i} 轮结果")
        print(f"\\r进行中 {i}/{rounds}", end="")
except KeyboardInterrupt:
    print("\\n收到中断信号 → 不再发起新请求")
finally:
    print(f"\\n优雅收尾：已保存 {len(saved)} 条进度")
    with open("progress.json", "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False)
print("进度已写 progress.json，下次可断点续抓")`
  ),

  // ================= 存储与清洗 =================
  ct(
    'store-csv',
    '抓取结果存 CSV',
    'csv.DictWriter 落盘 + 回读校验：爬虫数据的第一落点。',
    [],
    () => `import csv

rows = requests.get(BASE + "/api/items?page=1", timeout=10).json()["items"]
with open("items.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "name", "price"])
    w.writeheader()
    w.writerows(rows)
with open("items.csv", encoding="utf-8") as f:
    back = list(csv.DictReader(f))
print(f"写入 {len(rows)} 行 → 回读 {len(back)} 行，首行: {back[0]}")`
  ),
  ct(
    'store-jsonl',
    'JSONL 追加存储',
    '一行一 JSON 的追加式存储：流式抓取的标配落盘形态。',
    [],
    () => `for page in (1, 2):
    items = requests.get(BASE + f"/api/items?page={page}", timeout=10).json()["items"]
    with open("items.jsonl", "a", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\\n")
with open("items.jsonl", encoding="utf-8") as f:
    lines = f.readlines()
print(f"追加两页后共 {len(lines)} 行")
back = json.loads(lines[-1])
print("末行反序列化:", back)`
  ),
  ct(
    'store-sqlite',
    'SQLite 入库',
    '建表 / 参数化插入 / 聚合查询：结构化落库三步走。',
    [],
    () => `import sqlite3

conn = sqlite3.connect("spider.db")
conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, price REAL)")
for page in (1, 2):
    for it in requests.get(BASE + f"/api/items?page={page}", timeout=10).json()["items"]:
        conn.execute("INSERT OR REPLACE INTO items VALUES (?, ?, ?)", (it["id"], it["name"], it["price"]))
conn.commit()
row = conn.execute("SELECT COUNT(*), ROUND(AVG(price), 2) FROM items").fetchone()
print(f"入库 {row[0]} 条，均价 ¥{row[1]}")
print("价格 Top3:", conn.execute("SELECT name, price FROM items ORDER BY price DESC LIMIT 3").fetchall())
conn.close()`
  ),
  ct(
    'dataset-clean',
    '抓取数据清洗',
    '脏数据四板斧：去空白 / 类型转换 / 去重 / 缺省填充。',
    [],
    () => `raw = requests.get(BASE + "/dirty", timeout=10).json()["records"]
print("原始:", len(raw), "条，含空白/非数字年龄/整行重复/缺城市")
clean, seen = [], set()
for r in raw:
    name = r["name"].strip()
    if name in seen:
        continue
    seen.add(name)
    try:
        age = int(r["age"])
    except ValueError:
        age = -1
    clean.append({"name": name, "age": age, "city": r["city"] or "未知"})
print("清洗后:", json.dumps(clean, ensure_ascii=False))`
  ),
  ct(
    'export-report',
    '汇总报表输出',
    '分组聚合 → 对齐文本报表：抓取结果的最终交付形态。',
    [],
    () => `items = []
for page in (1, 2, 3):
    items.extend(requests.get(BASE + f"/api/items?page={page}", timeout=10).json()["items"])
buckets = {}
for it in items:
    tier = "高价" if it["price"] >= 8 else "中价" if it["price"] >= 5 else "低价"
    buckets.setdefault(tier, []).append(it)
print("价位     数量   均价")
for tier in ("高价", "中价", "低价"):
    group = buckets.get(tier, [])
    if group:
        avg = sum(i["price"] for i in group) / len(group)
        print(f"{tier:6} {len(group):4d} {avg:8.2f}")
print(f"合计 {len(items)} 条，输出报表 report.txt")
with open("report.txt", "w", encoding="utf-8") as f:
    f.write(json.dumps({k: len(v) for k, v in buckets.items()}, ensure_ascii=False))`
  ),
  ct(
    'pandas-clean',
    'pandas 数据清洗',
    'DataFrame 接住脏数据：strip/转数值/去重/填充一条龙 + 分组统计。',
    [],
    () => `import pandas as pd

raw = requests.get(BASE + "/dirty", timeout=10).json()["records"]
df = pd.DataFrame(raw)
df["name"] = df["name"].str.strip()
df["age"] = pd.to_numeric(df["age"], errors="coerce")
df = df.drop_duplicates(subset="name").fillna({"age": 0, "city": "未知"})
print(df.to_string(index=False))
print("年龄均值:", round(df["age"].mean(), 1), "（非数字年龄已被 coerce 为空再填充）")`
  ),
  ct(
    'rss',
    'RSS 订阅解析',
    'xml.etree 解析 RSS 频道：频道信息 + 条目列表标准读法。',
    [],
    () => `import xml.etree.ElementTree as ET

resp = requests.get(BASE + "/feed.xml", timeout=10)
root = ET.fromstring(resp.content)
channel = root.find("channel")
print("频道:", channel.findtext("title"))
for item in channel.findall("item"):
    print(" -", item.findtext("title"), "|", item.findtext("pubDate"))`
  ),
  ct(
    'xml-ns',
    '带命名空间的 XML',
    '命名空间 XML 的正确打开方式：注册前缀再按前缀取路径。',
    [],
    () => `import xml.etree.ElementTree as ET

NS = {"dc": "http://purl.org/dc/elements/1.1/"}
sample = "<?xml version='1.0'?><rss version='2.0' xmlns:dc=\\"http://purl.org/dc/elements/1.1/\\">" \\
         "<channel><title>快讯</title>" \\
         "<item><title>条目一</title><dc:creator>小叶</dc:creator></item></channel></rss>"
root = ET.fromstring(sample)
print("标题:", root.findtext("channel/title"))
creator = root.findtext("channel/item/dc:creator", namespaces=NS)
print("dc:creator（命名空间路径）:", creator)`
  ),

  // ================= 工程化 =================
  ct(
    'eng-logging',
    '抓取日志',
    'logging 模块配置：格式/级别/落文件，生产爬虫的可观测性地基。',
    [],
    () => `import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", filename="spider.log", filemode="w")
log = logging.getLogger("spider")
for page in (1, 2, 3):
    r = requests.get(BASE + f"/page/{page}", timeout=10)
    log.info("GET /page/%d -> %d (%d bytes)", page, r.status_code, len(r.text))
log.warning("演示一条警告：限流临近")
print("已写 spider.log：")
print(open("spider.log", encoding="utf-8").read())`
  ),
  ct(
    'eng-config-dataclass',
    '爬虫配置类',
    'dataclass 集中管理配置：超时/重试/UA 一处声明，处处消费。',
    [N('timeout', '超时（秒）', 10), N('retries', '重试次数', 3)],
    (v) => `from dataclasses import dataclass

@dataclass
class CrawlerConfig:
    base_url: str
    timeout: int = ${int(v.timeout, 10, 1, 60)}
    retries: int = ${int(v.retries, 3, 1, 10)}
    user_agent: str = "PyCaseDemo/1.0"

cfg = CrawlerConfig(BASE)
print("配置:", cfg)
s = requests.Session()
s.headers["User-Agent"] = cfg.user_agent
r = s.get(cfg.base_url + "/api/items?page=1", timeout=cfg.timeout)
print(f"按配置抓取 → {r.status_code}（timeout={cfg.timeout}s, retries={cfg.retries}）")`
  ),
  ct(
    'eng-cli',
    '命令行入口',
    'argparse 构造可复用的抓取脚本入口：参数/默认值/帮助文案。',
    [N('pages', '--pages', 2), F('keyword', '--keyword', '爬虫')],
    (v) => `import argparse

# 生成脚本等价于: python crawler_cli.py --pages ${int(v.pages, 2, 1, 3)} --keyword ${JSON.stringify(str(v.keyword) || '爬虫')}
parser = argparse.ArgumentParser(description="通用抓取脚本骨架")
parser.add_argument("--pages", type=int, default=${int(v.pages, 2, 1, 3)}, help="抓取页数")
parser.add_argument("--keyword", default=${JSON.stringify(str(v.keyword) || '爬虫')}, help="过滤关键词")
parser.add_argument("--output", default="out.jsonl", help="输出文件")
args = parser.parse_args()
print(f"计划抓取 {args.pages} 页，关键词={args.keyword or '无'}，输出={args.output}")
rows = []
for page in range(1, args.pages + 1):
    data = requests.get(BASE + f"/api/items?page={page}", timeout=10).json()
    hits = [i for i in data["items"] if args.keyword in i["name"]] or data["items"]
    rows.extend(hits)
    print(f"  第 {page} 页完成，命中 {len(hits)}/{len(data['items'])} 条")
with open(args.output, "w", encoding="utf-8") as f:
    f.write(json.dumps(rows, ensure_ascii=False))
print(f"落盘 {len(rows)} 条 → {args.output}")`
  ),
  ct(
    'checkpoint',
    '断点续抓',
    '检查点文件：每页落 state.json，重启后从断点继续而不是从头来。',
    [],
    () => `import os

STATE = "state.json"
state = {"done": [], "last_page": 0}
if os.path.exists(STATE):
    state = json.load(open(STATE, encoding="utf-8"))
    print(f"发现断点：已完成 {state['last_page']} 页，续抓")
for page in range(state["last_page"] + 1, 4):
    data = requests.get(BASE + f"/api/items?page={page}", timeout=10).json()
    state["done"].extend(data["items"])
    state["last_page"] = page
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"第 {page} 页完成并写检查点")
print(f"累计 {len(state['done'])} 条；再次运行会直接报告已完成")`
  ),
  ct(
    'structure',
    '爬虫项目结构',
    '工程化目录骨架：spiders/pipelines/storage 分层 + 入口收敛，一键生成。',
    [],
    () => `import os

TREE = {"my_spider/spiders/__init__.py": "", "my_spider/pipelines/__init__.py": "", "my_spider/storage/__init__.py": ""}
TREE["my_spider/spiders/demo.py"] = "from my_spider.pipelines import save\\n\\ndef crawl():\\n    save([1, 2, 3])\\n"
TREE["my_spider/pipelines/__init__.py"] = "def save(rows):\\n    print('入库', len(rows), '条')\\n"
TREE["my_spider/main.py"] = "from my_spider.spiders.demo import crawl\\n\\nif __name__ == '__main__':\\n    crawl()\\n"
for path, content in TREE.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
for root, dirs, files in os.walk("my_spider"):
    level = root.count(os.sep)
    print("  " * level + os.path.basename(root) + "/")
    for fn in files:
        print("  " * (level + 1) + fn)`
  ),
  ct(
    'test-spider',
    '爬虫单测',
    '解析逻辑与请求分离后可单测：unittest 跑解析器用例（不发网络请求）。',
    [],
    () => `import sys
import unittest

from bs4 import BeautifulSoup

def parse_items(html):
    soup = BeautifulSoup(html, "html.parser")
    return [li.get_text(strip=True) for li in soup.find_all("li", class_="item")]

html = requests.get(BASE + "/page/1", timeout=10).text

class TestParse(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(parse_items(html)), 3)

    def test_text(self):
        self.assertTrue(all("条目" in t for t in parse_items(html)))

    def test_empty(self):
        self.assertEqual(parse_items("<html></html>"), [])

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestParse)
unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)`
  ),
  ct(
    'mini-framework',
    '迷你爬虫框架',
    'Spider 基类 + 子类注册 + 引擎调度：40 行看懂 Scrapy 的骨架思想。',
    [],
    () => `class Spider:
    start_paths = ()

    def parse(self, resp):
        raise NotImplementedError

class ItemSpider(Spider):
    start_paths = ("/api/items?page=1",)

    def parse(self, resp):
        return [i["name"] for i in resp.json()["items"]]

class QuoteSpider(Spider):
    start_paths = ("/quotes",)

    def parse(self, resp):
        import re
        return re.findall(r'class="text">([^<]+)<', resp.text)

def run(spider_cls):
    spider = spider_cls()
    out = []
    for path in spider.start_paths:
        out.extend(spider.parse(requests.get(BASE + path, timeout=10)))
    print(f"{spider_cls.__name__}: {out}")

run(ItemSpider)
run(QuoteSpider)`
  ),
  ct(
    'scheduler',
    '定时抓取',
    'apscheduler 间隔调度：有限轮次演示 + 优雅 shutdown（真实部署改 cron 触发）。',
    [N('rounds', '执行轮次', 2)],
    (v) => `rounds = ${int(v.rounds, 2, 1, 5)}
from apscheduler.schedulers.blocking import BlockingScheduler

count = {"n": 0}
sched = BlockingScheduler()

@sched.scheduled_job("interval", seconds=1, id="demo")
def tick():
    count["n"] += 1
    r = requests.get(BASE + "/api/items?page=1", timeout=10)
    print(f"第 {count['n']} 轮定时抓取 → {r.status_code}")
    if count["n"] >= rounds:
        sched.shutdown(wait=False)

sched.start()
print(f"调度器已停止（演示跑满 {rounds} 轮）")`
  ),
  ct(
    'health-check',
    '抓取健康监控',
    '批量探活 + 延迟统计 + 异常端点标记：给爬虫配个体检面板。',
    [],
    () => `endpoints = ["/api/items?page=1", "/quotes", "/table", "/status/404", "/status/500"]
print("端点                     状态  延迟")
for ep in endpoints:
    t0 = time.monotonic()
    try:
        r = requests.get(BASE + ep, timeout=5)
        ms = (time.monotonic() - t0) * 1000
        flag = "OK" if r.status_code == 200 else "异常"
        print(f"{ep:22} {r.status_code}  {ms:5.0f}ms  {flag}")
    except requests.exceptions.RequestException as e:
        print(f"{ep:22} ERR   —      {type(e).__name__}")`
  ),
  ct(
    'etag',
    'ETag 条件请求',
    'If-None-Match 协商缓存：内容没变服务端回 304，省流量省算力。',
    [],
    () => `s = requests.Session()
r1 = s.get(BASE + "/etag", timeout=10)
etag = r1.headers["ETag"]
print("首次:", r1.status_code, "| ETag:", etag, "| 数据:", r1.json()["data"])
r2 = s.get(BASE + "/etag", headers={"If-None-Match": etag}, timeout=10)
print("二次:", r2.status_code, "（304 = 未变更，正文为空）")
if r2.status_code == 304:
    print("使用本地缓存:", r1.json()["data"], "→ 零下载成本")`
  ),
  ct(
    'lastmod',
    'Last-Modified 增量',
    'If-Modified-Since 按时间协商：老资源 304 秒回，增量抓取的另一半。',
    [],
    () => `s = requests.Session()
r1 = s.get(BASE + "/lastmod", timeout=10)
lm = r1.headers["Last-Modified"]
print("首次:", r1.status_code, "| Last-Modified:", lm)
r2 = s.get(BASE + "/lastmod", headers={"If-Modified-Since": lm}, timeout=10)
print("二次:", r2.status_code, "→" if r2.status_code == 304 else "！内容有更新")
print("结论: ETag 按内容、Last-Modified 按时间，两者常配合使用")`
  ),

  // ================= 真实目标 API =================
  ct(
    'github-api',
    'GitHub API 实战',
    '仓库信息拉取：REST 形态 / 分页头 / 限流头的标准消费姿势（演示端点为本地仿真）。',
    [F('owner', 'owner', 'demo'), F('repo', 'repo', 'pycase')],
    (v) => `owner = ${JSON.stringify(str(v.owner) || 'demo')}
repo = ${JSON.stringify(str(v.repo) || 'pycase')}
TARGET = ${JSON.stringify(str(v.url))} or BASE + f"/repos/{owner}/{repo}"
r = requests.get(TARGET, timeout=10)
data = r.json()
print(f"{data['full_name']} ★{data['stargazers_count']} fork {data['forks_count']} 语言 {data['language']}")
print("限流头:", r.headers.get("X-RateLimit-Remaining", "仿真端点未下发"))
print("真实用法: TARGET = 'https://api.github.com/repos/' + owner + '/' + repo")`
  ),
  ct(
    'relations',
    '关联资源抓取',
    '用户 → 帖子 → 评论三级关联链：REST 关联资源逐层下钻。',
    [N('user', '用户 id', 1)],
    (v) => `uid = ${int(v.user, 1, 1, 1)}
user = requests.get(BASE + f"/users/{uid}", timeout=10).json()
print("用户:", user["name"], user["email"])
posts = requests.get(BASE + f"/users/{uid}/posts", timeout=10).json()
for p in posts:
    comments = requests.get(BASE + f"/posts/{p['id']}/comments", timeout=10).json()
    print(f"  帖子「{p['title']}」← {len(comments)} 条评论")
print(f"共 {len(posts)} 篇帖子（真实场景建议并发生成评论请求）")`
  ),
  ct(
    'wikipedia-api',
    'Wikipedia API',
    'REST 摘要端点消费：extract / content_urls 字段与 UA 礼仪（本地仿真）。',
    [F('term', '词条', 'Python')],
    (v) => `term = ${JSON.stringify(str(v.term) || 'Python')}
TARGET = ${JSON.stringify(str(v.url))} or BASE + f"/api/rest_v1/page/summary/{term}"
r = requests.get(TARGET, headers={"User-Agent": "PyCaseDemo/1.0 (edu)"}, timeout=10)
data = r.json()
print("词条:", data["title"])
print("摘要:", data["extract"][:60], "…")
print("桌面端链接:", data["content_urls"]["desktop"]["page"])
print("真实用法: TARGET = 'https://zh.wikipedia.org/api/rest_v1/page/summary/' + term")`
  ),
  ct(
    'hmac-sign',
    'API 签名（HMAC）',
    '请求签名：path+时间戳用密钥算 HMAC，服务端同法校验——开放 API 的鉴权地基。',
    [F('secret', '密钥', 'demo-secret')],
    (v) => `import hashlib
import hmac

SECRET = ${JSON.stringify(str(v.secret) || 'demo-secret')}
path, ts = "/api/items?page=1", str(int(time.time()))
payload = path + ts
sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
print("待签内容:", payload)
print("HMAC 签名:", sig[:32], "…")
r = requests.get(BASE + "/signed", params={"ts": ts, "sig": sig[:8] + "…"}, timeout=10)
print("服务端回执:", r.json())
print("真实服务端会用同一密钥重算 HMAC 比对——密钥永不上网")`
  ),
  ct(
    'm3u8',
    'm3u8 视频分段模式',
    '拉索引 → 解析分段清单 → 逐段下载：流媒体视频的通用形态。',
    [],
    () => `index = requests.get(BASE + "/video/index.m3u8", timeout=10).text
segs = [ln.strip() for ln in index.splitlines() if ln.strip() and not ln.startswith("#")]
print("分段清单:", segs)
total = 0
for i, seg in enumerate(segs, 1):
    body = requests.get(BASE + "/video/" + seg, timeout=10).content
    total += len(body)
    print(f"  seg{i} {len(body)} 字节")
print(f"共 {len(segs)} 段 / {total // 1024} KB（真实场景再按二进制合并为视频文件）")`
  ),
  ct(
    'websocket',
    'WebSocket 行情流',
    '订阅/消费模式演示：消息结构、心跳与断线重连思路（演示数据本地生成）。',
    [N('msgs', '演示消息数', 3)],
    (v) => `n = ${int(v.msgs, 3, 1, 8)}
SAMPLE = [{"channel": "trades", "data": {"price": 64500.1 + i * 1.4, "side": "buy" if i % 2 else "sell"}} for i in range(n)]
print("订阅 trades 频道 → 消费", n, "条演示消息")
best = 0
for msg in SAMPLE:
    d = msg["data"]
    best = max(best, d["price"])
    print(f"  {d['side']:4} @ {d['price']}")
print("区间最高价:", best)
print("真实写法: from websocket import create_connection; ws = create_connection('wss://…')")`
  )
]

// ---------------------------------------------------------------------------
// 爬虫实验室：57 家族归并单页（类型选择器 + 动态参数表单，与 games-lab 同构）
// ---------------------------------------------------------------------------
const CRAWLER_TYPE_FIELD: FieldSpec = {
  key: 'type',
  label: '爬虫类型',
  type: 'select',
  default: 'http-get',
  width: 'full',
  options: CRAWLER_TYPES.map((t) => ({ value: t.value, label: t.label }))
}

export const crawlerLabSchema: InteractiveToolSchema = {
  id: 'interactive:crawler-lab',
  title: '爬虫实验室',
  description:
    '请求/礼仪/解析/并发/存储/工程化/真实目标 API 七组 57 个类型：生成的脚本默认抓本地演示服务器，离线可跑通；填入真实 URL 即直连目标站。',
  tags: ['爬虫', '网络'],
  fields: (v) => {
    const t = CRAWLER_TYPES.find((x) => x.value === v.type) ?? CRAWLER_TYPES[0]!
    return [CRAWLER_TYPE_FIELD, ...(t.fields ?? [])]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '类型', value: String(v.type ?? 'http-get') }] }),
  headerFor: (v) => {
    const t = CRAWLER_TYPES.find((x) => x.value === v.type) ?? CRAWLER_TYPES[0]!
    return { title: t.label, description: t.description }
  },
  pyCode: (v) => {
    const t = CRAWLER_TYPES.find((x) => x.value === v.type) ?? CRAWLER_TYPES[0]!
    return `${CRAWLER_HEAD}\n# ---- 类型：${t.label} ----\n${t.body(v)}\n`
  }
}
