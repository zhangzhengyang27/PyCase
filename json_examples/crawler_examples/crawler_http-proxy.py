"""代理：企业内网/爬虫池的接入口径。"""
import requests

proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}
try:
    resp = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
    print("出口 IP:", resp.json())
except requests.RequestException as e:
    print("代理不可达（本机未开 7890 端口属正常）:", type(e).__name__)
