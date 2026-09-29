"""冻结窗格与自动筛选。"""
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.append(["订单号", "客户", "金额", "状态"])
for i in range(1, 21):
    ws.append([f"SO{i:04d}", f"客户{i}", i * 37.5, "已付" if i % 2 else "未付"])
ws.freeze_panes = "A2"          # 冻结首行
ws.auto_filter.ref = ws.dimensions  # 表头筛选
wb.save("订单表.xlsx")
print("已生成 冻结首行 + 筛选的 订单表.xlsx")
