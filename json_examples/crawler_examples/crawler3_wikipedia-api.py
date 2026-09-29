"""Wikipedia 摘要接口：词条概要抓取。"""
import requests

resp = requests.get("https://zh.wikipedia.org/api/rest_v1/page/summary/Python",
                    headers={"User-Agent": "learning-demo/1.0"}, timeout=10)
data = resp.json()
print("标题:", data.get("title"))
print("摘要:", (data.get("extract") or "")[:80], "...")
