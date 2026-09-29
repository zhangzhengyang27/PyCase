"""POST 提交：表单 vs JSON。"""
import requests

form = requests.post("https://httpbin.org/post", data={"user": "demo", "page": 2}, timeout=10)
print("表单字段:", form.json()["form"])

payload = {"items": [1, 2, 3], "verbose": True}
js = requests.post("https://httpbin.org/post", json=payload, timeout=10)
print("JSON 体:", js.json()["json"])
