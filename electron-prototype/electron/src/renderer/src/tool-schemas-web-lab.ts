// tool-schemas-web-lab.ts：Web 开发实验室（新域，10 类型 = 语料 web_examples 一一对应母本）。
// 全部离线：stdlib http.server + requests 本地闭环，运行结束自动收尾。
// 结构：head 提供路由基座（BaseHandler + serve 工厂），body 定义 Handler 子类后启动再自请求——
// 服务必须在子类定义之后启动，否则路由永不生效（首版曾把启动放 head 而全类型 404）。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const str = (v: unknown): string => String(v ?? '').trim()
const int = (v: unknown, def: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, Math.trunc(Number(v) || def)))

const WEB_HEAD = `"""（Web 实验室生成脚本：http.server + requests 本地闭环，离线可跑）"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import requests


class BaseHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8", headers=None):
        data = body if isinstance(body, bytes) else str(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[-1] for k, v in parse_qs(u.query).items()}
        self._get(u.path, q)

    def do_POST(self):
        u = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        self._post(u.path, raw, self.headers.get("Content-Type", ""))

    def _get(self, path, q):
        self._send(404, "404 Not Found")

    def _post(self, path, raw, ctype):
        self._send(404, "404 Not Found")


def serve(handler_cls):
    """启动线程化本地服务，返回实例（BASE 由 server_address 推出）"""
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
`

const F = (key: string, label: string, def = ''): FieldSpec => ({
  key,
  label,
  type: 'text',
  default: def,
  width: 'half'
})
const N = (key: string, label: string, def: number): FieldSpec => ({
  key,
  label,
  type: 'number',
  default: def,
  width: 'half'
})

export interface WebType {
  value: string
  label: string
  description: string
  fields?: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const wt = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): WebType => ({ value, label, description, fields, body })

