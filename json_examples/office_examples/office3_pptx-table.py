"""PPT 表格与图片页。"""
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "指标表"
rows, cols = 3, 3
table = slide.shapes.add_table(rows, cols, Inches(1), Inches(2), Inches(8), Inches(2)).table
for c, h in enumerate(["指标", "本周", "上周"]):
    table.cell(0, c).text = h
for r, row in enumerate([["示例数", "3120", "176"], ["测试", "全绿", "全绿"]], 1):
    for c, v in enumerate(row):
        table.cell(r, c).text = str(v)
prs.save("指标汇报.pptx")
print("已生成 指标汇报.pptx")
