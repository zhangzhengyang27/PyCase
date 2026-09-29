"""Cookie 登录态：从 JSON 文件恢复（配合浏览器导出）。"""
import json
import requests

# cookie 文件格式: [{"name": "sessdata", "value": "...", "domain": ".bilibili.com"}, ...]
SAMPLE = [{"name": "demo_session", "value": "abc123"}]
cookie_file = "cookies.json"
with open(cookie_file, "w", encoding="utf-8") as f:
    json.dump(SAMPLE, f)

s = requests.Session()
for ck in json.load(open(cookie_file)):
    s.cookies.set(ck["name"], ck["value"])
print("已装载 Cookie:", [(c.name, c.value) for c in s.cookies])
resp = s.get("https://httpbin.org/cookies", timeout=10)
print("服务端视角:", resp.json()["cookies"])
