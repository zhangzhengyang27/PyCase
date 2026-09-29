"""Last-Modified：按修改时间增量抓取。"""
import requests

since = "Sat, 20 Sep 2026 00:00:00 GMT"
resp = requests.get("https://httpbin.org/response-headers",
                    params={"Last-Modified": since}, timeout=10)
print("响应 Last-Modified:", resp.headers.get("Last-Modified"))
print("真实场景：本地存时间戳，未变更则跳过解析")
