"""状态码分类：生产级响应处理骨架。"""
import requests

for code in (200, 301, 404, 500):
    resp = requests.get(f"https://httpbin.org/status/{code}", timeout=10, allow_redirects=False)
    kind = ("成功" if resp.status_code < 300
            else "重定向" if resp.status_code < 400
            else "客户端错误" if resp.status_code < 500 else "服务端错误")
    print(f"{code} -> {kind}")
try:
    requests.get("https://httpbin.org/status/404", timeout=10).raise_for_status()
except requests.HTTPError as e:
    print("raise_for_status:", e)
