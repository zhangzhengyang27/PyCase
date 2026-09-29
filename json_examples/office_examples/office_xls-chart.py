"""Excel 图表：月度数据的内嵌柱状图。"""
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference

wb = Workbook()
ws = wb.active
ws.append(["月份", "销售额"])
for m, v in zip(["1月", "2月", "3月", "4月"], [120, 135, 150, 142]):
    ws.append([m, v])
chart = BarChart()
chart.title = "月度销售额"
data = Reference(ws, min_col=2, min_row=1, max_row=5)
cats = Reference(ws, min_col=1, min_row=2, max_row=5)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "D2")
wb.save("月度图表.xlsx")
print("已生成含图表的 月度图表.xlsx")
