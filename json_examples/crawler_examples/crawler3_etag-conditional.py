"""ETag 条件请求：内容未变时 304，省流量。"""
import requests

cache = {"etag": None, "body": None}
url = "https://httpbin.org/etag/w3s4all"
headers = {"If-None-Match": cache["etag"]} if cache["etag"] else {}
resp = requests.get(url, headers=headers, timeout=10)
if resp.status_code == 304:
    print("内容未变（304），使用缓存")
else:
    cache["etag"] = resp.headers.get("ETag")
    cache["body"] = resp.text
    print("新内容已缓存，ETag =", cache["etag"])
