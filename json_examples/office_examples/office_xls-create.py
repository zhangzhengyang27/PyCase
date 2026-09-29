"""Excel 建表：生成月度销售表。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "销售明细"
ws.append(["日期", "商品", "数量", "金额"])
rows = [["2026-09-01", "键盘", 3, 897.0], ["2026-09-02", "鼠标", 5, 495.0],
        ["2026-09-03", "显示器", 2, 2998.0]]
for r in rows:
    ws.append(r)
wb.save("销售明细.xlsx")
print("已生成 销售明细.xlsx，", ws.max_row - 1, "条记录")
