"""Excel 读取：遍历 + 汇总。"""
from openpyxl import load_workbook

wb = load_workbook("销售明细.xlsx")
ws = wb["销售明细"]
total = 0.0
for row in ws.iter_rows(min_row=2, values_only=True):
    date, item, qty, amount = row
    print(f"{date} {item} ×{qty} = {amount}")
    total += amount
print("合计金额:", total)
