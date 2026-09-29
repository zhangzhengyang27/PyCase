"""跨表关联：主表 + 字典表拼接。"""
from openpyxl import Workbook

main = [["E001", "销售", 8000], ["E002", "研发", 12000], ["E003", "市场", 9000]]
lookup = {"E001": "张三", "E002": "李四", "E003": "王五"}
wb = Workbook()
ws = wb.active
ws.append(["工号", "姓名", "部门", "工资"])
for emp_id, dept, salary in main:
    ws.append([emp_id, lookup.get(emp_id, "<未知>"), dept, salary])
wb.save("关联结果.xlsx")
print("关联完成:", ws.max_row - 1, "行")
