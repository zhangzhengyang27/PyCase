"""库存盘点：期初/入库/出库 三表核算。"""
from collections import defaultdict

opening = {"键盘": 12, "鼠标": 30, "显示器": 5}
inflow = {"键盘": 10, "鼠标": 5}
outflow = {"键盘": 8, "鼠标": 15, "显示器": 2}

stock = defaultdict(int, opening)
for k, v in inflow.items():
    stock[k] += v
for k, v in outflow.items():
    stock[k] -= v
print(f"{'商品':<6}{'期末库存':>8}")
for k in sorted(stock):
    flag = " ⚠️需补货" if stock[k] < 5 else ""
    print(f"{k:<6}{stock[k]:>8}{flag}")
