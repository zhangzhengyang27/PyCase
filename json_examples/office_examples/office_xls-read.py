"""Excel 读取：遍历 + 汇总。
没有数据？运行时自动生成示例工作簿 销售明细.xlsx 再读取。"""
import os

from openpyxl import Workbook, load_workbook

SRC = "销售明细.xlsx"
if not os.path.exists(SRC):
    wb0 = Workbook()
    ws0 = wb0.active
    ws0.title = "销售明细"
    ws0.append(["日期", "商品", "数量", "金额"])
    for row in [
        ("2024-01-08", "机械键盘", 2, 399.0),
        ("2024-01-09", "无线鼠标", 3, 129.0),
        ("2024-01-12", "显示器支架", 1, 219.0),
        ("2024-02-03", "USB-C 扩展坞", 2, 259.0),
        ("2024-02-15", "机械键盘", 1, 399.0),
    ]:
        ws0.append(row)
    wb0.save(SRC)
    print("未找到数据文件：已自动生成示例工作簿", SRC)

wb = load_workbook(SRC)
ws = wb["销售明细"]
total = 0.0
for row in ws.iter_rows(min_row=2, values_only=True):
    date, item, qty, amount = row
    print(f"{date} {item} ×{qty} = {amount}")
    total += amount
print("合计金额:", total)
