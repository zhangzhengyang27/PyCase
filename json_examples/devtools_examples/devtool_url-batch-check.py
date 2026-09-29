"""URL 体检：HEAD 批量检查死链。"""
import concurrent.futures
import requests

urls = [
    "https://httpbin.org/status/200",
    "https://httpbin.org/status/404",
    "https://api.github.com",
]

def check(u):
    try:
        return u, requests.head(u, timeout=8, allow_redirects=True).status_code
    except requests.RequestException as e:
        return u, str(type(e).__name__)

with concurrent.futures.ThreadPoolExecutor(8) as pool:
    for url, code in pool.map(check, urls):
        mark = "✓" if isinstance(code, int) and code < 400 else "✗"
        print(f"{mark} {code}  {url}")
