"""条件格式：超阈值标红。"""
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill

wb = Workbook()
ws = wb.active
ws.append(["项目", "支出"])
for r in [["服务器", 3200], ["差旅", 880], ["外包", 5600], ["培训", 1500]]:
    ws.append(r)
red = PatternFill("solid", fgColor="FFC7CE")
ws.conditional_formatting.add(
    f"B2:B{ws.max_row}",
    CellIsRule(operator="greaterThan", formula=["3000"], fill=red, font=Font(color="9C0006")))
wb.save("支出表.xlsx")
print("超 3000 的行已自动标红")
