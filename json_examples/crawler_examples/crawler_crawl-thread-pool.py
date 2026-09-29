"""并发抓取：线程池 + as_completed 收集结果。"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

urls = [f"https://httpbin.org/delay/1/{i}" for i in range(5)]

def fetch(url):
    resp = requests.get(url, timeout=15)
    return url, resp.status_code

with ThreadPoolExecutor(max_workers=5) as pool:
    futures = [pool.submit(fetch, u) for u in urls]
    for fut in as_completed(futures):
        url, code = fut.result()
        print(f"{code} {url[-14:]}")
