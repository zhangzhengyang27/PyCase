"""深层嵌套容错：生产爬虫的安全取值习惯。"""
import requests

resp = requests.get("https://jsonplaceholder.typicode.com/users/1", timeout=10)
u = resp.json()
# 链式 get + or 默认值：任何一层缺失都不会抛异常
city = (u.get("address") or {}).get("city") or "未知"
geo = (u.get("address") or {}).get("geo") or {}
lat = geo.get("lat") or "-"
print(f"{u.get('name')} @ {city}（lat={lat}）")
print("不存在字段:", (u.get("profile") or {}).get("wechat") or "<无>")
