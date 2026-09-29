"""分页抓取：jsonplaceholder 分页模式。"""
import time
import requests

BASE = "https://jsonplaceholder.typicode.com/posts"
all_items, page, max_page = [], 1, 5
while page <= max_page:
    resp = requests.get(BASE, params={"_page": page, "_limit": 20}, timeout=10)
    items = resp.json()
    if not items:
        print(f"第 {page} 页为空，停止")
        break
    all_items.extend(items)
    print(f"第 {page} 页 +{len(items)}")
    page += 1
    time.sleep(0.3)  # 礼貌延时
print("合计抓取:", len(all_items))
