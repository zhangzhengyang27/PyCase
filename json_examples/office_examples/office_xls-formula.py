"""Excel 公式：SUMIF 与总计行。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(["部门", "金额"])
ws.append(["研发", 25000])
ws.append(["市场", 18000])
ws.append(["研发", 12000])
last = ws.max_row
ws.append(["研发小计", f"=SUMIF(A2:A{last}, \"研发\", B2:B{last})"])
ws.append(["总计", f"=SUM(B2:B{last})"])
wb.save("汇总表.xlsx")
print("公式已写入（用 Excel 打开可见计算结果）")
