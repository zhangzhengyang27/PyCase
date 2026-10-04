"""（Web 实验室生成脚本：http.server + requests 本地闭环，离线可跑）"""
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

# ---- 类型：表单接收 ----
from urllib.parse import parse_qs as parse_body

class Handler(BaseHandler):
    def _post(self, path, raw, ctype):
        if path == "/login":
            form = {k: v[-1] for k, v in parse_body(raw).items()}
            ok = bool(form.get("username") and form.get("pwd"))
            self._send(200, json.dumps({"user": form.get("username"), "login": ok}, ensure_ascii=False),
                       "application/json")

SRV = serve(Handler)
BASE = "http://127.0.0.1:" + str(SRV.server_address[1])
r = requests.post(BASE + "/login", data={"username": "小叶", "pwd": "secret"}, timeout=5)
print("服务端回执:", r.json())
SRV.shutdown()
