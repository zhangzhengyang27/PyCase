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

# ---- 类型：REST 资源增查删 ----
BOOKS = {1: "Python 基础", 2: "数据可视化"}
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
SRV.shutdown()
