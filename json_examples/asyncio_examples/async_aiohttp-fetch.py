"""（并发实验室生成脚本：stdlib asyncio，离线可跑，有限轮次收尾）"""
import asyncio
import time

# ---- 类型：aiohttp 并发抓取 ----
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = "http://127.0.0.1:" + str(srv.server_address[1])

import aiohttp

n = 4

async def fetch(session, i):
    async with session.get(base + f"/p{i}") as resp:
        return i, resp.status

async def main():
    async with aiohttp.ClientSession() as s:
        results = await asyncio.gather(*(fetch(s, i) for i in range(n)))
    print("并发抓取结果:", sorted(results))

asyncio.run(main())
srv.shutdown()