export const WEB_TYPES: WebType[] = [
  wt(
    'hello-server',
    '最小 HTTP 服务',
    'http.server 起服务 → 自请求 → 关停：Web 服务的最小闭环。',
    [F('message', '首页文案', '你好，Web！')],
    (v) => `class Handler(BaseHandler):
    def _get(self, path, q):
        if path == "/":
            self._send(200, ${JSON.stringify(str(v.message) || '你好，Web！')})

SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
resp = requests.get(BASE + "/", timeout=5)
print("状态:", resp.status_code, "| 正文:", resp.text)
SRV.shutdown()
print("服务已优雅关停")`
  ),
  wt(
    'routes',
    '路由分发',
    'path → handler 字典路由表：一个服务多个端点的组织方式。',
    [],
    () => `def home():
    return 200, "首页"

def about():
    return 200, "关于本站"

ROUTES = {"/": home, "/about": about}

class Handler(BaseHandler):
    def _get(self, path, q):
        handler = ROUTES.get(path)
        if handler:
            self._send(*handler())
        else:
            self._send(404, f"路由 {path} 未注册")

SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
for p in ("/", "/about", "/nope"):
    r = requests.get(BASE + p, timeout=5)
    print(f"{p} → {r.status_code} {r.text}")
SRV.shutdown()`
  ),
  wt(
    'query-params',
    '查询参数解析',
    'parse_qs 解析查询串：多值参数与默认值兜底。',
    [F('kw', '搜索词', 'python')],
    (v) => `class Handler(BaseHandler):
    def _get(self, path, q):
        if path == "/search":
            kw = q.get("kw", "")
            page = int(q.get("page", "1"))
            self._send(200, json.dumps({"kw": kw, "page": page}, ensure_ascii=False), "application/json")

SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
r = requests.get(BASE + "/search", params={"kw": ${JSON.stringify(str(v.kw) || 'python')}, "page": 2}, timeout=5)
print("服务端解析结果:", r.json())
SRV.shutdown()`
  ),
  wt(
    'json-api',
    'JSON API 端点',
    '返回 JSON 的 API 端点：Content-Type 与数据结构约定。',
    [N('count', '返回条数', 3)],
    (v) => `ITEMS = [{"id": i, "name": f"物品{i}"} for i in range(1, 6)]

class Handler(BaseHandler):
    def _get(self, path, q):
        if path == "/api/items":
            self._send(200, json.dumps({"items": ITEMS[: int(q.get("count", "3"))]}, ensure_ascii=False),
                       "application/json")

count = ${int(v.count, 3, 1, 5)}
SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
r = requests.get(BASE + "/api/items", params={"count": count}, timeout=5)
print("Content-Type:", r.headers.get("Content-Type"))
print("数据:", r.json()["items"])
SRV.shutdown()`
  ),
  wt(
    'post-form',
    '表单接收',
    'do_POST 解析 urlencoded 表单：服务端回执与校验。',
    [F('username', '用户名', '小叶')],
    (v) => `from urllib.parse import parse_qs as parse_body

class Handler(BaseHandler):
    def _post(self, path, raw, ctype):
        if path == "/login":
            form = {k: v[-1] for k, v in parse_body(raw).items()}
            ok = bool(form.get("username") and form.get("pwd"))
            self._send(200, json.dumps({"user": form.get("username"), "login": ok}, ensure_ascii=False),
                       "application/json")

SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
r = requests.post(BASE + "/login", data={"username": ${JSON.stringify(str(v.username) || '小叶')}, "pwd": "secret"}, timeout=5)
print("服务端回执:", r.json())
SRV.shutdown()`
  ),
  wt(
    'static-files',
    '静态文件服务',
    'SimpleHTTPRequestHandler 托管目录：把本地文件夹变成网站。',
    [],
    () => `import functools
import os
import tempfile
from http.server import SimpleHTTPRequestHandler

docroot = tempfile.mkdtemp(prefix="web-static-")
with open(os.path.join(docroot, "index.html"), "w", encoding="utf-8") as f:
    f.write("<h1>静态页</h1><p>由 SimpleHTTPRequestHandler 托管</p>")

Static = functools.partial(SimpleHTTPRequestHandler, directory=docroot)
SRV = serve(Static)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
r = requests.get(BASE + "/index.html", timeout=5)
print("状态:", r.status_code)
print("正文:", r.text)
print("Content-Type:", r.headers.get("Content-Type"))
SRV.shutdown()`
  ),
  wt(
    'error-pages',
    '错误页与异常',
    '404/500 的统一错误响应：状态码语义与客户端分支。',
    [],
    () => `class Handler(BaseHandler):
    def _get(self, path, q):
        if path == "/boom":
            self._send(500, "服务器内部错误")
        else:
            self._send(404, "页面不存在")

SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
for p in ("/missing", "/boom"):
    r = requests.get(BASE + p, timeout=5)
    verdict = "客户端应提示重试/回首页" if r.status_code == 404 else "客户端应告警并保留现场"
    print(f"{p} → {r.status_code}（{r.text}）→ {verdict}")
r = requests.get(BASE + "/missing", timeout=5)
try:
    r.raise_for_status()
except requests.exceptions.HTTPError as e:
    print("raise_for_status 抛出:", type(e).__name__)
SRV.shutdown()`
  ),
  wt(
    'headers-cookies',
    '响应头与 Set-Cookie',
    '自定义响应头与 Cookie 下发：会话保持的第一步。',
    [F('session', '会话 id', 'sess-9527')],
    (v) => `class Handler(BaseHandler):
    def _get(self, path, q):
        if path == "/login":
            self._send(200, "已登录", headers={
                "X-Request-Id": "req-1",
                'Set-Cookie': 'session=' + ${JSON.stringify(str(v.session) || 'sess-9527')} + '; Path=/',
            })
        elif path == "/me":
            self._send(200, "你的会话: " + (self.headers.get("Cookie") or "<无>"))

SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
s = requests.Session()
r1 = s.get(BASE + "/login", timeout=5)
print("登录响应头 X-Request-Id:", r1.headers.get("X-Request-Id"))
print("Set-Cookie:", r1.headers.get("Set-Cookie"))
r2 = s.get(BASE + "/me", timeout=5)
print("会话自动携带 →", r2.text)
SRV.shutdown()`
  ),
  wt(
    'rest-crud',
    'REST 资源增查删',
    '内存资源表上的 GET/POST/DELETE：REST 风格最小实现。',
    [],
    () => `BOOKS = {1: "Python 基础", 2: "数据可视化"}
NEXT_ID = {"n": 3}

class Handler(BaseHandler):
    def _get(self, path, q):
        if path == "/books":
            self._send(200, json.dumps(BOOKS, ensure_ascii=False), "application/json")

    def _post(self, path, raw, ctype):
        if path == "/books":
            title = json.loads(raw)["title"]
            BOOKS[NEXT_ID["n"]] = title
            NEXT_ID["n"] += 1
            self._send(201, json.dumps({"id": NEXT_ID["n"] - 1}, ensure_ascii=False), "application/json")

    def do_DELETE(self):
        bid = int(urlparse(self.path).path.split("/")[-1])
        BOOKS.pop(bid, None)
        self._send(204, "")

SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
print("当前:", requests.get(BASE + "/books", timeout=5).json())
new_id = requests.post(BASE + "/books", json={"title": "Flask 入门"}, timeout=5).json()["id"]
print("新增 id:", new_id)
requests.delete(BASE + "/books/1", timeout=5)
print("删除 1 号后:", requests.get(BASE + "/books", timeout=5).json())
SRV.shutdown()`
  ),
  wt(
    'client-server',
    '客户端服务端闭环',
    '同一脚本里同时扮演服务端与客户端：理解请求/响应的完整往返。',
    [],
    () => `HITS = {"n": 0}

class Handler(BaseHandler):
    def _get(self, path, q):
        if path == "/counter":
            HITS["n"] += 1
            self._send(200, json.dumps({"visits": HITS["n"]}, ensure_ascii=False), "application/json")

SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
for i in range(3):
    r = requests.get(BASE + "/counter", timeout=5)
    print(f"第 {i + 1} 次请求 → 服务端计数 {r.json()['visits']}")
print("\\n要点：服务端状态独立于客户端，3 次请求共享同一个计数器")
SRV.shutdown()`
  )
]

const WEB_TYPE_FIELD: FieldSpec = {
  key: 'type',
  label: 'Web 类型',
  type: 'select',
  default: 'hello-server',
  width: 'full',
  options: WEB_TYPES.map((t) => ({ value: t.value, label: t.label }))
}

export const webLabSchema: InteractiveToolSchema = {
  id: 'interactive:web-lab',
  title: 'Web 开发实验室',
  description:
    'http.server 十个类型：最小服务/路由/查询参数/JSON API/表单/静态托管/错误页/Cookie/REST/客户端服务端闭环，本地服务离线可跑。',
  tags: ['Web开发', 'http'],
  fields: (v) => {
    const t = WEB_TYPES.find((x) => x.value === v.type) ?? WEB_TYPES[0]!
    return [WEB_TYPE_FIELD, ...(t.fields ?? [])]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '类型', value: String(v.type ?? 'hello-server') }] }),
  headerFor: (v) => {
    const t = WEB_TYPES.find((x) => x.value === v.type) ?? WEB_TYPES[0]!
    return { title: t.label, description: t.description }
  },
  pyCode: (v) => {
    const t = WEB_TYPES.find((x) => x.value === v.type) ?? WEB_TYPES[0]!
    return `${WEB_HEAD}\n# ---- 类型：${t.label} ----\n${t.body(v)}\n`
  }
}
