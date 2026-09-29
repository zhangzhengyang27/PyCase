"""Excel 去重合并：重复工号只保留首条。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(["工号", "姓名", "电话"])
seen = set()
for sheet_data in [[["E001", "张三", "13800000001"], ["E002", "李四", "13800000002"]],
                   [["E002", "李四", "13900000002"], ["E003", "王五", "13800000003"]]]:
    for row in sheet_data:
        if row[0] in seen:
            continue
        seen.add(row[0])
        ws.append(row)
wb.save("合并去重.xlsx")
print("合并后:", ws.max_row - 1, "条")
