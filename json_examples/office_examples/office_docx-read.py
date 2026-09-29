"""Word 读取：先跑 docx-create 生成文件，再提取内容。"""
from docx import Document

doc = Document("周会纪要.docx")
print("== 段落 ==")
for p in doc.paragraphs[:6]:
    if p.text.strip():
        print(f"  [{p.style.name}] {p.text[:30]}")
