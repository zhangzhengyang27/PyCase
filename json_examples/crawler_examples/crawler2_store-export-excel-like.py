"""汇总报表：按类目聚合抓取结果。"""
from collections import defaultdict

items = [
    {"cat": "数码", "name": "键盘", "amount": 299},
    {"cat": "数码", "name": "鼠标", "amount": 99},
    {"cat": "图书", "name": "Python Cookbook", "amount": 128},
    {"cat": "图书", "name": "算法图解", "amount": 78},
]
by_cat = defaultdict(list)
for it in items:
    by_cat[it["cat"]].append(it)
print(f"{'类目':<6}{'条数':>4}{'金额合计':>10}")
for cat, rows in by_cat.items():
    total = sum(r["amount"] for r in rows)
    print(f"{cat:<6}{len(rows):>4}{total:>10}")
