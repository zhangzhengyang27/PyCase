"""JSON API 解析：jsonplaceholder 典型列表接口。"""
import requests

resp = requests.get("https://jsonplaceholder.typicode.com/users", timeout=10)
users = resp.json()
for u in users[:5]:
    print(f"{u['id']:>2} {u['name']:<22} {u['email']:<28} {u['address']['city']}")
print("共", len(users), "个用户；第一个公司:", users[0]["company"]["name"])
