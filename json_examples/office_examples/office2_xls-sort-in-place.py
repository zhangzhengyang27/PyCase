"""Excel 排序：按金额降序重写。"""
from openpyxl import Workbook, load_workbook

wb = Workbook()
ws = wb.active
ws.append(["姓名", "分数"])
for r in [["甲", 78], ["乙", 92], ["丙", 85], ["丁", 66]]:
    ws.append(r)
wb.save("成绩原始.xlsx")

rows = list(load_workbook("成绩原始.xlsx").active.iter_rows(min_row=2, values_only=True))
rows.sort(key=lambda r: -r[1])
out = Workbook()
osheet = out.active
osheet.append(["姓名", "分数"])
for r in rows:
    osheet.append(r)
out.save("成绩排序.xlsx")
print("排序完成:", rows)
