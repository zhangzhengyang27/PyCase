"""CSV 存储：utf-8-sig 让 Excel 直接打开不乱码。"""
import csv

rows = [
    {"标题": "商品A", "价格": 129.0, "评分": 4.8},
    {"标题": "商品B", "价格": 89.5, "评分": 4.6},
    {"标题": "商品C", "价格": 259.0, "评分": 4.9},
]
with open("crawl_result.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["标题", "价格", "评分"])
    writer.writeheader()
    writer.writerows(rows)
print("已写 crawl_result.csv，", len(rows), "行")
