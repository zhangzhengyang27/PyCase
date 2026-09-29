"""Excel 数据校验：错误行收集报告。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(["日期", "工时", "备注"])
data = [["2026-09-20", 8, ""], ["2026-09-21", 12, "加班"], ["2026-09-22", 0, ""], ["2026-09-23", -2, ""]]
errors = []
for i, (d, h, note) in enumerate(data, start=2):
    if not isinstance(h, (int, float)) or not (0 < h <= 16):
        errors.append(f"第{i}行 工时非法: {h}")
        continue
    ws.append([d, h, note])
wb.save("工时表.xlsx")
print("校验报告:", errors or "全部通过")
