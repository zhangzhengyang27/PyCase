"""Word 读取：提取段落与表格。
没有数据？运行时自动生成示例文档 周会纪要.docx 再读取。"""
import os

from docx import Document

SRC = "周会纪要.docx"
if not os.path.exists(SRC):
    doc0 = Document()
    doc0.add_heading("周会纪要", level=1)
    doc0.add_paragraph("日期：2024-03-08    记录人：张三")
    doc0.add_paragraph("一、本周进展")
    doc0.add_paragraph("1. 数据导入模块联调完成，覆盖率 92%。")
    doc0.add_paragraph("2. 报表导出性能优化，耗时下降 40%。")
    doc0.add_paragraph("二、风险与依赖")
    doc0.add_paragraph("1. 第三方接口限流，需要申请配额。")
    doc0.save(SRC)
    print("未找到数据文件：已自动生成示例文档", SRC)

doc = Document(SRC)
print("== 段落 ==")
for p in doc.paragraphs[:6]:
    if p.text.strip():
        print(f"  [{p.style.name}] {p.text[:30]}")
