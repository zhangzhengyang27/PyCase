"""两表对比：新增与移除名单。"""
from openpyxl import Workbook

old = {"E001": "张三", "E002": "李四", "E003": "王五"}
new = {"E002": "李四", "E003": "王五", "E004": "赵六"}

added = {k: v for k, v in new.items() if k not in old}
removed = {k: v for k, v in old.items() if k not in new}
print("新增:", added)
print("移除:", removed)

wb = Workbook()
ws = wb.active
ws.append(["变更类型", "工号", "姓名"])
for k, v in added.items():
    ws.append(["新增", k, v])
for k, v in removed.items():
    ws.append(["移除", k, v])
wb.save("人员变更.xlsx")
