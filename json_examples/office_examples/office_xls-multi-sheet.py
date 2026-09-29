"""多 Sheet：按部门拆分工作表。"""
from openpyxl import Workbook

data = [("研发", "张三", 25000), ("市场", "李四", 18000), ("研发", "王五", 27000)]
wb = Workbook()
wb.remove(wb.active)
sheets = {}
for dept, name, salary in data:
    ws = sheets.setdefault(dept, wb.create_sheet(dept))
    if ws["A1"].value is None:
        ws.append(["姓名", "工资"])
    ws.append([name, salary])
wb.save("部门拆分.xlsx")
print("工作表:", wb.sheetnames)
