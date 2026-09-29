"""GET 请求基础：httpbin 回显服务演示响应各部分。"""
import requests

resp = requests.get("https://httpbin.org/get", params={"q": "python", "page": 1}, timeout=10)
print("状态码:", resp.status_code)
print("响应头 Content-Type:", resp.headers.get("Content-Type"))
print("编码:", resp.encoding)
data = resp.json()  # httpbin 返回 JSON
print("服务端看到的查询参数:", data["args"])
print("请求 UA:", data["headers"].get("User-Agent", "<未知>")[:40], "...")
